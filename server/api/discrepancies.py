from collections import defaultdict
import uuid
from typing import AbstractSet, Iterator, TypedDict
from werkzeug.exceptions import Conflict
from flask import jsonify, request

from sqlalchemy import func
from sqlalchemy.orm import selectinload

from . import api
from ..models import *
from ..auth import restrict_access, UserType
from ..database import db_session
from ..util.get_json import safe_get_json_dict
from ..util.jsonschema import validate
from ..audit_math import macro
from .shared import (
    ContestVoteDeltas,
    ballot_vote_deltas,
    batch_change_in_margin,
    batch_tallies,
    batch_vote_deltas,
    contest_ids_to_audit_in_round,
    cvrs_for_contest,
    get_current_round,
    group_combined_batches,
    with_combined_sub_batches,
    sampled_ballot_interpretations_to_cvrs,
    sampled_batch_results,
)
from .jurisdictions import (
    JurisdictionAuditBoardStatus,
    jurisdiction_audit_board_status,
)


class BatchContestDiscrepancies(TypedDict):
    reportedVotes: macro.ChoiceVotes
    auditedVotes: macro.ChoiceVotes
    hasDiscrepancy: bool
    changeInMargin: int
    numBallots: int
    status: str | None


# Ballot comparison compares CVRs, whose votes are strings: ES&S records an
# overvote as "o" and an undervote as "u"
class BallotContestDiscrepancies(TypedDict):
    reportedVotes: dict[str, str]
    auditedVotes: dict[str, str]
    discrepancies: ContestVoteDeltas


# Keyed by jurisdiction id, then batch name, then contest id
BatchContestDiscrepanciesByJurisdiction = dict[
    str, dict[str, dict[str, BatchContestDiscrepancies]]
]
# Keyed by jurisdiction id, then a readable ballot identifier, then contest id
BallotDiscrepanciesByJurisdiction = dict[
    str, dict[str, dict[str, BallotContestDiscrepancies]]
]


@api.route("/election/<election_id>/discrepancy", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_discrepancies_by_jurisdiction(election: Election):
    current_round = get_current_round(election)
    if not current_round:
        raise Conflict("Audit not started")

    discrepancies_by_jurisdiction: (
        BatchDiscrepanciesByJurisdiction | BallotDiscrepanciesByJurisdiction
    ) = {}

    if election.audit_type == AuditType.BATCH_COMPARISON:
        discrepancies_by_jurisdiction = serialize_batch_discrepancies_by_jurisdiction(
            election, current_round
        )
    elif election.audit_type == AuditType.BALLOT_COMPARISON:
        discrepancies_by_jurisdiction = (
            get_ballot_comparison_discrepancies_by_jurisdiction(election, current_round)
        )
    else:
        raise Conflict(
            "Discrepancies are only implemented for batch and ballot comparison audits"
        )

    return jsonify(discrepancies_by_jurisdiction)


def drawn_batches_in_round(election: Election, round: Round) -> list[Batch]:
    return (
        Batch.query.join(SampledBatchDraw)  # ty: ignore[unsound-return-statement]
        .filter_by(round_id=round.id)
        .join(Jurisdiction)
        .filter_by(election_id=election.id)
        .order_by(func.human_sort(Batch.name))
        .options(
            selectinload(Batch.draws),
            selectinload(Batch.contest_statuses),
            selectinload(Batch.jurisdiction).selectinload(Jurisdiction.contests),
        )
        .all()
    )


# Every batch-contest audited this round, with the contests a batch is still
# audited for after earlier rounds. Statuses sit on a combined batch's
# representative.
def get_batch_comparison_discrepancies_by_jurisdiction(
    election: Election, round: Round
) -> BatchContestDiscrepanciesByJurisdiction:
    discrepancies_by_jurisdiction: BatchContestDiscrepanciesByJurisdiction = (
        defaultdict(lambda: defaultdict(dict))
    )

    # A batch drawn again for a new contest keeps its earlier contests' results
    # on its tally sheet, so only the contests it's audited for this round count
    contest_ids_in_round_by_batch_key: dict[tuple[str, str], set[str]] = {}
    sub_batches_by_batch_key: dict[tuple[str, str], list[Batch]] = {}
    status_by_batch_key: dict[tuple[str, str], dict[str, BatchContestStatus]] = {}
    # A jurisdiction is under review once it has finalized, which gives every
    # batch-contest it audits this round a status; unfinalizing to re-tally
    # keeps the statuses
    jurisdiction_ids_under_review: set[str] = set()
    for batch, sub_batches in batches_with_sub_batches(
        drawn_batches_in_round(election, round)
    ):
        contest_ids = set(contest_ids_to_audit_in_round(round, batch))
        for sub_batch in sub_batches:
            contest_ids_in_round_by_batch_key[
                (sub_batch.jurisdiction.name, sub_batch.name)
            ] = contest_ids
        batch_key = (batch.jurisdiction.name, batch.name)
        sub_batches_by_batch_key[batch_key] = sub_batches
        status_by_batch_key[batch_key] = {
            contest_status.contest_id: contest_status
            for contest_status in batch.contest_statuses
        }
        if contest_ids & status_by_batch_key[batch_key].keys():
            jurisdiction_ids_under_review.add(batch.jurisdiction_id)

    jurisdiction_name_to_id = dict(
        Jurisdiction.query.filter_by(election_id=election.id).with_entities(
            Jurisdiction.name, Jurisdiction.id
        )
    )

    combined_sub_batches = (
        Batch.query.join(Jurisdiction)
        .filter_by(election_id=election.id)
        .filter(Batch.combined_batch_name.isnot(None))
        .all()
    )
    combined_batches = group_combined_batches(combined_sub_batches)

    all_combined_batch_keys = {
        (sub_batch.jurisdiction.name, sub_batch.name)
        for combined_batch in combined_batches
        for sub_batch in combined_batch["sub_batches"]
    }

    representative_batch_to_combined_batch = {
        (
            combined_batch["representative_batch"].jurisdiction.name,
            combined_batch["representative_batch"].name,
        ): combined_batch
        for combined_batch in combined_batches
    }

    show_discrepancies_by_jurisdiction = (
        show_batch_comparison_discrepancies_by_jurisdiction(
            election, round, jurisdiction_ids_under_review
        )
    )

    for contest in list(election.contests):
        audited_batch_results = sampled_batch_results(
            contest, include_non_rla_batches=True
        )
        reported_batch_results = batch_tallies(contest)

        for batch_key, audited_batch_result in audited_batch_results.items():
            jurisdiction_name, batch_name = batch_key
            jurisdiction_id = jurisdiction_name_to_id[jurisdiction_name]
            if not show_discrepancies_by_jurisdiction[jurisdiction_id]:
                continue

            if contest.id not in contest_ids_in_round_by_batch_key.get(
                batch_key, set()
            ):
                continue

            audited_contest_result = audited_batch_result[contest.id]
            reported_contest_result = reported_batch_results[batch_key][contest.id]

            # Special case: for combined batches, only count discrepancies in the representative batch
            combined_batch_name = None
            if batch_key in all_combined_batch_keys:
                if batch_key not in representative_batch_to_combined_batch:
                    continue
                combined_batch = representative_batch_to_combined_batch[batch_key]
                combined_batch_name = combined_batch["name"]
                sub_batches = combined_batch["sub_batches"]
                sub_batch_reported_results = list(
                    sub_batch.jurisdiction.batch_tallies[sub_batch.name].get(contest.id)
                    for sub_batch in sub_batches
                )
                reported_contest_result = {
                    choice.id: sum(
                        reported_results[choice.id]
                        for reported_results in sub_batch_reported_results
                        if reported_results is not None
                    )
                    for choice in contest.choices
                }

            # Once finalized, every audited batch-contest has a status
            contest_status = status_by_batch_key[batch_key].get(contest.id)
            has_discrepancy = (
                batch_vote_deltas(reported_contest_result, audited_contest_result)
                is not None
            )
            if not has_discrepancy and contest_status is None:
                continue

            discrepancies_by_jurisdiction[jurisdiction_id][
                combined_batch_name or batch_name
            ][contest.id] = {
                "reportedVotes": reported_contest_result,
                "auditedVotes": audited_contest_result,
                "hasDiscrepancy": has_discrepancy,
                "changeInMargin": batch_change_in_margin(
                    contest, reported_contest_result, audited_contest_result
                )
                or 0,
                "numBallots": sum(
                    sub_batch.num_ballots_for_contest(contest.id)
                    for sub_batch in sub_batches_by_batch_key[batch_key]
                ),
                "status": contest_status.status if contest_status else None,
            }

    return discrepancies_by_jurisdiction


# Statuses an audit admin still has to act on
OUTSTANDING_STATUSES = {
    BatchDiscrepancyStatus.NEEDS_REVIEW,
    BatchDiscrepancyStatus.JURISDICTION_CONTACTED,
}


# The statuses of a batch's contests audited this round
def contest_statuses_in_round(round: Round, batch: Batch) -> list[BatchContestStatus]:
    contest_ids = set(contest_ids_to_audit_in_round(round, batch))
    return [
        contest_status
        for contest_status in batch.contest_statuses
        if contest_status.contest_id in contest_ids
    ]


# Finalizing judges each batch-contest audited this round by its tallies: a
# discrepancy needs review unless an audit admin accepted it, and matching
# tallies match
def record_batch_results_finalized(
    round: Round,
    batches: list[Batch],
    discrepancies_by_batch_name: dict[str, dict[str, BatchContestDiscrepancies]],
):
    for batch, _ in batches_with_sub_batches(batches):
        name = batch.combined_batch_name or batch.name
        status_by_contest_id: dict[str, BatchContestStatus] = {
            contest_status.contest_id: contest_status
            for contest_status in batch.contest_statuses
        }
        for contest_id in contest_ids_to_audit_in_round(round, batch):
            contest_discrepancies = discrepancies_by_batch_name.get(name, {}).get(
                contest_id
            )
            has_discrepancy = (
                contest_discrepancies is not None
                and contest_discrepancies["hasDiscrepancy"]
            )
            contest_status = status_by_contest_id.get(contest_id)
            if contest_status is None:
                contest_status = BatchContestStatus(contest_id=contest_id)
                batch.contest_statuses.append(contest_status)
            if not has_discrepancy:
                contest_status.status = BatchDiscrepancyStatus.MATCHES  # ty: ignore[invalid-assignment]
            elif contest_status.status != BatchDiscrepancyStatus.ACCEPTED:
                contest_status.status = BatchDiscrepancyStatus.NEEDS_REVIEW  # ty: ignore[invalid-assignment]


# The batch-contests still under review this round, with their batch
def outstanding_contest_statuses(
    round: Round, batches: list[Batch]
) -> Iterator[tuple[Batch, BatchContestStatus]]:
    for batch, _ in batches_with_sub_batches(batches):
        for contest_status in contest_statuses_in_round(round, batch):
            if contest_status.status in OUTSTANDING_STATUSES:
                yield batch, contest_status


# Unfinalizing reopens the batch-contests still under review for re-tallying;
# the rest keep their status until the next finalize judges the tallies again
def record_batch_results_unfinalized(round: Round, batches: list[Batch]):
    for _, contest_status in outstanding_contest_statuses(round, batches):
        contest_status.status = BatchDiscrepancyStatus.RE_TALLYING  # ty: ignore[invalid-assignment]


# In multi-jurisdiction audits, hide discrepancies if the jurisdiction hasn't finalized tallies
# Finalized in the given round or under review in it, or finalized in any round
# when round is None
def show_batch_comparison_discrepancies_by_jurisdiction(
    election: Election,
    round: Round | None,
    jurisdiction_ids_under_review: AbstractSet[str] = frozenset(),
) -> dict[str, bool]:
    jurisdictions = list(election.jurisdictions)
    is_single_jurisdiction_election = len(jurisdictions) == 1
    if is_single_jurisdiction_election:
        jurisidiction_id = jurisdictions[0].id
        return {jurisidiction_id: True}

    finalized = BatchResultsFinalized.query
    if round is not None:
        finalized = finalized.filter_by(round_id=round.id)
    shown_jurisdiction_ids = {
        jurisdiction_id
        for (jurisdiction_id,) in finalized.with_entities(
            BatchResultsFinalized.jurisdiction_id
        )
    } | jurisdiction_ids_under_review

    return {
        jurisdiction.id: (jurisdiction.id in shown_jurisdiction_ids)
        for jurisdiction in jurisdictions
    }


def add_jurisdiction_note(jurisdiction: Jurisdiction, text: str):
    db_session.add(
        JurisdictionNote(
            id=str(uuid.uuid4()), jurisdiction_id=jurisdiction.id, text=text
        )
    )


JURISDICTION_DISCREPANCY_NOTE_SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string", "minLength": 1}},
    "required": ["text"],
    "additionalProperties": False,
}


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/discrepancy-notes",
    methods=["POST"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def create_jurisdiction_note(election: Election, jurisdiction: Jurisdiction):
    note = safe_get_json_dict(request)
    validate(note, JURISDICTION_DISCREPANCY_NOTE_SCHEMA)
    add_jurisdiction_note(jurisdiction, note["text"])
    db_session.commit()

    return jsonify(status="ok")


# Each batch paired with the batches whose tallies it carries: itself, or for
# a combined batch's representative, every sub-batch
def batches_with_sub_batches(batches: list[Batch]) -> list[tuple[Batch, list[Batch]]]:
    batches = with_combined_sub_batches(batches)
    return [
        (batch, [batch]) for batch in batches if batch.combined_batch_name is None
    ] + [
        (combined_batch["representative_batch"], combined_batch["sub_batches"])
        for combined_batch in group_combined_batches(
            [batch for batch in batches if batch.combined_batch_name is not None]
        )
    ]


class BatchDiscrepancies(TypedDict):
    name: str
    isExtra: bool
    discrepancies: dict[str, BatchContestDiscrepancies]


class DiscrepancyNote(TypedDict):
    createdAt: str
    text: str


class JurisdictionDiscrepancies(TypedDict):
    notes: list[DiscrepancyNote]
    batches: dict[str, BatchDiscrepancies]  # Keyed by batch id


# Keyed by jurisdiction id
BatchDiscrepanciesByJurisdiction = dict[str, JurisdictionDiscrepancies]


# Every jurisdiction under review, with its notes and each of its batches with a
# status or a discrepancy. A combined batch is listed once, under its
# representative's id.
def serialize_batch_discrepancies_by_jurisdiction(
    election: Election, round: Round
) -> BatchDiscrepanciesByJurisdiction:
    discrepancies_by_jurisdiction = get_batch_comparison_discrepancies_by_jurisdiction(
        election, round
    )
    batches_with_discrepancies_by_jurisdiction: dict[
        str, dict[str, BatchDiscrepancies]
    ] = defaultdict(dict)
    for batch, sub_batches in batches_with_sub_batches(
        drawn_batches_in_round(election, round)
    ):
        name = batch.combined_batch_name or batch.name
        discrepancies_by_contest = discrepancies_by_jurisdiction.get(
            batch.jurisdiction_id, {}
        ).get(name, {})
        if not discrepancies_by_contest:
            continue
        batches_with_discrepancies_by_jurisdiction[batch.jurisdiction_id][batch.id] = (
            BatchDiscrepancies(
                name=name,
                isExtra=all(
                    draw.ticket_number == EXTRA_TICKET_NUMBER
                    for sub_batch in sub_batches
                    for draw in sub_batch.draws
                    if draw.round_id == round.id
                ),
                discrepancies=discrepancies_by_contest,
            )
        )

    notes_by_jurisdiction: dict[str, list[JurisdictionNote]] = defaultdict(list)
    for note in (
        JurisdictionNote.query.join(Jurisdiction)
        .filter_by(election_id=election.id)
        .order_by(JurisdictionNote.created_at)
    ):
        notes_by_jurisdiction[note.jurisdiction_id].append(note)

    return {
        jurisdiction_id: JurisdictionDiscrepancies(
            notes=[
                DiscrepancyNote(
                    createdAt=note.created_at.isoformat(),
                    text=note.text,
                )
                for note in notes_by_jurisdiction[jurisdiction_id]
            ],
            batches=batches_with_discrepancies_by_jurisdiction[jurisdiction_id],
        )
        for jurisdiction_id in batches_with_discrepancies_by_jurisdiction
    }


def get_ballot_comparison_discrepancies_by_jurisdiction(
    election: Election, round: Round
) -> BallotDiscrepanciesByJurisdiction:
    discrepancies_by_jurisdiction: BallotDiscrepanciesByJurisdiction = defaultdict(
        lambda: defaultdict(dict)
    )

    ballots_in_round = (
        SampledBallot.query.join(SampledBallotDraw)
        .filter_by(round_id=round.id)
        .distinct(SampledBallot.id)
        .with_entities(SampledBallot.id)
        .subquery()
    )
    sampled_ballot_id_to_jurisdiction_id = dict(
        SampledBallot.query.filter(SampledBallot.id.in_(ballots_in_round))
        .join(Batch)
        .with_entities(SampledBallot.id, Batch.jurisdiction_id)
    )
    # make a readable identifier of the same format for all ballots
    # Ex. "Container 0, Tabulator X, Batch Y, Ballot Z" or "Tabulator X, Batch Y, Ballot Z"
    sampled_ballot_id_to_readable_id = dict(
        (
            sampled_ballot_id,
            (f"Container {container}, " if container is not None else "")
            + f"{tabulator}, {batch_name}, Ballot {ballot_position}",
        )
        for sampled_ballot_id, tabulator, batch_name, ballot_position, container in SampledBallot.query.filter(
            SampledBallot.id.in_(ballots_in_round)
        )
        .join(Batch)
        .with_entities(
            SampledBallot.id,
            Batch.tabulator,
            Batch.name,
            SampledBallot.ballot_position,
            Batch.container,
        )
    )

    show_discrepancies_by_jurisdiction = (
        show_ballot_comparison_discrepancies_by_jurisdiction(election, round)
    )

    for contest in election.contests:
        audited_results = sampled_ballot_interpretations_to_cvrs(contest)
        reported_results = cvrs_for_contest(contest)
        for ballot_id, audited_result in audited_results.items():
            if ballot_id not in sampled_ballot_id_to_jurisdiction_id:
                continue
            jurisdiction_id = sampled_ballot_id_to_jurisdiction_id[ballot_id]
            if not show_discrepancies_by_jurisdiction[jurisdiction_id]:
                continue

            audited_cvr = audited_result["cvr"]
            reported_cvr = reported_results.get(ballot_id)
            vote_deltas = ballot_vote_deltas(contest, reported_cvr, audited_cvr)
            if not vote_deltas or isinstance(vote_deltas, str):
                continue

            # CVRs are guaranteed to be non-null due to ballot_vote_deltas() checks
            assert isinstance(audited_cvr, dict)
            audited_votes = audited_cvr.get(contest.id, {})
            assert isinstance(reported_cvr, dict)
            reported_votes = reported_cvr.get(contest.id, {})

            readable_ballot_id = sampled_ballot_id_to_readable_id[ballot_id]
            discrepancies_by_jurisdiction[jurisdiction_id][readable_ballot_id][
                contest.id
            ] = {
                "reportedVotes": reported_votes,
                "auditedVotes": audited_votes,
                "discrepancies": vote_deltas,
            }

    return discrepancies_by_jurisdiction


# In multi-jurisdiction audits, hide discrepancies if the jurisdiction hasn't signed off
def show_ballot_comparison_discrepancies_by_jurisdiction(
    election: Election, round: Round
) -> dict[str, bool]:
    jurisdictions = list(election.jurisdictions)
    is_single_jurisdiction_election = len(jurisdictions) == 1
    if is_single_jurisdiction_election:
        jurisidiction_id = jurisdictions[0].id
        return {jurisidiction_id: True}

    audit_board_status_by_jurisdiction = jurisdiction_audit_board_status(
        jurisdictions, round
    )
    return {
        jurisdiction.id: (
            audit_board_status_by_jurisdiction[jurisdiction.id]
            == JurisdictionAuditBoardStatus.SIGNED_OFF
        )
        for jurisdiction in jurisdictions
    }

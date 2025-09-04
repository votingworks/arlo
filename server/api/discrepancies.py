from collections import defaultdict
from typing import Dict, Union
from werkzeug.exceptions import Conflict
from flask import jsonify

from . import api
from ..models import *
from ..auth import restrict_access, UserType
from .shared import (
    ballot_vote_deltas,
    batch_tallies,
    batch_vote_deltas,
    cvrs_for_contest,
    get_current_round,
    group_combined_batches,
    sampled_ballot_interpretations_to_cvrs,
    sampled_batch_results,
)
from .jurisdictions import (
    JurisdictionAuditBoardStatus,
    jurisdiction_audit_board_status,
)

DiscrepanciesByJurisdiction = Dict[
    str, Dict[str, Dict[str, Dict[str, Union[Dict[str, int], Dict[str, str]]]]]
]
# DiscrepanciesByJurisdiction = {
#     jurisdictionID: {
#         batchName/ballotReadableIdentifier: {
#             contestID: {
#                 reportedVotes:  {choiceID: int/str}, // 8, -1, o, u
#                 auditedVotes:   {choiceID: int/str},
#                 discrepancies:  {choiceID: int/str}, // only int
#     }
# }


@api.route("/election/<election_id>/discrepancy", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_discrepancies_by_jurisdiction(election: Election):
    current_round = get_current_round(election)
    if not current_round:
        raise Conflict("Audit not started")

    discrepancies_by_jurisdiction: DiscrepanciesByJurisdiction = {}

    if election.audit_type == AuditType.BATCH_COMPARISON:
        discrepancies_by_jurisdiction = (
            get_batch_comparison_discrepancies_by_jurisdiction(
                election, current_round.id
            )
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


def get_batch_comparison_discrepancies_by_jurisdiction(
    election: Election, round_id: str
) -> DiscrepanciesByJurisdiction:
    discrepancies_by_jurisdiction: DiscrepanciesByJurisdiction = defaultdict(
        lambda: defaultdict(dict)
    )

    batch_keys_in_round = set(
        SampledBatchDraw.query.filter_by(round_id=round_id)
        .join(Batch)
        .join(Jurisdiction)
        .with_entities(Jurisdiction.name, Batch.name)
        .all()
    )

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
        show_batch_comparison_discrepancies_by_jurisdiction(election)
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

            if batch_key not in batch_keys_in_round:
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
                    sub_batch.jurisdiction.batch_tallies[sub_batch.name].get(contest.id)  # type: ignore
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

            vote_deltas = batch_vote_deltas(
                reported_contest_result, audited_contest_result
            )
            if not vote_deltas:
                continue

            discrepancies_by_jurisdiction[jurisdiction_id][
                combined_batch_name or batch_name
            ][contest.id] = {
                "reportedVotes": reported_contest_result,
                "auditedVotes": audited_contest_result,
                "discrepancies": vote_deltas,
            }

    return discrepancies_by_jurisdiction


# In multi-jurisdiction audits, hide discrepancies if the jurisdiction hasn't finalized tallies
def show_batch_comparison_discrepancies_by_jurisdiction(
    election: Election,
) -> Dict[str, bool]:
    jurisdictions = list(election.jurisdictions)
    is_single_jurisdiction_election = len(jurisdictions) == 1
    if is_single_jurisdiction_election:
        jurisidiction_id = jurisdictions[0].id
        return {jurisidiction_id: True}

    finalized_jurisdiction_ids = {
        jurisdiction_id
        for (jurisdiction_id,) in BatchResultsFinalized.query.with_entities(
            BatchResultsFinalized.jurisdiction_id
        )
    }

    return {
        jurisdiction.id: (jurisdiction.id in finalized_jurisdiction_ids)
        for jurisdiction in jurisdictions
    }


def get_ballot_comparison_discrepancies_by_jurisdiction(
    election: Election, round: Round
) -> DiscrepanciesByJurisdiction:
    discrepancies_by_jurisdiction: DiscrepanciesByJurisdiction = defaultdict(
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
) -> Dict[str, bool]:
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

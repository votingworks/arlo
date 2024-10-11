import uuid
from typing import (
    List,
    Tuple,
    Dict,
)
from datetime import datetime
from flask import jsonify, request
from jsonschema import validate
from werkzeug.exceptions import BadRequest, Conflict
from sqlalchemy import and_, func, not_


from . import api
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from .shared import (
    BallotDraw,
    SampleSize,
    active_targeted_contests,
    batch_tallies,
    compute_sample_ballots,
    compute_sample_batches,
    contest_results_by_round,
    cvrs_for_contest,
    full_hand_tally_sizes,
    get_current_round,
    get_previous_round,
    hybrid_contest_strata,
    is_full_hand_tally,
    needs_full_hand_tally,
    round_sizes,
    sampled_ballot_interpretations_to_cvrs,
    sampled_batch_results,
    sampled_batches_by_ticket_number,
    samples_not_found_by_round,
)
from ..auth import restrict_access, UserType
from ..util.isoformat import isoformat
from ..util.collections import group_by
from ..audit_math import (
    ballot_polling,
    macro,
    supersimple,
    sampler_contest,
    suite,
)
from .ballot_manifest import hybrid_contest_total_ballots
from ..worker.tasks import (
    background_task,
    create_background_task,
    serialize_background_task,
)
from ..activity_log import (
    record_activity,
    activity_base,
    StartRound,
    EndRound,
)
from ..feature_flags import is_enabled_automatically_end_audit_after_one_round
from ..util.get_json import safe_get_json_dict


def is_round_ready_to_finish(election: Election, round: Round) -> bool:
    # For batch audits, check that all jurisdictions with sampled batches this
    # round have finalized batch results
    if election.audit_type == AuditType.BATCH_COMPARISON:
        num_jurisdictions_not_finalized: int = (
            Jurisdiction.query.filter_by(election_id=election.id)
            .filter(
                Jurisdiction.id.in_(
                    SampledBatchDraw.query.filter_by(round_id=round.id)
                    .join(Batch)
                    .with_entities(Batch.jurisdiction_id)
                    .subquery()
                )
            )
            .filter(
                Jurisdiction.id.notin_(
                    BatchResultsFinalized.query.filter_by(round_id=round.id)
                    .with_entities(BatchResultsFinalized.jurisdiction_id)
                    .subquery()
                )
            )
            .with_entities(Jurisdiction.id)
            .count()
        )
        return num_jurisdictions_not_finalized == 0

    # For online audits, check that all the audit boards are finished auditing
    if election.online:
        num_jurisdictions_without_audit_boards_set_up: int = (
            # For each jurisdiction...
            Jurisdiction.query.filter_by(election_id=election.id)
            # Where there are ballots that haven't been audited...
            .join(Jurisdiction.batches)
            .join(Batch.ballots)
            .filter(SampledBallot.status == BallotStatus.NOT_AUDITED)
            # And those ballots got sampled this round...
            .join(SampledBallot.draws)
            .filter_by(round_id=round.id)
            # Count the number of audit boards set up.
            .outerjoin(
                AuditBoard,
                and_(
                    AuditBoard.jurisdiction_id == Jurisdiction.id,
                    AuditBoard.round_id == round.id,
                ),
            )
            .group_by(Jurisdiction.id)
            # Finally, count how many jurisdictions have no audit boards set up.
            .having(func.count(AuditBoard.id) == 0)
            .count()
        )
        num_audit_boards_with_ballots_not_signed_off: int = (
            AuditBoard.query.filter_by(round_id=round.id, signed_off_at=None)
            .join(SampledBallot)
            .group_by(AuditBoard.id)
            .count()
        )
        return (
            num_jurisdictions_without_audit_boards_set_up == 0
            and num_audit_boards_with_ballots_not_signed_off == 0
        )

    # For offline audits, check that we have results recorded for every
    # jurisdiction that had ballots sampled
    else:
        num_jurisdictions_without_results: int
        # Special case: if we are in a full hand tally, we just check every
        # jurisdiction in the targeted contest's universe
        if is_full_hand_tally(round, election):
            num_jurisdictions_without_results = (
                Contest.query.filter_by(election_id=election.id, is_targeted=True)
                .join(Contest.jurisdictions)
                .outerjoin(
                    JurisdictionResult,
                    and_(
                        JurisdictionResult.jurisdiction_id == Jurisdiction.id,
                        JurisdictionResult.contest_id == Contest.id,
                        JurisdictionResult.round_id == round.id,
                    ),
                )
                .group_by(Jurisdiction.id, Contest.id)
                .having(func.count(JurisdictionResult.result) == 0)
                .count()
            )
        else:
            num_jurisdictions_without_results = (
                # For each jurisdiction...
                Jurisdiction.query.filter_by(election_id=election.id)
                # Where ballots were sampled...
                .join(Jurisdiction.batches)
                .join(Batch.ballots)
                # And those ballots were sampled this round...
                .join(SampledBallot.draws)
                .filter_by(round_id=round.id)
                .join(SampledBallotDraw.contest)
                # Count the number of results recorded for each contest.
                .outerjoin(
                    JurisdictionResult,
                    and_(
                        JurisdictionResult.jurisdiction_id == Jurisdiction.id,
                        JurisdictionResult.contest_id == Contest.id,
                        JurisdictionResult.round_id == round.id,
                    ),
                )
                # Finally, count the number of jurisdiction/contest pairs for which
                # there is no result recorded
                .group_by(Jurisdiction.id, Contest.id)
                .having(func.count(JurisdictionResult.result) == 0)
                .count()
            )
        return num_jurisdictions_without_results == 0


def is_audit_complete(round: Round):
    if not round.ended_at:
        return None
    if is_enabled_automatically_end_audit_after_one_round(round.election):
        return True
    targeted_round_contests = (
        RoundContest.query.filter_by(round_id=round.id)
        .join(Contest)
        .filter_by(is_targeted=True)
        .all()
    )
    return all(c.is_complete for c in targeted_round_contests)


def count_audited_votes(election: Election, round: Round):
    for round_contest in round.round_contests:
        contest = round_contest.contest

        # For batch audits, count the votes for each audited Batch
        if election.audit_type == AuditType.BATCH_COMPARISON:
            vote_counts = dict(
                BatchResult.query.filter(
                    BatchResult.tally_sheet_id.in_(
                        BatchResultTallySheet.query.join(Batch)
                        .join(SampledBatchDraw)
                        # Special case: don't include extra sampled batches
                        .filter(SampledBatchDraw.ticket_number != EXTRA_TICKET_NUMBER)
                        .filter_by(round_id=round.id)
                        .with_entities(BatchResultTallySheet.id)
                        .subquery()
                    )
                )
                .group_by(BatchResult.contest_choice_id)
                .values(BatchResult.contest_choice_id, func.sum(BatchResult.result))
            )

        # Otherwise, handle ballot polling, ballot comparison, and hybrid
        # audits. Note that we will only actually use these vote counts in the
        # p-value calculation for ballot polling audits and hybrid audits (just
        # counting the non-CVR ballot segment). In ballot comparison, we just
        # show these totals for the audit report.
        else:
            # For online audits, count the votes from each BallotInterpretation
            if election.online:
                interpretations_query = (
                    BallotInterpretation.query.filter_by(
                        contest_id=contest.id,
                        is_overvote=False,
                        interpretation=Interpretation.VOTE,
                    )
                    .join(SampledBallot)
                    .join(SampledBallotDraw)
                    .filter_by(round_id=round.id)
                    .join(BallotInterpretation.selected_choices)
                    .group_by(ContestChoice.id)
                )

                # For hybrid audits, only count the non-CVR ballots
                if election.audit_type == AuditType.HYBRID:
                    interpretations_query = interpretations_query.join(Batch).filter_by(
                        has_cvrs=False
                    )

                # For a targeted contest, count the ballot draws sampled for the contest
                if contest.is_targeted:
                    vote_counts = dict(
                        interpretations_query.filter(
                            SampledBallotDraw.contest_id == contest.id
                        ).values(ContestChoice.id, func.count())
                    )
                # For an opportunistic contest, count the unique ballots that were
                # audited for this contest, regardless of which contest they were
                # sampled for.
                else:
                    vote_counts = dict(
                        interpretations_query.values(
                            ContestChoice.id, func.count(SampledBallot.id.distinct())
                        )
                    )

            # For offline audits, sum the JurisdictionResults
            else:
                assert election.audit_type == AuditType.BALLOT_POLLING
                vote_counts = dict(
                    JurisdictionResult.query.filter_by(
                        round_id=round.id,
                        contest_id=contest.id,
                    )
                    .group_by(JurisdictionResult.contest_choice_id)
                    .values(
                        JurisdictionResult.contest_choice_id,
                        func.sum(JurisdictionResult.result),
                    )
                )

        for contest_choice in contest.choices:
            result = RoundContestResult(
                round_id=round.id,
                contest_id=contest.id,
                contest_choice_id=contest_choice.id,
                result=vote_counts.get(contest_choice.id, 0),
            )
            db_session.add(result)


def calculate_risk_measurements(election: Election, round: Round):
    assert election.risk_limit is not None

    for round_contest in round.round_contests:
        contest = round_contest.contest

        if election.audit_type == AuditType.BALLOT_POLLING:
            assert election.audit_math_type is not None
            p_values, is_complete = ballot_polling.compute_risk(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                contest_results_by_round(contest) or {},
                samples_not_found_by_round(contest),
                AuditMathType(election.audit_math_type),
                round_sizes(contest),
            )
            p_value = max(p_values.values())
        elif election.audit_type == AuditType.BATCH_COMPARISON:
            p_value, is_complete = macro.compute_risk(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                batch_tallies(contest),
                sampled_batch_results(contest),
                sampled_batches_by_ticket_number(contest),
            )
        elif election.audit_type == AuditType.BALLOT_COMPARISON:
            p_value, is_complete = supersimple.compute_risk(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                cvrs_for_contest(contest),
                sampled_ballot_interpretations_to_cvrs(contest),
            )
        else:
            assert election.audit_type == AuditType.HYBRID
            non_cvr_stratum, cvr_stratum = hybrid_contest_strata(contest)
            p_value, is_complete = suite.compute_risk(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                non_cvr_stratum,
                cvr_stratum,
            )

        round_contest.end_p_value = p_value
        round_contest.is_complete = is_complete


@background_task
def draw_sample(round_id: str, election_id: str):
    round = Round.query.filter_by(id=round_id, election_id=election_id).one()
    election = round.election

    contest_sample_sizes = [
        (round_contest.contest, round_contest.sample_size)
        for round_contest in round.round_contests
        if round_contest.sample_size
    ]

    # Special case: if we are in a full hand tally, we don't need to actually
    # draw a sample. Instead, we force an offline audit.
    if is_full_hand_tally(round, election):
        election.online = False
        return

    if election.audit_type == AuditType.BATCH_COMPARISON:
        draw_sample_batches(election, round, contest_sample_sizes)
    elif election.audit_type in [AuditType.BALLOT_POLLING, AuditType.BALLOT_COMPARISON]:
        draw_sample_ballots(election, round, contest_sample_sizes)
    else:
        assert election.audit_type == AuditType.HYBRID
        draw_sample_ballots(election, round, contest_sample_sizes, filter_has_cvrs=True)
        draw_sample_ballots(
            election, round, contest_sample_sizes, filter_has_cvrs=False
        )


def draw_sample_batches(
    election: Election,
    round: Round,
    contest_sample_sizes: List[Tuple[Contest, SampleSize]],
):
    sample = compute_sample_batches(election, round.round_num, contest_sample_sizes)
    for batch_draw in sample:
        sampled_batch_draw = SampledBatchDraw(
            batch_id=batch_draw["batch_id"],
            round_id=round.id,
            contest_id=batch_draw["contest_id"],
            ticket_number=batch_draw["ticket_number"],
        )
        db_session.add(sampled_batch_draw)


def draw_sample_ballots(
    election: Election,
    round: Round,
    contest_sample_sizes: List[Tuple[Contest, SampleSize]],
    # For hybrid audits only, Batch.has_cvrs will be true/false if the batch
    # contains ballots with CVRs or not (based on the manifest).
    # filter_has_cvrs will constrain the ballots to sample based on
    # Batch.has_cvrs. Since Batch.has_cvrs is None for all other audit types,
    # the default filter is None.
    filter_has_cvrs: bool = None,
):
    sample = compute_sample_ballots(election, contest_sample_sizes, filter_has_cvrs)

    # Group all sample draws by ballot
    sample_draws_by_ballot: Dict[Tuple[str, int], List[BallotDraw]] = group_by(
        sample,
        key=lambda sample_draw: (
            sample_draw["batch_id"],
            sample_draw["ballot_position"],
        ),
    )

    # Record which ballots are sampled in the db.
    # Note that a ballot may be sampled more than once (within a round or
    # across multiple rounds). We create one SampledBallot for each real-world
    # ballot that gets sampled, and record each time it gets sampled with a
    # SampledBallotDraw. That way we can ensure that we don't need to actually
    # look at a real-world ballot that we've already audited, even if it gets
    # sampled again.
    for ballot_key, sample_draws in sample_draws_by_ballot.items():
        batch_id, ballot_position = ballot_key

        sampled_ballot = SampledBallot.query.filter_by(
            batch_id=batch_id, ballot_position=ballot_position
        ).first()
        if not sampled_ballot:
            sampled_ballot = SampledBallot(
                id=str(uuid.uuid4()),
                batch_id=batch_id,
                ballot_position=ballot_position,
                status=BallotStatus.NOT_AUDITED,
            )
            db_session.add(sampled_ballot)

        for sample_draw in sample_draws:
            sampled_ballot_draw = SampledBallotDraw(
                ballot_id=sampled_ballot.id,
                round_id=round.id,
                contest_id=sample_draw["contest_id"],
                ticket_number=sample_draw["ticket_number"],
            )
            db_session.add(sampled_ballot_draw)


def create_selected_sample_sizes_schema(audit_type: AuditType):
    return {
        "type": "object",
        "patternProperties": {
            "^.*$": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "prob": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    **(
                        {
                            "sizeCvr": {"type": "integer"},
                            "sizeNonCvr": {"type": "integer"},
                            "size": {"type": "integer"},
                        }
                        if audit_type == AuditType.HYBRID
                        else {"size": {"type": "integer"}}
                    ),
                },
                "additionalProperties": False,
                "required": (
                    ["sizeCvr", "sizeNonCvr", "size", "key", "prob"]
                    if audit_type == AuditType.HYBRID
                    else ["size", "key", "prob"]
                ),
            }
        },
    }


def create_round_schema(audit_type: AuditType):
    return {
        "type": "object",
        "properties": {
            "roundNum": {"type": "integer", "minimum": 1},
            "sampleSizes": create_selected_sample_sizes_schema(audit_type),
        },
        "additionalProperties": False,
        "required": ["roundNum", "sampleSizes"],
    }


# Raises if invalid
def validate_round(round: dict, election: Election):
    validate(round, create_round_schema(AuditType(election.audit_type)))

    current_round = get_current_round(election)
    next_round_num = current_round.round_num + 1 if current_round else 1
    if round["roundNum"] != next_round_num:
        raise BadRequest(f"The next round should be round number {next_round_num}")

    if current_round and not current_round.ended_at:
        raise Conflict("The current round is not complete")


def validate_sample_size(round: dict, election: Election):
    targeted_contests = active_targeted_contests(election)
    if set(round["sampleSizes"].keys()) != {c.id for c in targeted_contests}:
        raise BadRequest("Sample sizes provided do not match targeted contest ids")

    full_hand_tally_size = full_hand_tally_sizes(election)

    for contest in targeted_contests:
        sample_size = round["sampleSizes"][contest.id]
        valid_keys = {
            AuditType.BALLOT_POLLING: (
                ["asn", "0.9", "0.8", "0.7", "custom", "all-ballots"]
            ),
            AuditType.BALLOT_COMPARISON: ["supersimple", "custom"],
            AuditType.BATCH_COMPARISON: ["macro", "custom"],
            AuditType.HYBRID: ["suite", "custom"],
        }[AuditType(election.audit_type)]

        if sample_size["key"] not in valid_keys:
            raise BadRequest(
                f"Invalid sample size key for contest {contest.name}: {sample_size['key']}"
            )

        if sample_size["key"] == "custom":
            if election.audit_type == AuditType.HYBRID:
                total_ballots = hybrid_contest_total_ballots(contest)
                assert (
                    sample_size["sizeCvr"] + sample_size["sizeNonCvr"]
                    == sample_size["size"]
                )
                if sample_size["sizeCvr"] > total_ballots.cvr:
                    raise BadRequest(
                        f"CVR sample size for contest {contest.name} must be less than or equal to:"
                        f" {total_ballots.cvr} (the total number of CVR ballots in the contest)"
                    )
                if sample_size["sizeNonCvr"] > total_ballots.non_cvr:
                    raise BadRequest(
                        f"Non-CVR sample size for contest {contest.name} must be less than or equal to:"
                        f" {total_ballots.non_cvr} (the total number of non-CVR ballots in the contest)"
                    )

            elif sample_size["size"] > full_hand_tally_size[contest.id]:
                ballots_or_batches = (
                    "batches"
                    if election.audit_type == AuditType.BATCH_COMPARISON
                    else "ballots"
                )
                raise BadRequest(
                    f"Sample size for contest {contest.name} must be less than or equal to:"
                    f" {full_hand_tally_size[contest.id]} (the total number of {ballots_or_batches} in the contest)"
                )

        if sample_size["size"] >= full_hand_tally_size[contest.id]:
            if election.audit_type not in [
                AuditType.BALLOT_POLLING,
                AuditType.BATCH_COMPARISON,
            ]:
                raise BadRequest(
                    "For a full hand tally, use the ballot polling or batch comparison audit type."
                )
            if len(targeted_contests) > 1:
                raise BadRequest("For a full hand tally, use only one target contest.")


def delete_round_and_corresponding_sampled_ballots(round: Round):
    db_session.delete(round)

    # Delete any sampled ballots that were created this round (they will have no associated
    # SampledBallotDraws since they are deleted by cascade when deleting the round)
    SampledBallot.query.filter(
        SampledBallot.id.in_(
            SampledBallot.query.join(Batch)
            .join(Jurisdiction)
            .filter_by(election_id=round.election_id)
            .filter(not_(SampledBallot.draws.any()))
            .with_entities(SampledBallot.id)
            .subquery()
        )
    ).with_entities(SampledBallot).delete(synchronize_session=False)

    db_session.commit()


@api.route("/election/<election_id>/round", methods=["POST"])
@restrict_access([UserType.AUDIT_ADMIN])
def create_round(election: Election):
    json_round = safe_get_json_dict(request)
    validate_round(json_round, election)

    round = Round(
        id=str(uuid.uuid4()),
        election_id=election.id,
        round_num=json_round["roundNum"],
    )
    db_session.add(round)

    # For round 1, use the given sample size for each contest. In later rounds,
    # we'll select a sample size automatically when drawing the sample.
    validate_sample_size(json_round, election)

    # Figure out which contests still need auditing
    previous_round = get_previous_round(election, round)
    contests_that_havent_met_risk_limit = (
        [
            round_contest.contest
            for round_contest in previous_round.round_contests
            if not round_contest.is_complete
        ]
        if previous_round
        else election.contests
    )

    # Create RoundContest objects to include the contests in this round
    round.round_contests = [
        RoundContest(
            round=round,
            contest=contest,
            sample_size=json_round["sampleSizes"].get(contest.id, None),
        )
        for contest in contests_that_havent_met_risk_limit
    ]

    # Create a new task to draw the sample in the background.
    round.draw_sample_task = create_background_task(
        draw_sample,
        dict(election_id=election.id, round_id=round.id),
    )

    record_activity(
        StartRound(
            timestamp=round.created_at,
            base=activity_base(election),
            round_num=round.round_num,
        )
    )

    db_session.commit()

    return jsonify({"status": "ok"})


@api.route("/election/<election_id>/round/current/finish", methods=["POST"])
@restrict_access([UserType.AUDIT_ADMIN])
def finish_round(election: Election):
    current_round = get_current_round(election)
    if not current_round:
        raise Conflict("Audit not started")
    if not is_round_ready_to_finish(election, current_round):
        raise Conflict("Auditing is still in progress")
    if current_round.ended_at:
        raise Conflict("Round already finished")

    count_audited_votes(election, current_round)
    calculate_risk_measurements(election, current_round)
    current_round.ended_at = datetime.now(timezone.utc)

    db_session.flush()  # Ensure round contest results are queryable by is_audit_complete
    record_activity(
        EndRound(
            timestamp=current_round.ended_at,
            base=activity_base(election),
            round_num=current_round.round_num,
            is_audit_complete=is_audit_complete(current_round),
        )
    )

    db_session.commit()

    return jsonify(status="ok")


def serialize_round(round: Round) -> dict:
    return {
        "id": round.id,
        "roundNum": round.round_num,
        "startedAt": isoformat(round.created_at),
        "endedAt": isoformat(round.ended_at),
        "isAuditComplete": is_audit_complete(round),
        "needsFullHandTally": needs_full_hand_tally(round, round.election),
        "isFullHandTally": is_full_hand_tally(round, round.election),
        "drawSampleTask": serialize_background_task(round.draw_sample_task),
    }


@api.route("/election/<election_id>/round", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def list_rounds_audit_admin(election: Election):
    return jsonify({"rounds": [serialize_round(r) for r in election.rounds]})


# Make a separate endpoint for jurisdiction admins to access the list of
# rounds. This makes our permission scheme simpler (every route only allows one
# user type), even though the logic of this particular pair our routes is
# identical.
@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round", methods=["GET"]
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def list_rounds_jurisdiction_admin(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    return jsonify({"rounds": [serialize_round(r) for r in election.rounds]})


@api.route("/election/<election_id>/round/current", methods=["DELETE"])
@restrict_access([UserType.AUDIT_ADMIN])
def undo_round_start(election: Election):
    current_round = get_current_round(election)
    if not current_round:
        raise Conflict("Audit not started")

    if len(list(current_round.audit_boards)) > 0:
        raise Conflict(
            "Cannot undo starting this round because some jurisdictions have already created audit boards."
        )

    delete_round_and_corresponding_sampled_ballots(current_round)

    return jsonify(status="ok")

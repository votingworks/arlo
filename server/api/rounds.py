import uuid
from collections import defaultdict
from typing import Optional, NamedTuple, List, Tuple, Dict, cast as typing_cast
from datetime import datetime
from flask import jsonify, request
from jsonschema import validate
from werkzeug.exceptions import BadRequest, Conflict
from sqlalchemy import and_

from . import api
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..auth import with_election_access, with_jurisdiction_access
from . import sample_sizes as sample_sizes_module
from ..util.isoformat import isoformat
from ..util.group_by import group_by
from ..audit_math import sampler, bravo, macro, sampler_contest


def get_current_round(election: Election) -> Optional[Round]:
    if len(list(election.rounds)) == 0:
        return None
    return max(election.rounds, key=lambda r: r.round_num)


def get_previous_round(election: Election, round: Round) -> Optional[Round]:
    if round.round_num == 1:
        return None
    return next(r for r in election.rounds if r.round_num == round.round_num - 1)


def is_audit_complete(round: Round):
    if not round.ended_at:
        return None
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

        # For batch audits, count the votes from each BatchResult
        if election.audit_type == AuditType.BATCH_COMPARISON:
            vote_counts = dict(
                BatchResult.query.join(
                    SampledBatchDraw, BatchResult.batch_id == SampledBatchDraw.batch_id
                )
                .filter_by(round_id=round.id)
                .group_by(BatchResult.contest_choice_id)
                .values(BatchResult.contest_choice_id, func.sum(BatchResult.result),)
            )

        # For ballot polling audits...
        else:
            # For online audits, count the votes from each BallotInterpretation
            if election.online:
                interpretations_query = (
                    BallotInterpretation.query.filter_by(
                        contest_id=contest.id, is_overvote=False
                    )
                    .join(SampledBallot)
                    .join(SampledBallotDraw)
                    .filter_by(round_id=round.id)
                    .join(BallotInterpretation.selected_choices)
                    .group_by(ContestChoice.id)
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
                vote_counts = dict(
                    JurisdictionResult.query.filter_by(
                        round_id=round.id, contest_id=contest.id,
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


# Sum the audit results for each contest choice from all rounds so far
def cumulative_contest_results(contest: Contest) -> Dict[str, int]:
    results_by_choice: Dict[str, int] = defaultdict(int)
    for result in contest.results:
        results_by_choice[result.contest_choice_id] += result.result
    return results_by_choice


# { batch_key: { contest_id: { choice_id: votes }}}
BatchTallies = Dict[Tuple[str, str], Dict[str, Dict[str, int]]]


def batch_tallies(election: Election) -> BatchTallies:
    # We only support one contest for batch audits
    contest = list(election.contests)[0]

    # Validate the batch tallies files. We can't do this validation when they
    # are uploaded because we need all of the jurisdictions' files.
    total_votes_by_choice: Dict[str, int] = defaultdict(int)
    for jurisdiction in contest.jurisdictions:
        batch_tallies = typing_cast(BatchTallies, jurisdiction.batch_tallies)
        if batch_tallies is None:
            raise Conflict(
                "Some jurisdictions haven't uploaded their batch tallies files yet."
            )
        for tally in batch_tallies.values():
            for choice_id, votes in tally[contest.id].items():
                total_votes_by_choice[choice_id] += votes

    for choice in contest.choices:
        if total_votes_by_choice[choice.id] > choice.num_votes:
            raise Conflict(
                f"Total votes in batch tallies files for contest choice {choice.name}"
                f" ({total_votes_by_choice[choice.id]}) is greater than the"
                f" reported number of votes for that choice ({choice.num_votes})."
            )

    # Key each batch by jurisdiction name and batch name since batch names
    # are only guaranteed unique within a jurisdiction
    return {
        (jurisdiction.name, batch_name): tally
        for jurisdiction in contest.jurisdictions
        for batch_name, tally in jurisdiction.batch_tallies.items()  # type: ignore
    }


def cumulative_batch_results(election: Election) -> BatchTallies:
    results_by_batch_and_choice = (
        Batch.query.join(Jurisdiction)
        .filter_by(election_id=election.id)
        .join(SampledBatchDraw)
        .join(Jurisdiction.contests)
        .join(ContestChoice)
        .outerjoin(
            BatchResult,
            and_(
                BatchResult.batch_id == Batch.id,
                BatchResult.contest_choice_id == ContestChoice.id,
            ),
        )
        .group_by(Jurisdiction.id, Batch.id, ContestChoice.id)
        .values(
            Jurisdiction.name,
            Batch.name,
            ContestChoice.id,
            func.coalesce(func.sum(BatchResult.result), 0),
        )
    )
    results_by_batch = group_by(
        results_by_batch_and_choice,
        key=lambda result: (result[0], result[1]),  # (jurisdiction_name, batch_name)
    )
    # We only support one contest for batch audits
    contest_id = list(election.contests)[0].id
    return {
        batch_key: {
            contest_id: {
                choice_id: result for (_, _, choice_id, result) in batch_results
            }
        }
        for batch_key, batch_results in results_by_batch.items()
    }


def calculate_risk_measurements(election: Election, round: Round):
    if not election.risk_limit:  # Shouldn't happen, we need this for typechecking
        raise Exception("Risk limit not defined")  # pragma: no cover
    risk_limit: int = election.risk_limit

    for round_contest in round.round_contests:
        contest = round_contest.contest

        if election.audit_type == AuditType.BALLOT_POLLING:
            p_values, is_complete = bravo.compute_risk(
                float(risk_limit) / 100,
                sampler_contest.from_db_contest(contest),
                cumulative_contest_results(contest),
            )
            p_value = max(p_values.values())
        else:
            p_value, is_complete = macro.compute_risk(
                float(risk_limit) / 100,
                sampler_contest.from_db_contest(contest),
                batch_tallies(election),
                cumulative_batch_results(election),
            )

        round_contest.end_p_value = p_value
        round_contest.is_complete = is_complete


def end_round(election: Election, round: Round):
    count_audited_votes(election, round)
    calculate_risk_measurements(election, round)
    round.ended_at = datetime.utcnow()


def is_round_complete(election: Election, round: Round) -> bool:
    # For batch audits, check that all sampled batches have recorded results
    if election.audit_type == AuditType.BATCH_COMPARISON:
        num_batches_without_results: int = (
            Batch.query.join(SampledBatchDraw)
            .filter_by(round_id=round.id)
            .outerjoin(BatchResult)
            .group_by(Batch.id)
            .having(func.count(BatchResult.batch_id) == 0)
            .count()
        )
        return num_batches_without_results == 0

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
        num_jurisdictions_without_results: int = (
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


class BallotDraw(NamedTuple):
    # ballot_key: ((jurisdiction name, batch name), ballot_position)
    ballot_key: Tuple[Tuple[str, str], int]
    contest_id: str
    ticket_number: str


def draw_sample(election: Election, round: Round, sample_sizes: Dict[str, int]):
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
    for contest in contests_that_havent_met_risk_limit:
        round_contest = RoundContest(
            round_id=round.id,
            contest_id=contest.id,
            # Store the sample size we use for each contest so we can report on
            # it later. Opportunistic contests don't have a sample size, so we
            # store None.
            sample_size=sample_sizes.get(contest.id, None),
        )
        db_session.add(round_contest)

    contests_to_sample = [
        contest
        for contest in contests_that_havent_met_risk_limit
        if contest.is_targeted
    ]

    if election.audit_type == AuditType.BALLOT_POLLING:
        return sample_ballots(election, round, contests_to_sample, sample_sizes)
    else:
        return sample_batches(election, round, contests_to_sample, sample_sizes)


def sample_ballots(
    election: Election,
    round: Round,
    contests: List[Contest],
    sample_sizes: Dict[str, int],
):
    def draw_sample_for_contest(contest: Contest, sample_size: int) -> List[BallotDraw]:
        # Compute the total number of ballot samples in all rounds leading up to
        # this one. Note that this corresponds to the number of SampledBallotDraws,
        # not SampledBallots.
        num_previously_sampled = SampledBallotDraw.query.filter_by(
            contest_id=contest.id
        ).count()

        # Create the pool of ballots to sample (aka manifest) by combining the
        # manifests from every jurisdiction in the contest's universe.
        # Audits must be deterministic and repeatable for the same real world
        # inputs. So the sampler expects the same input for the same real world
        # data. Thus, we use the jurisdiction and batch names (deterministic real
        # world ids) instead of the jurisdiction and batch ids (non-deterministic
        # uuids that we generate for each audit).
        manifest = {
            (jurisdiction.name, batch.name): batch.num_ballots
            for jurisdiction in contest.jurisdictions
            for batch in jurisdiction.batches
        }

        # Do the math! i.e. compute the actual sample
        sample = sampler.draw_sample(
            str(election.random_seed), manifest, sample_size, num_previously_sampled
        )
        return [
            BallotDraw(
                ballot_key=ballot_key,
                contest_id=contest.id,
                ticket_number=ticket_number,
            )
            for (ticket_number, ballot_key, _) in sample
        ]

    # Draw a sample for each targeted contest
    samples = [
        draw_sample_for_contest(contest, sample_sizes[contest.id])
        for contest in contests
    ]

    # Group all sample draws by ballot
    sample_draws_by_ballot = group_by(
        [sample_draw for sample in samples for sample_draw in sample],
        key=lambda sample_draw: sample_draw.ballot_key,
    )

    # Create a mapping from batch keys used in the sampling back to batch ids
    batches = (
        Batch.query.join(Jurisdiction)
        .filter_by(election_id=election.id)
        .values(Jurisdiction.name, Batch.name, Batch.id)
    )
    batch_key_to_id = {
        (jurisdiction_name, batch_name): batch_id
        for jurisdiction_name, batch_name, batch_id in batches
    }

    # Record which ballots are sampled in the db.
    # Note that a ballot may be sampled more than once (within a round or
    # across multiple rounds). We create one SampledBallot for each real-world
    # ballot that gets sampled, and record each time it gets sampled with a
    # SampledBallotDraw. That way we can ensure that we don't need to actually
    # look at a real-world ballot that we've already audited, even if it gets
    # sampled again.
    for ballot_key, sample_draws in sample_draws_by_ballot.items():
        batch_key, ballot_position = ballot_key
        batch_id = batch_key_to_id[batch_key]

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
                contest_id=sample_draw.contest_id,
                ticket_number=sample_draw.ticket_number,
            )
            db_session.add(sampled_ballot_draw)


def sample_batches(
    election: Election,
    round: Round,
    contests: List[Contest],
    sample_sizes: Dict[str, int],
):
    # We currently only support one contest for batch audits
    contest = contests[0]

    num_previously_sampled = (
        SampledBatchDraw.query.join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election.id)
        .count()
    )

    # Create a mapping from batch keys used in the sampling back to batch ids
    batches = (
        Batch.query.join(Jurisdiction)
        .filter_by(election_id=election.id)
        .values(Jurisdiction.name, Batch.name, Batch.id)
    )
    batch_key_to_id = {
        (jurisdiction_name, batch_name): batch_id
        for jurisdiction_name, batch_name, batch_id in batches
    }

    sample = sampler.draw_ppeb_sample(
        str(election.random_seed),
        sampler_contest.from_db_contest(contest),
        sample_sizes[contest.id],
        num_previously_sampled,
        batch_tallies(election),
    )

    for (ticket_number, batch_key, _) in sample:
        sampled_batch_draw = SampledBatchDraw(
            batch_id=batch_key_to_id[batch_key],
            round_id=round.id,
            ticket_number=ticket_number,
        )
        db_session.add(sampled_batch_draw)


CREATE_ROUND_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "roundNum": {"type": "integer", "minimum": 1,},
        "sampleSizes": {
            "type": "object",
            "patternProperties": {"^.*$": {"type": "integer"}},
        },
    },
    "additionalProperties": False,
    "required": ["roundNum"],
}

# Raises if invalid
def validate_round(round: dict, election: Election):
    validate(round, CREATE_ROUND_REQUEST_SCHEMA)

    current_round = get_current_round(election)
    next_round_num = current_round.round_num + 1 if current_round else 1
    if round["roundNum"] != next_round_num:
        raise BadRequest(f"The next round should be round number {next_round_num}")

    if current_round and not current_round.ended_at:
        raise Conflict("The current round is not complete")

    if round["roundNum"] == 1:
        if "sampleSizes" not in round:
            raise BadRequest("Sample sizes are required for round 1")

        targeted_contest_ids = {c.id for c in election.contests if c.is_targeted}
        if set(round["sampleSizes"].keys()) != targeted_contest_ids:
            raise BadRequest("Sample sizes provided do not match targeted contest ids")


@api.route("/election/<election_id>/round", methods=["POST"])
@with_election_access
def create_round(election: Election):
    json_round = request.get_json()
    validate_round(json_round, election)

    round = Round(
        id=str(uuid.uuid4()), election_id=election.id, round_num=json_round["roundNum"],
    )
    db_session.add(round)

    # For round 1, use the given sample size for each contest.
    if json_round["roundNum"] == 1:
        sample_sizes = json_round["sampleSizes"]
    # In later rounds, use:
    # - the 90% probability sample size for ballot polling audits
    # - the macro sample size for batch comparison audits
    else:
        sample_size_options = sample_sizes_module.sample_size_options(election)
        sample_sizes = {
            contest_id: (
                options["0.9"]["size"]
                if election.audit_type == AuditType.BALLOT_POLLING
                else options["macro"]["size"]
            )
            for contest_id, options in sample_size_options.items()
        }

    draw_sample(election, round, sample_sizes)

    db_session.commit()

    return jsonify({"status": "ok"})


def serialize_round(round: Round) -> dict:
    return {
        "id": round.id,
        "roundNum": round.round_num,
        "startedAt": isoformat(round.created_at),
        "endedAt": isoformat(round.ended_at),
        "isAuditComplete": is_audit_complete(round),
    }


@api.route("/election/<election_id>/round", methods=["GET"])
@with_election_access
def list_rounds_audit_admin(election: Election):
    return jsonify({"rounds": [serialize_round(r) for r in election.rounds]})


# Make a separate endpoint for jurisdiction admins to access the list of
# rounds. This makes our permission scheme simpler (every route only allows one
# user type), even though the logic of this particular pair our routes is
# identical.
@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round", methods=["GET"]
)
@with_jurisdiction_access
def list_rounds_jurisdiction_admin(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    return jsonify({"rounds": [serialize_round(r) for r in election.rounds]})

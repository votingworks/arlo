import uuid
from typing import Optional, NamedTuple, List, Tuple
from flask import jsonify, request
from jsonschema import validate
from werkzeug.exceptions import BadRequest, Conflict

from . import api
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..auth import with_election_access, with_jurisdiction_access
from .sample_sizes import sample_size_options
from ..util.isoformat import isoformat
from ..util.group_by import group_by
from ..audit_math import sampler


CREATE_ROUND_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "roundNum": {"type": "integer", "minimum": 1,},
        "sampleSize": {"type": "integer", "minimum": 1,},
    },
    "additionalProperties": False,
    "required": ["roundNum"],
}


def serialize_round(round: Round) -> dict:
    return {
        "id": round.id,
        "roundNum": round.round_num,
        "startedAt": isoformat(round.created_at),
        "endedAt": isoformat(round.ended_at),
        "isAuditComplete": is_audit_complete(round),
    }


def get_current_round(election: Election) -> Optional[Round]:
    rounds = sorted(election.rounds, key=lambda r: r.round_num, reverse=True)
    return next(iter(rounds), None)


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


# Raises if invalid
def validate_round(round: dict, election: Election):
    validate(round, CREATE_ROUND_REQUEST_SCHEMA)

    current_round = get_current_round(election)
    next_round_num = current_round.round_num + 1 if current_round else 1
    if round["roundNum"] != next_round_num:
        raise BadRequest(f"The next round should be round number {next_round_num}")

    if current_round and not current_round.ended_at:
        raise Conflict("The current round is not complete")

    if round["roundNum"] == 1 and "sampleSize" not in round:
        raise BadRequest("Sample size is required for round 1")


class SampleDraw(NamedTuple):
    # ballot_key: ((jurisdiction name, batch name), ballot_position)
    ballot_key: Tuple[Tuple[str, str], int]
    contest_id: str
    ticket_number: str


def sample_ballots(election: Election, round: Round, sample_size: int):
    # Figure out which contests still need auditing
    last_round = get_current_round(election)
    contests_that_havent_met_risk_limit = (
        [
            round_contest.contest
            for round_contest in last_round.round_contests
            if not round_contest.is_complete
        ]
        if last_round
        else election.contests
    )

    # Create RoundContest objects to include the contests in this round
    for contest in contests_that_havent_met_risk_limit:
        round_contest = RoundContest(
            round_id=round.id, contest_id=contest.id, sample_size=sample_size
        )
        db_session.add(round_contest)

    def draw_sample_for_contest(contest: Contest, sample_size: int) -> List[SampleDraw]:
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
            SampleDraw(
                ballot_key=ballot_key,
                contest_id=contest.id,
                ticket_number=ticket_number,
            )
            for (ticket_number, ballot_key, _) in sample
        ]

    # Draw a sample for each targeted contest
    # - For jointly targeted contest, we can draw one a sample for each contest
    # and reuse it, since the contests have the same universe and sample size.
    # - TODO For independently targeted contests, each contest needs its own
    # sample.
    one_targeted_contest = next(
        contest
        for contest in contests_that_havent_met_risk_limit
        if contest.is_targeted
    )
    one_sample = draw_sample_for_contest(one_targeted_contest, sample_size)
    samples = [
        [sample_draw._replace(contest_id=contest.id) for sample_draw in one_sample]
        for contest in contests_that_havent_met_risk_limit
        if contest.is_targeted
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


@api.route("/election/<election_id>/round", methods=["POST"])
@with_election_access
def create_round(election: Election):
    json_round = request.get_json()
    validate_round(json_round, election)

    # TODO change this for independently targeted contests - maybe take in
    # which sample size level to use rather than the size itself?
    # For round 1, use the given sample size. In later rounds, use the 90%
    # probability sample size.
    sample_size = (
        json_round["sampleSize"]
        if json_round["roundNum"] == 1
        else sample_size_options(election)["0.9"]["size"]
    )

    round = Round(
        id=str(uuid.uuid4()), election_id=election.id, round_num=json_round["roundNum"],
    )
    db_session.add(round)

    sample_ballots(election, round, sample_size)

    db_session.commit()

    return jsonify({"status": "ok"})

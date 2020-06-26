import uuid
from typing import Optional
from flask import jsonify, request
from jsonschema import validate
from werkzeug.exceptions import BadRequest, Conflict

from . import api
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..auth import with_election_access, with_jurisdiction_access
from .sample_sizes import sample_size_options
from ..util.isoformat import isoformat
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


def sample_ballots(election: Election, round: Round, sample_size: int):
    # For now, we only support jointly targeted contests, which all must have
    # the same contest universe. So we can just take any of them to build the
    # pool of ballots to sample.
    targeted_contest = next(c for c in election.contests if c.is_targeted)

    # Compute the total number of ballot samples in all rounds leading up to
    # this one. Note that this corresponds to the number of SampledBallotDraws,
    # not SampledBallots.
    num_previously_sampled = (
        SampledBallotDraw.query.join(Round).filter_by(election_id=election.id).count()
    )

    # Create the pool of ballots to sample (aka manifest) by combining the
    # manifests from every jurisdiction in the contest's universe.
    # Audits must be deterministic and repeatable for the same real world
    # inputs. So the sampler expects the same input for the same real world
    # data. Thus, we use the jurisdiction and batch names (deterministic real
    # world ids) instead of the jurisdiction and batch ids (non-deterministic
    # uuids that we generate for each audit).
    manifest = {
        (jurisdiction.name, batch.name): batch.num_ballots
        for jurisdiction in targeted_contest.jurisdictions
        for batch in jurisdiction.batches
    }
    batch_key_to_id = {
        (jurisdiction.name, batch.name): batch.id
        for jurisdiction in targeted_contest.jurisdictions
        for batch in jurisdiction.batches
    }

    # Do the math! I.e. compute the actual sample
    sample = sampler.draw_sample(
        str(election.random_seed), manifest, sample_size, num_previously_sampled
    )

    # Record which ballots are sampled in the db.
    # Note that a ballot may be sampled more than once (within a round or
    # across multiple rounds). We create one SampledBallot for each real-world
    # ballot that gets sampled, and record each time it gets sampled with a
    # SampledBallotDraw. That way we can ensure that we don't need to actually
    # look at a real-world ballot that we've already audited, even if it gets
    # sampled again.
    for (ticket_number, (batch_key, ballot_position), times_sampled) in sample:
        batch_id = batch_key_to_id[batch_key]
        if times_sampled == 1:
            sampled_ballot = SampledBallot(
                id=str(uuid.uuid4()),
                batch_id=batch_id,
                ballot_position=ballot_position,
                status=BallotStatus.NOT_AUDITED,
            )
            db_session.add(sampled_ballot)
        else:
            sampled_ballot = SampledBallot.query.filter_by(
                batch_id=batch_id, ballot_position=ballot_position
            ).one()

        sampled_ballot_draw = SampledBallotDraw(
            ballot_id=sampled_ballot.id, round_id=round.id, ticket_number=ticket_number,
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

    for contest in election.contests:
        round_contest = RoundContest(
            round_id=round.id, contest_id=contest.id, sample_size=sample_size
        )
        db_session.add(round_contest)

    sample_ballots(election, round, sample_size)

    db_session.commit()

    return jsonify({"status": "ok"})

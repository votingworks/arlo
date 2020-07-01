from typing import List, Dict, Optional
from flask import request, jsonify
from werkzeug.exceptions import BadRequest, Conflict
from sqlalchemy import func

from . import api
from ..auth import with_election_access, with_audit_board_access
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from .rounds import get_current_round
from ..util.jsonschema import validate, JSONDict


CONTEST_CHOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "numVotes": {"type": "integer", "minimum": 0},
    },
    "additionalProperties": False,
    "required": ["id", "name", "numVotes"],
}

CONTEST_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "isTargeted": {"type": "boolean"},
        "choices": {"type": "array", "items": CONTEST_CHOICE_SCHEMA},
        "totalBallotsCast": {"type": "integer", "minimum": 0},
        "numWinners": {"type": "integer", "minimum": 1},
        "votesAllowed": {"type": "integer", "minimum": 1},
        "jurisdictionIds": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
    "required": [
        "id",
        "name",
        "isTargeted",
        "choices",
        "totalBallotsCast",
        "numWinners",
        "votesAllowed",
        "jurisdictionIds",
    ],
}


def serialize_contest_choice(contest_choice: ContestChoice) -> JSONDict:
    return {
        "id": contest_choice.id,
        "name": contest_choice.name,
        "numVotes": contest_choice.num_votes,
    }


def serialize_contest(
    contest: Contest, round_status: Optional[JSONDict] = None
) -> JSONDict:
    return {
        "id": contest.id,
        "name": contest.name,
        "isTargeted": contest.is_targeted,
        "choices": [serialize_contest_choice(c) for c in contest.choices],
        "totalBallotsCast": contest.total_ballots_cast,
        "numWinners": contest.num_winners,
        "votesAllowed": contest.votes_allowed,
        "jurisdictionIds": [j.id for j in contest.jurisdictions],
        "currentRoundStatus": round_status,
    }


def deserialize_contest_choice(
    contest_choice: JSONDict, contest_id: str
) -> ContestChoice:
    return ContestChoice(
        id=contest_choice["id"],
        contest_id=contest_id,
        name=contest_choice["name"],
        num_votes=contest_choice["numVotes"],
    )


def deserialize_contest(contest: JSONDict, election_id: str) -> Contest:
    jurisdictions = (
        Jurisdiction.query.filter_by(election_id=election_id)
        .filter(Jurisdiction.id.in_(contest["jurisdictionIds"]))
        .all()
    )
    choices = [deserialize_contest_choice(c, contest["id"]) for c in contest["choices"]]
    return Contest(
        election_id=election_id,
        id=contest["id"],
        name=contest["name"],
        is_targeted=contest["isTargeted"],
        choices=choices,
        total_ballots_cast=contest["totalBallotsCast"],
        num_winners=contest["numWinners"],
        votes_allowed=contest["votesAllowed"],
        jurisdictions=jurisdictions,
    )


# Raises if invalid
def validate_contests(contests: List[JSONDict], election: Election):
    if len(list(election.rounds)) > 0:
        raise Conflict("Cannot update contests after audit has started.")

    validate(contests, {"type": "array", "items": CONTEST_SCHEMA})

    for contest in contests:
        total_votes = sum(c["numVotes"] for c in contest["choices"])
        total_allowed_votes = contest["totalBallotsCast"] * contest["votesAllowed"]
        if total_votes > total_allowed_votes:
            raise BadRequest(
                f"Too many votes cast in contest: {contest['name']}"
                f" ({total_votes} votes, {total_allowed_votes} allowed)"
            )

    # Jointly targeted contests must all have the same contest universe and total ballots
    targeted_contests = [contest for contest in contests if contest["isTargeted"]]
    if any(
        set(contest["jurisdictionIds"]) != set(contests[0]["jurisdictionIds"])
        for contest in targeted_contests[1:]
    ):
        raise BadRequest("All targeted contests must have the same jurisdictions.")

    if any(
        contest["totalBallotsCast"] != contests[0]["totalBallotsCast"]
        for contest in targeted_contests[1:]
    ):
        raise BadRequest("All targeted contests must have the same total ballots cast.")


def round_status_by_contest(
    round: Optional[Round], contests: List[Contest]
) -> Dict[str, Optional[JSONDict]]:
    if not round:
        return {c.id: None for c in contests}

    sampled_ballot_count_by_contest = dict(
        SampledBallotDraw.query.filter_by(round_id=round.id)
        .join(SampledBallot)
        .join(Batch)
        .join(Jurisdiction)
        .join(Jurisdiction.contests)
        .group_by(Contest.id)
        .values(Contest.id, func.count())
    )
    round_is_complete_by_contest = dict(
        RoundContest.query.filter_by(round_id=round.id).values(
            RoundContest.contest_id, RoundContest.is_complete
        )
    )

    # isRiskLimitMet will be None until we have computed the risk measurement
    # for that contest, which happens once we're done auditing its sampled
    # ballots. Once the risk measurement is calculated, isRiskLimitMet will be
    # a boolean.
    return {
        c.id: {
            "isRiskLimitMet": round_is_complete_by_contest[c.id],
            "numBallotsSampled": sampled_ballot_count_by_contest.get(c.id, 0),
        }
        for c in contests
    }


@api.route("/election/<election_id>/contest", methods=["PUT"])
@with_election_access
def create_or_update_all_contests(election: Election):
    json_contests = request.get_json()
    validate_contests(json_contests, election)

    Contest.query.filter_by(election_id=election.id).delete()

    for json_contest in json_contests:
        contest = deserialize_contest(json_contest, election.id)
        db_session.add(contest)

    db_session.commit()

    return jsonify(status="ok")


@api.route("/election/<election_id>/contest", methods=["GET"])
@with_election_access
def list_contests(election: Election):
    current_round = get_current_round(election)
    round_status = round_status_by_contest(current_round, list(election.contests))

    json_contests = [
        serialize_contest(c, round_status[c.id]) for c in election.contests
    ]
    return jsonify({"contests": json_contests})


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/contest",
    methods=["GET"],
)
@with_audit_board_access
def list_audit_board_contests(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,  # pylint: disable=unused-argument
    audit_board: AuditBoard,  # pylint: disable=unused-argument
):
    json_contests = [serialize_contest(c) for c in jurisdiction.contests]
    return jsonify({"contests": json_contests})

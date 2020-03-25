from typing import List
from flask import request, jsonify
from jsonschema import validate
from werkzeug.exceptions import BadRequest

from arlo_server import app, db
from arlo_server.routes import with_election_access, UserType
from arlo_server.models import Contest, ContestChoice, Election, Jurisdiction

contest_choice_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "numVotes": {"type": "integer", "minimum": 0},
    },
    "required": ["id", "name", "numVotes"],
}

contest_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "isTargeted": {"type": "boolean"},
        "choices": {"type": "array", "items": contest_choice_schema},
        "totalBallotsCast": {"type": "integer", "minimum": 0},
        "numWinners": {"type": "integer", "minimum": 1},
        "votesAllowed": {"type": "integer", "minimum": 1},
        "jurisdictionIds": {"type": "array", "items": {"type": "string"}},
    },
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


def serialize_contest_choice(db_contest_choice: ContestChoice) -> dict:
    return {
        "id": db_contest_choice.id,
        "name": db_contest_choice.name,
        "numVotes": db_contest_choice.num_votes,
    }


def serialize_contest(db_contest: Contest) -> dict:
    return {
        "id": db_contest.id,
        "name": db_contest.name,
        "isTargeted": db_contest.is_targeted,
        "choices": [serialize_contest_choice(c) for c in db_contest.choices],
        "totalBallotsCast": db_contest.total_ballots_cast,
        "numWinners": db_contest.num_winners,
        "votesAllowed": db_contest.votes_allowed,
        "jurisdictionIds": [j.id for j in db_contest.jurisdictions],
    }


def deserialize_contest_choice(json_contest_choice: dict, contest_id: str) -> Contest:
    return ContestChoice(
        id=json_contest_choice["id"],
        contest_id=contest_id,
        name=json_contest_choice["name"],
        num_votes=json_contest_choice["numVotes"],
    )


def deserialize_contest(json_contest: dict, election_id: str) -> Contest:
    jurisdictions = (
        db.session.query(Jurisdiction)
        .filter_by(election_id=election_id)
        .filter(Jurisdiction.id.in_(json_contest["jurisdictionIds"]))
        .all()
    )
    choices = [
        deserialize_contest_choice(c, json_contest["id"])
        for c in json_contest["choices"]
    ]
    return Contest(
        election_id=election_id,
        id=json_contest["id"],
        name=json_contest["name"],
        is_targeted=json_contest["isTargeted"],
        choices=choices,
        total_ballots_cast=json_contest["totalBallotsCast"],
        num_winners=json_contest["numWinners"],
        votes_allowed=json_contest["votesAllowed"],
        jurisdictions=jurisdictions,
    )


# Raises if invalid
def validate_contests(json_contests: List[dict]) -> None:
    validate(json_contests, {"type": "array", "items": contest_schema})

    for contest in json_contests:
        total_votes = sum(c["numVotes"] for c in contest["choices"])
        total_allowed_votes = contest["totalBallotsCast"] * contest["votesAllowed"]
        if total_votes > total_allowed_votes:
            raise BadRequest(
                f"Too many votes cast in contest: {contest['name']}"
                f" ({total_votes} votes, {total_allowed_votes} allowed)"
            )


@app.route("/election/<election_id>/contest", methods=["PUT"])
@with_election_access(UserType.AUDIT_ADMIN)
def create_or_update_all_contests(election: Election):
    json_contests = request.get_json()
    validate_contests(json_contests)

    db.session.query(Contest).filter_by(election_id=election.id).delete()

    for json_contest in json_contests:
        contest = deserialize_contest(json_contest, election.id)
        db.session.add(contest)

    db.session.commit()

    return jsonify(status="ok")


@app.route("/election/<election_id>/contest", methods=["GET"])
@with_election_access(UserType.AUDIT_ADMIN)
def list_contests(election: Election):
    return jsonify([serialize_contest(c) for c in election.contests])

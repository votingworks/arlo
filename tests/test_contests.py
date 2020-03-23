import pytest
from flask.testing import FlaskClient

import json, uuid

from helpers import post_json, put_json
from arlo_server.models import Jurisdiction


def test_contests_list_empty(client, election_id):
    rv = client.get(f"/election/{election_id}/contest")
    contests = json.loads(rv.data)
    assert contests == []


def test_contests_create_get_update_one(client, election_id, jurisdiction_ids):
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 48121,},
            {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 38026,},
        ],
        "totalBallotsCast": 86147,
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
    }
    rv = put_json(client, f"/election/{election_id}/contest", [contest])
    assert json.loads(rv.data) == {"status": "ok"}

    rv = client.get(f"/election/{election_id}/contest")
    contests = json.loads(rv.data)
    assert contests == [contest]

    contest["totalBallotsCast"] = contest["totalBallotsCast"] + 21
    contest["numWinners"] = 2
    contest["choices"].append(
        {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 21,}
    )

    rv = put_json(client, f"/election/{election_id}/contest", [contest])
    print(json.loads(rv.data))
    assert json.loads(rv.data) == {"status": "ok"}

    rv = client.get(f"/election/{election_id}/contest")
    contests = json.loads(rv.data)
    assert contests == [contest]


def test_contests_create_get_update_multiple(client, election_id, jurisdiction_ids):
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 48121,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 38026,},
            ],
            "totalBallotsCast": 86147,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": [],
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 2",
            "isTargeted": False,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 200,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 300,},
            ],
            "totalBallotsCast": 500,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 3",
            "isTargeted": False,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 200,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400,},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 600,},
            ],
            "totalBallotsCast": 700,
            "numWinners": 2,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]
    rv = put_json(client, f"/election/{election_id}/contest", contests)
    assert json.loads(rv.data) == {"status": "ok"}

    rv = client.get(f"/election/{election_id}/contest")
    json_contests = json.loads(rv.data)
    assert contests == json_contests

    contests[0]["name"] = "Changed name"
    contests[1]["isTargeted"] = True
    contests[2]["jurisdictionIds"] = jurisdiction_ids[1:]

    rv = put_json(client, f"/election/{election_id}/contest", contests)
    assert json.loads(rv.data) == {"status": "ok"}

    rv = client.get(f"/election/{election_id}/contest")
    json_contests = json.loads(rv.data)
    assert contests == json_contests


def test_contests_missing_field(client, election_id, jurisdiction_ids):
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 48121,},
            {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 38026,},
        ],
        "totalBallotsCast": 86147,
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
    }

    for field in contest:
        invalid_contest = contest.copy()
        del invalid_contest[field]

        rv = put_json(client, f"/election/{election_id}/contest", [invalid_contest])
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "message": f"'{field}' is a required property",
                    "errorType": "Bad Request",
                }
            ]
        }

    for field in contest["choices"][0]:
        invalid_contest = contest.copy()
        invalid_contest_choice = invalid_contest["choices"][0].copy()
        del invalid_contest_choice[field]
        invalid_contest["choices"] = [invalid_contest_choice]

        rv = put_json(client, f"/election/{election_id}/contest", [invalid_contest])
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "message": f"'{field}' is a required property",
                    "errorType": "Bad Request",
                }
            ]
        }


def test_contest_too_many_votes(client, election_id):
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 400,},
            {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 101,},
        ],
        "totalBallotsCast": 500,
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": [],
    }

    rv = put_json(client, f"/election/{election_id}/contest", [contest])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": f"Too many votes cast in contest: Contest 1 (501 votes, 500 allowed)",
                "errorType": "Bad Request",
            }
        ]
    }

    contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 700,},
            {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 301,},
        ],
        "totalBallotsCast": 500,
        "numWinners": 1,
        "votesAllowed": 2,
        "jurisdictionIds": [],
    }

    rv = put_json(client, f"/election/{election_id}/contest", [contest])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": f"Too many votes cast in contest: Contest 1 (1001 votes, 1000 allowed)",
                "errorType": "Bad Request",
            }
        ]
    }

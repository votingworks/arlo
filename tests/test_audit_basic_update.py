import json, uuid
import pytest

from helpers import post_json
from test_app import client


def test_audit_basic_update_create_contest(client):
    rv = client.post("/election/new")
    election_id = json.loads(rv.data)["electionId"]
    assert election_id

    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())

    rv = post_json(
        client,
        f"/election/{election_id}/audit/basic",
        {
            "name": "Create Contest",
            "riskLimit": 10,
            "randomSeed": "a1234567890987654321b",
            "online": False,
            "contests": [
                {
                    "id": contest_id,
                    "name": "Contest 1",
                    "isTargeted": True,
                    "choices": [
                        {"id": candidate_id_1, "name": "Candidate 1", "numVotes": 1325},
                        {"id": candidate_id_2, "name": "Candidate 2", "numVotes": 792},
                    ],
                    "totalBallotsCast": 2123,
                    "numWinners": 1,
                    "votesAllowed": 1,
                }
            ],
        },
    )

    assert json.loads(rv.data)["status"] == "ok"


def test_audit_basic_update_contest_required_fields(client):
    rv = client.post("/election/new")
    election_id = json.loads(rv.data)["electionId"]
    assert election_id

    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())

    contest = {
        "id": contest_id,
        "name": "Contest 1",
        "choices": [
            {"id": candidate_id_1, "name": "Candidate 1", "numVotes": 1325},
            {"id": candidate_id_2, "name": "Candidate 2", "numVotes": 792},
        ],
        "totalBallotsCast": 2123,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    for field in contest:
        contest_missing_field = contest.copy()
        del contest_missing_field[field]

        rv = post_json(
            client,
            f"/election/{election_id}/audit/basic",
            {
                "name": "Create Contest",
                "riskLimit": 10,
                "randomSeed": "a1234567890987654321b",
                "online": False,
                "contests": [contest],
            },
        )

        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "message": "Missing required field contest.isTargeted",
                    "errorType": "BadRequest",
                }
            ]
        }

    rv = client.get(f"/election/{election_id}/audit/status")
    assert json.loads(rv.data)["contests"] == []

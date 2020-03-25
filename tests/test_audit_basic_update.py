import json, uuid
import pytest

from helpers import post_json


def test_audit_basic_update_create_contest(client, election_id):
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


def test_audit_basic_update_sets_default_for_contest_is_targeted(client, election_id):
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

    rv = client.get(f"/election/{election_id}/audit/status")
    assert json.loads(rv.data)["contests"][0]["isTargeted"] is True

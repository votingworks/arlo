import pytest
from flask.testing import FlaskClient
from typing import List
import json, uuid

from helpers import put_json
from arlo_server.models import USState


@pytest.fixture
def contest(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]) -> str:
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 600,},
            {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400,},
        ],
        "totalBallotsCast": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
    }
    rv = put_json(client, f"/election/{election_id}/contest", [contest])
    assert json.loads(rv.data) == {"status": "ok"}
    yield contest


@pytest.fixture
def election_settings(client: FlaskClient, election_id: str) -> None:
    settings = {
        "electionName": "Test Election",
        "online": True,
        "randomSeed": "1234567890",
        "riskLimit": 10,
        "state": USState.California,
    }
    rv = put_json(client, f"/election/{election_id}/settings", settings)
    assert json.loads(rv.data) == {"status": "ok"}


def test_sample_sizes_without_contests(client: FlaskClient, election_id: str):
    rv = client.get(f"/election/{election_id}/sample-sizes")
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Cannot compute sample sizes until contests are set",
                "errorType": "Bad Request",
            }
        ]
    }


def test_sample_sizes_without_risk_limit(
    client: FlaskClient, election_id: str, contest: str
):
    rv = client.get(f"/election/{election_id}/sample-sizes")
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Cannot compute sample sizes until risk limit is set",
                "errorType": "Bad Request",
            }
        ]
    }


def test_sample_sizes_round_1(
    client: FlaskClient, election_id: str, contest: str, election_settings: None
):
    rv = client.get(f"/election/{election_id}/sample-sizes")
    sample_sizes = json.loads(rv.data)
    assert sample_sizes == {
        "sampleSizes": [
            {"prob": 0.52, "size": 119, "type": "ASN"},
            {"prob": 0.7, "size": 184, "type": None},
            {"prob": 0.8, "size": 244, "type": None},
            {"prob": 0.9, "size": 351, "type": None},
        ]
    }

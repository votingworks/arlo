import pytest
from flask.testing import FlaskClient
import json, io, uuid
from typing import List

from arlo_server import app, db
from arlo_server.models import Jurisdiction, USState
from helpers import post_json, put_json, create_election
from bgcompute import bgcompute_update_election_jurisdictions_file

# The fixtures in this module are available in any test via dependency
# injection.


@pytest.fixture
def client() -> FlaskClient:
    app.config["TESTING"] = True
    client = app.test_client()

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield client

    db.session.commit()


@pytest.fixture
def election_id(client: FlaskClient) -> str:
    election_id = create_election(client)
    yield election_id


@pytest.fixture
def jurisdiction_ids(client: FlaskClient, election_id: str) -> List[str]:
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    b"Jurisdiction,Admin Email\n"
                    b"J1,a1@example.com\n"
                    b"J2,a2@example.com\n"
                    b"J3,a3@example.com"
                ),
                "jurisdictions.csv",
            )
        },
    )
    assert json.loads(rv.data) == {"status": "ok"}
    bgcompute_update_election_jurisdictions_file()
    jurisdictions = Jurisdiction.query.filter_by(election_id=election_id).all()
    yield [j.id for j in jurisdictions]


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

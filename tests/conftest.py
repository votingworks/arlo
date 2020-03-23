import pytest
from flask.testing import FlaskClient
import json, io
from typing import List

from arlo_server import app, db
from arlo_server.models import Jurisdiction
from helpers import post_json, create_election

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
    jurisdictions = Jurisdiction.query.filter_by(election_id=election_id).all()
    yield [j.id for j in jurisdictions]

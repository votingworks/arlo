import pytest
import json
from flask.testing import FlaskClient

from arlo_server import app, db
from helpers import post_json

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
def election_id(client: FlaskClient, request) -> str:
    rv = post_json(
        client,
        "/election/new",
        {"auditName": f"Test Audit {request.function.__name__}"},
    )
    election_id = json.loads(rv.data)["electionId"]
    yield election_id

import pytest
import json
from flask.testing import FlaskClient

from arlo_server import app, db
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

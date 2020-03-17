import json
import pytest
from flask.testing import FlaskClient
from typing import Any

from arlo_server import app, db
from arlo_server.routes import create_organization, UserType
from tests.helpers import create_org_and_admin, set_logged_in_user, post_json


@pytest.fixture
def client() -> FlaskClient:
    app.config["TESTING"] = True
    client = app.test_client()

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield client

    db.session.commit()


def test_without_org_with_anonymous_user(client: FlaskClient):
    rv = client.post("/election/new")
    assert json.loads(rv.data)["electionId"]
    assert rv.status_code == 200


def test_in_org_with_anonymous_user(client: FlaskClient):
    org = create_organization()
    rv = post_json(client, "/election/new", {"organizationId": org.id})
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": f"Anonymous users do not have access to organization {org.id}",
                "errorType": "Unauthorized",
            }
        ]
    }
    assert rv.status_code == 401


def test_in_org_with_logged_in_admin(client: FlaskClient):
    org_id, _user_id = create_org_and_admin(user_email="admin@example.com")
    set_logged_in_user(
        client, user_type=UserType.AUDIT_ADMIN, user_email="admin@example.com"
    )

    rv = post_json(client, "/election/new", {"organizationId": org_id})
    response = json.loads(rv.data)
    election_id = response.get("electionId", None)
    assert election_id, response

    rv = client.get(f"/election/{election_id}/audit/status")

    assert json.loads(rv.data)["organizationId"] == org_id


def test_in_org_with_logged_in_admin_without_access(client: FlaskClient):
    _org1_id, _user1_id = create_org_and_admin(user_email="admin1@example.com")
    org2_id, _user2_id = create_org_and_admin(user_email="admin2@example.com")
    set_logged_in_user(
        client, user_type=UserType.AUDIT_ADMIN, user_email="admin1@example.com"
    )

    rv = post_json(client, "/election/new", {"organizationId": org2_id})
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": f"admin1@example.com does not have access to organization {org2_id}",
                "errorType": "Forbidden",
            }
        ]
    }
    assert rv.status_code == 403


def test_in_org_with_logged_in_jurisdiction_admin(client: FlaskClient):
    org_id, _user_id = create_org_and_admin(user_email="admin@example.com")
    set_logged_in_user(
        client, user_type=UserType.JURISDICTION_ADMIN, user_email="admin@example.com"
    )

    rv = post_json(client, "/election/new", {"organizationId": org_id})
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": f"admin@example.com is not logged in as an audit admin and so does not have access to organization {org_id}",
                "errorType": "Forbidden",
            }
        ]
    }
    assert rv.status_code == 403

import json, uuid
from flask.testing import FlaskClient

from arlo_server.auth import UserType
from arlo_server.routes import create_organization
from tests.helpers import assert_ok, create_org_and_admin, set_logged_in_user, post_json


def test_without_org_with_anonymous_user(client: FlaskClient):
    rv = post_json(
        client,
        "/election/new",
        {"auditName": "Test Audit", "isMultiJurisdiction": False},
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]


def test_in_org_with_anonymous_user(client: FlaskClient):
    org = create_organization()
    rv = post_json(
        client,
        "/election/new",
        {
            "auditName": "Test Audit",
            "organizationId": org.id,
            "isMultiJurisdiction": True,
        },
    )
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

    rv = post_json(
        client,
        "/election/new",
        {
            "auditName": "Test Audit",
            "organizationId": org_id,
            "isMultiJurisdiction": True,
        },
    )
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

    rv = post_json(
        client,
        "/election/new",
        {
            "auditName": "Test Audit",
            "organizationId": org2_id,
            "isMultiJurisdiction": True,
        },
    )
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

    rv = post_json(
        client,
        "/election/new",
        {
            "auditName": "Test Audit",
            "organizationId": org_id,
            "isMultiJurisdiction": True,
        },
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": f"admin@example.com is not logged in as an audit admin and so does not have access to organization {org_id}",
                "errorType": "Forbidden",
            }
        ]
    }
    assert rv.status_code == 403


def test_missing_audit_name(client: FlaskClient):
    rv = post_json(client, "/election/new", {})
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "'auditName' is a required property",
                "errorType": "Bad Request",
            }
        ]
    }


def test_without_org_duplicate_audit_name(client: FlaskClient):
    rv = post_json(
        client,
        "/election/new",
        {"auditName": "Test Audit", "isMultiJurisdiction": False},
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]

    rv = post_json(
        client,
        "/election/new",
        {"auditName": "Test Audit", "isMultiJurisdiction": False},
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]


def test_in_org_duplicate_audit_name(client: FlaskClient):
    org_id, _user_id = create_org_and_admin(user_email="admin@example.com")
    set_logged_in_user(
        client, user_type=UserType.AUDIT_ADMIN, user_email="admin@example.com"
    )

    rv = post_json(
        client,
        "/election/new",
        {
            "auditName": "Test Audit",
            "organizationId": org_id,
            "isMultiJurisdiction": True,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]

    rv = post_json(
        client,
        "/election/new",
        {
            "auditName": "Test Audit",
            "organizationId": org_id,
            "isMultiJurisdiction": True,
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": f"An audit with name 'Test Audit' already exists within your organization",
                "errorType": "Conflict",
            }
        ]
    }


def test_two_orgs_same_name(client: FlaskClient):
    org_id_1, _ = create_org_and_admin(user_email="admin1@example.com")
    org_id_2, _ = create_org_and_admin(user_email="admin2@example.com")
    set_logged_in_user(
        client, user_type=UserType.AUDIT_ADMIN, user_email="admin1@example.com"
    )

    rv = post_json(
        client,
        "/election/new",
        {
            "auditName": "Test Audit",
            "organizationId": org_id_1,
            "isMultiJurisdiction": True,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]

    set_logged_in_user(
        client, user_type=UserType.AUDIT_ADMIN, user_email="admin2@example.com"
    )

    rv = post_json(
        client,
        "/election/new",
        {
            "auditName": "Test Audit",
            "organizationId": org_id_2,
            "isMultiJurisdiction": True,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]


def test_election_reset(client, election_id):
    rv = client.post(f"/election/{election_id}/audit/reset")
    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)

    assert status["riskLimit"] is None
    assert status["randomSeed"] is None
    assert status["contests"] == []
    assert status["jurisdictions"] == []
    assert status["rounds"] == []


def test_election_reset_not_found(client):
    rv = client.post(f"/election/{str(uuid.uuid4())}/audit/reset")
    assert rv.status_code == 404

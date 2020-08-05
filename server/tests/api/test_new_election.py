import json, uuid
from flask.testing import FlaskClient

from ...auth import UserType
from ...api.routes import create_organization
from ..helpers import assert_ok, create_org_and_admin, set_logged_in_user, post_json
from ...models import *  # pylint: disable=wildcard-import


def test_without_org_with_anonymous_user(client: FlaskClient):
    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit Without Org",
            "isMultiJurisdiction": False,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]


def test_in_org_with_anonymous_user(client: FlaskClient):
    org = create_organization()
    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit In Org Anonymous",
            "organizationId": org.id,
            "isMultiJurisdiction": True,
            "auditType": AuditType.BALLOT_POLLING,
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
    org_id, _user_id = create_org_and_admin(user_email="logged-in-aa@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "logged-in-aa@example.com")

    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit In Org Logged In AA",
            "organizationId": org_id,
            "isMultiJurisdiction": True,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    response = json.loads(rv.data)
    election_id = response.get("electionId", None)
    assert election_id, response

    rv = client.get(f"/api/election/{election_id}/audit/status")

    assert json.loads(rv.data)["organizationId"] == org_id


def test_in_org_with_logged_in_admin_without_access(client: FlaskClient):
    _org1_id, _user1_id = create_org_and_admin(user_email="without-access@example.com")
    org2_id, _user2_id = create_org_and_admin(user_email="with-access@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "without-access@example.com")

    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit Logged In Without Access",
            "organizationId": org2_id,
            "isMultiJurisdiction": True,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": f"without-access@example.com does not have access to organization {org2_id}",
                "errorType": "Forbidden",
            }
        ]
    }
    assert rv.status_code == 403


def test_in_org_with_logged_in_jurisdiction_admin(client: FlaskClient):
    org_id, _user_id = create_org_and_admin(user_email="logged-in-ja@example.com")
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, "logged-in-ja@example.com")

    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit In Org Logged In JA",
            "organizationId": org_id,
            "isMultiJurisdiction": True,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": f"User is not logged in as an audit admin and so does not have access to organization {org_id}",
                "errorType": "Forbidden",
            }
        ]
    }
    assert rv.status_code == 403


def test_bad_audit_type(client: FlaskClient):
    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit",
            "isMultiJurisdiction": False,
            "auditType": "NOT A REAL TYPE",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "'NOT A REAL TYPE' is not one of ['BALLOT_POLLING', 'BATCH_COMPARISON']",
                "errorType": "Bad Request",
            }
        ]
    }


def test_missing_audit_name(client: FlaskClient):
    rv = post_json(client, "/api/election/new", {})
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
        "/api/election/new",
        {
            "auditName": "Test Audit Duplicate",
            "isMultiJurisdiction": False,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]

    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit Duplicate",
            "isMultiJurisdiction": False,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]


def test_in_org_duplicate_audit_name(client: FlaskClient):
    org_id, _user_id = create_org_and_admin(user_email="duplicate-name@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "duplicate-name@example.com")

    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit In Org Duplicate",
            "organizationId": org_id,
            "isMultiJurisdiction": True,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]

    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit In Org Duplicate",
            "organizationId": org_id,
            "isMultiJurisdiction": True,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "An audit with name 'Test Audit In Org Duplicate' already exists within your organization",
                "errorType": "Conflict",
            }
        ]
    }


def test_two_orgs_same_name(client: FlaskClient):
    org_id_1, _ = create_org_and_admin(user_email="admin-org1@example.com")
    org_id_2, _ = create_org_and_admin(user_email="admin-org2@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "admin-org1@example.com")

    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit Two Orgs Duplicate",
            "organizationId": org_id_1,
            "isMultiJurisdiction": True,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]

    set_logged_in_user(client, UserType.AUDIT_ADMIN, "admin-org2@example.com")

    rv = post_json(
        client,
        "/api/election/new",
        {
            "auditName": "Test Audit Two Orgs Duplicate",
            "organizationId": org_id_2,
            "isMultiJurisdiction": True,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]


def test_election_reset(client, election_id):
    rv = client.post(f"/api/election/{election_id}/audit/reset")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/audit/status")
    status = json.loads(rv.data)

    assert status["riskLimit"] is None
    assert status["randomSeed"] is None
    assert status["contests"] == []
    assert status["jurisdictions"] == []
    assert status["rounds"] == []


def test_election_reset_not_found(client):
    rv = client.post(f"/api/election/{str(uuid.uuid4())}/audit/reset")
    assert rv.status_code == 404

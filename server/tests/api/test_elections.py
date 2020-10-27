import json
from flask.testing import FlaskClient

from ...auth import UserType
from ..helpers import *  # pylint: disable=wildcard-import
from ...models import *  # pylint: disable=wildcard-import


def test_create_election_missing_fields(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    for field in ["auditName", "auditType", "organizationId"]:
        new_election = {
            "auditName": f"Test Missing {field}",
            "auditType": AuditType.BALLOT_POLLING,
            "organizationId": org_id,
        }

        del new_election[field]

        rv = post_json(client, "/api/election", new_election)
        print(rv.data)
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "message": f"'{field}' is a required property",
                    "errorType": "Bad Request",
                }
            ]
        }


def test_create_election_not_logged_in(client: FlaskClient, org_id: str):
    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit Not Logged In",
            "organizationId": org_id,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert json.loads(rv.data) == {
        "errors": [
            {"message": "Please log in to access Arlo", "errorType": "Unauthorized",}
        ]
    }
    assert rv.status_code == 401


def test_create_election(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit In Org Logged In AA",
            "organizationId": org_id,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    response = json.loads(rv.data)
    election_id = response.get("electionId", None)
    assert election_id, response
    election = Election.query.get(election_id)
    assert election.organization_id == org_id
    assert election.online is False


def test_create_election_new_batch_comparison_audit(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit Batch Comparison",
            "organizationId": org_id,
            "auditType": "BATCH_COMPARISON",
        },
    )
    assert rv.status_code == 200
    election_id = json.loads(rv.data)["electionId"]
    assert Election.query.get(election_id).online is False


def test_create_election_new_ballot_comparison_audit(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit Ballot Comparison",
            "organizationId": org_id,
            "auditType": "BALLOT_COMPARISON",
        },
    )
    assert rv.status_code == 200
    election_id = json.loads(rv.data)["electionId"]
    assert election_id

    assert Election.query.get(election_id).online is True


def test_create_election_in_org_with_logged_in_admin_without_access(
    client: FlaskClient, org_id: str
):
    create_org_and_admin(user_email="without-access@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "without-access@example.com")

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit Logged In Without Access",
            "organizationId": org_id,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": f"without-access@example.com does not have access to organization {org_id}",
                "errorType": "Forbidden",
            }
        ]
    }
    assert rv.status_code == 403


def test_create_election_jurisdiction_admin(
    client: FlaskClient,
    org_id: str,
    election_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit In Org Logged In JA",
            "organizationId": org_id,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Access forbidden for user type jurisdiction_admin",
                "errorType": "Forbidden",
            }
        ]
    }
    assert rv.status_code == 403


def test_create_election_bad_audit_type(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit",
            "auditType": "NOT A REAL TYPE",
            "organizationId": org_id,
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "'NOT A REAL TYPE' is not one of ['BALLOT_POLLING', 'BATCH_COMPARISON', 'BALLOT_COMPARISON']",
                "errorType": "Bad Request",
            }
        ]
    }


def test_create_election_in_org_duplicate_audit_name(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit In Org Duplicate",
            "organizationId": org_id,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit In Org Duplicate",
            "organizationId": org_id,
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


def test_create_election_two_orgs_same_name(client: FlaskClient):
    org_id_1, _ = create_org_and_admin(user_email="admin-org1@example.com")
    org_id_2, _ = create_org_and_admin(user_email="admin-org2@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "admin-org1@example.com")

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit Two Orgs Duplicate",
            "organizationId": org_id_1,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]

    set_logged_in_user(client, UserType.AUDIT_ADMIN, "admin-org2@example.com")

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit Two Orgs Duplicate",
            "organizationId": org_id_2,
            "auditType": AuditType.BALLOT_POLLING,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]

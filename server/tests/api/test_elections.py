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
            "auditMathType": AuditMathType.BRAVO,
            "organizationId": org_id,
        }

        del new_election[field]

        rv = post_json(client, "/api/election", new_election)
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
            "auditMathType": AuditMathType.BRAVO,
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
            "auditMathType": AuditMathType.BRAVO,
        },
    )
    response = json.loads(rv.data)
    election_id = response.get("electionId", None)
    assert election_id, response
    election = Election.query.get(election_id)
    assert election.organization_id == org_id
    assert election.online is True


def test_create_election_new_batch_comparison_audit(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit Batch Comparison",
            "organizationId": org_id,
            "auditType": "BATCH_COMPARISON",
            "auditMathType": AuditMathType.MACRO,
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
            "auditMathType": AuditMathType.SUPERSIMPLE,
        },
    )
    assert rv.status_code == 200
    election_id = json.loads(rv.data)["electionId"]
    assert election_id

    assert Election.query.get(election_id).online is True


def test_create_election_new_hybrid_audit(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit Hybrid",
            "organizationId": org_id,
            "auditType": "HYBRID",
            "auditMathType": AuditMathType.SUITE,
        },
    )
    assert rv.status_code == 200
    election_id = json.loads(rv.data)["electionId"]
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
            "auditMathType": AuditMathType.BRAVO,
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
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit In Org Logged In JA",
            "organizationId": org_id,
            "auditType": AuditType.BALLOT_POLLING,
            "auditMathType": AuditMathType.BRAVO,
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
            "auditMathType": AuditMathType.BRAVO,
            "organizationId": org_id,
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "'NOT A REAL TYPE' is not one of ['BALLOT_POLLING', 'BATCH_COMPARISON', 'BALLOT_COMPARISON', 'HYBRID']",
                "errorType": "Bad Request",
            }
        ]
    }


def test_create_election_bad_bp_type(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit",
            "auditType": AuditType.BALLOT_POLLING,
            "auditMathType": "NOT A REAL TYPE",
            "organizationId": org_id,
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "'NOT A REAL TYPE' is not one of ['BRAVO', 'MINERVA', 'SUPERSIMPLE', 'MACRO', 'SUITE']",
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
            "auditMathType": AuditMathType.BRAVO,
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
            "auditMathType": AuditMathType.BRAVO,
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
            "auditMathType": AuditMathType.BRAVO,
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
            "auditMathType": AuditMathType.BRAVO,
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data)["electionId"]


def test_delete_election(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.delete(f"/api/election/{election_id}")
    assert_ok(rv)

    # Should not show up in any API responses
    aa_user = User.query.filter_by(email=DEFAULT_AA_EMAIL).one()
    rv = client.get(f"/api/audit_admins/{aa_user.id}/organizations")
    resp = json.loads(rv.data)
    assert all(
        election["id"] != election_id
        for organization in resp
        for election in organization["elections"]
    )

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get("/api/me")
    resp = json.loads(rv.data)
    assert all(
        jurisdiction["election"]["id"] != election_id
        for jurisdiction in resp["user"]["jurisdictions"]
    )

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get("/api/me")
    resp = json.loads(rv.data)
    assert resp["user"] is None

    # All endpoints should 404
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 404

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    assert rv.status_code == 404

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    assert rv.status_code == 404


def test_list_organizations(client: FlaskClient):
    aa_email = "list_orgs_email@example.gov"
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    org_id, aa_id = create_org_and_admin("Test Org List", aa_email)
    election_id = create_election(client, "Test Audit Org List", organization_id=org_id)
    org_id_2, _ = create_org_and_admin("Test Org List 2", aa_email)
    rv = client.get(f"/api/audit_admins/{aa_id}/organizations")
    assert json.loads(rv.data) == [
        {
            "name": "Test Org List",
            "id": org_id,
            "elections": [
                {
                    "id": election_id,
                    "auditName": "Test Audit Org List",
                    "electionName": None,
                    "state": None,
                }
            ],
        },
        {"name": "Test Org List 2", "id": org_id_2, "elections": []},
    ]


def test_list_organizations_not_authorized(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    aa_user = User.query.filter_by(email=DEFAULT_AA_EMAIL).one()
    db_session.expunge(aa_user)

    clear_logged_in_user(client)
    rv = client.get(f"/api/audit_admins/{aa_user.id}/organizations")
    assert rv.status_code == 403

    ja_user = User.query.filter_by(email=default_ja_email(election_id)).one()
    db_session.expunge(ja_user)
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(f"/api/audit_admins/{ja_user.id}/organizations")
    assert rv.status_code == 403

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get("/api/audit_admins/not-a-real-id/organizations")
    assert rv.status_code == 403

    rv = client.get(f"/api/audit_admins/{ja_user.id}/organizations")
    assert rv.status_code == 403

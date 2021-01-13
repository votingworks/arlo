from unittest.mock import Mock, patch
from urllib.parse import urlparse
from flask.testing import FlaskClient

from ..helpers import *  # pylint: disable=wildcard-import
from ...api.support import (
    AUTH0_DOMAIN,
    AUDITADMIN_AUTH0_CLIENT_ID,
    AUDITADMIN_AUTH0_CLIENT_SECRET,
    Auth0Error,
)

SUPPORT_EMAIL = "support@example.org"


def test_support_list_organizations(client: FlaskClient, org_id: str):
    set_superadmin_user(client, SUPPORT_EMAIL)
    rv = client.get("/api/support/organizations")
    orgs = json.loads(rv.data)
    # This will load orgs from all tests, so we can't check its exact length/value
    assert len(orgs) >= 1
    org = next(org for org in orgs if org["id"] == org_id)
    assert org == {"id": org_id, "name": "Test Org test_support_list_organizations"}


def test_support_get_organization(client: FlaskClient, org_id: str, election_id: str):
    set_superadmin_user(client, SUPPORT_EMAIL)
    rv = client.get(f"/api/support/organizations/{org_id}")
    compare_json(
        json.loads(rv.data),
        {
            "id": org_id,
            "name": "Test Org test_support_get_organization",
            "elections": [
                {
                    "id": election_id,
                    "auditName": "Test Audit test_support_get_organization",
                    "auditType": "BALLOT_POLLING",
                }
            ],
            "auditAdmins": [{"email": DEFAULT_AA_EMAIL}],
        },
    )


def test_support_get_election(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_superadmin_user(client, SUPPORT_EMAIL)
    rv = client.get(f"/api/support/elections/{election_id}")
    compare_json(
        json.loads(rv.data),
        {
            "id": election_id,
            "auditName": "Test Audit test_support_get_election",
            "auditType": "BALLOT_POLLING",
            "jurisdictions": [
                {
                    "id": jurisdiction_ids[0],
                    "name": "J1",
                    "jurisdictionAdmins": [{"email": default_ja_email(election_id)}],
                },
                {
                    "id": jurisdiction_ids[1],
                    "name": "J2",
                    "jurisdictionAdmins": [{"email": default_ja_email(election_id)}],
                },
                {
                    "id": jurisdiction_ids[2],
                    "name": "J3",
                    "jurisdictionAdmins": [{"email": f"j3-{election_id}@example.com"}],
                },
            ],
        },
    )


@patch("server.api.support.GetToken")
@patch("server.api.support.Auth0")
def test_support_create_audit_admin(  # pylint: disable=invalid-name
    MockAuth0, MockGetToken, client: FlaskClient, org_id: str,
):
    MockGetToken.return_value = Mock()
    MockGetToken.return_value.client_credentials = Mock(
        return_value={"access_token": "test token"}
    )
    MockAuth0.return_value = Mock()
    MockAuth0.return_value.users = Mock()
    MockAuth0.return_value.users.create = Mock(
        return_value={"user_id": "test auth0 user id"}
    )

    new_admin_email = f"new-audit-admin-{org_id}@example.com"

    set_superadmin_user(client, SUPPORT_EMAIL)
    rv = post_json(
        client,
        f"/api/support/organizations/{org_id}/audit-admins",
        {"email": new_admin_email},
    )
    assert_ok(rv)

    rv = client.get(f"/api/support/organizations/{org_id}")
    assert json.loads(rv.data)["auditAdmins"] == [
        {"email": DEFAULT_AA_EMAIL},
        {"email": new_admin_email},
    ]

    user = User.query.filter_by(email=new_admin_email).one()
    assert user.external_id == "test auth0 user id"

    MockGetToken.assert_called_with(AUTH0_DOMAIN)
    MockGetToken.return_value.client_credentials.assert_called_with(
        AUDITADMIN_AUTH0_CLIENT_ID,
        AUDITADMIN_AUTH0_CLIENT_SECRET,
        f"https://{AUTH0_DOMAIN}/api/v2/",
    )
    MockAuth0.assert_called_with(AUTH0_DOMAIN, "test token")
    MockAuth0.return_value.users.create.assert_called()
    create_spec = MockAuth0.return_value.users.create.call_args[0][0]
    assert create_spec["email"] == f"new-audit-admin-{org_id}@example.com"
    assert create_spec["password"]
    assert create_spec["connection"] == "Username-Password-Authentication"


@patch("server.api.support.GetToken")
@patch("server.api.support.Auth0")
def test_support_create_audit_admin_already_in_auth0(  # pylint: disable=invalid-name
    MockAuth0, MockGetToken, client: FlaskClient, org_id: str,
):
    MockGetToken.return_value = Mock()
    MockGetToken.return_value.client_credentials = Mock(
        return_value={"access_token": "test token"}
    )
    MockAuth0.return_value = Mock()
    MockAuth0.return_value.users = Mock()
    MockAuth0.return_value.users.create = Mock(
        side_effect=Auth0Error(409, 1, "already exists")
    )
    MockAuth0.return_value.users_by_email = Mock()
    MockAuth0.return_value.users_by_email.search_users_by_email = Mock(
        return_value=[{"user_id": "test auth0 existing user id"}]
    )

    new_admin_email = f"new-audit-admin-{org_id}@example.com"

    set_superadmin_user(client, SUPPORT_EMAIL)
    rv = post_json(
        client,
        f"/api/support/organizations/{org_id}/audit-admins",
        {"email": new_admin_email},
    )
    assert_ok(rv)

    rv = client.get(f"/api/support/organizations/{org_id}")
    assert json.loads(rv.data)["auditAdmins"] == [
        {"email": DEFAULT_AA_EMAIL},
        {"email": new_admin_email},
    ]

    user = User.query.filter_by(email=new_admin_email).one()
    assert user.external_id == "test auth0 existing user id"

    MockAuth0.return_value.users.create.assert_called()
    MockAuth0.return_value.users_by_email.search_users_by_email.assert_called_with(
        new_admin_email
    )


@patch("server.api.support.GetToken")
@patch("server.api.support.Auth0")
def test_support_create_audit_admin_already_exists(  # pylint: disable=invalid-name,unused-argument
    MockAuth0, MockGetToken, client: FlaskClient, org_id: str,
):
    # Start with an existing user that isn't already an audit admin for this org
    user = create_user(email="already-exists@example.org")

    set_superadmin_user(client, SUPPORT_EMAIL)
    rv = client.get(f"/api/support/organizations/{org_id}")
    assert json.loads(rv.data)["auditAdmins"] == [
        {"email": DEFAULT_AA_EMAIL},
    ]

    rv = post_json(
        client,
        f"/api/support/organizations/{org_id}/audit-admins",
        {"email": user.email},
    )
    assert_ok(rv)

    rv = client.get(f"/api/support/organizations/{org_id}")
    assert json.loads(rv.data)["auditAdmins"] == [
        {"email": DEFAULT_AA_EMAIL},
        {"email": user.email},
    ]


@patch("server.api.support.GetToken")
@patch("server.api.support.Auth0")
def test_support_create_audit_admin_already_admin(  # pylint: disable=invalid-name,unused-argument
    MockAuth0, MockGetToken, client: FlaskClient, org_id: str,
):
    set_superadmin_user(client, SUPPORT_EMAIL)
    rv = post_json(
        client,
        f"/api/support/organizations/{org_id}/audit-admins",
        {"email": DEFAULT_AA_EMAIL},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Conflict", "message": "Audit admin already exists"}]
    }


def test_support_log_in_as_audit_admin(
    client: FlaskClient, election_id: str,  # pylint: disable=unused-argument
):
    set_superadmin_user(client, SUPPORT_EMAIL)

    with client.session_transaction() as session:  # type: ignore
        original_created_at = session["_created_at"]
        original_last_request_at = session["_last_request_at"]

    rv = client.get(f"/api/support/audit-admins/{DEFAULT_AA_EMAIL}/login")
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/"

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"]["type"] == UserType.AUDIT_ADMIN
        assert session["_user"]["key"] == DEFAULT_AA_EMAIL
        assert session["_created_at"] == original_created_at
        assert session["_last_request_at"] != original_last_request_at


def test_support_log_in_as_jurisdiction_admin(
    client: FlaskClient, election_id: str,
):
    set_superadmin_user(client, SUPPORT_EMAIL)

    with client.session_transaction() as session:  # type: ignore
        original_created_at = session["_created_at"]
        original_last_request_at = session["_last_request_at"]

    rv = client.get(
        f"/api/support/jurisdiction-admins/{default_ja_email(election_id)}/login"
    )
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/"

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"]["type"] == UserType.JURISDICTION_ADMIN
        assert session["_user"]["key"] == default_ja_email(election_id)
        assert session["_created_at"] == original_created_at
        assert session["_last_request_at"] != original_last_request_at

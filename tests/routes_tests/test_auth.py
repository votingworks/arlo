import pytest
from flask.testing import FlaskClient
import json
from unittest.mock import Mock, MagicMock

from arlo_server.auth import UserType
from arlo_server.routes import (
    auth0_aa,
    auth0_ja,
)
from tests.helpers import (
    set_logged_in_user,
    clear_logged_in_user,
    create_org_and_admin,
    create_jurisdiction_and_admin,
    create_election,
)


AA_EMAIL = "aa@example.com"
JA_EMAIL = "ja@example.com"


@pytest.fixture
def org_id():
    org_id, aa_id = create_org_and_admin("Test Org", AA_EMAIL)
    return org_id


@pytest.fixture
def election_id(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, AA_EMAIL)
    return create_election(client, organization_id=org_id)


@pytest.fixture
def jurisdiction_id(election_id: str):
    jurisdiction_id, ja_id = create_jurisdiction_and_admin(
        election_id, user_email=JA_EMAIL
    )
    return jurisdiction_id


def test_auth_me_audit_admin(
    client: FlaskClient, org_id: str, election_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, AA_EMAIL)

    rv = client.get("/auth/me")
    assert json.loads(rv.data) == {
        "type": UserType.AUDIT_ADMIN,
        "email": AA_EMAIL,
        "organizations": [
            {
                "name": "Test Org",
                "id": org_id,
                "elections": [
                    {
                        "id": election_id,
                        "auditName": "Test Audit",
                        "electionName": None,
                        "state": None,
                        "electionDate": None,
                        "isMultiJurisdiction": True,
                    }
                ],
            }
        ],
        "jurisdictions": [],
    }


def test_auth_me_jurisdiction_admin(
    client: FlaskClient, election_id: str, jurisdiction_id: str
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, JA_EMAIL)

    rv = client.get("/auth/me")
    assert json.loads(rv.data) == {
        "type": UserType.JURISDICTION_ADMIN,
        "email": JA_EMAIL,
        "organizations": [],
        "jurisdictions": [
            {
                "id": jurisdiction_id,
                "name": "Test Jurisdiction",
                "election": {
                    "id": election_id,
                    "auditName": "Test Audit",
                    "electionName": None,
                    "state": None,
                    "electionDate": None,
                    "isMultiJurisdiction": True,
                },
            }
        ],
    }


def test_auditadmin_start(client: FlaskClient):
    rv = client.get("/auth/auditadmin/start")
    assert rv.status_code == 302


def test_auditadmin_callback(
    client: FlaskClient, org_id: str,  # pylint: disable=unused-argument
):
    auth0_aa.authorize_access_token = MagicMock(return_value=None)

    mock_response = Mock()
    mock_response.json = MagicMock(return_value={"email": AA_EMAIL})
    auth0_aa.get = Mock(return_value=mock_response)

    rv = client.get("/auth/auditadmin/callback?code=foobar")
    assert rv.status_code == 302

    with client.session_transaction() as session:
        assert session["_user"]["type"] == UserType.AUDIT_ADMIN
        assert session["_user"]["email"] == AA_EMAIL

    assert auth0_aa.authorize_access_token.called
    assert auth0_aa.get.called


def test_jurisdictionadmin_start(client: FlaskClient):
    rv = client.get("/auth/jurisdictionadmin/start")
    assert rv.status_code == 302


def test_jurisdictionadmin_callback(
    client: FlaskClient, jurisdiction_id: str  # pylint: disable=unused-argument
):
    auth0_ja.authorize_access_token = MagicMock(return_value=None)

    mock_response = Mock()
    mock_response.json = MagicMock(return_value={"email": JA_EMAIL})
    auth0_ja.get = Mock(return_value=mock_response)

    rv = client.get("/auth/jurisdictionadmin/callback?code=foobar")
    assert rv.status_code == 302

    with client.session_transaction() as session:
        assert session["_user"]["type"] == UserType.JURISDICTION_ADMIN
        assert session["_user"]["email"] == JA_EMAIL

    assert auth0_ja.authorize_access_token.called
    assert auth0_ja.get.called


def test_logout(client: FlaskClient):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, AA_EMAIL)

    rv = client.get("/auth/logout")

    with client.session_transaction() as session:
        assert session["_user"] is None

    assert rv.status_code == 302


# Tests for route decorators. We have added special routes to test the
# decorators that are set up in conftest.py.


def test_with_election_access_audit_admin(client: FlaskClient, election_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, AA_EMAIL)
    rv = client.get(f"/election/{election_id}/test_auth")
    assert rv.status_code == 200
    assert json.loads(rv.data) == election_id


def test_with_election_access_wrong_org(
    client: FlaskClient, org_id: str, election_id: str
):
    create_org_and_admin("Org 2", "aa2@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "aa2@example.com")
    rv = client.get(f"/election/{election_id}/test_auth")
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"aa2@example.com does not have access to organization {org_id}",
            }
        ]
    }


def test_with_election_access_not_found(
    client: FlaskClient, election_id: str  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "aa2@example.com")
    rv = client.get(f"/election/not-a-real-id/test_auth")
    assert rv.status_code == 404


def test_with_election_access_jurisdiction_admin(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, JA_EMAIL)
    rv = client.get(f"/election/{election_id}/test_auth")
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"{JA_EMAIL} is not logged in as an audit admin and so does not have access to organization {org_id}",
            }
        ]
    }


def test_with_election_access_anonymous_user(
    client: FlaskClient, org_id: str, election_id: str
):
    clear_logged_in_user(client)
    rv = client.get(f"/election/{election_id}/test_auth")
    assert rv.status_code == 401
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Unauthorized",
                "message": f"Anonymous users do not have access to organization {org_id}",
            }
        ]
    }


def test_with_jurisdiction_access_jurisdiction_admin(
    client: FlaskClient, election_id: str, jurisdiction_id: str
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, JA_EMAIL)
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_id}/test_auth")
    assert rv.status_code == 200
    assert json.loads(rv.data) == [election_id, jurisdiction_id]


def test_with_jurisdiction_access_wrong_org(
    client: FlaskClient, election_id: str, jurisdiction_id: str
):
    org_id_2, _ = create_org_and_admin("Org 2", "aa2@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "aa2@example.com")
    election_id_2 = create_election(client, organization_id=org_id_2)
    create_jurisdiction_and_admin(election_id_2, user_email="ja2@example.com")
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, "ja2@example.com")
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_id}/test_auth")
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"ja2@example.com does not have access to jurisdiction {jurisdiction_id}",
            }
        ]
    }


def test_with_jurisdiction_access_wrong_election(
    client: FlaskClient, org_id: str, election_id: str, jurisdiction_id: str
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, AA_EMAIL)
    election_id_2 = create_election(
        client, audit_name="Audit 2", organization_id=org_id
    )
    create_jurisdiction_and_admin(election_id_2, user_email="ja2@example.com")
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, "ja2@example.com")
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_id}/test_auth")
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"ja2@example.com does not have access to jurisdiction {jurisdiction_id}",
            }
        ]
    }


def test_with_jurisdiction_access_wrong_jurisdiction(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,  # pylint: disable=unused-argument
):
    jurisdiction_id_2, _ = create_jurisdiction_and_admin(
        election_id, jurisdiction_name="Jurisdiction 2", user_email="ja2@example.com"
    )
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_id_2}/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"{JA_EMAIL} does not have access to jurisdiction {jurisdiction_id_2}",
            }
        ]
    }


def test_with_jurisdiction_access_election_not_found(
    client: FlaskClient,
    election_id: str,  # pylint: disable=unused-argument
    jurisdiction_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, JA_EMAIL)
    rv = client.get(f"/election/not-a-real-id/jurisdiction/{jurisdiction_id}/test_auth")
    assert rv.status_code == 404


def test_with_jurisdiction_access_jurisdiction_not_found(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, JA_EMAIL)
    rv = client.get(f"/election/{election_id}/jurisdiction/not-a-real-id/test_auth")
    assert rv.status_code == 404


def test_with_jurisdiction_access_audit_admin(
    client: FlaskClient, election_id: str, jurisdiction_id: str
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, AA_EMAIL)
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_id}/test_auth")
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"{AA_EMAIL} is not logged in as a jurisdiction admin and so does not have access to jurisdiction {jurisdiction_id}",
            }
        ]
    }


def test_with_jurisdiction_access_anonymous_user(
    client: FlaskClient, election_id: str, jurisdiction_id: str
):
    clear_logged_in_user(client)
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_id}/test_auth")
    assert rv.status_code == 401
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Unauthorized",
                "message": f"Anonymous users do not have access to jurisdiction {jurisdiction_id}",
            }
        ]
    }

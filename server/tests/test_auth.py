import time
from datetime import timedelta
import json, re, uuid
from typing import List, Optional
from unittest.mock import Mock, MagicMock, patch
from urllib.parse import urlparse, parse_qs
import pytest
from flask.testing import FlaskClient

from ..auth import UserType
from ..auth.routes import auth0_sa, auth0_aa, auth0_ja
from ..models import *  # pylint: disable=wildcard-import
from ..util.jsonschema import JSONDict
from .helpers import *  # pylint: disable=wildcard-import
from ..app import app


SA_EMAIL = "sa@voting.works"
AA_EMAIL = "aa@example.com"
JA_EMAIL = "ja@example.com"


@pytest.fixture
def aa_email(org_id: str) -> str:
    email = f"aa-{org_id}@example.com"
    audit_admin = create_user(email)
    admin = AuditAdministration(organization_id=org_id, user_id=audit_admin.id)
    db_session.add(admin)
    db_session.commit()
    return email


@pytest.fixture
def election_id(client: FlaskClient, org_id: str, aa_email: str) -> str:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    return create_election(client, organization_id=org_id)


@pytest.fixture
def jurisdiction_id(election_id: str) -> str:
    jurisdiction = create_jurisdiction(election_id)
    return str(jurisdiction.id)


@pytest.fixture
def ja_email(jurisdiction_id: str) -> str:
    email = f"ja-{jurisdiction_id}@example.com"
    jurisdiction_admin = create_user(email)
    admin = JurisdictionAdministration(
        jurisdiction_id=jurisdiction_id, user_id=jurisdiction_admin.id
    )
    db_session.add(admin)
    db_session.commit()
    return email


def create_round(election_id: str, round_num=1) -> str:
    round = Round(id=str(uuid.uuid4()), election_id=election_id, round_num=round_num)
    db_session.add(round)
    db_session.commit()
    return str(round.id)


@pytest.fixture
def round_id(election_id: str) -> str:
    return create_round(election_id)


def create_audit_board(jurisdiction_id: str, round_id: str) -> str:
    audit_board_id = str(uuid.uuid4())
    audit_board = AuditBoard(
        id=audit_board_id,
        jurisdiction_id=jurisdiction_id,
        round_id=round_id,
        passphrase=f"passphrase-{audit_board_id}",
    )
    db_session.add(audit_board)
    db_session.commit()
    return str(audit_board.id)


@pytest.fixture
def audit_board_id(jurisdiction_id: str, round_id: str) -> str:
    return create_audit_board(jurisdiction_id, round_id)


# Tests for log in/log out flows


def check_redirect_contains_redirect_uri(response, expected_url):
    assert response.status_code == 302
    location = urlparse(response.location)
    query_vars = parse_qs(location.query)
    assert query_vars["redirect_uri"]
    redirect_uri = query_vars["redirect_uri"][0]

    # common problem is a trailing slash on origin
    # which makes a double slash like 'http://localhost//authorize'
    # which won't work. So testing to make sure there is no '//'
    # other than '://'
    assert re.search("[^:]//", redirect_uri) is None
    assert expected_url in redirect_uri


def test_superadmin_start(client: FlaskClient):
    rv = client.get("/auth/superadmin/start")
    check_redirect_contains_redirect_uri(rv, "/auth/superadmin/callback")


def test_superadmin_callback(
    client: FlaskClient, org_id: str,  # pylint: disable=unused-argument
):
    with patch.object(auth0_sa, "authorize_access_token", return_value=None):
        mock_response = Mock()
        mock_response.json = MagicMock(return_value={"email": SA_EMAIL})
        with patch.object(auth0_sa, "get", return_value=mock_response):

            rv = client.get("/auth/superadmin/callback?code=foobar")
            assert rv.status_code == 302
            assert urlparse(rv.location).path == "/superadmin/"

            with client.session_transaction() as session:  # type: ignore
                assert session["_superadmin"]
                assert list(session.keys()) == ["_superadmin"]

            assert auth0_sa.authorize_access_token.called
            assert auth0_sa.get.called


def test_superadmin_callback_rejected(
    client: FlaskClient, org_id: str,  # pylint: disable=unused-argument
):
    bad_user_infos: List[Optional[JSONDict]] = [None, {}, {"email": AA_EMAIL}]
    for bad_user_info in bad_user_infos:
        with patch.object(auth0_sa, "authorize_access_token", return_value=None):
            mock_response = Mock()
            mock_response.json = MagicMock(return_value=bad_user_info)
            with patch.object(auth0_sa, "get", return_value=mock_response):

                rv = client.get("/auth/superadmin/callback?code=foobar")
                assert rv.status_code == 302
                assert urlparse(rv.location).path == "/"

                with client.session_transaction() as session:  # type: ignore
                    assert "_superadmin" not in session

                assert auth0_sa.authorize_access_token.called
                assert auth0_sa.get.called


def test_auditadmin_start(client: FlaskClient):
    rv = client.get("/auth/auditadmin/start")
    check_redirect_contains_redirect_uri(rv, "/auth/auditadmin/callback")


def test_auditadmin_callback(client: FlaskClient, aa_email: str):
    with patch.object(auth0_aa, "authorize_access_token", return_value=None):

        mock_response = Mock()
        mock_response.json = MagicMock(return_value={"email": aa_email})
        with patch.object(auth0_aa, "get", return_value=mock_response):

            rv = client.get("/auth/auditadmin/callback?code=foobar")
            assert rv.status_code == 302

            with client.session_transaction() as session:  # type: ignore
                assert session["_user"]["type"] == UserType.AUDIT_ADMIN
                assert session["_user"]["key"] == aa_email

            assert auth0_aa.authorize_access_token.called
            assert auth0_aa.get.called


def test_jurisdictionadmin_start(client: FlaskClient):
    rv = client.get("/auth/jurisdictionadmin/start")
    check_redirect_contains_redirect_uri(rv, "/auth/jurisdictionadmin/callback")


def test_jurisdictionadmin_callback(client: FlaskClient, ja_email: str):
    with patch.object(auth0_ja, "authorize_access_token", return_value=None):

        mock_response = Mock()
        mock_response.json = MagicMock(return_value={"email": ja_email})
        with patch.object(auth0_ja, "get", return_value=mock_response):

            rv = client.get("/auth/jurisdictionadmin/callback?code=foobar")
            assert rv.status_code == 302

            with client.session_transaction() as session:  # type: ignore
                assert session["_user"]["type"] == UserType.JURISDICTION_ADMIN
                assert session["_user"]["key"] == ja_email

            assert auth0_ja.authorize_access_token.called
            assert auth0_ja.get.called


def test_audit_board_log_in(
    client: FlaskClient, election_id: str, audit_board_id: str,
):
    audit_board = AuditBoard.query.get(audit_board_id)
    rv = client.get(f"/auditboard/{audit_board.passphrase}")
    assert rv.status_code == 302
    location = urlparse(rv.location)
    assert location.path == f"/election/{election_id}/audit-board/{audit_board.id}"

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"]["type"] == UserType.AUDIT_BOARD
        assert session["_user"]["key"] == audit_board.id


def test_logout(client: FlaskClient, aa_email: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    set_superadmin(client)

    rv = client.get("/auth/logout")
    assert rv.status_code == 302

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"] is None
        assert "_superadmin" not in session.keys()

    # logging out a second time should not cause an error
    rv = client.get("/auth/logout")
    assert rv.status_code == 302


def test_auth0_error(client: FlaskClient):
    rv = client.get(
        "/auth/auditadmin/callback?error=invalid_request&error_description=some%20error%20from%20auth0"
    )
    assert rv.status_code == 302
    location = urlparse(rv.location)
    assert location.path == "/"
    assert (
        location.query
        == "error=oauth&message=Login+error%3A+invalid_request+-+some+error+from+auth0"
    )


# Tests for /api/me


def test_auth_me_audit_admin(
    client: FlaskClient, election_id: str, org_id: str, aa_email: str
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    election = Election.query.get(election_id)

    rv = client.get("/api/me")
    assert json.loads(rv.data) == {
        "type": "audit_admin",
        "email": aa_email,
        "organizations": [
            {
                "name": "Test Org test_auth_me_audit_admin",
                "id": org_id,
                "elections": [
                    {
                        "id": election_id,
                        "auditName": election.audit_name,
                        "electionName": None,
                        "state": None,
                    }
                ],
            }
        ],
        "jurisdictions": [],
    }


def test_auth_me_jurisdiction_admin(
    client: FlaskClient, election_id: str, jurisdiction_id: str, ja_email: str
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    election = Election.query.get(election_id)

    rv = client.get("/api/me")
    assert json.loads(rv.data) == {
        "type": UserType.JURISDICTION_ADMIN,
        "email": ja_email,
        "organizations": [],
        "jurisdictions": [
            {
                "id": jurisdiction_id,
                "name": "Test Jurisdiction",
                "election": {
                    "id": election_id,
                    "auditName": election.audit_name,
                    "electionName": None,
                    "state": None,
                },
            }
        ],
    }


def test_auth_me_audit_board(
    client: FlaskClient, audit_board_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get("/api/me")
    audit_board = AuditBoard.query.get(audit_board_id)
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "type": UserType.AUDIT_BOARD,
        "id": audit_board.id,
        "jurisdictionId": audit_board.jurisdiction_id,
        "roundId": audit_board.round_id,
        "name": audit_board.name,
        "members": [],
        "signedOffAt": None,
    }


def test_auth_me_not_logged_in(client: FlaskClient):
    clear_logged_in_user(client)
    rv = client.get("/api/me")
    assert rv.status_code == 200
    assert json.loads(rv.data) is None


def test_session_expiration(client: FlaskClient, aa_email: str):
    original_session_lifetime = app.permanent_session_lifetime
    assert original_session_lifetime > timedelta(minutes=1)

    # In order to make sure the session only expires after the user has been
    # inactive for the specified amount of time, we need to make sure the
    # session gets refreshed every request. This is turned on by default in
    # Flask, so we just check to make sure it didn't accidentally get turned
    # off.
    assert app.config["SESSION_REFRESH_EACH_REQUEST"] is True

    app.permanent_session_lifetime = timedelta(milliseconds=1)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    rv = client.get("/api/me")
    assert json.loads(rv.data) is not None

    time.sleep(1.0)

    rv = client.get("/api/me")
    assert json.loads(rv.data) is None

    app.permanent_session_lifetime = original_session_lifetime


# Tests for route decorators. We have added special routes to test the
# decorators that are set up in conftest.py.


def test_restrict_access_audit_admin(client: FlaskClient, election_id: str, aa_email):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    rv = client.get(f"/api/election/{election_id}/test_auth")
    assert rv.status_code == 200
    assert json.loads(rv.data) == election_id


def test_restrict_access_audit_admin_wrong_org(
    client: FlaskClient, org_id: str, election_id: str
):
    create_org_and_admin("Org 2", "aa2@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "aa2@example.com")
    rv = client.get(f"/api/election/{election_id}/test_auth")
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"aa2@example.com does not have access to organization {org_id}",
            }
        ]
    }


def test_restrict_access_audit_admin_not_found(
    client: FlaskClient,
    election_id: str,  # pylint: disable=unused-argument
    aa_email: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    rv = client.get("/api/election/not-a-real-id/test_auth")
    assert rv.status_code == 404


def test_restrict_access_audit_admin_with_jurisdiction_admin(
    client: FlaskClient,
    org_id: str,  # pylint: disable=unused-argument
    election_id: str,
    ja_email: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.get(f"/api/election/{election_id}/test_auth")
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": "Access forbidden for user type jurisdiction_admin",
            }
        ]
    }


def test_restrict_access_audit_admin_audit_board_user(
    client: FlaskClient,
    org_id: str,  # pylint: disable=unused-argument
    election_id: str,
    audit_board_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)

    rv = client.get(f"/api/election/{election_id}/test_auth")
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": "Access forbidden for user type audit_board",
            }
        ]
    }


def test_restrict_access_audit_admin_anonymous_user(
    client: FlaskClient,
    org_id: str,  # pylint: disable=unused-argument
    election_id: str,
):
    clear_logged_in_user(client)
    rv = client.get(f"/api/election/{election_id}/test_auth")
    assert rv.status_code == 401
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Unauthorized", "message": "Please log in to access Arlo",}
        ]
    }


def test_restrict_access_jurisdiction_admin_jurisdiction_admin(
    client: FlaskClient, election_id: str, jurisdiction_id: str, ja_email: str
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/test_auth"
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == [election_id, jurisdiction_id]


def test_restrict_access_jurisdiction_admin_wrong_org(
    client: FlaskClient, election_id: str, jurisdiction_id: str
):
    org_id_2, _ = create_org_and_admin("Org 2", "aa2@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "aa2@example.com")
    election_id_2 = create_election(client, organization_id=org_id_2)
    create_jurisdiction_and_admin(election_id_2, user_email="ja2@example.com")
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, "ja2@example.com")
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"ja2@example.com does not have access to jurisdiction {jurisdiction_id}",
            }
        ]
    }


def test_restrict_access_jurisdiction_admin_wrong_election(
    client: FlaskClient, org_id: str, election_id: str, aa_email: str
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    election_id_2 = create_election(
        client, audit_name="Audit 2", organization_id=org_id
    )
    jurisdiction_id_2, _ = create_jurisdiction_and_admin(
        election_id_2, user_email="ja2@example.com"
    )
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, "ja2@example.com")
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id_2}/test_auth"
    )
    assert rv.status_code == 404


def test_restrict_access_jurisdiction_admin_wrong_jurisdiction(
    client: FlaskClient, election_id: str, ja_email: str,
):
    jurisdiction_id_2, _ = create_jurisdiction_and_admin(
        election_id, jurisdiction_name="Jurisdiction 2", user_email="ja2@example.com"
    )
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id_2}/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"{ja_email} does not have access to jurisdiction {jurisdiction_id_2}",
            }
        ]
    }


def test_restrict_access_jurisdiction_admin_election_not_found(
    client: FlaskClient, jurisdiction_id: str, ja_email: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.get(
        f"/api/election/not-a-real-id/jurisdiction/{jurisdiction_id}/test_auth"
    )
    assert rv.status_code == 404


def test_restrict_access_jurisdiction_admin_jurisdiction_not_found(
    client: FlaskClient, election_id: str, ja_email: str
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.get(f"/api/election/{election_id}/jurisdiction/not-a-real-id/test_auth")
    assert rv.status_code == 404


def test_restrict_access_jurisdiction_admin_with_audit_admin(
    client: FlaskClient, election_id: str, jurisdiction_id: str, aa_email: str
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/test_auth"
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == [election_id, jurisdiction_id]


def test_restrict_access_jurisdiction_admin_with_audit_board_user(
    client: FlaskClient, election_id: str, jurisdiction_id: str, audit_board_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": "Access forbidden for user type audit_board",
            }
        ]
    }


def test_restrict_access_jurisdiction_admin_with_anonymous_user(
    client: FlaskClient, election_id: str, jurisdiction_id: str
):
    clear_logged_in_user(client)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/test_auth"
    )
    assert rv.status_code == 401
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Unauthorized", "message": "Please log in to access Arlo"}
        ]
    }


def test_restrict_access_audit_board_with_audit_board_user(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,
    round_id: str,
    audit_board_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == [
        election_id,
        jurisdiction_id,
        round_id,
        audit_board_id,
    ]


def test_restrict_access_audit_board_with_audit_admin(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,
    round_id: str,
    audit_board_id: str,
    aa_email: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": "Access forbidden for user type audit_admin",
            }
        ]
    }


def test_restrict_access_audit_board_with_jurisdiction_admin(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,
    round_id: str,
    audit_board_id: str,
    ja_email: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": "Access forbidden for user type jurisdiction_admin",
            }
        ]
    }


def test_restrict_access_audit_board_with_anonymous_user(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,
    round_id: str,
    audit_board_id: str,
):
    clear_logged_in_user(client)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 401
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Unauthorized", "message": "Please log in to access Arlo"}
        ]
    }


def test_restrict_access_audit_board_wrong_org(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,
    round_id: str,
    audit_board_id: str,
):
    org_id_2, _ = create_org_and_admin("Org 3", "aa3@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "aa3@example.com")
    election_id_2 = create_election(client, organization_id=org_id_2)
    jurisdiction_id_2, _ = create_jurisdiction_and_admin(
        election_id_2, user_email="ja3@example.com"
    )
    round_id_2 = create_round(election_id_2)
    audit_board_id_2 = create_audit_board(jurisdiction_id_2, round_id_2)

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id_2)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"User does not have access to audit board {audit_board_id}",
            }
        ]
    }


def test_restrict_access_audit_board_wrong_election(
    client: FlaskClient, audit_board_id: str,
):
    org_id_2, _ = create_org_and_admin("Org 4", "aa4@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "aa4@example.com")
    election_id_2 = create_election(client, organization_id=org_id_2)
    jurisdiction_id_2, _ = create_jurisdiction_and_admin(
        election_id_2, user_email="ja4@example.com"
    )
    round_id_2 = create_round(election_id_2)

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)

    rv = client.get(
        f"/api/election/{election_id_2}/jurisdiction/{jurisdiction_id_2}/round/{round_id_2}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 404


def test_restrict_access_audit_board_wrong_jurisdiction(
    client: FlaskClient,
    election_id: str,
    round_id: str,
    audit_board_id: str,
    aa_email: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    jurisdiction_id_2, _ = create_jurisdiction_and_admin(
        election_id, jurisdiction_name="J5", user_email="ja5@example.com"
    )

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id_2}/round/{round_id}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 404


def test_restrict_access_audit_board_wrong_round(
    client: FlaskClient, election_id: str, jurisdiction_id: str, audit_board_id: str,
):
    round_id_2 = create_round(election_id, round_num=2)
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id_2}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 404


def test_restrict_access_audit_board_wrong_audit_board(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,
    round_id: str,
    audit_board_id: str,
):
    audit_board_id_2 = create_audit_board(jurisdiction_id, round_id)
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/{audit_board_id_2}/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"User does not have access to audit board {audit_board_id_2}",
            }
        ]
    }


def test_restrict_access_audit_board_election_not_found(
    client: FlaskClient, jurisdiction_id: str, round_id: str, audit_board_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get(
        f"/api/election/not-a-real-id/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 404


def test_restrict_access_audit_board_jurisdiction_not_found(
    client: FlaskClient, election_id: str, round_id: str, audit_board_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/not-a-real-id/round/{round_id}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 404


def test_restrict_access_audit_board_round_not_found(
    client: FlaskClient, election_id: str, jurisdiction_id: str, audit_board_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/not-a-real-id/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 404


def test_restrict_access_audit_board_audit_board_not_found(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,
    round_id: str,
    audit_board_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/not-a-real-id/test_auth"
    )
    assert rv.status_code == 404


def test_superadmin(client: FlaskClient):
    set_superadmin(client)
    rv = client.get("/superadmin/")
    assert rv.status_code == 200

    clear_superadmin(client)
    rv = client.get("/superadmin/")
    assert rv.status_code == 403

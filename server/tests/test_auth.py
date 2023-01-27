from smtplib import SMTPServerDisconnected
import time
from datetime import timedelta
import json, re, uuid
from typing import List, Optional
from unittest.mock import Mock, MagicMock, patch
from urllib.parse import urlparse, parse_qs
import pytest
from flask.testing import FlaskClient

from ..auth import UserType
from ..auth.auth_routes import auth0_sa, auth0_aa
from ..models import *  # pylint: disable=wildcard-import
from ..util.jsonschema import JSONDict
from .helpers import *  # pylint: disable=wildcard-import
from .. import config
from ..app import csrf, app


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
def batch_election_id(client: FlaskClient, org_id: str, aa_email: str) -> str:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    return create_election(
        client,
        organization_id=org_id,
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
    )


@pytest.fixture
def jurisdiction_id(election_id: str) -> str:
    jurisdiction = create_jurisdiction(election_id)
    return str(jurisdiction.id)


@pytest.fixture
def batch_jurisdiction_id(batch_election_id: str) -> str:
    jurisdiction = create_jurisdiction(batch_election_id)
    return str(jurisdiction.id)


@pytest.fixture
def ja_email(jurisdiction_id: str) -> str:
    email = f"ja-{jurisdiction_id}@example.com"
    create_jurisdiction_admin(jurisdiction_id, email)
    return email


@pytest.fixture
def batch_ja_email(batch_jurisdiction_id: str) -> str:
    email = f"ja-{jurisdiction_id}@example.com"
    create_jurisdiction_admin(batch_jurisdiction_id, email)
    return email


def create_round(election_id: str, round_num=1) -> str:
    round = Round(id=str(uuid.uuid4()), election_id=election_id, round_num=round_num)
    db_session.add(round)
    db_session.commit()
    return str(round.id)


@pytest.fixture
def round_id(election_id: str) -> str:
    return create_round(election_id)


@pytest.fixture
def batch_round_id(batch_election_id: str) -> str:
    return create_round(batch_election_id)


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


def create_tally_entry_user(jurisdiction_id: str) -> str:
    tally_entry_user_id = str(uuid.uuid4())
    tally_entry_user = TallyEntryUser(
        id=tally_entry_user_id,
        jurisdiction_id=jurisdiction_id,
        login_confirmed_at=datetime.now(timezone.utc),
    )
    db_session.add(tally_entry_user)
    db_session.commit()
    return str(tally_entry_user.id)


@pytest.fixture
def tally_entry_user_id(batch_jurisdiction_id: str) -> str:
    return create_tally_entry_user(batch_jurisdiction_id)


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


def test_support_start(client: FlaskClient):
    rv = client.get("/auth/support/start")
    check_redirect_contains_redirect_uri(rv, "/auth/support/callback")


def test_support_callback(
    client: FlaskClient, org_id: str,  # pylint: disable=unused-argument
):
    with patch.object(auth0_sa, "authorize_access_token", return_value=None):
        mock_response = Mock()
        mock_response.json = MagicMock(return_value={"email": SA_EMAIL})
        with patch.object(auth0_sa, "get", return_value=mock_response):

            rv = client.get("/auth/support/callback?code=foobar")
            assert rv.status_code == 302
            assert urlparse(rv.location).path == "/support"

            with client.session_transaction() as session:  # type: ignore
                assert session["_support_user"] == SA_EMAIL
                assert_is_date(session["_created_at"])
                assert datetime.now(timezone.utc) - datetime.fromisoformat(
                    session["_created_at"]
                ) < timedelta(seconds=1)
                assert_is_date(session["_last_request_at"])
                assert datetime.now(timezone.utc) - datetime.fromisoformat(
                    session["_last_request_at"]
                ) < timedelta(seconds=1)
                assert session.get("_user") is None

            assert auth0_sa.authorize_access_token.called
            assert auth0_sa.get.called


def test_support_callback_rejected(
    client: FlaskClient, org_id: str,  # pylint: disable=unused-argument
):
    bad_user_infos: List[Optional[JSONDict]] = [None, {}, {"email": AA_EMAIL}]
    for bad_user_info in bad_user_infos:
        with patch.object(auth0_sa, "authorize_access_token", return_value=None):
            mock_response = Mock()
            mock_response.json = MagicMock(return_value=bad_user_info)
            with patch.object(auth0_sa, "get", return_value=mock_response):

                rv = client.get("/auth/support/callback?code=foobar")
                assert rv.status_code == 302
                assert urlparse(rv.location).path == "/"

                with client.session_transaction() as session:  # type: ignore
                    assert session.get("_support_user") is None

                assert auth0_sa.authorize_access_token.called
                assert auth0_sa.get.called


def test_support_callback_multiple_allowed_domains(
    client: FlaskClient, org_id: str,  # pylint: disable=unused-argument
):
    config.SUPPORT_EMAIL_DOMAINS = ["voting.works", "example.gov"]
    with patch.object(auth0_sa, "authorize_access_token", return_value=None):
        mock_response = Mock()
        mock_response.json = MagicMock(return_value={"email": "sa@example.gov"})
        with patch.object(auth0_sa, "get", return_value=mock_response):
            rv = client.get("/auth/support/callback?code=foobar")
            assert rv.status_code == 302
            assert urlparse(rv.location).path == "/support"

            with client.session_transaction() as session:  # type: ignore
                assert session["_support_user"] == "sa@example.gov"
    config.SUPPORT_EMAIL_DOMAINS = ["voting.works"]


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
                assert_is_date(session["_created_at"])
                assert (
                    datetime.now(timezone.utc)
                    - datetime.fromisoformat(session["_created_at"])
                ) < timedelta(seconds=1)
                assert_is_date(session["_last_request_at"])
                assert (
                    datetime.now(timezone.utc)
                    - datetime.fromisoformat(session["_last_request_at"])
                ) < timedelta(seconds=1)

            assert auth0_aa.authorize_access_token.called
            assert auth0_aa.get.called


def parse_login_code(text: str):
    code_match = re.search(r"Your verification code is: (\d\d\d\d\d\d)", text)
    assert code_match
    code = code_match.group(1)
    assert code
    return code


def parse_login_code_from_smtp(mock_smtp):
    message = mock_smtp.return_value.send_message.call_args.args[0]
    return parse_login_code(message.get_body(("plain")).get_content())


@patch("smtplib.SMTP", autospec=True)
def test_jurisdiction_admin_login(mock_smtp, client: FlaskClient, ja_email: str):
    rv = post_json(
        client,
        "/auth/jurisdictionadmin/code",
        dict(email=ja_email.upper()),  # Login should not be case sensitive
    )
    assert_ok(rv)

    mock_smtp.assert_called_once_with(host=config.SMTP_HOST, port=config.SMTP_PORT)
    mock_smtp.return_value.login.assert_called_once_with(
        config.SMTP_USERNAME, config.SMTP_PASSWORD
    )
    mock_smtp.return_value.send_message.assert_called_once()
    message = mock_smtp.return_value.send_message.call_args.args[0]
    assert message["To"] == ja_email
    assert message["From"] == "Arlo Support <rla@vx.support>"
    assert (
        message["Subject"] == "Welcome to Arlo - Use the Code in this Email to Log In"
    )

    code = parse_login_code(message.get_body(("plain")).get_content())
    assert code in message.get_body(("html")).get_content()

    rv = post_json(
        client,
        "/auth/jurisdictionadmin/login",
        dict(email=ja_email.upper(), code=code),  # Login should not be case sensitive
    )
    assert_ok(rv)

    # JA should be logged in
    with client.session_transaction() as session:  # type: ignore
        assert session["_user"]["type"] == UserType.JURISDICTION_ADMIN
        assert session["_user"]["key"] == ja_email
        assert_is_date(session["_created_at"])
        assert (
            datetime.now(timezone.utc) - datetime.fromisoformat(session["_created_at"])
        ) < timedelta(seconds=1)
        assert_is_date(session["_last_request_at"])
        assert (
            datetime.now(timezone.utc)
            - datetime.fromisoformat(session["_last_request_at"])
        ) < timedelta(seconds=1)

    time.sleep(1)

    # Try requesting a code again - should get a new code
    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=ja_email))
    assert_ok(rv)
    assert parse_login_code_from_smtp(mock_smtp) != code


@patch("smtplib.SMTP", autospec=True)
def test_jurisdiction_admin_two_users(
    mock_smtp, client: FlaskClient, election_id: str, ja_email: str
):
    create_jurisdiction_and_admin(election_id, "Jurisdiction 2", "ja2@example.com")

    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=ja_email))
    assert_ok(rv)
    code = parse_login_code_from_smtp(mock_smtp)

    rv = post_json(
        client, "/auth/jurisdictionadmin/code", dict(email="ja2@example.com")
    )
    assert_ok(rv)
    assert parse_login_code_from_smtp(mock_smtp) != code


def test_jurisdiction_admin_bad_email(client: FlaskClient):
    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=DEFAULT_AA_EMAIL))
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "This email address is not authorized to access Arlo. Please check that you typed the email correctly, or contact your Arlo administrator for access.",
            }
        ]
    }

    rv = post_json(
        client, "/auth/jurisdictionadmin/code", dict(email="invalid@example.com")
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "This email address is not authorized to access Arlo. Please check that you typed the email correctly, or contact your Arlo administrator for access.",
            }
        ]
    }


@patch("smtplib.SMTP", autospec=True)
def test_jurisdiction_admin_reuse_code(mock_smtp, client: FlaskClient, ja_email: str):
    config.LOGIN_CODE_LIFETIME = timedelta(seconds=1)

    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=ja_email))
    assert_ok(rv)
    code = parse_login_code_from_smtp(mock_smtp)

    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=ja_email))
    assert_ok(rv)
    assert parse_login_code_from_smtp(mock_smtp) == code

    time.sleep(1.0)

    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=ja_email))
    assert_ok(rv)
    assert parse_login_code_from_smtp(mock_smtp) != code


@patch("smtplib.SMTP", autospec=True)
def test_jurisdiction_admin_smtp_error(mock_smtp, client: FlaskClient, ja_email: str):
    app.config["PROPAGATE_EXCEPTIONS"] = False

    # Mock error when using the wrong SMTP password
    mock_smtp.return_value.send_message.side_effect = SMTPServerDisconnected(
        "Connection unexpectedly closed"
    )

    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=ja_email))
    assert rv.status_code == 500
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Internal Server Error",
                "message": "Connection unexpectedly closed",
            }
        ]
    }


@patch("smtplib.SMTP", autospec=True)
def test_jurisdiction_admin_bad_code(mock_smtp, client: FlaskClient, ja_email: str):
    clear_logged_in_user(client)

    # Try logging in without generating a code
    rv = post_json(
        client, "/auth/jurisdictionadmin/login", dict(email=ja_email, code=None)
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Bad Request", "message": "Please request a new code.",}
        ]
    }

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"] is None

    # Try again with a code generated
    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=ja_email))
    assert_ok(rv)
    code = parse_login_code_from_smtp(mock_smtp)

    rv = post_json(
        client, "/auth/jurisdictionadmin/login", dict(email=ja_email, code="123456")
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Invalid code. Try entering the code again or click Back and request a new code.",
            }
        ]
    }

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"] is None

    # Try with the right code, wrong email
    rv = post_json(
        client, "/auth/jurisdictionadmin/login", dict(email=DEFAULT_AA_EMAIL, code=code)
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Bad Request", "message": "Invalid email address.",}]
    }

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"] is None


@patch("smtplib.SMTP", autospec=True)
def test_jurisdiction_admin_too_many_attempts(
    mock_smtp, client: FlaskClient, ja_email: str
):
    config.LOGIN_CODE_LIFETIME = timedelta(seconds=1)
    clear_logged_in_user(client)

    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=ja_email))
    assert_ok(rv)
    code = parse_login_code_from_smtp(mock_smtp)

    for _ in range(10):
        rv = post_json(
            client, "/auth/jurisdictionadmin/login", dict(email=ja_email, code="123456")
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Bad Request",
                    "message": "Invalid code. Try entering the code again or click Back and request a new code.",
                }
            ]
        }

    rv = post_json(
        client, "/auth/jurisdictionadmin/login", dict(email=ja_email, code=code)
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Too many incorrect login attempts. Please wait 15 minutes and then request a new code.",
            }
        ]
    }

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"] is None

    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=ja_email))
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Too many incorrect login attempts. Please wait 15 minutes and then request a new code.",
            }
        ]
    }

    time.sleep(1)

    rv = post_json(client, "/auth/jurisdictionadmin/code", dict(email=ja_email))
    assert_ok(rv)
    new_code = parse_login_code_from_smtp(mock_smtp)
    assert new_code != code
    rv = post_json(
        client, "/auth/jurisdictionadmin/login", dict(email=ja_email, code=new_code)
    )
    assert_ok(rv)


def test_audit_board_log_in(
    client: FlaskClient, election_id: str, audit_board_id: str,
):
    audit_board = AuditBoard.query.get(audit_board_id)
    db_session.expunge(audit_board)

    rv = client.get(f"/auditboard/{audit_board.passphrase}")
    assert rv.status_code == 302
    location = urlparse(rv.location)
    assert location.path == f"/election/{election_id}/audit-board/{audit_board_id}"

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"]["type"] == UserType.AUDIT_BOARD
        assert session["_user"]["key"] == audit_board_id
        assert_is_date(session["_created_at"])
        assert (
            datetime.now(timezone.utc) - datetime.fromisoformat(session["_created_at"])
        ) < timedelta(seconds=1)
        assert_is_date(session["_last_request_at"])
        assert (
            datetime.now(timezone.utc)
            - datetime.fromisoformat(session["_last_request_at"])
        ) < timedelta(seconds=1)


def test_tally_entry_login(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    batch_ja_email: str,
    batch_round_id: str,  # pylint: disable=unused-argument
):
    tally_entry_client = app.test_client()

    election_id = batch_election_id
    jurisdiction_id = batch_jurisdiction_id
    ja_email = batch_ja_email
    election = Election.query.get(election_id)
    jurisdiction = Jurisdiction.query.get(jurisdiction_id)

    db_session.expunge(election)
    db_session.expunge(jurisdiction)

    # Tally entry login starts out turned off
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.get(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == dict(passphrase=None, loginRequests=[],)

    # Turn on tally entry login, generating a login link passphrase
    rv = client.post(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert_ok(rv)

    rv = client.get(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 200
    tally_entry_status = json.loads(rv.data)
    compare_json(
        tally_entry_status, dict(passphrase=assert_is_passphrase, loginRequests=[])
    )

    # As an un-logged-in user, visit the login link
    login_link = f"/tallyentry/{tally_entry_status['passphrase']}"
    rv = tally_entry_client.get(login_link)
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/tally-entry"

    # Load the jurisdiction info
    rv = tally_entry_client.get("/api/me")
    assert rv.status_code == 200
    tally_entry_me_response = json.loads(rv.data)
    compare_json(
        tally_entry_me_response,
        dict(
            user=dict(
                type="tally_entry",
                id=assert_is_id,
                loginCode=None,
                loginConfirmedAt=None,
                jurisdictionId=jurisdiction_id,
                jurisdictionName=jurisdiction.name,
                electionId=election_id,
                auditName=election.audit_name,
                roundId=batch_round_id,
                members=[],
            ),
            supportUser=None,
        ),
    )

    # Jurisdiction admin doesn't see the request yet
    rv = client.get(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 200
    tally_entry_status = json.loads(rv.data)
    compare_json(
        tally_entry_status, dict(passphrase=assert_is_passphrase, loginRequests=[])
    )

    # Enter tally entry user details and start login
    members = [
        dict(name="Alice", affiliation="DEM"),
        dict(name="Bob", affiliation=None),
    ]
    rv = post_json(tally_entry_client, "/auth/tallyentry/code", dict(members=members))
    assert_ok(rv)

    # Poll for login status
    rv = tally_entry_client.get("/api/me")
    assert rv.status_code == 200
    tally_entry_me_response = json.loads(rv.data)
    login_code = tally_entry_me_response["user"]["loginCode"]
    assert login_code is not None
    assert re.match(r"^\d{3}$", login_code)
    assert tally_entry_me_response["user"]["members"] == members
    tally_entry_user_id = tally_entry_me_response["user"]["id"]

    # JA sees the login request on their screen
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.get(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 200
    compare_json(
        json.loads(rv.data),
        dict(
            passphrase=assert_is_passphrase,
            loginRequests=[
                dict(
                    tallyEntryUserId=tally_entry_user_id,
                    members=members,
                    loginConfirmedAt=None,
                )
            ],
        ),
    )

    # Tell login code to JA, who enters it on their screen
    rv = post_json(
        client,
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}/confirm",
        dict(tallyEntryUserId=tally_entry_user_id, loginCode=login_code),
    )
    assert_ok(rv)

    # Tally entry user is logged in
    rv = tally_entry_client.get("/api/me")
    assert rv.status_code == 200
    tally_entry_me_response = json.loads(rv.data)
    assert_is_date(tally_entry_me_response["user"]["loginConfirmedAt"])


def test_tally_entry_reject_login_request(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    batch_ja_email: str,
    batch_round_id: str,  # pylint: disable=unused-argument
):
    tally_entry_client = app.test_client()

    election_id = batch_election_id
    jurisdiction_id = batch_jurisdiction_id
    ja_email = batch_ja_email

    # Turn on tally entry login, generating a login link passphrase
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.post(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert_ok(rv)

    rv = client.get(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 200
    tally_entry_status = json.loads(rv.data)

    # As an un-logged-in user, visit the login link
    login_link = f"/tallyentry/{tally_entry_status['passphrase']}"
    rv = tally_entry_client.get(login_link)
    assert rv.status_code == 302

    # Enter tally entry user details and start login
    members = [
        dict(name="Alice", affiliation="DEM"),
        dict(name="Bob", affiliation=None),
    ]
    rv = post_json(tally_entry_client, "/auth/tallyentry/code", dict(members=members))
    assert_ok(rv)

    # JA sees the login request on their screen
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.get(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 200
    tally_entry_status = json.loads(rv.data)
    tally_entry_user_id = tally_entry_status["loginRequests"][0]["tallyEntryUserId"]

    # JA rejects the login request
    rv = post_json(
        client,
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}/reject",
        dict(tallyEntryUserId=tally_entry_user_id),
    )
    assert_ok(rv)

    # Tally entry user is logged out
    rv = tally_entry_client.get("/api/me")
    assert rv.status_code == 200
    assert json.loads(rv.data) == dict(user=None, supportUser=None)


def test_tally_entry_wrong_audit_type(
    client: FlaskClient, election_id: str, jurisdiction_id: str, ja_email: str
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.post(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Tally entry accounts are only supported in batch comparison audits.",
            }
        ]
    }


def test_tally_entry_generate_unique_code(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    batch_ja_email: str,
    batch_round_id: str,  # pylint: disable=unused-argument
):
    # To make sure that the login codes are unique within a jurisdiction, we'll
    # create tally entry users with every possible login code except one (000)
    # and then try to login. We should end up with login code 000.
    codes = [
        f"{d1}{d2}{d3}"
        for d1 in range(0, 10)
        for d2 in range(0, 10)
        for d3 in range(0, 10)
        if not (d1 == 0 and d2 == 0 and d3 == 0)
    ]
    assert len(codes) == 10 * 10 * 10 - 1
    for code in codes:
        db_session.add(
            TallyEntryUser(
                id=str(uuid.uuid4()),
                jurisdiction_id=batch_jurisdiction_id,
                login_code=code,
            )
        )
    db_session.commit()

    tally_entry_client = app.test_client()

    election_id = batch_election_id
    jurisdiction_id = batch_jurisdiction_id
    ja_email = batch_ja_email

    # Turn on tally entry login, generating a login link passphrase
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.post(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert_ok(rv)

    rv = client.get(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 200
    tally_entry_status = json.loads(rv.data)

    # As an un-logged-in user, visit the login link
    login_link = f"/tallyentry/{tally_entry_status['passphrase']}"
    rv = tally_entry_client.get(login_link)
    assert rv.status_code == 302

    # Enter tally entry user details and start login
    members = [dict(name="Alice", affiliation=None)]
    rv = post_json(tally_entry_client, "/auth/tallyentry/code", dict(members=members))
    assert_ok(rv)

    # Poll for login status
    rv = tally_entry_client.get("/api/me")
    assert rv.status_code == 200
    tally_entry_me_response = json.loads(rv.data)
    login_code = tally_entry_me_response["user"]["loginCode"]
    assert login_code == "000"


def test_tally_entry_invalid_passphrase(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    batch_ja_email: str,
):
    tally_entry_client = app.test_client()
    election_id = batch_election_id
    jurisdiction_id = batch_jurisdiction_id
    ja_email = batch_ja_email

    # Turn on tally entry login, generating a login link passphrase
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.post(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert_ok(rv)

    # As an un-logged-in user, visit an incorrect login link
    login_link = "/tallyentry/invalid-passphrase"
    rv = tally_entry_client.get(login_link)
    assert rv.status_code == 302
    location = urlparse(rv.location)
    assert location.path == "/tally-entry"
    assert location.query == "error=login_link_not_found"


def test_tally_entry_invalid_members(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    batch_ja_email: str,
):
    tally_entry_client = app.test_client()
    election_id = batch_election_id
    jurisdiction_id = batch_jurisdiction_id
    ja_email = batch_ja_email

    # Turn on tally entry login, generating a login link passphrase
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.post(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert_ok(rv)

    rv = client.get(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 200
    tally_entry_status = json.loads(rv.data)

    # As an un-logged-in user, visit the login link
    login_link = f"/tallyentry/{tally_entry_status['passphrase']}"
    rv = tally_entry_client.get(login_link)
    assert rv.status_code == 302

    invalid_member_requests = [
        ([{"affiliation": "DEM"}], "'name' is a required property"),
        ([{"name": "Joe Schmo"}], "'affiliation' is a required property"),
        ([{"name": "", "affiliation": "DEM"}], "'name' must not be empty."),
        ([{"name": None, "affiliation": "DEM"}], "None is not of type 'string'"),
        (
            [{"name": "Jane Plain", "affiliation": ""}],
            "'' is not one of ['DEM', 'REP', 'LIB', 'IND', 'OTH']",
        ),
        (
            [{"name": "Jane Plain", "affiliation": "Democrat"}],
            "'Democrat' is not one of ['DEM', 'REP', 'LIB', 'IND', 'OTH']",
        ),
        ([], "Must have at least one member.",),
        (
            [
                {"name": "Joe Schmo", "affiliation": "DEM"},
                {"name": "Jane Plain", "affiliation": "REP"},
                {"name": "Extra Member", "affiliation": "IND"},
            ],
            "Cannot have more than two members.",
        ),
    ]
    for invalid_members, expected_message in invalid_member_requests:
        rv = post_json(
            tally_entry_client, "/auth/tallyentry/code", dict(members=invalid_members)
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": expected_message}]
        }


def test_tally_entry_invalid_code(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    batch_ja_email: str,
    batch_round_id: str,  # pylint: disable=unused-argument
    election_id: str,
    jurisdiction_id: str,
    ja_email: str,
):
    tally_entry_client = app.test_client()
    other_election_id = election_id
    other_jurisdiction_id = jurisdiction_id
    other_ja_email = ja_email
    election_id = batch_election_id
    jurisdiction_id = batch_jurisdiction_id
    ja_email = batch_ja_email

    # Turn on tally entry login, generating a login link passphrase
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    rv = client.post(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert_ok(rv)

    rv = client.get(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 200
    tally_entry_status = json.loads(rv.data)

    # As an un-logged-in user, visit the login link
    login_link = f"/tallyentry/{tally_entry_status['passphrase']}"
    rv = tally_entry_client.get(login_link)
    assert rv.status_code == 302

    # Enter tally entry user details and start login
    members = [dict(name="Alice", affiliation=None)]
    rv = post_json(tally_entry_client, "/auth/tallyentry/code", dict(members=members))
    assert_ok(rv)

    # Poll for login status
    rv = tally_entry_client.get("/api/me")
    assert rv.status_code == 200
    tally_entry_me_response = json.loads(rv.data)
    login_code = tally_entry_me_response["user"]["loginCode"]
    tally_entry_user_id = tally_entry_me_response["user"]["id"]

    # Try to log in with an invalid code
    invalid_code = "000" if login_code != "000" else "111"
    rv = post_json(
        client,
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}/confirm",
        dict(tallyEntryUserId=tally_entry_user_id, code=invalid_code),
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Bad Request", "message": "Invalid code, please try again."}
        ]
    }

    # Try to log in with another user's code
    members = [dict(name="Alice", affiliation=None)]
    rv = post_json(tally_entry_client, "/auth/tallyentry/code", dict(members=members))
    assert_ok(rv)
    rv = tally_entry_client.get("/api/me")
    assert rv.status_code == 200
    tally_entry_me_response = json.loads(rv.data)
    other_tally_entry_user_id = tally_entry_me_response["user"]["id"]
    rv = post_json(
        client,
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}/confirm",
        dict(tallyEntryUserId=other_tally_entry_user_id, code=login_code),
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Bad Request", "message": "Invalid code, please try again."}
        ]
    }

    # Try to log in with an invalid user id
    rv = post_json(
        client,
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}/confirm",
        dict(tallyEntryUserId="invalid", code=login_code),
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Bad Request", "message": "Tally entry user not found."}
        ]
    }

    # Try to log in with the wrong jurisdiction
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, other_ja_email)
    rv = post_json(
        client,
        f"/auth/tallyentry/election/{other_election_id}/jurisdiction/{other_jurisdiction_id}/confirm",
        dict(tallyEntryUserId=tally_entry_user_id, code=login_code),
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Bad Request", "message": "Tally entry user not found.",}
        ]
    }


def test_logout(client: FlaskClient, aa_email: str):
    # Logging out when not logged in should not cause an error
    rv = client.get("/auth/logout")
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/"

    # Logging out without support user should redirect to home
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)

    with client.session_transaction() as session:  # type: ignore
        previous_session = session.copy()

    rv = client.get("/auth/logout")
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/"

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"] is None
        assert session.get("_support_user") is None
        assert session["_created_at"] == previous_session["_created_at"]
        assert (
            datetime.fromisoformat(session["_last_request_at"])
            - datetime.fromisoformat(previous_session["_last_request_at"])
        ) < timedelta(seconds=1)

    # Logging out of audit admin while logged in as support user should
    # redirect to /support
    set_support_user(client, SA_EMAIL)
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)

    with client.session_transaction() as session:  # type: ignore
        previous_session = session.copy()

    rv = client.get("/auth/logout")
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/support"

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"] is None
        # support user shouldn't get logged out
        assert session["_support_user"] == SA_EMAIL
        assert session["_created_at"] == previous_session["_created_at"]
        assert (
            datetime.fromisoformat(session["_last_request_at"])
            - datetime.fromisoformat(previous_session["_last_request_at"])
        ) < timedelta(seconds=1)


def test_support_logout(client: FlaskClient, aa_email: str):
    # Logging out when not logged in should not cause an error
    rv = client.get("/auth/support/logout")
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/"

    # Logging out from support user only
    set_support_user(client, SA_EMAIL)

    with client.session_transaction() as session:  # type: ignore
        previous_session = session.copy()

    rv = client.get("/auth/support/logout")
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/"

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"] is None
        assert session["_support_user"] is None
        assert session["_created_at"] == previous_session["_created_at"]
        assert (
            datetime.fromisoformat(session["_last_request_at"])
            - datetime.fromisoformat(previous_session["_last_request_at"])
        ) < timedelta(seconds=1)

    # Logging out from support user when logged in as an audit admin
    set_support_user(client, SA_EMAIL)
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)

    with client.session_transaction() as session:  # type: ignore
        previous_session = session.copy()

    rv = client.get("/auth/support/logout")
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/"

    with client.session_transaction() as session:  # type: ignore
        # Audit admin logged out as well
        assert session["_user"] is None
        assert session["_support_user"] is None
        assert session["_created_at"] == previous_session["_created_at"]
        assert (
            datetime.fromisoformat(session["_last_request_at"])
            - datetime.fromisoformat(previous_session["_last_request_at"])
        ) < timedelta(seconds=1)


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


def test_audit_board_not_found(client: FlaskClient,):
    rv = client.get("/auditboard/not-a-real-passphrase")
    assert rv.status_code == 302
    location = urlparse(rv.location)
    assert location.path == "/"
    assert (
        location.query == "error=audit_board_not_found&message=Audit+board+not+found."
    )

    with client.session_transaction() as session:  # type: ignore
        assert session.get("_user") is None


# Tests for /api/me


def test_auth_me_audit_admin(client: FlaskClient, aa_email: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)

    user = User.query.filter_by(email=aa_email).one()
    db_session.expunge(user)

    rv = client.get("/api/me")
    assert json.loads(rv.data) == {
        "user": {"type": "audit_admin", "email": aa_email, "id": user.id},
        "supportUser": None,
    }


def test_auth_me_jurisdiction_admin(
    client: FlaskClient, election_id: str, jurisdiction_id: str, ja_email: str
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, ja_email)
    election = Election.query.get(election_id)
    db_session.expunge(election)

    rv = client.get("/api/me")
    assert json.loads(rv.data) == {
        "user": {
            "type": UserType.JURISDICTION_ADMIN,
            "email": ja_email,
            "jurisdictions": [
                {
                    "id": jurisdiction_id,
                    "name": "Test Jurisdiction",
                    "election": {
                        "id": election_id,
                        "auditName": election.audit_name,
                        "electionName": None,
                        "state": None,
                        "organizationId": election.organization_id,
                    },
                    "numBallots": None,
                }
            ],
        },
        "supportUser": None,
    }


def test_auth_me_audit_board(
    client: FlaskClient, audit_board_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get("/api/me")
    audit_board = AuditBoard.query.get(audit_board_id)
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "user": {
            "type": UserType.AUDIT_BOARD,
            "id": audit_board.id,
            "jurisdictionId": audit_board.jurisdiction_id,
            "jurisdictionName": audit_board.jurisdiction.name,
            "electionId": audit_board.jurisdiction.election.id,
            "roundId": audit_board.round_id,
            "name": audit_board.name,
            "members": [],
            "signedOffAt": None,
        },
        "supportUser": None,
    }


def test_auth_me_not_logged_in(client: FlaskClient):
    clear_logged_in_user(client)
    rv = client.get("/api/me")
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"user": None, "supportUser": None}


# Tests for session expiration


def test_session_expires_on_inactivity(client: FlaskClient, aa_email: str):
    original_inactivity_timeout = config.SESSION_INACTIVITY_TIMEOUT
    config.SESSION_INACTIVITY_TIMEOUT = timedelta(milliseconds=100)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    rv = client.get("/api/me")
    assert json.loads(rv.data)["user"] is not None

    time.sleep(0.5)

    rv = client.get("/api/me")
    assert json.loads(rv.data)["user"] is None

    config.SESSION_INACTIVITY_TIMEOUT = original_inactivity_timeout


def test_session_expires_after_lifetime(client: FlaskClient, aa_email: str):
    original_lifetime = config.SESSION_LIFETIME
    config.SESSION_LIFETIME = timedelta(milliseconds=1000)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    rv = client.get("/api/me")
    assert json.loads(rv.data)["user"] is not None

    time.sleep(1)

    rv = client.get("/api/me")
    assert json.loads(rv.data)["user"] is None

    config.SESSION_LIFETIME = original_lifetime


def test_support_session_expires_on_inactivity(client: FlaskClient, aa_email: str):
    original_inactivity_timeout = config.SESSION_INACTIVITY_TIMEOUT
    config.SESSION_INACTIVITY_TIMEOUT = timedelta(milliseconds=100)

    set_support_user(client, SA_EMAIL)
    rv = client.get("/api/support/organizations")
    assert rv.status_code == 200

    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email, from_support_user=True)
    rv = client.get("/api/me")
    assert json.loads(rv.data)["user"] is not None
    assert json.loads(rv.data)["supportUser"] is not None

    time.sleep(0.5)

    rv = client.get("/api/support/organizations")
    assert rv.status_code == 403

    rv = client.get("/api/me")
    assert json.loads(rv.data)["user"] is None
    assert json.loads(rv.data)["supportUser"] is None

    config.SESSION_INACTIVITY_TIMEOUT = original_inactivity_timeout


def test_support_session_expires_after_lifetime(client: FlaskClient, aa_email: str):
    original_lifetime = config.SESSION_LIFETIME
    config.SESSION_LIFETIME = timedelta(milliseconds=1000)

    set_support_user(client, SA_EMAIL)
    rv = client.get("/api/support/organizations")
    assert rv.status_code == 200

    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email, from_support_user=True)
    rv = client.get("/api/me")
    assert json.loads(rv.data)["user"] is not None
    assert json.loads(rv.data)["supportUser"] is not None

    time.sleep(1)

    rv = client.get("/api/support/organizations")
    assert rv.status_code == 403

    rv = client.get("/api/me")
    assert json.loads(rv.data)["user"] is None
    assert json.loads(rv.data)["supportUser"] is None

    config.SESSION_LIFETIME = original_lifetime


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


def test_restrict_access_audit_admin_tally_entry_user(
    client: FlaskClient, batch_election_id: str, tally_entry_user_id: str,
):
    set_logged_in_user(client, UserType.TALLY_ENTRY, tally_entry_user_id)
    rv = client.get(f"/api/election/{batch_election_id}/test_auth")
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": "Access forbidden for user type tally_entry",
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
    org_id_2, _ = create_org_and_admin("Organization 2", "aa2@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "aa2@example.com")
    election_id_2 = create_election(client, organization_id=org_id_2)
    create_jurisdiction_and_admin(election_id_2, "Test Jurisdiction", "ja2@example.com")
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
        election_id_2, "Test Jurisdiction", "ja2@example.com"
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
        election_id, "Jurisdiction 2", "ja2@example.com"
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


def test_restrict_access_jurisdiction_admin_with_tally_entry_user(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    tally_entry_user_id: str,
):
    set_logged_in_user(client, UserType.TALLY_ENTRY, tally_entry_user_id)
    rv = client.get(
        f"/api/election/{batch_election_id}/jurisdiction/{batch_jurisdiction_id}/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": "Access forbidden for user type tally_entry",
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


def test_restrict_access_audit_board_with_tally_entry_user(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,
    round_id: str,
    audit_board_id: str,
    tally_entry_user_id: str,
):
    set_logged_in_user(client, UserType.TALLY_ENTRY, tally_entry_user_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/{audit_board_id}/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": "Access forbidden for user type tally_entry",
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
        election_id_2, "Test Jurisdiction", "ja3@example.com"
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
        election_id_2, "Test Jurisdiction", "ja4@example.com"
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
        election_id, "J5", "ja5@example.com"
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


def test_restrict_access_tally_entry_with_tally_entry_user(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    tally_entry_user_id: str,
):
    set_logged_in_user(client, UserType.TALLY_ENTRY, tally_entry_user_id)
    rv = client.get(
        f"/api/election/{batch_election_id}/jurisdiction/{batch_jurisdiction_id}/tally-entry/test_auth"
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == [
        batch_election_id,
        batch_jurisdiction_id,
    ]


def test_restrict_access_tally_entry_with_audit_admin(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    aa_email: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, aa_email)
    rv = client.get(
        f"/api/election/{batch_election_id}/jurisdiction/{batch_jurisdiction_id}/tally-entry/test_auth"
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


def test_restrict_access_tally_entry_with_jurisdiction_admin(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    batch_ja_email: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, batch_ja_email)
    rv = client.get(
        f"/api/election/{batch_election_id}/jurisdiction/{batch_jurisdiction_id}/tally-entry/test_auth"
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


def test_restrict_access_tally_entry_with_audit_board(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    audit_board_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get(
        f"/api/election/{batch_election_id}/jurisdiction/{batch_jurisdiction_id}/tally-entry/test_auth"
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


def test_restrict_access_tally_entry_with_anonymous_user(
    client: FlaskClient, batch_election_id: str, batch_jurisdiction_id: str,
):
    clear_logged_in_user(client)
    rv = client.get(
        f"/api/election/{batch_election_id}/jurisdiction/{batch_jurisdiction_id}/tally-entry/test_auth"
    )
    assert rv.status_code == 401
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Unauthorized", "message": "Please log in to access Arlo"}
        ]
    }


def test_restrict_access_tally_entry_election_not_found(
    client: FlaskClient, batch_jurisdiction_id: str, tally_entry_user_id: str,
):
    set_logged_in_user(client, UserType.TALLY_ENTRY, tally_entry_user_id)
    rv = client.get(
        f"/api/election/not-a-real-id/jurisdiction/{batch_jurisdiction_id}/tally-entry/test_auth"
    )
    assert rv.status_code == 404


def test_restrict_access_tally_entry_jurisdiction_not_found(
    client: FlaskClient, batch_election_id: str, tally_entry_user_id: str,
):
    set_logged_in_user(client, UserType.TALLY_ENTRY, tally_entry_user_id)
    rv = client.get(
        f"/api/election/{batch_election_id}/jurisdiction/not-a-real-id/tally-entry/test_auth"
    )
    assert rv.status_code == 404


def test_restrict_access_tally_entry_tally_entry_user_not_logged_in(
    client: FlaskClient,
    batch_election_id: str,
    batch_jurisdiction_id: str,
    tally_entry_user_id: str,
):
    user = TallyEntryUser.query.get(tally_entry_user_id)
    user.login_confirmed_at = None
    db_session.commit()

    set_logged_in_user(client, UserType.TALLY_ENTRY, tally_entry_user_id)
    rv = client.get(
        f"/api/election/{batch_election_id}/jurisdiction/{batch_jurisdiction_id}/tally-entry/test_auth"
    )
    assert rv.status_code == 401
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Unauthorized",
                "message": "Your jurisdiction manager must confirm your login code.",
            }
        ]
    }


def test_restrict_access_tally_entry_wrong_election(
    client: FlaskClient,
    tally_entry_user_id: str,
    election_id: str,
    jurisdiction_id: str,
):
    set_logged_in_user(client, UserType.TALLY_ENTRY, tally_entry_user_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/tally-entry/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"User does not have access to jurisdiction {jurisdiction_id}",
            }
        ]
    }


def test_restrict_access_tally_entry_wrong_jurisdiction(
    client: FlaskClient, batch_election_id: str, tally_entry_user_id: str,
):
    jurisdiction_id = create_jurisdiction(batch_election_id, "Other jurisdiction").id

    set_logged_in_user(client, UserType.TALLY_ENTRY, tally_entry_user_id)
    rv = client.get(
        f"/api/election/{batch_election_id}/jurisdiction/{jurisdiction_id}/tally-entry/test_auth"
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Forbidden",
                "message": f"User does not have access to jurisdiction {jurisdiction_id}",
            }
        ]
    }


# Additional auth tests


def test_support(client: FlaskClient):
    set_support_user(client, SA_EMAIL)
    rv = client.get("/api/support/organizations")
    assert rv.status_code == 200

    clear_support_user(client)
    rv = client.get("/api/support/organizations")
    assert rv.status_code == 403


def test_csrf(client: FlaskClient, org_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    csrf._csrf_disable = False  # pylint: disable=protected-access

    body = json.dumps(
        dict(
            auditName="Test CSRF",
            organizationId=org_id,
            auditType="BALLOT_POLLING",
            auditMathType="BRAVO",
        )
    )

    rv = client.post(
        "/api/election", headers={"Content-Type": "application/json"}, data=body
    )
    assert rv.status_code == 403
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Forbidden", "message": "CSRF token missing or incorrect."}
        ]
    }

    rv = client.get("/")
    csrf_token = next(
        cookie for cookie in client.cookie_jar if cookie.name == "_csrf_token"
    ).value
    rv = client.post(
        "/api/election",
        headers={"Content-Type": "application/json", "X-CSRFToken": csrf_token},
        data=body,
    )
    assert rv.status_code == 200

    csrf._csrf_disable = True  # pylint: disable=protected-access

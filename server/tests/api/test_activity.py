from typing import List
from unittest.mock import MagicMock, patch, Mock
from flask.testing import FlaskClient

from ...auth.routes import auth0_aa
from ...util.jsonschema import JSONDict
from ..helpers import *  # pylint: disable=wildcard-import
from ..test_auth import parse_login_code_from_smtp


def test_list_activities(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
):
    set_support_user(client, "support@example.gov")
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/organizations/{org_id}/activities")
    activities = json.loads(rv.data)

    compare_json(
        activities,
        [
            {
                "activityName": "CreateAuditBoards",
                "election": {
                    "auditName": "Test Audit test_list_activities",
                    "auditType": "BALLOT_POLLING",
                    "id": election_id,
                },
                "id": assert_is_id,
                "info": {
                    "jurisdiction_id": jurisdiction_ids[0],
                    "jurisdiction_name": "J1",
                    "num_audit_boards": 1,
                },
                "timestamp": assert_is_date,
                "user": {
                    "key": default_ja_email(election_id),
                    "supportUser": "support@example.gov",
                    "type": "jurisdiction_admin",
                },
            },
            {
                "activityName": "StartRound",
                "election": {
                    "auditName": "Test Audit test_list_activities",
                    "auditType": "BALLOT_POLLING",
                    "id": election_id,
                },
                "id": assert_is_id,
                "info": {"round_num": 1},
                "timestamp": assert_is_date,
                "user": {
                    "key": DEFAULT_AA_EMAIL,
                    "supportUser": None,
                    "type": "audit_admin",
                },
            },
            {
                "activityName": "CalculateSampleSizes",
                "election": {
                    "auditName": "Test Audit test_list_activities",
                    "auditType": "BALLOT_POLLING",
                    "id": election_id,
                },
                "id": assert_is_id,
                "info": {},
                "timestamp": assert_is_date,
                "user": {
                    "key": DEFAULT_AA_EMAIL,
                    "supportUser": None,
                    "type": "audit_admin",
                },
            },
            {
                "activityName": "UploadFile",
                "election": {
                    "auditName": "Test Audit test_list_activities",
                    "auditType": "BALLOT_POLLING",
                    "id": election_id,
                },
                "id": assert_is_id,
                "info": {
                    "error": None,
                    "file_type": "ballot_manifest",
                    "jurisdiction_id": jurisdiction_ids[1],
                    "jurisdiction_name": "J2",
                },
                "timestamp": assert_is_date,
                # Note that in non-test environments, file uploads happen in the
                # background, so we don't have a user session to pull this info
                # from, and "user" is None. But we can't easily simulate that in test.
                "user": {
                    "key": default_ja_email(election_id),
                    "supportUser": None,
                    "type": "jurisdiction_admin",
                },
            },
            {
                "activityName": "UploadFile",
                "election": {
                    "auditName": "Test Audit test_list_activities",
                    "auditType": "BALLOT_POLLING",
                    "id": election_id,
                },
                "id": assert_is_id,
                "info": {
                    "error": None,
                    "file_type": "ballot_manifest",
                    "jurisdiction_id": jurisdiction_ids[0],
                    "jurisdiction_name": "J1",
                },
                "timestamp": assert_is_date,
                "user": {
                    "key": default_ja_email(election_id),
                    "supportUser": None,
                    "type": "jurisdiction_admin",
                },
            },
            {
                "activityName": "CreateAudit",
                "election": {
                    "auditName": "Test Audit test_list_activities",
                    "auditType": "BALLOT_POLLING",
                    "id": election_id,
                },
                "id": assert_is_id,
                "info": {},
                "timestamp": assert_is_date,
                "user": {
                    "key": DEFAULT_AA_EMAIL,
                    "supportUser": None,
                    "type": "audit_admin",
                },
            },
        ],
    )

    timestamps = [
        datetime.fromisoformat(activity["timestamp"]) for activity in activities
    ]
    assert timestamps == list(reversed(sorted(timestamps)))


def test_list_activities_wrong_org(
    client: FlaskClient, org_id: str,
):
    create_org_and_admin("Test Activities Wrong Org", "other-admin@example.com")
    set_logged_in_user(client, UserType.AUDIT_ADMIN, "other-admin@example.com")
    rv = client.get(f"/api/organizations/{org_id}/activities")
    assert rv.status_code == 403


def test_list_activities_wrong_user_type(
    client: FlaskClient, org_id: str, election_id: str
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(f"/api/organizations/{org_id}/activities")
    assert rv.status_code == 403


def test_list_activities_not_logged_in(client: FlaskClient, org_id: str):
    clear_logged_in_user(client)
    rv = client.get(f"/api/organizations/{org_id}/activities")
    assert rv.status_code == 403


def test_list_activities_logins(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    # Try to log in a jurisdiction admin
    with patch("smtplib.SMTP", autospec=True) as smtp:
        rv = post_json(
            client,
            "/auth/jurisdictionadmin/code",
            dict(email=default_ja_email(election_id)),
        )
        code = parse_login_code_from_smtp(smtp)
        assert_ok(rv)

        # Wrong code
        rv = post_json(
            client,
            "/auth/jurisdictionadmin/login",
            dict(email=default_ja_email(election_id), code="invalid"),
        )
        assert rv.status_code == 400

        # Too many attempts
        user = User.query.filter_by(email=default_ja_email(election_id)).one()
        user.login_code_attempts = 10
        db_session.commit()
        rv = post_json(
            client,
            "/auth/jurisdictionadmin/login",
            dict(email=default_ja_email(election_id), code="invalid"),
        )
        assert rv.status_code == 400

        # Successful login
        user = User.query.filter_by(email=default_ja_email(election_id)).one()
        user.login_code_attempts = 0
        db_session.commit()
        rv = post_json(
            client,
            "/auth/jurisdictionadmin/code",
            dict(email=default_ja_email(election_id)),
        )
        assert_ok(rv)
        rv = post_json(
            client,
            "/auth/jurisdictionadmin/login",
            dict(email=default_ja_email(election_id), code=code),
        )
        assert_ok(rv)

        # Try to reuse used code
        rv = post_json(
            client,
            "/auth/jurisdictionadmin/login",
            dict(email=default_ja_email(election_id), code=code),
        )
        assert rv.status_code == 400

    # TODO implement login logs for audit admin
    # Log in an audit admin
    with patch.object(auth0_aa, "authorize_access_token", return_value=None):
        mock_response = Mock()
        mock_response.json = MagicMock(return_value={"email": DEFAULT_AA_EMAIL})
        with patch.object(auth0_aa, "get", return_value=mock_response):
            rv = client.get("/auth/auditadmin/callback?code=foobar")
            assert rv.status_code == 302

    rv = client.get(f"/api/organizations/{org_id}/activities")
    activities = json.loads(rv.data)

    expected_activity: JSONDict = {
        "activityName": "JurisdictionAdminLogin",
        "election": None,
        "id": assert_is_id,
        "info": {},
        "timestamp": assert_is_date,
        "user": {
            "key": default_ja_email(election_id),
            "supportUser": None,
            "type": "jurisdiction_admin",
        },
    }
    compare_json(
        activities,
        [
            {**expected_activity, "info": {"error": "Needs new code"}},
            {**expected_activity, "info": {"error": None}},
            {**expected_activity, "info": {"error": "Too many incorrect attempts"}},
            {**expected_activity, "info": {"error": "Invalid code"}},
            {
                **expected_activity,
                "activityName": "CreateAudit",
                "election": {
                    "id": election_id,
                    "auditName": "Test Audit test_list_activities_logins",
                    "auditType": "BALLOT_POLLING",
                },
                "user": {
                    "key": DEFAULT_AA_EMAIL,
                    "type": "audit_admin",
                    "supportUser": None,
                },
            },
        ],
    )

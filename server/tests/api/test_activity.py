import io
from typing import List
from unittest.mock import MagicMock, patch, Mock
from flask.testing import FlaskClient

from ...auth.auth_routes import auth0_aa
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
    with patch("smtplib.SMTP_SSL", autospec=True) as smtp:
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


def test_file_upload_errors(
    client: FlaskClient, org_id: str, election_id: str, jurisdiction_ids: List[str],
):
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "isTargeted": True,
                "choices": [
                    {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 5000},
                    {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 2500},
                    {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 2500},
                ],
                "numWinners": 1,
                "votesAllowed": 2,
                "totalBallotsCast": 10000,
                "jurisdictionIds": jurisdiction_ids[:2],
            },
        ],
    )
    assert_ok(rv)
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={"manifest": (io.BytesIO(b"invalid"), "manifest.csv")},
    )
    assert_ok(rv)

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(b"Batch Name,Number of Ballots\n" b"A,1"),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    election = Election.query.get(election_id)
    election.audit_type = AuditType.BATCH_COMPARISON
    db_session.commit()

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={"batchTallies": (io.BytesIO(b"invalid"), "tallies.csv")},
    )
    assert rv.status_code == 200

    election = Election.query.get(election_id)
    election.audit_type = AuditType.BALLOT_COMPARISON
    db_session.commit()

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={"cvrs": (io.BytesIO(b""), "cvrs.csv"), "cvrFileType": "DOMINION",},
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/organizations/{org_id}/activities")
    activities = json.loads(rv.data)

    expected_activity: JSONDict = {
        "activityName": "UploadFile",
        "election": {
            "auditName": "Test Audit test_file_upload_errors",
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
    }
    compare_json(
        activities,
        [
            {
                **expected_activity,
                "election": {
                    **expected_activity["election"],
                    "auditType": "BALLOT_COMPARISON",
                },
                "info": {
                    **expected_activity["info"],
                    "file_type": "cvrs",
                    "error": "CSV cannot be empty.",
                },
            },
            {
                **expected_activity,
                "election": {
                    **expected_activity["election"],
                    "auditType": "BATCH_COMPARISON",
                },
                "info": {
                    **expected_activity["info"],
                    "file_type": "batch_tallies",
                    "error": "Missing required columns: Batch Name, candidate 1, candidate 2, candidate 3.",
                },
            },
            expected_activity,
            {
                **expected_activity,
                "info": {
                    **expected_activity["info"],
                    "error": "Missing required columns: Batch Name, Number of Ballots.",
                },
            },
            {
                **expected_activity,
                "activityName": "CreateAudit",
                "election": {
                    "id": election_id,
                    "auditName": "Test Audit test_file_upload_errors",
                    "auditType": "BALLOT_POLLING",
                },
                "info": {},
                "user": {
                    "key": DEFAULT_AA_EMAIL,
                    "type": "audit_admin",
                    "supportUser": None,
                },
            },
        ],
    )

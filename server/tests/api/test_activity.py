from typing import List
from flask.testing import FlaskClient

from ..helpers import *  # pylint: disable=wildcard-import


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
                "user": None,
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
                "user": None,
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

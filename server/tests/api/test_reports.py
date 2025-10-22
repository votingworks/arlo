from flask.testing import FlaskClient
from .test_audit_boards import set_up_audit_board
from ...models import *
from ..helpers import *
from ...auth import UserType


def test_audit_admin_report(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
    contest_ids: list[str],
    audit_board_round_1_ids: list[str],
    snapshot,
):
    for audit_board_id in audit_board_round_1_ids:
        set_up_audit_board(
            client,
            election_id,
            jurisdiction_ids[0],
            round_1_id,
            contest_ids[0],
            audit_board_id,
        )
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert (
        scrub_datetime(rv.headers["Content-Disposition"])
        == 'attachment; filename="audit-report-Test-Audit-test-audit-admin-report-DATETIME.csv"'
    )
    assert_match_report(rv.data, snapshot)


def test_audit_admin_report_round_2(
    client: FlaskClient,
    election_id: str,
    round_2_id: str,
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert (
        scrub_datetime(rv.headers["Content-Disposition"])
        == 'attachment; filename="audit-report-Test-Audit-test-audit-admin-report-round-2-DATETIME.csv"'
    )
    assert_match_report(rv.data, snapshot)


def test_jurisdiction_admin_report(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id,
    contest_ids: list[str],
    audit_board_round_1_ids: list[str],
    snapshot,
):
    for audit_board_id in audit_board_round_1_ids:
        set_up_audit_board(
            client,
            election_id,
            jurisdiction_ids[0],
            round_1_id,
            contest_ids[0],
            audit_board_id,
        )
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    assert (
        scrub_datetime(rv.headers["Content-Disposition"])
        == 'attachment; filename="audit-report-J1-Test-Audit-test-jurisdiction-admin-report-DATETIME.csv"'
    )
    assert_match_report(rv.data, snapshot)


def test_report_before_audit_starts(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Cannot generate report until audit starts",
            }
        ]
    }

    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Cannot generate report until audit starts",
            }
        ]
    }

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Cannot generate report until audit starts",
            }
        ]
    }


def test_discrepancy_report_wrong_audit_type(
    client: FlaskClient,
    election_id: str,
    round_1_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Discrepancy report not supported for this audit type",
            }
        ]
    }

from typing import List
from flask.testing import FlaskClient
from .test_audit_boards import set_up_audit_board
from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...auth import UserType


def test_audit_admin_report(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    contest_ids: List[str],
    audit_board_round_1_ids: List[str],
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


def test_jurisdiction_admin_report(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id,
    contest_ids: List[str],
    audit_board_round_1_ids: List[str],
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
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    assert (
        scrub_datetime(rv.headers["Content-Disposition"])
        == 'attachment; filename="audit-report-J1-Test-Audit-test-jurisdiction-admin-report-DATETIME.csv"'
    )
    assert_match_report(rv.data, snapshot)

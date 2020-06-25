from typing import List
from flask.testing import FlaskClient
from .test_audit_boards import set_up_audit_board
from ..helpers import set_logged_in_user, DEFAULT_JA_EMAIL, assert_match_report
from ...auth import UserType


# TODO This is just a basic snapshot test. We still need to implement more
# comprehensive testing.
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
    rv = client.get(f"/api/election/{election_id}/report")
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
    assert_match_report(rv.data, snapshot)

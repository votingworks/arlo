from flask.testing import FlaskClient
from .test_audit_boards import set_up_audit_board
from ...api import reports
from ...api.reports import reported_runoff_results_label
from ...database import db_session
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
        scrub_filename_datetime(rv.headers["Content-Disposition"])
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
        scrub_filename_datetime(rv.headers["Content-Disposition"])
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
        scrub_filename_datetime(rv.headers["Content-Disposition"])
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


def test_reported_runoff_results_majority():
    # Leader has 55% of valid votes — strict majority.
    assert (
        reported_runoff_results_label(choice_votes=[55, 25, 15, 5])
        == "Majority received, no runoff required"
    )


def test_reported_runoff_results_no_majority():
    # Leader has 40% — below 50%.
    assert (
        reported_runoff_results_label(choice_votes=[40, 35, 15, 10])
        == "No majority, runoff required"
    )


def test_reported_runoff_results_exact_50_is_not_majority():
    # 50% is NOT a strict majority (Ga. Code § 21-2-501 requires > 50%).
    assert (
        reported_runoff_results_label(choice_votes=[50, 30, 20])
        == "No majority, runoff required"
    )


def test_contest_rows_runoff_columns(org_id: str):
    # Two contests, one flagged and one unflagged. Asserts contest_rows emits
    # both runoff columns and populates both branches.
    election = Election(
        id=str(uuid.uuid4()),
        audit_name="Test Audit contest_rows_runoff_columns",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
        organization_id=org_id,
        online=False,
    )
    flagged = Contest(
        id=str(uuid.uuid4()),
        election_id=election.id,
        name="Flagged Contest",
        is_targeted=True,
        num_winners=1,
        votes_allowed=1,
        total_ballots_cast=100,
        is_subject_to_runoff=True,
    )
    flagged.choices = [
        ContestChoice(id=str(uuid.uuid4()), name="Alice", num_votes=55),
        ContestChoice(id=str(uuid.uuid4()), name="Bob", num_votes=25),
        ContestChoice(id=str(uuid.uuid4()), name="Carla", num_votes=20),
    ]
    unflagged = Contest(
        id=str(uuid.uuid4()),
        election_id=election.id,
        name="Unflagged Contest",
        is_targeted=True,
        num_winners=1,
        votes_allowed=1,
        total_ballots_cast=100,
        is_subject_to_runoff=False,
    )
    unflagged.choices = [
        ContestChoice(id=str(uuid.uuid4()), name="X", num_votes=60),
        ContestChoice(id=str(uuid.uuid4()), name="Y", num_votes=40),
    ]
    election.contests = [flagged, unflagged]
    db_session.add(election)
    db_session.commit()

    rows = reports.contest_rows(election)
    header = rows[1]
    assert header[-2:] == ["Runoff Law", "Reported Runoff Results"]

    flagged_row = next(row for row in rows[2:] if row[0] == "Flagged Contest")
    assert flagged_row[-2:] == [
        "Subject to runoff law",
        "Majority received, no runoff required",
    ]

    unflagged_row = next(row for row in rows[2:] if row[0] == "Unflagged Contest")
    assert unflagged_row[-2:] == ["", ""]

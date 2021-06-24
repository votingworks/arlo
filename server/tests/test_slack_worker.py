import json
from unittest.mock import patch, Mock
import pytest
from flask.testing import FlaskClient

from ..models import *  # pylint: disable=wildcard-import
from ..auth import UserType
from .helpers import *  # pylint: disable=wildcard-import
from .. import config
from ..activity_log import slack_worker
from .. import activity_log


@pytest.fixture(autouse=True)
def setup():
    config.SLACK_WEBHOOK_URL = "test slack webhook url"
    yield
    config.SLACK_WEBHOOK_URL = None


def test_slack_worker_require_webhook_url():
    config.SLACK_WEBHOOK_URL = None
    with pytest.raises(Exception, match="Missing SLACK_WEBHOOK_URL"):
        slack_worker.send_new_slack_notification()


@patch("requests.post")
def test_slack_worker_happy_path(mock_post, client: FlaskClient, org_id: str):
    mock_post.return_value = Mock(status_code=200)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit test_slack_worker_happy_path",
            "auditType": "BALLOT_POLLING",
            "auditMathType": "BRAVO",
            "organizationId": org_id,
        },
    )
    assert rv.status_code == 200

    slack_worker.send_new_slack_notification(organization_id=org_id)

    mock_post.assert_called_once()
    assert mock_post.call_args.args[0] == "test slack webhook url"
    assert (
        mock_post.call_args.kwargs["json"]["text"]
        == "admin@example.com created an audit: Test Audit test_slack_worker_happy_path (Ballot Polling)"
    )


@patch("requests.post")
def test_slack_worker_one_notification_at_a_time(
    mock_post, client: FlaskClient, org_id: str
):
    mock_post.return_value = Mock(status_code=200)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, user_key=DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit test_slack_worker_one_notification_at_a_time",
            "auditType": "BALLOT_POLLING",
            "auditMathType": "BRAVO",
            "organizationId": org_id,
        },
    )
    assert rv.status_code == 200
    election_id = json.loads(rv.data)["electionId"]

    rv = client.delete(f"/api/election/{election_id}")
    assert_ok(rv)

    slack_worker.send_new_slack_notification(organization_id=org_id)

    mock_post.assert_called_once()
    assert (
        mock_post.call_args.kwargs["json"]["text"]
        == "admin@example.com created an audit: Test Audit test_slack_worker_one_notification_at_a_time (Ballot Polling)"
    )
    mock_post.reset_mock()

    slack_worker.send_new_slack_notification(organization_id=org_id)

    mock_post.assert_called_once()
    assert (
        mock_post.call_args.kwargs["json"]["text"]
        == "admin@example.com deleted an audit: Test Audit test_slack_worker_one_notification_at_a_time (Ballot Polling)"
    )


@patch("requests.post")
def test_slack_worker_error_in_slack_api(mock_post, client: FlaskClient, org_id: str):
    mock_post.return_value = Mock(status_code=400, text="test slack error")

    set_logged_in_user(client, UserType.AUDIT_ADMIN, user_key=DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit test_slack_worker_error_in_slack_api",
            "auditType": "BALLOT_POLLING",
            "auditMathType": "BRAVO",
            "organizationId": org_id,
        },
    )
    assert rv.status_code == 200

    record = ActivityLogRecord.query.filter_by(organization_id=org_id).one()

    with pytest.raises(
        Exception, match=f"Error posting record {record.id}:\n\ntest slack error"
    ):
        slack_worker.send_new_slack_notification(organization_id=org_id)

    record = ActivityLogRecord.query.filter_by(organization_id=org_id).one()
    assert record.posted_to_slack_at is None


def test_slack_worker_message_format(snapshot):
    timestamp = datetime.fromisoformat("2021-05-19T18:31:13.576657+00:00")
    base = activity_log.ActivityBase(
        organization_id="test_org_id",
        organization_name="Test Org",
        election_id="test_election_id",
        audit_name="Test Audit",
        audit_type="BALLOT_COMPARISON",
        user_type="audit_admin",
        user_key="test_user@example.com",
        support_user_email=None,
    )
    snapshot.assert_match(
        slack_worker.slack_message(activity_log.CreateAudit(timestamp, base))
    )

    base.support_user_email = "support_user@example.com"
    base.audit_type = "BATCH_COMPARISON"
    snapshot.assert_match(
        slack_worker.slack_message(activity_log.DeleteAudit(timestamp, base))
    )

    base.support_user_email = None
    base.audit_type = "BALLOT_COMPARISON"
    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.StartRound(timestamp, base, round_num=1)
        )
    )

    base.audit_type = "HYBRID"
    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.EndRound(timestamp, base, round_num=1, is_audit_complete=False)
        )
    )
    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.EndRound(timestamp, base, round_num=2, is_audit_complete=True)
        )
    )

    snapshot.assert_match(
        slack_worker.slack_message(activity_log.CalculateSampleSizes(timestamp, base))
    )

    base.user_type = None
    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.UploadFile(
                timestamp,
                base,
                jurisdiction_id="test_jurisdiction_id",
                jurisdiction_name="Test Jurisdiction",
                file_type="ballot_manifest",
                error=None,
            )
        )
    )
    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.UploadFile(
                timestamp,
                base,
                jurisdiction_id="test_jurisdiction_id",
                jurisdiction_name="Test Jurisdiction",
                file_type="cvrs",
                error="Something went wrong",
            )
        )
    )
    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.UploadFile(
                timestamp,
                base,
                jurisdiction_id="test_jurisdiction_id",
                jurisdiction_name="Test Jurisdiction",
                file_type="batch_tallies",
                error=None,
            )
        )
    )

    base.user_type = "jurisdiction_admin"
    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.CreateAuditBoards(
                timestamp,
                base,
                jurisdiction_id="test_jurisdiction_id",
                jurisdiction_name="Test Jurisdiction",
                num_audit_boards=3,
            )
        )
    )

    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.RecordResults(
                timestamp,
                base,
                jurisdiction_id="test_jurisdiction_id",
                jurisdiction_name="Test Jurisdiction",
            )
        )
    )

    base.user_type = "audit_board"
    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.AuditBoardSignOff(
                timestamp,
                base,
                jurisdiction_id="test_jurisdiction_id",
                jurisdiction_name="Test Jurisdiction",
                audit_board_name="Audit Board #1",
            )
        )
    )

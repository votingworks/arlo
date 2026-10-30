import re
import json
from unittest.mock import patch, Mock
import pytest
from flask.testing import FlaskClient

from ..models import *
from ..auth import UserType
from .helpers import *
from .. import config
from ..activity_log import slack_worker
from .. import activity_log


@pytest.fixture(autouse=True)
def setup():
    config.SLACK_BOT_TOKEN = "test-slack-bot-token"
    yield
    config.SLACK_BOT_TOKEN = None


def slack_ok_response():
    return Mock(status_code=200, **{"json.return_value": {"ok": True}})


def test_slack_worker_require_bot_token():
    config.SLACK_BOT_TOKEN = None
    with pytest.raises(Exception, match="Missing SLACK_BOT_TOKEN"):
        slack_worker.send_new_slack_notification()


@patch("requests.post")
def test_slack_worker_happy_path(mock_post, client: FlaskClient, org_id: str):
    mock_post.return_value = slack_ok_response()

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
    assert mock_post.call_args.args[0] == "https://slack.com/api/chat.postMessage"
    assert mock_post.call_args.kwargs["headers"] == {
        "Authorization": "Bearer test-slack-bot-token"
    }
    assert mock_post.call_args.kwargs["json"]["channel"] == "#arlo-activity"
    assert (
        mock_post.call_args.kwargs["json"]["text"]
        == "admin@example.com created an audit: Test Audit test_slack_worker_happy_path (Ballot Polling)"
    )


@patch("requests.post")
def test_slack_worker_one_notification_at_a_time(
    mock_post, client: FlaskClient, org_id: str
):
    mock_post.return_value = slack_ok_response()

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

    create_record, delete_record = (
        ActivityLogRecord.query.filter_by(organization_id=org_id)
        .order_by(ActivityLogRecord.timestamp)
        .all()
    )

    # Each activity is posted to one channel at a time, and fully posted
    # before moving on to the next activity
    for expected_channels in [
        ["#arlo-activity"],
        ["#arlo-activity", "#arlo-activity-others"],
    ]:
        slack_worker.send_new_slack_notification(organization_id=org_id)

        mock_post.assert_called_once()
        assert (
            mock_post.call_args.kwargs["json"]["text"]
            == "admin@example.com created an audit: Test Audit test_slack_worker_one_notification_at_a_time (Ballot Polling)"
        )
        mock_post.reset_mock()
        assert create_record.posted_to_slack_channels == expected_channels

    assert create_record.posted_to_slack_at is not None
    assert delete_record.posted_to_slack_at is None

    slack_worker.send_new_slack_notification(organization_id=org_id)

    mock_post.assert_called_once()
    assert (
        mock_post.call_args.kwargs["json"]["text"]
        == "admin@example.com deleted an audit: Test Audit test_slack_worker_one_notification_at_a_time (Ballot Polling)"
    )
    assert delete_record.posted_to_slack_channels == ["#arlo-activity"]


@patch("requests.post")
def test_slack_worker_error_in_slack_api(mock_post, client: FlaskClient, org_id: str):
    # Slack returns a 200 for most errors, with ok=false in the body
    mock_post.return_value = Mock(
        status_code=200,
        text='{"ok":false,"error":"not_in_channel"}',
        **{"json.return_value": {"ok": False, "error": "not_in_channel"}},
    )

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
        Exception,
        match=re.escape(
            f'Error posting record {record.id} to #arlo-activity:\n\n{{"ok":false,"error":"not_in_channel"}}'
        ),
    ):
        slack_worker.send_new_slack_notification(organization_id=org_id)

    record = ActivityLogRecord.query.filter_by(organization_id=org_id).one()
    assert record.posted_to_slack_at is None
    assert record.posted_to_slack_channels == []


@patch("requests.post")
def test_slack_worker_error_partway_through_channels(
    mock_post, client: FlaskClient, org_id: str
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, user_key=DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": "Test Audit test_slack_worker_error_partway_through_channels",
            "auditType": "BALLOT_POLLING",
            "auditMathType": "BRAVO",
            "organizationId": org_id,
        },
    )
    assert rv.status_code == 200
    record = ActivityLogRecord.query.filter_by(organization_id=org_id).one()

    mock_post.return_value = slack_ok_response()
    slack_worker.send_new_slack_notification(organization_id=org_id)
    db_session.commit()

    # Posting to the second channel fails
    mock_post.return_value = Mock(status_code=429, text="ratelimited")
    with pytest.raises(
        Exception,
        match=f"Error posting record {record.id} to #arlo-activity-others:\n\nratelimited",
    ):
        slack_worker.send_new_slack_notification(organization_id=org_id)
    db_session.rollback()

    record = ActivityLogRecord.query.filter_by(organization_id=org_id).one()
    assert record.posted_to_slack_channels == ["#arlo-activity"]
    assert record.posted_to_slack_at is None

    # Retrying only posts to the channel that failed
    mock_post.reset_mock()
    mock_post.return_value = slack_ok_response()
    slack_worker.send_new_slack_notification(organization_id=org_id)
    mock_post.assert_called_once()
    assert record.posted_to_slack_channels == [
        "#arlo-activity",
        "#arlo-activity-others",
    ]
    assert record.posted_to_slack_at is not None


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

    base.user_type = "jurisdiction_admin"
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

    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.FinalizeBatchResults(
                timestamp,
                base,
                jurisdiction_id="test_jurisdiction_id",
                jurisdiction_name="Test Jurisdiction",
                num_batches_with_discrepancies=0,
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

    base.user_type = "audit_admin"
    snapshot.assert_match(
        slack_worker.slack_message(
            activity_log.FullHandTallyRequired(timestamp, base, round_num=1)
        )
    )


def test_slack_worker_state_flag_emoji():
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

    def message_json(base: activity_log.ActivityBase) -> str:
        return json.dumps(
            slack_worker.slack_message(activity_log.CreateAudit(timestamp, base))
        )

    assert ":flag-us:" in message_json(base)

    base.state = "CA"
    assert ":flag-california:" in message_json(base)
    assert ":flag-us:" not in message_json(base)

    base.state = "RI"
    assert ":flag-rhodeisland:" in message_json(base)

    # States without an uploaded emoji fall back to the US flag
    base.state = "OH"
    assert ":flag-us:" in message_json(base)


def test_slack_worker_finalize_batch_results_discrepancies():
    timestamp = datetime.fromisoformat("2021-05-19T18:31:13.576657+00:00")
    base = activity_log.ActivityBase(
        organization_id="test_org_id",
        organization_name="Test Org",
        election_id="test_election_id",
        audit_name="Test Audit",
        audit_type="BATCH_COMPARISON",
        user_type="jurisdiction_admin",
        user_key="test_user@example.com",
        support_user_email=None,
    )

    def message_json(num_batches_with_discrepancies: int) -> str:
        return json.dumps(
            slack_worker.slack_message(
                activity_log.FinalizeBatchResults(
                    timestamp,
                    base,
                    jurisdiction_id="test_jurisdiction_id",
                    jurisdiction_name="Test Jurisdiction",
                    num_batches_with_discrepancies=num_batches_with_discrepancies,
                )
            )
        )

    assert ":white_check_mark: No discrepancies" in message_json(0)
    assert ":warning: 1 batch with discrepancies" in message_json(1)
    assert ":warning: 3 batches with discrepancies" in message_json(3)


def test_slack_worker_truncate_long_error_messages():
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
    max_error_len = 4000
    long_error = "".join(["x" for _ in range(0, max_error_len + 1)])
    message = slack_worker.slack_message(
        activity_log.UploadFile(
            timestamp,
            base,
            jurisdiction_id="test_jurisdiction_id",
            jurisdiction_name="Test Jurisdiction",
            file_type="batch_tallies",
            error=long_error,
        )
    )
    error_message = message["blocks"][1]["elements"][0]["text"]
    error_prefix = ":x: "
    assert len(error_message) == max_error_len + len(error_prefix)


def test_slack_worker_channels():
    timestamp = datetime.fromisoformat("2021-05-19T18:31:13.576657+00:00")
    base = activity_log.ActivityBase(
        organization_id="test_org_id",
        organization_name="Test Org",
        election_id="test_election_id",
        audit_name="Test Audit",
        audit_type="BATCH_COMPARISON",
        user_type="audit_admin",
        user_key="test_user@example.com",
        support_user_email=None,
    )
    create_audit = activity_log.CreateAudit(timestamp, base)
    end_round = activity_log.EndRound(
        timestamp, base, round_num=1, is_audit_complete=True
    )

    # States with their own channel
    for state, state_channel in [
        ("GA", "#arlo-activity-ga"),
        ("MD", "#arlo-activity-md"),
        ("TX", "#arlo-activity-tx"),
    ]:
        base.state = state
        assert slack_worker.slack_channels(create_audit) == [
            "#arlo-activity",
            state_channel,
        ]
        assert slack_worker.slack_channels(end_round) == [
            "#arlo-activity",
            state_channel,
            "#arlo-activity-critical",
        ]

    # Other states, or no state, go to the catchall channel
    for state in ["MI", None]:
        base.state = state
        assert slack_worker.slack_channels(create_audit) == [
            "#arlo-activity",
            "#arlo-activity-others",
        ]
        assert slack_worker.slack_channels(end_round) == [
            "#arlo-activity",
            "#arlo-activity-others",
            "#arlo-activity-critical",
        ]


def test_slack_worker_is_critical():
    timestamp = datetime.fromisoformat("2021-05-19T18:31:13.576657+00:00")
    base = activity_log.ActivityBase(
        organization_id="test_org_id",
        organization_name="Test Org",
        election_id="test_election_id",
        audit_name="Test Audit",
        audit_type="BATCH_COMPARISON",
        user_type="audit_admin",
        user_key="test_user@example.com",
        support_user_email=None,
    )
    jurisdiction = dict(
        jurisdiction_id="test_jurisdiction_id",
        jurisdiction_name="Test Jurisdiction",
    )

    def finalize_batch_results(num_batches_with_discrepancies: int):
        return activity_log.FinalizeBatchResults(
            timestamp,
            base,
            **jurisdiction,
            num_batches_with_discrepancies=num_batches_with_discrepancies,
        )

    critical = [
        activity_log.CalculateSampleSizes(timestamp, base),
        activity_log.StartRound(timestamp, base, round_num=1),
        activity_log.EndRound(timestamp, base, round_num=1, is_audit_complete=True),
        activity_log.EndRound(timestamp, base, round_num=2, is_audit_complete=False),
        finalize_batch_results(1),
    ]
    not_critical = [
        activity_log.FullHandTallyRequired(timestamp, base, round_num=1),
        activity_log.CreateAudit(timestamp, base),
        activity_log.DeleteAudit(timestamp, base),
        activity_log.StartRound(timestamp, base, round_num=2),
        finalize_batch_results(0),
        activity_log.UploadFile(
            timestamp, base, **jurisdiction, file_type="cvrs", error=None
        ),
        activity_log.CreateAuditBoards(
            timestamp, base, **jurisdiction, num_audit_boards=2
        ),
        activity_log.RecordResults(timestamp, base, **jurisdiction),
        activity_log.AuditBoardSignOff(
            timestamp, base, **jurisdiction, audit_board_name="Audit Board #1"
        ),
    ]
    for activity in critical:
        assert slack_worker.is_critical(activity), activity
    for activity in not_critical:
        assert not slack_worker.is_critical(activity), activity


def test_slack_worker_channel_override():
    config.SLACK_CHANNEL_OVERRIDE = "#arlo-test"
    try:
        timestamp = datetime.fromisoformat("2021-05-19T18:31:13.576657+00:00")
        base = activity_log.ActivityBase(
            organization_id="test_org_id",
            organization_name="Test Org",
            state="GA",
        )
        assert slack_worker.slack_channels(
            activity_log.EndRound(timestamp, base, round_num=1, is_audit_complete=True)
        ) == ["#arlo-test"]
    finally:
        config.SLACK_CHANNEL_OVERRIDE = None

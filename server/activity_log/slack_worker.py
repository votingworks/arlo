import time
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests

from .. import config
from ..models import ActivityLogRecord
from ..database import db_session
from . import activity_log


def slack_message(activity: activity_log.Activity):
    base = activity.base
    org_link = urljoin(config.HTTP_ORIGIN, f"/support/orgs/{base.organization_id}")
    org_context = dict(
        type="mrkdwn", text=f":flag-us: <{org_link}|{base.organization_name}>",
    )
    user_context = dict(
        type="mrkdwn",
        text=(
            f":technologist: Support user {base.support_user_email} logged in as audit admin {base.user_key}"
            if base.support_user_email
            else f":technologist: Audit admin {base.user_key}"
        ),
    )
    time_context = dict(
        type="mrkdwn",
        text=f":clock3: <!date^{int(activity.timestamp.timestamp())}^{{date_short}}, {{time_secs}}|{activity.timestamp.isoformat()}>",
    )

    audit_link = urljoin(config.HTTP_ORIGIN, f"/support/audits/{base.election_id}")
    audit_type = dict(
        BALLOT_POLLING="Ballot Polling",
        BALLOT_COMPARISON="Ballot Comparison",
        BATCH_COMPARISON="Batch Comparison",
        HYBRID="Hybrid",
    )[base.audit_type]
    audit_context = dict(
        type="mrkdwn",
        text=f":microscope: <{audit_link}|{base.audit_name}> ({audit_type})",
    )

    acting_user = base.support_user_email or base.user_key

    if isinstance(activity, activity_log.CreateAudit):
        return dict(
            text=f"{acting_user} created an audit: {base.audit_name} ({audit_type})",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{acting_user} created an audit: <{audit_link}|{base.audit_name}>* ({audit_type})",
                    ),
                ),
                dict(
                    type="context", elements=[org_context, time_context, user_context],
                ),
            ],
        )

    if isinstance(activity, activity_log.DeleteAudit):
        return dict(
            text=f"{acting_user} deleted an audit: {base.audit_name} ({audit_type})",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{acting_user} deleted an audit: <{audit_link}|{base.audit_name}>* ({audit_type})",
                    ),
                ),
                dict(
                    type="context", elements=[org_context, time_context, user_context],
                ),
            ],
        )

    if isinstance(activity, activity_log.StartRound):
        return dict(
            text=f"{acting_user} started round {activity.round_num}",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{acting_user} started round {activity.round_num}*",
                    ),
                ),
                dict(
                    type="context",
                    elements=[org_context, audit_context, time_context, user_context],
                ),
            ],
        )

    if isinstance(activity, activity_log.EndRound):
        audit_status = (
            "audit complete"
            if activity.is_audit_complete
            else "another round is needed"
        )
        return dict(
            text=f"Round {activity.round_num} ended, {audit_status}",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*Round {activity.round_num} ended, {audit_status}*",
                    ),
                ),
                dict(
                    type="context", elements=[org_context, audit_context, time_context],
                ),
            ],
        )

    if isinstance(activity, activity_log.CalculateSampleSizes):
        return dict(
            text=f"{acting_user} calculated sample sizes",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn", text=f"*{acting_user} calculated sample sizes*"
                    ),
                ),
                dict(
                    type="context",
                    elements=[org_context, audit_context, time_context, user_context],
                ),
            ],
        )

    raise Exception(  # pragma: no cover
        f"slack_message not implemented for activity type: {activity.__class__.__name__}"
    )


# The optional organization_id parameter makes this function thread-safe for
# testing. Each test has its own org, and we don't want tests running in
# parallel to influence each other.
def send_new_slack_notification(organization_id: str = None) -> None:
    if config.SLACK_WEBHOOK_URL is None:
        raise Exception("Missing SLACK_WEBHOOK_URL")

    record = (
        ActivityLogRecord.query.filter(ActivityLogRecord.posted_to_slack_at.is_(None))
        .filter_by(**dict(organization_id=organization_id) if organization_id else {})
        .order_by(ActivityLogRecord.timestamp)
        .limit(1)
        .one_or_none()
    )
    if record:
        ActivityClass = getattr(  # pylint: disable=invalid-name
            activity_log, record.activity_name
        )
        activity: activity_log.Activity = ActivityClass(
            **dict(
                record.info,
                base=activity_log.ActivityBase(**record.info["base"]),
                timestamp=record.timestamp,
            )
        )

        rv = requests.post(config.SLACK_WEBHOOK_URL, json=slack_message(activity))
        if rv.status_code != 200:
            raise Exception(f"Error posting record {record.id}:\n\n{rv.text}")

        record.posted_to_slack_at = datetime.now(timezone.utc)


if __name__ == "__main__":  # pragma: no cover
    # We send at most one Slack notification per second, since that's what the
    # Slack API allows.
    while True:
        send_new_slack_notification()
        # We always commit the current transaction before sleeping, otherwise
        # we will have "idle in transaction" queries that will lock the
        # database, which gets in the way of migrations.
        db_session.commit()
        time.sleep(1)

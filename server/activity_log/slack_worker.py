import time
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests

from ..config import SLACK_WEBHOOK_URL, HTTP_ORIGIN
from ..models import ActivityLogRecord
from ..database import db_session
from .activity_log import *  # pylint: disable=wildcard-import
from . import activity_log


def slack_message(activity: ActivityBase):
    org_link = urljoin(HTTP_ORIGIN, f"/support/orgs/{activity.organization_id}")
    org_context = dict(
        type="mrkdwn", text=f":flag-us: <{org_link}|{activity.organization_name}>",
    )
    user_context = dict(
        type="mrkdwn",
        text=(
            f":technologist: Support user {activity.support_user_email} logged in as audit admin {activity.user_display_name}"
            if activity.support_user_email
            else f":technologist: Audit admin {activity.user_display_name}"
        ),
    )
    assert activity.timestamp is not None
    time_context = dict(
        type="mrkdwn",
        text=f":clock3: <!date^{int(activity.timestamp.timestamp())}^{{date_short}}, {{time_secs}}|{activity.timestamp.isoformat()}>",
    )

    org_level_activity_context = dict(
        type="context", elements=[org_context, time_context, user_context],
    )

    acting_user = activity.support_user_email or activity.user_display_name

    if isinstance(activity, AuditActivity):
        audit_link = urljoin(HTTP_ORIGIN, f"/support/audits/{activity.election_id}")
        audit_type = dict(
            BALLOT_POLLING="Ballot Polling",
            BALLOT_COMPARISON="Ballot Comparison",
            BATCH_COMPARISON="Batch Comparison",
            HYBRID="Hybrid",
        )[activity.audit_type]
        audit_context = dict(
            type="mrkdwn",
            text=f":microscope: <{audit_link}|{activity.audit_name}> ({audit_type})",
        )
        audit_level_activity_context = dict(
            type="context",
            elements=[org_context, audit_context, time_context, user_context],
        )

    if isinstance(activity, CreateAudit):
        return dict(
            text=f"{acting_user} created an audit: {activity.audit_name} ({audit_type})",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{acting_user} created an audit:*\n*<{audit_link}|{activity.audit_name}>* ({audit_type})",
                    ),
                ),
                org_level_activity_context,
            ],
        )

    if isinstance(activity, DeleteAudit):
        return dict(
            text=f"{acting_user} deleted an audit: {activity.audit_name} ({audit_type})",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{acting_user} deleted an audit:*\n*<{audit_link}|{activity.audit_name}>* ({audit_type})",
                    ),
                ),
                org_level_activity_context,
            ],
        )

    if isinstance(activity, StartRound):
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
                audit_level_activity_context,
            ],
        )

    if isinstance(activity, EndRound):
        return dict(
            text=f"Round {activity.round_num} ended",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn", text=f"*Round {activity.round_num} ended*"
                    ),
                ),
                dict(
                    type="context", elements=[org_context, audit_context, time_context],
                ),
            ],
        )

    raise Exception(  # pragma: no cover
        f"slack_message not implemented for activity type: {activity.__class__.__name__}"
    )


def watch_and_send_slack_notifications():
    if SLACK_WEBHOOK_URL is None:
        return

    # We send at most one Slack notification per second, since that's what the
    # Slack API allows.
    while True:
        record = (
            ActivityLogRecord.query.filter(
                ActivityLogRecord.posted_to_slack_at.is_(None)
            )
            .order_by(ActivityLogRecord.created_at.desc())
            .limit(1)
            .one_or_none()
        )
        if record:
            ActivityClass: ActivityBase = getattr(  # pylint: disable=invalid-name
                activity_log, record.activity_name
            )
            activity = ActivityClass(**dict(record.info, timestamp=record.created_at))

            rv = requests.post(SLACK_WEBHOOK_URL, json=slack_message(activity))
            if rv.status_code != 200:
                raise Exception(f"Error posting record {record.id}:\n\n{rv.text}")

            record.posted_to_slack_at = datetime.now(timezone.utc)

        # We always commit the current transaction before sleeping, otherwise
        # we will have "idle in transaction" queries that will lock the
        # database, which gets in the way of migrations.
        db_session.commit()
        time.sleep(1)


if __name__ == "__main__":
    watch_and_send_slack_notifications()

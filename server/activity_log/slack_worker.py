import time
from datetime import datetime, timezone
import requests

from ..config import SLACK_WEBHOOK_URL
from ..models import ActivityLogRecord
from ..database import db_session
from .activity_log import *  # pylint: disable=wildcard-import
from . import activity_log


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
            message = ActivityClass(**record.info).slack_message(record.created_at)
            print(message)

            rv = requests.post(SLACK_WEBHOOK_URL, json=message)
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

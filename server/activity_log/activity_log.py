# pylint: disable=no-member
import uuid
from typing import NamedTuple, Optional
from datetime import datetime
from urllib.parse import urljoin
from attr import attrs
from flask import session

from ..config import HTTP_ORIGIN
from ..models import ActivityLogRecord
from ..database import db_session
from ..auth.lib import get_loggedin_user, get_support_user
from ..util.jsonschema import JSONDict


@attrs(auto_attribs=True, kw_only=True)
class ActivityBase:
    organization_id: str
    organization_name: str
    user_type: str = None
    user_key: str = None
    user_display_name: str = None
    support_user_email: str = None


@attrs(auto_attribs=True, kw_only=True)
class CreateAudit(ActivityBase):
    election_id: str
    audit_name: str
    audit_type: str

    def slack_message(self, timestamp: datetime) -> JSONDict:
        org_link = urljoin(HTTP_ORIGIN, f"/support/orgs/{self.organization_id}")
        audit_link = urljoin(HTTP_ORIGIN, f"/support/audits/{self.election_id}")
        audit_type = dict(
            BALLOT_POLLING="Ballot Polling",
            BALLOT_COMPARISON="Ballot Comparison",
            BATCH_COMPARISON="Batch Comparison",
            HYBRID="Hybrid",
        )[self.audit_type]

        return dict(
            text=f"{self.support_user_email or self.user_display_name} created an audit: {self.audit_name} ({audit_type})",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{self.support_user_email or self.user_display_name} created an audit:*\n*<{audit_link}|{self.audit_name}>* ({audit_type})",
                    ),
                ),
                dict(
                    type="context",
                    elements=[
                        dict(
                            type="mrkdwn",
                            text=f":flag-us: <{org_link}|{self.organization_name}>",
                        ),
                        dict(
                            type="mrkdwn",
                            text=f":clock3: <!date^{int(timestamp.timestamp())}^{{date_short}}, {{time_secs}}|{timestamp.isoformat()}>",
                        ),
                        dict(
                            type="mrkdwn",
                            text=(
                                f":technologist: Support user {self.support_user_email} logged in as audit admin {self.user_display_name}"
                                if self.support_user_email
                                else f":technologist: Audit admin {self.user_display_name}"
                            ),
                        ),
                    ],
                ),
            ],
        )


def record_activity(activity: ActivityBase):
    activity.user_type, activity.user_key = get_loggedin_user(session)
    activity.user_display_name = activity.user_key
    activity.support_user_email = get_support_user(session)

    db_session.add(
        ActivityLogRecord(
            id=str(uuid.uuid4()),
            organization_id=activity.organization_id,
            activity_name=activity.__class__.__name__,
            info=activity.__dict__,
        )
    )


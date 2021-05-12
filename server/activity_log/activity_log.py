import enum
import uuid
from typing import NamedTuple, Optional
from dataclasses import dataclass, field
from flask import session

from ..models import ActivityLogRecord
from ..database import db_session
from ..auth.lib import get_loggedin_user, get_support_user


@dataclass
class ActivityBase:
    organization_id: str
    organization_name: str
    user_type: Optional[str]
    user_key: Optional[str]
    user_display_name: Optional[str]
    support_user_email: Optional[str]

    def slack_message(self) -> str:
        return ""


@dataclass
class CreateAudit(ActivityBase):
    election_id: str
    audit_name: str
    audit_type: str

    def slack_message(self) -> str:
        return "\n".join(
            [
                f"*{self.user_display_name} created an audit*",
                f"_Audit Name_: {self.audit_name}",
                f"_Organization_: {self.organization_name}",
            ]
        )


def record_activity(activity: ActivityBase):
    activity.user_type, activity.user_key = get_loggedin_user(session)
    activity.support_user_email = get_support_user(session)

    db_session.add(
        ActivityLogRecord(
            id=str(uuid.uuid4()),
            organization_id=activity.organization_id,
            activity_name=activity.__class__.__name__,
            metadata=activity.__dict__,
        )
    )


# pylint: disable=no-member
import uuid
from typing import Optional
from datetime import datetime
from attr import attrs
from flask import session

from ..models import ActivityLogRecord
from ..database import db_session
from ..auth.lib import get_loggedin_user, get_support_user


@attrs(auto_attribs=True, kw_only=True)
class ActivityBase:
    organization_id: str
    organization_name: str
    # The following fields are auto-populated by record_activity, so we set them
    # to None by default.
    user_type: Optional[str] = None
    user_key: Optional[str] = None
    user_display_name: Optional[str] = None
    support_user_email: Optional[str] = None
    timestamp: Optional[datetime] = None


@attrs(auto_attribs=True, kw_only=True)
class AuditActivity(ActivityBase):
    election_id: str
    audit_name: str
    audit_type: str


@attrs(auto_attribs=True, kw_only=True)
class CreateAudit(AuditActivity):
    pass


@attrs(auto_attribs=True, kw_only=True)
class DeleteAudit(AuditActivity):
    pass


@attrs(auto_attribs=True, kw_only=True)
class StartRound(AuditActivity):
    round_num: int


@attrs(auto_attribs=True, kw_only=True)
class EndRound(AuditActivity):
    round_num: int


def record_activity(activity: ActivityBase):
    if session:
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

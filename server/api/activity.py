from typing import Any, Dict, cast
from flask import session
from flask.json import jsonify
from werkzeug.exceptions import Forbidden

from ..models import *
from ..auth.auth_helpers import UserType, allow_public_access, get_loggedin_user
from . import api
from ..util.isoformat import isoformat


def serialize_activity(activity: ActivityLogRecord):
    activity_info = cast(Dict[str, Any], activity.info)
    return dict(
        id=activity.id,
        activityName=activity.activity_name,
        timestamp=isoformat(activity.timestamp),
        user=(
            activity_info["base"].get("user_key")
            and dict(
                key=activity_info["base"]["user_key"],
                type=activity_info["base"]["user_type"],
                supportUser=(activity_info["base"].get("support_user_email")),
            )
        ),
        election=(
            activity_info["base"].get("election_id")
            and dict(
                id=activity_info["base"]["election_id"],
                auditName=activity_info["base"]["audit_name"],
                auditType=activity_info["base"]["audit_type"],
            )
        ),
        info={key: val for key, val in activity_info.items() if key != "base"},
    )


@api.route("/organizations/<organization_id>/activities", methods=["GET"])
@allow_public_access  # Access control implemented in the endpoint
def list_activities(organization_id: str):
    user_type, user_key = get_loggedin_user(session)
    user = User.query.filter_by(email=user_key).one_or_none()
    if (
        not user
        or user_type != UserType.AUDIT_ADMIN
        or not any(org.id == organization_id for org in user.organizations)
    ):
        return Forbidden()

    activities = (
        ActivityLogRecord.query.filter_by(organization_id=organization_id)
        .order_by(ActivityLogRecord.timestamp.desc())
        .all()
    )
    return jsonify([serialize_activity(activity) for activity in activities])

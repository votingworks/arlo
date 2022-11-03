from flask import session
from flask.json import jsonify
from werkzeug.exceptions import Forbidden

from ..models import *  # pylint: disable=wildcard-import
from ..auth.auth_helpers import UserType, allow_public_access, get_loggedin_user
from . import api
from ..util.isoformat import isoformat


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
    return jsonify(
        [
            dict(
                id=activity.id,
                activityName=activity.activity_name,
                timestamp=isoformat(activity.timestamp),
                user=(
                    activity.info["base"].get("user_key")
                    and dict(
                        key=activity.info["base"]["user_key"],
                        type=activity.info["base"]["user_type"],
                        supportUser=(activity.info["base"].get("support_user_email")),
                    )
                ),
                election=(
                    activity.info["base"].get("election_id")
                    and dict(
                        id=activity.info["base"]["election_id"],
                        auditName=activity.info["base"]["audit_name"],
                        auditType=activity.info["base"]["audit_type"],
                    )
                ),
                info={key: val for key, val in activity.info.items() if key != "base"},
            )
            for activity in activities
        ]
    )

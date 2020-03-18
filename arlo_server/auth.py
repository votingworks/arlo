from enum import Enum
from flask import session
from typing import Optional, Tuple, Union
from werkzeug.exceptions import Unauthorized, Forbidden

from arlo_server.models import User


class UserType(str, Enum):
    AUDIT_ADMIN = "audit_admin"
    JURISDICTION_ADMIN = "jurisdiction_admin"


def set_loggedin_user(user_type: UserType, user_email: str):
    session["_user"] = {"type": user_type, "email": user_email}


def get_loggedin_user() -> Union[Tuple[UserType, str], Tuple[None, None]]:
    user = session.get("_user", None)
    return (user["type"], user["email"]) if user else (None, None)


def get_loggedin_user_record():
    user_type, user_email = get_loggedin_user()
    return (
        (user_type, User.query.filter_by(email=user_email).one())
        if user_email
        else (None, None)
    )


def clear_loggedin_user():
    session["_user"] = None


def require_audit_admin_for_organization(organization_id: Optional[str]):
    if not organization_id:
        return

    user_type, user = get_loggedin_user_record()

    if not user:
        raise Unauthorized(
            description=f"Anonymous users do not have access to organization {organization_id}"
        )

    if user_type != UserType.AUDIT_ADMIN:
        raise Forbidden(
            description=f"{user.email} is not logged in as an audit admin and so does not have access to organization {organization_id}"
        )

    for org in user.organizations:
        if org.id == organization_id:
            return
    raise Forbidden(
        description=f"{user.email} does not have access to organization {organization_id}"
    )

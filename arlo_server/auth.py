import functools
from enum import Enum
from flask import session
from typing import Callable, Optional, Tuple, Union
from werkzeug.exceptions import Unauthorized, Forbidden

from arlo_server.models import Election, User


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


def with_election_access(user_type: UserType):
    """
    Flask route decorator that restricts access to a route based on the current
    logged-in user's access to the election at the route's path.

    To use this, you must have a path component named `election_id` and a route
    parameter named `election`.
    """
    if user_type != UserType.AUDIT_ADMIN:
        raise Exception(f"user type {user_type} is not yet supported")

    def decorator(route: Callable):
        @functools.wraps(route)
        def wrapper(*args, **kwargs):
            if "election_id" not in kwargs:
                raise Exception(f"expected 'election_id' in kwargs but got: {kwargs}")
            election = Election.query.get_or_404(kwargs.pop("election_id"))
            require_audit_admin_for_organization(election.organization_id)
            kwargs["election"] = election
            return route(*args, **kwargs)

        return wrapper

    return decorator

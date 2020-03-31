import functools
from enum import Enum
from flask import session
from typing import Callable, Optional, Tuple, Union
from werkzeug.exceptions import Unauthorized, Forbidden

from arlo_server.models import Election, User, Jurisdiction


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


def require_jurisdiction_admin_for_jurisdiction(
    jurisdiction_id: str, election: Election
):
    user_type, user = get_loggedin_user_record()

    if not user:
        raise Unauthorized(
            description=f"Anonymous users do not have access to jurisdiction {jurisdiction_id}"
        )

    if user_type != UserType.JURISDICTION_ADMIN:
        raise Forbidden(
            description=f"{user.email} is not logged in as a jurisdiction admin and so does not have access to jurisdiction {jurisdiction_id}"
        )

    jurisdiction = next(
        (j for j in user.jurisdictions if j.id == jurisdiction_id), None
    )
    if not jurisdiction:
        raise Forbidden(
            description=f"{user.email} does not have access to jurisdiction {jurisdiction_id}"
        )
    if jurisdiction.election_id != election.id:
        raise Forbidden(
            description=f"Jurisdiction {jurisdiction.id} is not associated with election {election.id}"
        )


def with_election_access(route: Callable):
    """
    Flask route decorator that restricts access to a route to Audit Admins
    that have access to the election at the route's path. It also loads the
    election object.

    To use this, you must have:
    - a path component named `election_id`
    - a route parameter named `election`
    """

    @functools.wraps(route)
    def wrapper(*args, **kwargs):
        if "election_id" not in kwargs:
            raise Exception(f"expected 'election_id' in kwargs but got: {kwargs}")

        election = Election.query.get_or_404(kwargs.pop("election_id"))

        require_audit_admin_for_organization(election.organization_id)

        kwargs["election"] = election

        return route(*args, **kwargs)

    return wrapper


def with_jurisdiction_access(route: Callable):
    """
    Flask route decorator that restricts access to a route to Jurisdiction
    Admins that have access to the election and jurisdiction at the route's
    path. It also loads the election and jurisdiction objects.

    To use this, you must have:
    - a path component named `election_id`
    - a route parameter named `election`
    - a path component named `jurisdiction_id`
    - a route parameter named `jurisdiction`
    """

    @functools.wraps(route)
    def wrapper(*args, **kwargs):
        if "election_id" not in kwargs:
            raise Exception(f"expected 'election_id' in kwargs but got: {kwargs}")
        if "jurisdiction_id" not in kwargs:
            raise Exception(f"expected 'jurisdiction_id' in kwargs but got: {kwargs}")

        election = Election.query.get_or_404(kwargs.pop("election_id"))
        jurisdiction = Jurisdiction.query.get_or_404(kwargs.pop("jurisdiction_id"))

        require_jurisdiction_admin_for_jurisdiction(jurisdiction.id, election)

        kwargs["election"] = election
        kwargs["jurisdiction"] = jurisdiction

        return route(*args, **kwargs)

    return wrapper

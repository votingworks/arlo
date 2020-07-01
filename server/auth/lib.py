import functools
import enum
from typing import Callable, Optional, Tuple, Union
from flask import session
from werkzeug.exceptions import Forbidden, Unauthorized

from ..models import *  # pylint: disable=wildcard-import


class UserType(str, enum.Enum):
    # Audit admins are represented with a User record associated with one or
    # more Organizations and use User.email as their login key.
    AUDIT_ADMIN = "audit_admin"
    # Jurisdiction admins are represented with a User record associated with
    # one or more Jurisdictions and use User.email as their login key.
    JURISDICTION_ADMIN = "jurisdiction_admin"
    # Audit boards are represented by the AuditBoard record and use
    # AuditBoard.id as their login key. In the real world, a member of an audit
    # board will log in on behalf of the audit board by navigating to
    # /audit-board/<passphrase>, initiating the session. We consider the whole
    # audit board to be one "logged in user," as opposed to trying to know
    # which specific audit board member logged in.
    AUDIT_BOARD = "audit_board"


_SUPERADMIN = "_superadmin"
_USER = "_user"


def set_loggedin_user(user_type: UserType, user_key: str):
    session[_USER] = {"type": user_type, "key": user_key}


def get_loggedin_user() -> Union[Tuple[UserType, str], Tuple[None, None]]:
    user = session.get(_USER, None)
    return (user["type"], user["key"]) if user else (None, None)


def clear_loggedin_user():
    session[_USER] = None


##
## The super admin bit lets a user impersonate any other user
## Having the bit only grants access to the superadmin functionality
## that enables becoming any other user, and then taking action as them.
##
## This state of superadmin'ness is kept separate from the normal user session
## field so that impersonation can be as close as possible to the same user session
## and so that a superadmin can become any other user at any other time without having
## to re-login
##


def set_superadmin():
    session[_SUPERADMIN] = True  # pragma: no cover


def clear_superadmin():  # pragma: no cover
    if _SUPERADMIN in session:
        del session[_SUPERADMIN]


def is_superadmin():
    return session.get(_SUPERADMIN, False)  # pragma: no cover


def require_superadmin():
    if not is_superadmin():
        raise Forbidden(description="requires superadmin privileges")


def require_audit_admin_for_organization(organization_id: Optional[str]):
    if not organization_id:
        return

    user_type, user_key = get_loggedin_user()

    if not user_type:
        raise Unauthorized(
            description=f"Anonymous users do not have access to organization {organization_id}"
        )

    if user_type != UserType.AUDIT_ADMIN:
        raise Forbidden(
            description=f"User is not logged in as an audit admin and so does not have access to organization {organization_id}"
        )

    user = User.query.filter_by(email=user_key).one()
    for org in user.organizations:
        if org.id == organization_id:
            return
    raise Forbidden(
        description=f"{user.email} does not have access to organization {organization_id}"
    )


def require_jurisdiction_admin_for_jurisdiction(jurisdiction_id: str, election_id: str):
    user_type, user_key = get_loggedin_user()

    if not user_type:
        raise Unauthorized(
            description=f"Anonymous users do not have access to jurisdiction {jurisdiction_id}"
        )

    if user_type != UserType.JURISDICTION_ADMIN:
        raise Forbidden(
            description=f"User is not logged in as a jurisdiction admin and so does not have access to jurisdiction {jurisdiction_id}"
        )

    user = User.query.filter_by(email=user_key).one()
    jurisdiction = next(
        (j for j in user.jurisdictions if j.id == jurisdiction_id), None
    )
    if not jurisdiction:
        raise Forbidden(
            description=f"{user.email} does not have access to jurisdiction {jurisdiction_id}"
        )
    if jurisdiction.election_id != election_id:
        raise Forbidden(
            description=f"Jurisdiction {jurisdiction.id} is not associated with election {election_id}"
        )


def require_audit_board_logged_in(
    audit_board: AuditBoard, election_id: str, jurisdiction: Jurisdiction, round_id: str
):
    user_type, user_key = get_loggedin_user()

    if not user_key:
        raise Unauthorized(
            description=f"Anonymous users do not have access to audit board {audit_board.id}"
        )

    if user_type != UserType.AUDIT_BOARD:
        raise Forbidden(
            description=f"User is not logged in as an audit board and so does not have access to audit board {audit_board.id}"
        )

    if audit_board.id != user_key:
        raise Forbidden(
            description=f"User does not have access to audit board {audit_board.id}"
        )

    if audit_board.jurisdiction.election_id != election_id:
        raise Forbidden(
            description=f"Audit board {audit_board.id} is not associated with election {election_id}"
        )
    if audit_board.jurisdiction_id != jurisdiction.id:
        raise Forbidden(
            description=f"Audit board {audit_board.id} is not associated with jurisdiction {jurisdiction.id}"
        )
    if audit_board.round_id != round_id:
        raise Forbidden(
            description=f"Audit board {audit_board.id} is not associated with round {round_id}"
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
            raise Exception(
                f"expected 'election_id' in kwargs but got: {kwargs}"
            )  # pragma: no cover

        election = get_or_404(Election, kwargs.pop("election_id"))

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
        for key in ["election_id", "jurisdiction_id"]:
            if key not in kwargs:
                raise Exception(
                    f"expected '{key}' in kwargs but got: {kwargs}"
                )  # pragma: no cover

        election = get_or_404(Election, kwargs.pop("election_id"))
        jurisdiction = get_or_404(Jurisdiction, kwargs.pop("jurisdiction_id"))

        require_jurisdiction_admin_for_jurisdiction(jurisdiction.id, election.id)

        kwargs["election"] = election
        kwargs["jurisdiction"] = jurisdiction

        return route(*args, **kwargs)

    return wrapper


def with_audit_board_access(route: Callable):
    """
    Flask route decorator that restricts access to a route to Audit Board
    members that are part of the audit board for the election, jurisdiction,
    round, and audit board ids in the route's path. It also loads the
    election, jurisdiction, round, and audit board objects.

    To use this, you must have:
    - a path component named `election_id`
    - a route parameter named `election`
    - a path component named `jurisdiction_id`
    - a route parameter named `jurisdiction`
    - a path component named `round_id`
    - a route parameter named `round`
    - a path component named `audit_board_id`
    - a route parameter named `audit_board`
    """

    @functools.wraps(route)
    def wrapper(*args, **kwargs):
        for key in ["election_id", "jurisdiction_id", "round_id", "audit_board_id"]:
            if key not in kwargs:
                raise Exception(
                    f"expected '{key}' in kwargs but got: {kwargs}"
                )  # pragma: no cover

        election = get_or_404(Election, kwargs.pop("election_id"))
        jurisdiction = get_or_404(Jurisdiction, kwargs.pop("jurisdiction_id"))
        round = get_or_404(Round, kwargs.pop("round_id"))
        audit_board = get_or_404(AuditBoard, kwargs.pop("audit_board_id"))

        require_audit_board_logged_in(audit_board, election.id, jurisdiction, round.id)

        kwargs["election"] = election
        kwargs["jurisdiction"] = jurisdiction
        kwargs["round"] = round
        kwargs["audit_board"] = audit_board

        return route(*args, **kwargs)

    return wrapper


def with_superadmin_access(route: Callable):
    """
    Flask route decorator that restricts access to a route to a superadmin.
    """

    @functools.wraps(route)
    def wrapper(*args, **kwargs):
        require_superadmin()
        return route(*args, **kwargs)

    return wrapper

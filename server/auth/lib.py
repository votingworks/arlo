import functools
import enum
from datetime import datetime, timezone
from typing import Callable, Tuple, Union, List, Optional
from flask import session
from werkzeug.exceptions import Forbidden, Unauthorized
from sqlalchemy.orm import Query

from ..models import *  # pylint: disable=wildcard-import
from .. import config


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
_CREATED_AT = "_created_at"
_LAST_REQUEST_AT = "_last_request_at"


def set_loggedin_user(
    session, user_type: UserType, user_key: str, from_superadmin: bool = False
):
    session[_USER] = {"type": user_type, "key": user_key}
    # We don't want to set the created time when a superadmin logs in as
    # another user, since it was already set when the superadmin logged in.
    if not from_superadmin:
        session[_CREATED_AT] = datetime.now(timezone.utc).isoformat()
    session[_LAST_REQUEST_AT] = datetime.now(timezone.utc).isoformat()


def get_loggedin_user(session) -> Union[Tuple[UserType, str], Tuple[None, None]]:
    check_session_expiration(session)
    user = session.get(_USER, None)
    return (user["type"], user["key"]) if user else (None, None)


def clear_loggedin_user(session):
    session[_USER] = None


def check_session_expiration(session):
    if (
        _CREATED_AT not in session
        or _LAST_REQUEST_AT not in session
        or (
            datetime.now(timezone.utc)
            > datetime.fromisoformat(session[_CREATED_AT]) + config.SESSION_LIFETIME
        )
        or (
            datetime.now(timezone.utc)
            > datetime.fromisoformat(session[_LAST_REQUEST_AT])
            + config.SESSION_INACTIVITY_TIMEOUT
        )
    ):
        clear_superadmin_user(session)
        clear_loggedin_user(session)
    else:
        session[_LAST_REQUEST_AT] = datetime.now(timezone.utc).isoformat()


## The super admin bit lets a user impersonate any other user
## Having the bit only grants access to the superadmin functionality
## that enables becoming any other user, and then taking action as them.
##
## This state of superadmin'ness is kept separate from the normal user session
## field so that impersonation can be as close as possible to the same user session
## and so that a superadmin can become any other user at any other time without having
## to re-login
def set_superadmin_user(session, email: str):
    session[_SUPERADMIN] = email
    session[_CREATED_AT] = datetime.now(timezone.utc).isoformat()
    session[_LAST_REQUEST_AT] = datetime.now(timezone.utc).isoformat()


def clear_superadmin_user(session):
    if _SUPERADMIN in session:
        del session[_SUPERADMIN]


def get_superadmin_user(session) -> Optional[str]:
    check_session_expiration(session)
    superadmin_email: Optional[str] = session.get(_SUPERADMIN)
    return superadmin_email


def find_or_404(query: Query):
    instance = query.first()
    if instance:
        return instance
    raise NotFound()


def check_access(
    user_types: List[UserType],
    election: Election,
    jurisdiction: Jurisdiction = None,
    audit_board: AuditBoard = None,
):
    # Check user type is allowed
    user_type, user_key = get_loggedin_user(session)
    if not user_key:
        raise Unauthorized("Please log in to access Arlo")

    if user_type not in user_types:
        raise Forbidden(f"Access forbidden for user type {user_type}")

    # Check that the user has access to the resource they are requesting
    if user_type == UserType.AUDIT_ADMIN:
        user = User.query.filter_by(email=user_key).one()
        if not any(
            org for org in user.organizations if org.id == election.organization_id
        ):
            raise Forbidden(
                description=f"{user.email} does not have access to organization {election.organization_id}"
            )

    elif user_type == UserType.JURISDICTION_ADMIN:
        assert jurisdiction
        user = User.query.filter_by(email=user_key).one()
        if not any(j for j in user.jurisdictions if j.id == jurisdiction.id):
            raise Forbidden(
                description=f"{user.email} does not have access to jurisdiction {jurisdiction.id}"
            )

    else:
        assert user_type == UserType.AUDIT_BOARD
        assert audit_board
        if audit_board.id != user_key:
            raise Forbidden(
                description=f"User does not have access to audit board {audit_board.id}"
            )


def restrict_access(user_types: List[UserType]):
    """
    Flask route decorator that restricts access to a route to the given user types.
    """

    def restrict_access_decorator(route: Callable):
        @functools.wraps(route)
        def wrapper(*args, **kwargs):
            if "jurisdiction_id" in kwargs and "election_id" not in kwargs:
                raise Exception(
                    "election_id required in route params"
                )  # pragma: no cover
            if "round_id" in kwargs and "election_id" not in kwargs:
                raise Exception(
                    "election_id required in route params"
                )  # pragma: no cover
            if "audit_board_id" in kwargs and "jurisdiction_id" not in kwargs:
                raise Exception(
                    "jurisdiction_id required in route params"
                )  # pragma: no cover
            if "audit_board_id" in kwargs and "round_id" not in kwargs:
                raise Exception("round_id required in route params")  # pragma: no cover

            # Substitute route params for their corresponding resources
            if "election_id" in kwargs:
                election = get_or_404(Election, kwargs.pop("election_id"))
                kwargs["election"] = election

            jurisdiction = None
            if "jurisdiction_id" in kwargs:
                jurisdiction = find_or_404(
                    Jurisdiction.query.filter_by(
                        id=kwargs.pop("jurisdiction_id"), election_id=election.id
                    )
                )
                kwargs["jurisdiction"] = jurisdiction

            round = None
            if "round_id" in kwargs:
                round = find_or_404(
                    Round.query.filter_by(
                        id=kwargs.pop("round_id"), election_id=election.id
                    )
                )
                kwargs["round"] = round

            audit_board = None
            if "audit_board_id" in kwargs:
                audit_board = find_or_404(
                    AuditBoard.query.filter_by(
                        id=kwargs.pop("audit_board_id"),
                        round_id=round.id,
                        jurisdiction_id=jurisdiction.id,
                    )
                )
                kwargs["audit_board"] = audit_board

            check_access(user_types, election, jurisdiction, audit_board)

            return route(*args, **kwargs)

        return wrapper

    return restrict_access_decorator


def restrict_access_superadmin(route: Callable):
    """
    Flask route decorator that restricts access to a route to a superadmin.
    """

    @functools.wraps(route)
    def wrapper(*args, **kwargs):
        if not get_superadmin_user(session):
            raise Forbidden(description="requires superadmin privileges")

        return route(*args, **kwargs)

    return wrapper

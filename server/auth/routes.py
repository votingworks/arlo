from datetime import datetime, timezone
from urllib.parse import urljoin, urlencode
from flask import redirect, jsonify, request, session, render_template
from authlib.integrations.flask_client import OAuth, OAuthError
from werkzeug.exceptions import BadRequest
from pyotp import HOTP
import requests

from . import auth
from ..models import *  # pylint: disable=wildcard-import
from ..database import db_session
from .lib import (
    get_loggedin_user,
    set_loggedin_user,
    clear_loggedin_user,
    set_support_user,
    clear_support_user,
    get_support_user,
    UserType,
)
from ..api.audit_boards import serialize_members
from ..util.isoformat import isoformat
from ..config import (
    LOGIN_CODE_LIFETIME,
    LOGIN_CODE_SECRET,
    MAILGUN_API_KEY,
    MAILGUN_DOMAIN,
    SUPPORT_AUTH0_BASE_URL,
    SUPPORT_AUTH0_CLIENT_ID,
    SUPPORT_AUTH0_CLIENT_SECRET,
    SUPPORT_EMAIL_DOMAIN,
    AUDITADMIN_AUTH0_BASE_URL,
    AUDITADMIN_AUTH0_CLIENT_ID,
    AUDITADMIN_AUTH0_CLIENT_SECRET,
)

SUPPORT_OAUTH_CALLBACK_URL = "/auth/support/callback"
AUDITADMIN_OAUTH_CALLBACK_URL = "/auth/auditadmin/callback"

oauth = OAuth()

auth0_sa = oauth.register(
    "auth0_sa",
    client_id=SUPPORT_AUTH0_CLIENT_ID,
    client_secret=SUPPORT_AUTH0_CLIENT_SECRET,
    api_base_url=SUPPORT_AUTH0_BASE_URL,
    access_token_url=f"{SUPPORT_AUTH0_BASE_URL}/oauth/token",
    authorize_url=f"{SUPPORT_AUTH0_BASE_URL}/authorize",
    authorize_params={"max_age": "0"},
    client_kwargs={"scope": "openid profile email"},
)

auth0_aa = oauth.register(
    "auth0_aa",
    client_id=AUDITADMIN_AUTH0_CLIENT_ID,
    client_secret=AUDITADMIN_AUTH0_CLIENT_SECRET,
    api_base_url=AUDITADMIN_AUTH0_BASE_URL,
    access_token_url=f"{AUDITADMIN_AUTH0_BASE_URL}/oauth/token",
    authorize_url=f"{AUDITADMIN_AUTH0_BASE_URL}/authorize",
    authorize_params={"max_age": "0"},
    client_kwargs={"scope": "openid profile email"},
)


def serialize_election(election):
    return {
        "id": election.id,
        "auditName": election.audit_name,
        "electionName": election.election_name,
        "state": election.state,
    }


@auth.route("/api/me")
def auth_me():
    user_type, user_key = get_loggedin_user(session)
    user = None
    if user_type in [UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN]:
        db_user = User.query.filter_by(email=user_key).one()
        user = dict(
            type=user_type,
            email=db_user.email,
            organizations=[
                {
                    "id": org.id,
                    "name": org.name,
                    "elections": [
                        serialize_election(election)
                        for election in org.elections
                        if election.deleted_at is None
                    ],
                }
                for org in db_user.organizations
            ],
            jurisdictions=[
                {
                    "id": jurisdiction.id,
                    "name": jurisdiction.name,
                    "election": serialize_election(jurisdiction.election),
                    "numBallots": jurisdiction.manifest_num_ballots,
                }
                for jurisdiction in db_user.jurisdictions
                if jurisdiction.election.deleted_at is None
            ],
        )
    elif user_type == UserType.AUDIT_BOARD:
        audit_board = AuditBoard.query.get(user_key)
        if audit_board.jurisdiction.election.deleted_at is None:
            user = dict(
                type=user_type,
                id=audit_board.id,
                jurisdictionId=audit_board.jurisdiction_id,
                jurisdictionName=audit_board.jurisdiction.name,
                electionId=audit_board.jurisdiction.election.id,
                roundId=audit_board.round_id,
                name=audit_board.name,
                members=serialize_members(audit_board),
                signedOffAt=isoformat(audit_board.signed_off_at),
            )

    support_user_email = get_support_user(session)
    return jsonify(
        user=user, supportUser=support_user_email and {"email": support_user_email}
    )


@auth.route("/auth/logout")
def logout():
    # Because we have max_age on the oauth requests, we don't need to log out
    # of Auth0.
    clear_loggedin_user(session)
    return redirect("/support" if get_support_user(session) else "/")


@auth.route("/auth/support/logout")
def support_logout():
    clear_support_user(session)
    clear_loggedin_user(session)
    return redirect("/")


@auth.route("/auth/support/start")
def support_login():
    redirect_uri = urljoin(request.host_url, SUPPORT_OAUTH_CALLBACK_URL)
    return auth0_sa.authorize_redirect(redirect_uri=redirect_uri)


@auth.route(SUPPORT_OAUTH_CALLBACK_URL)
def support_login_callback():
    auth0_sa.authorize_access_token()
    resp = auth0_sa.get("userinfo")
    userinfo = resp.json()

    # we rely on the auth0 auth here, but check against a single approved domain.
    if (
        userinfo
        and userinfo["email"]
        and userinfo["email"].split("@")[-1] == SUPPORT_EMAIL_DOMAIN
    ):
        set_support_user(session, userinfo["email"])
        return redirect("/support")
    else:
        return redirect("/")


@auth.route("/auth/auditadmin/start")
def auditadmin_login():
    redirect_uri = urljoin(request.host_url, AUDITADMIN_OAUTH_CALLBACK_URL)
    return auth0_aa.authorize_redirect(redirect_uri=redirect_uri)


@auth.route(AUDITADMIN_OAUTH_CALLBACK_URL)
def auditadmin_login_callback():
    auth0_aa.authorize_access_token()
    resp = auth0_aa.get("userinfo")
    userinfo = resp.json()

    if userinfo and userinfo["email"]:
        user = User.query.filter_by(email=userinfo["email"]).first()
        if user and len(user.audit_administrations) > 0:
            set_loggedin_user(session, UserType.AUDIT_ADMIN, userinfo["email"])

    return redirect("/")


def generate_login_code(timestamp: datetime):
    return HOTP(LOGIN_CODE_SECRET).at(
        int(timestamp.timestamp() / LOGIN_CODE_LIFETIME.total_seconds())
    )


def verify_login_code(timestamp: datetime, code: str):
    return HOTP(LOGIN_CODE_SECRET).verify(
        code, int(timestamp.timestamp() / LOGIN_CODE_LIFETIME.total_seconds())
    )


@auth.route("/auth/jurisdictionadmin/code", methods=["POST"])
def jurisdiction_admin_generate_code():
    body = request.get_json()
    user = User.query.filter_by(email=body.get("email")).one_or_none()
    if user is None:
        raise BadRequest(
            "This email address is not authorized to access Arlo."
            " Please check that you typed the email correctly,"
            " or contact your Arlo administrator for access."
        )

    if user.login_code_requested_at is None or (
        # Reuse the existing login code if it hasn't expired yet. That way if
        # they request a new code while waiting for a slow email, we won't wipe
        # out the code we sent when the email does come through.
        datetime.now(timezone.utc) - user.login_code_requested_at
        > LOGIN_CODE_LIFETIME
    ):
        user.login_code_requested_at = datetime.now(timezone.utc)

    user.login_code_attempts = 0

    code = generate_login_code(user.login_code_requested_at)
    email_response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": "Arlo Support <rla@vx.support>",
            "to": [user.email],
            "subject": "Welcome to Arlo - Use the Code in this Email to Log In",
            "text": render_template("email_login_code.txt", code=code),
            "html": render_template("email_login_code.html", code=code),
        },
    )
    email_response.raise_for_status()

    db_session.commit()

    return jsonify(status="ok")


@auth.route("/auth/jurisdictionadmin/login", methods=["POST"])
def jurisdiction_admin_login():
    body = request.get_json()
    user = User.query.filter_by(email=body.get("email")).with_for_update().one_or_none()
    if user is None:
        raise BadRequest("Invalid email address.")

    if user.login_code_attempts > 10:
        user.login_code_requested_at = None
        db_session.commit()
        raise BadRequest("Too many incorrect attempts. Please request a new code.")

    user.login_code_attempts += 1
    db_session.commit()

    if user.login_code_requested_at is None or (
        not verify_login_code(user.login_code_requested_at, body.get("code"))
    ):
        raise BadRequest(
            "Invalid code. Try entering the code again or click Back and request a new code."
        )

    user.login_code_requested_at = None
    db_session.commit()

    set_loggedin_user(session, UserType.JURISDICTION_ADMIN, user.email)

    return jsonify(status="ok")


@auth.route("/auditboard/<passphrase>", methods=["GET"])
def auditboard_passphrase(passphrase: str):
    audit_board = AuditBoard.query.filter_by(passphrase=passphrase).one_or_none()
    if not audit_board:
        return redirect(
            "/?"
            + urlencode(
                {"error": "audit_board_not_found", "message": "Audit board not found."}
            )
        )
    set_loggedin_user(session, UserType.AUDIT_BOARD, audit_board.id)
    return redirect(
        f"/election/{audit_board.jurisdiction.election.id}/audit-board/{audit_board.id}"
    )


@auth.errorhandler(OAuthError)
def handle_oauth_error(error):
    # If Auth0 sends an error to one of the callbacks, we want to redirect the
    # user to the login screen and display the error.
    return redirect(
        "/?"
        + urlencode(
            {
                "error": "oauth",
                "message": f"Login error: {error.error} - {error.description}",
            }
        )
    )

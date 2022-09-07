from email.message import EmailMessage
import secrets
import smtplib
import string
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin, urlencode
from flask import jsonify, request, session, render_template
from authlib.integrations.flask_client import OAuth, OAuthError
from werkzeug.exceptions import BadRequest

from server.util.redirect import redirect

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
from ..activity_log import JurisdictionAdminLogin, record_activity, ActivityBase
from ..util.isoformat import isoformat
from ..config import (
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
    SUPPORT_AUTH0_BASE_URL,
    SUPPORT_AUTH0_CLIENT_ID,
    SUPPORT_AUTH0_CLIENT_SECRET,
    AUDITADMIN_AUTH0_BASE_URL,
    AUDITADMIN_AUTH0_CLIENT_ID,
    AUDITADMIN_AUTH0_CLIENT_SECRET,
)
from .. import config

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
    if user_type == UserType.AUDIT_ADMIN:
        db_user = User.query.filter_by(email=user_key).one()
        user = dict(type=user_type, email=db_user.email, id=db_user.id)
    if user_type == UserType.JURISDICTION_ADMIN:
        db_user = User.query.filter_by(email=user_key).one()
        user = dict(
            type=user_type,
            email=db_user.email,
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

    # We rely on Auth0 here, but check against a list of approved domains.
    if (
        userinfo
        and userinfo["email"]
        and userinfo["email"].split("@")[-1] in config.SUPPORT_EMAIL_DOMAINS
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


def is_code_expired(timestamp: datetime):
    return datetime.now(timezone.utc) - timestamp > config.LOGIN_CODE_LIFETIME


@auth.route("/auth/jurisdictionadmin/code", methods=["POST"])
def jurisdiction_admin_generate_code():
    body = request.get_json()
    user = (
        User.query.filter_by(email=body.get("email").lower())
        .join(JurisdictionAdministration)
        .one_or_none()
    )
    if user is None:
        raise BadRequest(
            "This email address is not authorized to access Arlo."
            " Please check that you typed the email correctly,"
            " or contact your Arlo administrator for access."
        )

    if user.login_code is None or (
        # Only set a new login code if the old one expired. That way if they
        # request a new code while waiting for a slow email, we won't wipe out
        # the code we sent when the email does come through. This also creates
        # a speed bump for brute force attacks.
        is_code_expired(user.login_code_requested_at)
    ):
        user.login_code = "".join(secrets.choice(string.digits) for _ in range(6))
        user.login_code_requested_at = datetime.now(timezone.utc)
        user.login_code_attempts = 0

    if user.login_code_attempts >= 10:
        raise BadRequest(
            "Too many incorrect login attempts. Please wait 15 minutes and then request a new code."
        )

    message = EmailMessage()
    message["Subject"] = "Welcome to Arlo - Use the Code in this Email to Log In"
    message["From"] = "Arlo Support <rla@vx.support>"
    message["To"] = user.email
    message.set_content(render_template("email_login_code.txt", code=user.login_code))
    message.add_alternative(
        render_template("email_login_code.html", code=user.login_code), subtype="html"
    )
    smtp_server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    smtp_server.login(SMTP_USERNAME, SMTP_PASSWORD)
    smtp_server.send_message(message)
    smtp_server.quit()

    db_session.commit()

    return jsonify(status="ok")


def record_login(user: User, error: Optional[str] = None):
    # JAs can only belong to one organization
    organization = list(user.jurisdictions)[0].election.organization
    record_activity(
        JurisdictionAdminLogin(
            timestamp=datetime.now(timezone.utc),
            base=ActivityBase(
                organization_id=organization.id,
                organization_name=organization.name,
                election_id=None,
                audit_name=None,
                audit_type=None,
                user_type="jurisdiction_admin",
                user_key=user.email,
                support_user_email=None,
            ),
            error=error,
        )
    )


@auth.route("/auth/jurisdictionadmin/login", methods=["POST"])
def jurisdiction_admin_login():
    body = request.get_json()
    user = (
        User.query.filter_by(email=body.get("email"))
        .join(JurisdictionAdministration)
        .with_for_update()
        .one_or_none()
    )
    if user is None:
        raise BadRequest("Invalid email address.")

    if user.login_code is None:
        record_login(user, "Needs new code")
        db_session.commit()
        raise BadRequest("Please request a new code.")

    if user.login_code_attempts >= 10:
        record_login(user, "Too many incorrect attempts")
        db_session.commit()
        raise BadRequest(
            "Too many incorrect login attempts. Please wait 15 minutes and then request a new code."
        )

    user.login_code_attempts += 1
    db_session.commit()

    if is_code_expired(user.login_code_requested_at) or not secrets.compare_digest(
        body.get("code"), user.login_code
    ):
        record_login(user, "Invalid code")
        db_session.commit()
        raise BadRequest(
            "Invalid code. Try entering the code again or click Back and request a new code."
        )

    user.login_code = None
    user.login_code_requested_at = None

    set_loggedin_user(session, UserType.JURISDICTION_ADMIN, user.email)
    record_login(user)
    db_session.commit()

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

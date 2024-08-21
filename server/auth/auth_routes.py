from email.message import EmailMessage
import secrets
import smtplib
import string
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin, urlencode
import uuid
from flask import jsonify, request, session, render_template
from authlib.integrations.flask_client import OAuth, OAuthError
from werkzeug.exceptions import BadRequest, Conflict
from xkcdpass import xkcd_password as xp
from server.api.rounds import get_current_round

from . import auth
from ..models import *  # pylint: disable=wildcard-import
from ..database import db_session
from .auth_helpers import (
    allow_public_access,
    get_loggedin_user,
    restrict_access,
    set_loggedin_user,
    clear_loggedin_user,
    set_support_user,
    clear_support_user,
    get_support_user,
    UserType,
)
from ..api.audit_boards import WORDS, serialize_members, validate_members
from ..activity_log import JurisdictionAdminLogin, record_activity, ActivityBase
from ..util.isoformat import isoformat
from ..util.redirect import redirect
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
        "organizationId": election.organization_id,
    }


@auth.route("/api/me")
@allow_public_access
def api_me():
    user_type, user_key = get_loggedin_user(session)
    user = None
    if user_type == UserType.AUDIT_ADMIN:
        db_user = User.query.filter_by(email=user_key).one()
        user = dict(type=user_type, email=db_user.email, id=db_user.id)
    elif user_type == UserType.JURISDICTION_ADMIN:
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
    elif user_type == UserType.TALLY_ENTRY:
        tally_entry_user = TallyEntryUser.query.get(user_key)
        # If login was rejected, user is deleted, so clear them from the session
        if tally_entry_user is None:
            clear_loggedin_user(session)
        else:
            jurisdiction = tally_entry_user.jurisdiction
            if jurisdiction.election.deleted_at is None:
                # Tally entry users get a reponse from /api/me before their login
                # code is confirmed by the JA. Thus, it's important to make sure
                # that we only return data that they are allowed to see during the
                # login process. Data that is only available after login
                # confirmation should be accessed via separate endpoints.
                round = get_current_round(jurisdiction.election)
                assert round is not None
                user = dict(
                    type=user_type,
                    id=tally_entry_user.id,
                    loginCode=tally_entry_user.login_code,
                    loginConfirmedAt=isoformat(tally_entry_user.login_confirmed_at),
                    jurisdictionId=jurisdiction.id,
                    jurisdictionName=jurisdiction.name,
                    electionId=jurisdiction.election.id,
                    auditName=jurisdiction.election.audit_name,
                    roundId=round.id,
                    members=serialize_members(tally_entry_user),
                )

    support_user_email = get_support_user(session)
    return jsonify(
        user=user, supportUser=support_user_email and {"email": support_user_email}
    )


@auth.route("/auth/logout")
@allow_public_access
def logout():
    # Because we have max_age on the oauth requests, we don't need to log out
    # of Auth0.
    clear_loggedin_user(session)
    return redirect("/support" if get_support_user(session) else "/")


@auth.route("/auth/support/logout")
@allow_public_access
def support_logout():
    clear_support_user(session)
    clear_loggedin_user(session)
    return redirect("/")


@auth.route("/auth/support/start")
@allow_public_access
def support_login():
    redirect_uri = urljoin(request.host_url, SUPPORT_OAUTH_CALLBACK_URL)
    return auth0_sa.authorize_redirect(redirect_uri=redirect_uri)


@auth.route(SUPPORT_OAUTH_CALLBACK_URL)
@allow_public_access
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
@allow_public_access
def auditadmin_login():
    redirect_uri = urljoin(request.host_url, AUDITADMIN_OAUTH_CALLBACK_URL)
    return auth0_aa.authorize_redirect(redirect_uri=redirect_uri)


@auth.route(AUDITADMIN_OAUTH_CALLBACK_URL)
@allow_public_access
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
@allow_public_access
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
    smtp_server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
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
@allow_public_access
def jurisdiction_admin_login():
    body = request.get_json()
    user = (
        User.query.filter_by(email=body.get("email").lower())
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
@allow_public_access
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


@auth.route("/tallyentry/<passphrase>", methods=["GET"])
@allow_public_access
def tally_entry_passphrase(passphrase: str):
    jurisdiction = Jurisdiction.query.filter_by(
        tally_entry_passphrase=passphrase
    ).one_or_none()
    if jurisdiction is None:
        return redirect("/tally-entry?" + urlencode({"error": "login_link_not_found"}))

    tally_entry_user = TallyEntryUser(
        id=str(uuid.uuid4()), jurisdiction_id=jurisdiction.id,
    )
    db_session.add(tally_entry_user)
    db_session.commit()

    # We set the tally entry user in the session even though they haven't fully
    # logged in yet. This allows the user to hit /api/me to retrieve
    # jurisdiction name and login code to show on the login screens. The
    # restrict_access decorator ensures that they can't do anything else until
    # their login code is confirmed by the JA.
    set_loggedin_user(session, UserType.TALLY_ENTRY, tally_entry_user.id)

    return redirect("/tally-entry")


@auth.route("/auth/tallyentry/code", methods=["POST"])
@allow_public_access  # Access control is implemented within the route
def tally_entry_user_generate_code():
    _, user_key = get_loggedin_user(session)
    tally_entry_user = get_or_404(TallyEntryUser, user_key)

    body = request.get_json()
    members = body.get("members", [])
    validate_members(members)

    tally_entry_user.member_1 = members[0]["name"].strip()
    tally_entry_user.member_1_affiliation = members[0]["affiliation"]
    if len(members) > 1:
        tally_entry_user.member_2 = members[1]["name"].strip()
        tally_entry_user.member_2_affiliation = members[1]["affiliation"]

    # Generate a login code and make sure its unique to the jurisdiction.
    #
    # Note that this doesn't protect against race conditions that might result
    # in a duplicate code, but we have a unique index on the table that will
    # prevent the code from being written in that very rare case. Here we're
    # just checking for collisions not resulting from a race.
    while True:
        login_code = "".join(secrets.choice(string.digits) for _ in range(3))
        if not TallyEntryUser.query.filter_by(
            jurisdiction_id=tally_entry_user.jurisdiction_id, login_code=login_code
        ).one_or_none():
            tally_entry_user.login_code = login_code
            break

    # TODO add a login code created at timestamp so we can expire old codes
    # https://github.com/votingworks/arlo/issues/1633

    db_session.commit()

    return jsonify(status="ok")


@auth.route(
    "/auth/tallyentry/election/<election_id>/jurisdiction/<jurisdiction_id>",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def tally_entry_jurisdiction_generate_passphrase(
    election: Election, jurisdiction: Jurisdiction
):
    if election.audit_type != AuditType.BATCH_COMPARISON:
        raise Conflict(
            "Tally entry accounts are only supported in batch comparison audits."
        )

    jurisdiction.tally_entry_passphrase = xp.generate_xkcdpassword(
        WORDS, numwords=4, delimiter="-"
    )

    db_session.commit()
    return jsonify(status="ok")


@auth.route(
    "/auth/tallyentry/election/<election_id>/jurisdiction/<jurisdiction_id>",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def tally_entry_jurisdiction_status(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    tally_entry_users = (
        TallyEntryUser.query.filter_by(jurisdiction_id=jurisdiction.id)
        # The JA only needs to know about tally entry users that have gotten far
        # enough through the login process to have a login code
        .filter(TallyEntryUser.login_code.isnot(None))
        .order_by(TallyEntryUser.created_at.desc())
        .all()
    )
    return jsonify(
        passphrase=jurisdiction.tally_entry_passphrase,
        loginRequests=[
            dict(
                tallyEntryUserId=tally_entry_user.id,
                members=serialize_members(tally_entry_user),
                loginConfirmedAt=isoformat(tally_entry_user.login_confirmed_at),
            )
            for tally_entry_user in tally_entry_users
        ],
    )


@auth.route(
    "/auth/tallyentry/election/<election_id>/jurisdiction/<jurisdiction_id>/confirm",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def tally_entry_jurisdiction_confirm_login_code(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    body = request.get_json()
    tally_entry_user = TallyEntryUser.query.get(body.get("tallyEntryUserId"))
    if not tally_entry_user or tally_entry_user.jurisdiction_id != jurisdiction.id:
        raise BadRequest("Tally entry user not found.")

    if body.get("loginCode") != tally_entry_user.login_code:
        raise BadRequest("Invalid code, please try again.")

    tally_entry_user.login_confirmed_at = datetime.now(timezone.utc)

    db_session.commit()

    return jsonify(status="ok")


@auth.route(
    "/auth/tallyentry/election/<election_id>/jurisdiction/<jurisdiction_id>/reject",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def tally_entry_jurisdiction_reject_request(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    body = request.get_json()
    tally_entry_user = TallyEntryUser.query.get(body.get("tallyEntryUserId"))
    if not tally_entry_user or tally_entry_user.jurisdiction_id != jurisdiction.id:
        raise BadRequest("Tally entry user not found.")

    db_session.delete(tally_entry_user)
    db_session.commit()

    return jsonify(status="ok")


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

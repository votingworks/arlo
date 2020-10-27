from urllib.parse import urljoin
from flask import redirect, jsonify, request
from authlib.integrations.flask_client import OAuth

from . import auth
from ..models import *  # pylint: disable=wildcard-import
from .lib import (
    get_loggedin_user,
    set_loggedin_user,
    clear_loggedin_user,
    set_superadmin,
    clear_superadmin,
    UserType,
)
from ..api.audit_boards import serialize_members
from ..util.isoformat import isoformat
from ..config import (
    SUPERADMIN_AUTH0_BASE_URL,
    SUPERADMIN_AUTH0_CLIENT_ID,
    SUPERADMIN_AUTH0_CLIENT_SECRET,
    SUPERADMIN_EMAIL_DOMAIN,
    AUDITADMIN_AUTH0_BASE_URL,
    AUDITADMIN_AUTH0_CLIENT_ID,
    AUDITADMIN_AUTH0_CLIENT_SECRET,
    JURISDICTIONADMIN_AUTH0_BASE_URL,
    JURISDICTIONADMIN_AUTH0_CLIENT_ID,
    JURISDICTIONADMIN_AUTH0_CLIENT_SECRET,
)

SUPERADMIN_OAUTH_CALLBACK_URL = "/auth/superadmin/callback"
AUDITADMIN_OAUTH_CALLBACK_URL = "/auth/auditadmin/callback"
JURISDICTIONADMIN_OAUTH_CALLBACK_URL = "/auth/jurisdictionadmin/callback"

oauth = OAuth()

auth0_sa = oauth.register(
    "auth0_sa",
    client_id=SUPERADMIN_AUTH0_CLIENT_ID,
    client_secret=SUPERADMIN_AUTH0_CLIENT_SECRET,
    api_base_url=SUPERADMIN_AUTH0_BASE_URL,
    access_token_url=f"{SUPERADMIN_AUTH0_BASE_URL}/oauth/token",
    authorize_url=f"{SUPERADMIN_AUTH0_BASE_URL}/authorize",
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

auth0_ja = oauth.register(
    "auth0_ja",
    client_id=JURISDICTIONADMIN_AUTH0_CLIENT_ID,
    client_secret=JURISDICTIONADMIN_AUTH0_CLIENT_SECRET,
    api_base_url=JURISDICTIONADMIN_AUTH0_BASE_URL,
    access_token_url=f"{JURISDICTIONADMIN_AUTH0_BASE_URL}/oauth/token",
    authorize_url=f"{JURISDICTIONADMIN_AUTH0_BASE_URL}/authorize",
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
    user_type, user_key = get_loggedin_user()
    if user_type in [UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN]:
        user = User.query.filter_by(email=user_key).one()
        return jsonify(
            type=user_type,
            email=user.email,
            organizations=[
                {
                    "id": org.id,
                    "name": org.name,
                    "elections": [serialize_election(e) for e in org.elections],
                }
                for org in user.organizations
            ],
            jurisdictions=[
                {"id": j.id, "name": j.name, "election": serialize_election(j.election)}
                for j in user.jurisdictions
            ],
        )
    elif user_type == UserType.AUDIT_BOARD:
        audit_board = AuditBoard.query.get(user_key)
        return jsonify(
            type=user_type,
            id=audit_board.id,
            jurisdictionId=audit_board.jurisdiction_id,
            roundId=audit_board.round_id,
            name=audit_board.name,
            members=serialize_members(audit_board),
            signedOffAt=isoformat(audit_board.signed_off_at),
        )
    else:
        # sticking to JSON when not logged in, because same data type,
        # sending a null object because there is no user logged in.
        # Considered an empty object, but that seemed inconsistent.
        return jsonify(None)


@auth.route("/auth/logout")
def logout():
    clear_superadmin()

    user_type, _user_email = get_loggedin_user()
    if not user_type:
        return redirect("/")

    clear_loggedin_user()

    # because we have max_age on the oauth requests,
    # we don't need to log out of Auth0.
    return redirect("/")


@auth.route("/auth/superadmin/start")
def superadmin_login():
    redirect_uri = urljoin(request.host_url, SUPERADMIN_OAUTH_CALLBACK_URL)
    return auth0_sa.authorize_redirect(redirect_uri=redirect_uri)


@auth.route(SUPERADMIN_OAUTH_CALLBACK_URL)
def superadmin_login_callback():
    auth0_sa.authorize_access_token()
    resp = auth0_sa.get("userinfo")
    userinfo = resp.json()

    # we rely on the auth0 auth here, but check against a single approved domain.
    if (
        userinfo
        and userinfo["email"]
        and userinfo["email"].split("@")[-1] == SUPERADMIN_EMAIL_DOMAIN
    ):
        set_superadmin()
        return redirect("/superadmin/")
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
            set_loggedin_user(UserType.AUDIT_ADMIN, userinfo["email"])

    return redirect("/")


@auth.route("/auth/jurisdictionadmin/start")
def jurisdictionadmin_login():
    redirect_uri = urljoin(request.host_url, JURISDICTIONADMIN_OAUTH_CALLBACK_URL)
    return auth0_ja.authorize_redirect(redirect_uri=redirect_uri)


@auth.route(JURISDICTIONADMIN_OAUTH_CALLBACK_URL)
def jurisdictionadmin_login_callback():
    auth0_ja.authorize_access_token()
    resp = auth0_ja.get("userinfo")
    userinfo = resp.json()

    if userinfo and userinfo["email"]:
        user = User.query.filter_by(email=userinfo["email"]).first()
        if user and len(user.jurisdiction_administrations) > 0:
            set_loggedin_user(UserType.JURISDICTION_ADMIN, userinfo["email"])

    return redirect("/")


@auth.route("/auditboard/<passphrase>", methods=["GET"])
def auditboard_passphrase(passphrase):
    auditboard = AuditBoard.query.filter_by(passphrase=passphrase).one()
    set_loggedin_user(UserType.AUDIT_BOARD, auditboard.id)
    return redirect(
        f"/election/{auditboard.jurisdiction.election.id}/audit-board/{auditboard.id}"
    )

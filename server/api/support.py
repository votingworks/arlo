import uuid
import secrets
from typing import Optional
from urllib.parse import urlparse
from flask import jsonify, request, session, redirect
from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0
from auth0.v3.exceptions import Auth0Error
from werkzeug.exceptions import Conflict

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..database import db_session
from ..auth import (
    restrict_access_support,
    set_loggedin_user,
    UserType,
)
from ..config import (
    AUDITADMIN_AUTH0_BASE_URL,
    AUDITADMIN_AUTH0_CLIENT_ID,
    AUDITADMIN_AUTH0_CLIENT_SECRET,
    FLASK_ENV,
)
from ..util.jsonschema import validate

AUTH0_DOMAIN = urlparse(AUDITADMIN_AUTH0_BASE_URL).hostname


def auth0_get_token() -> str:
    response = GetToken(AUTH0_DOMAIN).client_credentials(
        AUDITADMIN_AUTH0_CLIENT_ID,
        AUDITADMIN_AUTH0_CLIENT_SECRET,
        f"https://{AUTH0_DOMAIN}/api/v2/",
    )
    return str(response["access_token"])


def auth0_create_audit_admin(email: str) -> Optional[str]:
    # In dev/staging environments, if we're pointing to a fake OAuth server
    # instead of Auth0, we shouldn't try to use the Auth0 API
    if FLASK_ENV in ["development", "staging"] and "auth0.com" not in str(AUTH0_DOMAIN):
        return None  # pragma: no cover

    token = auth0_get_token()
    auth0 = Auth0(AUTH0_DOMAIN, token)
    try:
        user = auth0.users.create(
            dict(
                email=email,
                password=secrets.token_urlsafe(),
                connection="Username-Password-Authentication",
            )
        )
        return str(user["user_id"])
    except Auth0Error as error:
        # If user already exists in Auth0, no problem!
        if error.status_code == 409:
            users = auth0.users_by_email.search_users_by_email(email.lower())
            return str(users[0]["user_id"])
        raise error


@api.route("/support/organizations", methods=["GET"])
@restrict_access_support
def list_organizations():
    organizations = Organization.query.order_by(Organization.name).all()
    return jsonify(
        [
            dict(id=organization.id, name=organization.name)
            for organization in organizations
        ]
    )


ORGANIZATION_SCHEMA = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "additionalProperties": False,
    "required": ["name"],
}


@api.route("/support/organizations", methods=["POST"])
@restrict_access_support
def create_organization():
    organization = request.get_json()
    validate(organization, ORGANIZATION_SCHEMA)

    if Organization.query.filter_by(name=organization["name"]).one_or_none():
        raise Conflict("Organization already exists")

    db_session.add(Organization(id=str(uuid.uuid4()), name=organization["name"]))
    db_session.commit()

    return jsonify(status="ok")


@api.route("/support/organizations/<organization_id>", methods=["GET"])
@restrict_access_support
def get_organization(organization_id: str):
    organization = get_or_404(Organization, organization_id)
    return jsonify(
        id=organization.id,
        name=organization.name,
        elections=[
            dict(
                id=election.id,
                auditName=election.audit_name,
                auditType=election.audit_type,
            )
            for election in organization.elections
        ],
        auditAdmins=sorted(
            [
                dict(email=admin.user.email)
                for admin in organization.audit_administrations
            ],
            key=lambda admin: str(admin["email"]),
        ),
    )


@api.route("/support/elections/<election_id>", methods=["GET"])
@restrict_access_support
def get_election(election_id: str):
    election = get_or_404(Election, election_id)
    return jsonify(
        id=election.id,
        auditName=election.audit_name,
        auditType=election.audit_type,
        jurisdictions=[
            dict(
                id=jurisdiction.id,
                name=jurisdiction.name,
                jurisdictionAdmins=sorted(
                    [
                        dict(email=admin.user.email)
                        for admin in jurisdiction.jurisdiction_administrations
                    ],
                    key=lambda admin: str(admin["email"]),
                ),
            )
            for jurisdiction in election.jurisdictions
        ],
    )


AUDIT_ADMIN_SCHEMA = {
    "type": "object",
    "properties": {"email": {"type": "string", "format": "email"}},
    "additionalProperties": False,
    "required": ["email"],
}


@api.route("/support/organizations/<organization_id>/audit-admins", methods=["POST"])
@restrict_access_support
def create_audit_admin(organization_id: str):
    get_or_404(Organization, organization_id)
    audit_admin = request.get_json()
    validate(audit_admin, AUDIT_ADMIN_SCHEMA)

    user = User.query.filter_by(email=audit_admin["email"]).one_or_none()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=audit_admin["email"],
            external_id=audit_admin["email"],
        )
        db_session.add(user)

    admin = AuditAdministration.query.filter_by(
        user_id=user.id, organization_id=organization_id
    ).one_or_none()
    if admin:
        raise Conflict("Audit admin already exists")
    admin = AuditAdministration(user_id=user.id, organization_id=organization_id)
    db_session.add(admin)

    auth0_user_id = auth0_create_audit_admin(audit_admin["email"])
    user.external_id = auth0_user_id

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/support/audit-admins/<email>/login", methods=["GET"],
)
@restrict_access_support
def log_in_as_audit_admin(email: str):
    set_loggedin_user(session, UserType.AUDIT_ADMIN, email, from_support_user=True)
    return redirect("/")


@api.route(
    "/support/jurisdiction-admins/<email>/login", methods=["GET"],
)
@restrict_access_support
def log_in_as_jurisdiction_admin(email: str):
    set_loggedin_user(
        session, UserType.JURISDICTION_ADMIN, email, from_support_user=True
    )
    return redirect("/")

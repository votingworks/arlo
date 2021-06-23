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
from ..util.isoformat import isoformat
from .rounds import get_current_round
from .batches import already_audited_batches

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
                online=election.online,
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
        online=election.online,
        jurisdictions=[
            dict(id=jurisdiction.id, name=jurisdiction.name,)
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


@api.route("/support/jurisdictions/<jurisdiction_id>", methods=["GET"])
@restrict_access_support
def get_jurisdiction(jurisdiction_id: str):
    jurisdiction = get_or_404(Jurisdiction, jurisdiction_id)
    round = get_current_round(jurisdiction.election)
    audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction.id, round_id=round and round.id
    )

    if jurisdiction.election.audit_type == AuditType.BATCH_COMPARISON:
        recorded_results_at = (
            BatchResult.query.join(Batch)
            .filter_by(jurisdiction_id=jurisdiction_id)
            .join(SampledBatchDraw)
            .filter_by(round_id=round and round.id)
            .limit(1)
            .value(BatchResult.created_at)
        )
    else:
        recorded_results_at = (
            JurisdictionResult.query.filter_by(
                jurisdiction_id=jurisdiction.id, round_id=round and round.id
            )
            .limit(1)
            .value(JurisdictionResult.created_at)
        )

    return jsonify(
        id=jurisdiction.id,
        name=jurisdiction.name,
        election=dict(
            id=jurisdiction.election.id,
            auditName=jurisdiction.election.audit_name,
            auditType=jurisdiction.election.audit_type,
            online=jurisdiction.election.online,
        ),
        jurisdictionAdmins=sorted(
            [
                dict(email=admin.user.email)
                for admin in jurisdiction.jurisdiction_administrations
            ],
            key=lambda admin: str(admin["email"]),
        ),
        auditBoards=[
            dict(
                id=audit_board.id,
                name=audit_board.name,
                signedOffAt=audit_board.signed_off_at,
            )
            for audit_board in audit_boards
        ],
        recordedResultsAt=isoformat(recorded_results_at),
    )


@api.route("/support/jurisdictions/<jurisdiction_id>/audit-boards", methods=["DELETE"])
@restrict_access_support
def clear_jurisdiction_audit_boards(jurisdiction_id: str):
    jurisdiction = get_or_404(Jurisdiction, jurisdiction_id)
    round = get_current_round(jurisdiction.election)
    audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction.id, round_id=round and round.id
    ).all()

    if len(audit_boards) == 0:
        raise Conflict("Jurisdiction has no audit boards")

    num_audited_ballots = (
        SampledBallot.query.join(AuditBoard)
        .filter(AuditBoard.id.in_([audit_board.id for audit_board in audit_boards]))
        .filter(SampledBallot.status != BallotStatus.NOT_AUDITED)
        .count()
    )
    if num_audited_ballots > 0:
        raise Conflict("Can't clear audit boards after ballots have been audited")

    AuditBoard.query.filter(
        AuditBoard.id.in_([audit_board.id for audit_board in audit_boards])
    ).delete(synchronize_session=False)
    db_session.commit()

    return jsonify(status="ok")


@api.route("/support/audit-boards/<audit_board_id>/sign-off", methods=["DELETE"])
@restrict_access_support
def reopen_audit_board(audit_board_id: str):
    audit_board = get_or_404(AuditBoard, audit_board_id)
    round = get_current_round(audit_board.jurisdiction.election)

    if not round or audit_board.round_id != round.id:
        raise Conflict("Audit board is not part of the current round.")
    if round.ended_at:
        raise Conflict("Can't reopen audit board after round ends.")
    if audit_board.signed_off_at is None:
        raise Conflict("Audit board has not signed off.")

    audit_board.signed_off_at = None
    db_session.commit()

    return jsonify(status="ok")


@api.route("/support/jurisdictions/<jurisdiction_id>/results", methods=["DELETE"])
@restrict_access_support
def clear_offline_results(jurisdiction_id: str):
    jurisdiction = get_or_404(Jurisdiction, jurisdiction_id)
    round = get_current_round(jurisdiction.election)

    if not round:
        raise Conflict("Audit has not started.")
    if round.ended_at:
        raise Conflict("Can't clear results after round ends.")

    if jurisdiction.election.audit_type == AuditType.BATCH_COMPARISON:
        num_deleted = (
            BatchResult.query.filter(
                BatchResult.batch_id.in_(
                    Batch.query.filter_by(jurisdiction_id=jurisdiction_id)
                    .join(SampledBatchDraw)
                    .filter_by(round_id=round.id)
                    .with_entities(Batch.id)
                    .subquery()
                )
            )
            .filter(Batch.id.notin_(already_audited_batches(jurisdiction, round)))
            .delete(synchronize_session=False)
        )
    else:
        num_deleted = JurisdictionResult.query.filter_by(
            jurisdiction_id=jurisdiction.id, round_id=round.id
        ).delete(synchronize_session=False)

    if num_deleted == 0:
        raise Conflict("Jurisdiction doesn't have any results recorded.")

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

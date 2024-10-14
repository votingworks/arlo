from datetime import datetime, timedelta
import uuid
import secrets
from typing import Optional
from urllib.parse import urlparse
from flask import jsonify, request, session
from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0
from auth0.v3.exceptions import Auth0Error
from werkzeug.exceptions import BadRequest, Conflict
from sqlalchemy.orm import contains_eager


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
from ..util.file import delete_file
from ..util.redirect import redirect
from .rounds import delete_round_and_corresponding_sampled_ballots, get_current_round
from ..util.get_json import safe_get_json_dict

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
        # pylint: disable=no-member
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
            # pylint: disable=no-member
            users = auth0.users_by_email.search_users_by_email(email.lower())
            return str(users[0]["user_id"])
        raise error  # pragma: no cover


@api.route("/support/elections/active", methods=["GET"])
@restrict_access_support
def list_active_elections():
    elections = (
        Election.query.filter(
            Election.id.in_(
                ActivityLogRecord.query.filter(
                    ActivityLogRecord.timestamp
                    > datetime.now(timezone.utc) - timedelta(days=14)
                )
                .with_entities(
                    ActivityLogRecord.info["base"]["election_id"].as_string()
                )
                .subquery()
            )
        )
        .join(Organization)
        .order_by(Organization.name, Election.audit_name)
        .options(
            contains_eager(Election.organization),
        )
    )
    return jsonify(
        [
            dict(
                id=election.id,
                auditName=election.audit_name,
                auditType=election.audit_type,
                online=election.online,
                deletedAt=isoformat(election.deleted_at),
                organization=dict(
                    id=election.organization.id, name=election.organization.name
                ),
            )
            for election in elections
        ]
    )


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
    "properties": {"name": {"type": "string", "minLength": 1}},
    "additionalProperties": False,
    "required": ["name"],
}


@api.route("/support/organizations", methods=["POST"])
@restrict_access_support
def create_organization():
    organization = safe_get_json_dict(request)
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
        defaultState=organization.default_state,
        elections=[
            dict(
                id=election.id,
                auditName=election.audit_name,
                auditType=election.audit_type,
                online=election.online,
                deletedAt=isoformat(election.deleted_at),
            )
            for election in organization.elections
        ],
        auditAdmins=sorted(
            [
                dict(id=admin.user.id, email=admin.user.email)
                for admin in organization.audit_administrations
            ],
            key=lambda admin: str(admin["email"]),
        ),
    )


@api.route("/support/organizations/<organization_id>", methods=["DELETE"])
@restrict_access_support
def delete_organization(organization_id: str):
    organization = get_or_404(Organization, organization_id)
    if any(election for election in organization.elections if not election.deleted_at):
        raise Conflict(
            "Cannot delete an org with audits."
            " If you really want to delete this org, first delete all of its audits."
        )

    db_session.delete(organization)
    db_session.commit()
    return jsonify(status="ok")


@api.route("/support/organizations/<organization_id>", methods=["PATCH"])
@restrict_access_support
def update_organization(organization_id: str):
    organization = get_or_404(Organization, organization_id)
    body = safe_get_json_dict(request)
    validate(
        body,
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "defaultState": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            },
            "required": ["name", "defaultState"],
            "additionalProperties": False,
        },
    )
    organization.name = body["name"]
    organization.default_state = body["defaultState"]
    db_session.commit()
    return jsonify(status="ok")


@api.route("/support/elections/<election_id>", methods=["GET"])
@restrict_access_support
def get_election(election_id: str):
    election = get_or_404(Election, election_id)
    return jsonify(
        id=election.id,
        auditName=election.audit_name,
        auditType=election.audit_type,
        online=election.online,
        organization=dict(id=election.organization.id, name=election.organization.name),
        jurisdictions=[
            dict(id=jurisdiction.id, name=jurisdiction.name)
            for jurisdiction in election.jurisdictions
        ],
        rounds=[
            dict(id=round.id, endedAt=round.ended_at, roundNum=round.round_num)
            for round in election.rounds
        ],
        deletedAt=isoformat(election.deleted_at),
    )


@api.route("/support/elections/<election_id>", methods=["DELETE"])
@restrict_access_support
def permanently_delete_election(election_id: str):
    election = get_or_404(Election, election_id)

    election_file_ids = [
        election.jurisdictions_file_id,
        election.standardized_contests_file_id,
    ]
    jurisdiction_file_ids = [
        file_id
        for jurisdiction in election.jurisdictions
        for file_id in [
            jurisdiction.manifest_file_id,
            jurisdiction.cvr_file_id,
            jurisdiction.batch_tallies_file_id,
        ]
    ]
    all_file_ids = [
        file_id for file_id in election_file_ids + jurisdiction_file_ids if file_id
    ]
    file_paths = File.query.filter(File.id.in_(all_file_ids)).values(File.storage_path)
    for (file_path,) in file_paths:
        delete_file(file_path)

    db_session.delete(election)
    db_session.commit()
    return jsonify(status="ok")


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
    audit_admin = safe_get_json_dict(request)
    validate(audit_admin, AUDIT_ADMIN_SCHEMA)

    user = User.query.filter_by(email=audit_admin["email"].lower()).one_or_none()
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
    "/support/organizations/<organization_id>/audit-admins/<audit_admin_id>",
    methods=["DELETE"],
)
@restrict_access_support
def remove_audit_admin_from_org(organization_id: str, audit_admin_id: str):
    organization = get_or_404(Organization, organization_id)
    user = get_or_404(User, audit_admin_id)
    if not any(
        organization.id == organization_id for organization in user.organizations
    ):
        raise BadRequest("This user is not an audit admin for this organization")

    user.organizations = [
        organization
        for organization in user.organizations
        if organization.id != organization_id
    ]
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
            BatchResultTallySheet.query.join(Batch)
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
        organization=dict(
            id=jurisdiction.election.organization.id,
            name=jurisdiction.election.organization.name,
        ),
        election=dict(
            id=jurisdiction.election.id,
            auditName=jurisdiction.election.audit_name,
            auditType=jurisdiction.election.audit_type,
            online=jurisdiction.election.online,
            deletedAt=isoformat(jurisdiction.election.deleted_at),
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


@api.route("/support/jurisdictions/<jurisdiction_id>/results", methods=["DELETE"])
@restrict_access_support
def clear_offline_results(jurisdiction_id: str):
    jurisdiction = get_or_404(Jurisdiction, jurisdiction_id)
    round = get_current_round(jurisdiction.election)

    if (
        jurisdiction.election.audit_type != AuditType.BALLOT_POLLING
        or jurisdiction.election.online
    ):
        raise Conflict("Can only clear results for offline ballot polling audits.")
    if not round:
        raise Conflict("Audit has not started.")
    if round.ended_at:
        raise Conflict("Can't clear results after round ends.")

    num_deleted = JurisdictionResult.query.filter_by(
        jurisdiction_id=jurisdiction.id, round_id=round.id
    ).delete(synchronize_session=False)

    if num_deleted == 0:
        raise Conflict("Jurisdiction doesn't have any results recorded.")

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/support/audit-admins/<email>/login",
    methods=["GET"],
)
@restrict_access_support
def log_in_as_audit_admin(email: str):
    set_loggedin_user(session, UserType.AUDIT_ADMIN, email, from_support_user=True)
    return redirect("/")


@api.route(
    "/support/jurisdiction-admins/<email>/login",
    methods=["GET"],
)
@restrict_access_support
def log_in_as_jurisdiction_admin(email: str):
    set_loggedin_user(
        session, UserType.JURISDICTION_ADMIN, email, from_support_user=True
    )
    return redirect("/")


@api.route(
    "/support/elections/<election_id>/login",
    methods=["GET"],
)
@restrict_access_support
def log_in_to_audit_as_audit_admin(election_id: str):
    election = get_or_404(Election, election_id)
    audit_admins = [
        audit_administration.user
        for audit_administration in election.organization.audit_administrations
    ]
    assert len(audit_admins) > 0
    set_loggedin_user(
        session, UserType.AUDIT_ADMIN, audit_admins[0].email, from_support_user=True
    )
    return redirect(f"/election/{election_id}")


@api.route("/support/jurisdictions/<jurisdiction_id>/login", methods=["GET"])
@restrict_access_support
def log_in_to_audit_as_jurisdiction_admin(jurisdiction_id: str):
    jurisdiction = get_or_404(Jurisdiction, jurisdiction_id)
    jurisdiction_admins = [
        jurisdiction_administration.user
        for jurisdiction_administration in jurisdiction.jurisdiction_administrations
    ]
    assert len(jurisdiction_admins) > 0
    set_loggedin_user(
        session,
        UserType.JURISDICTION_ADMIN,
        jurisdiction_admins[0].email,
        from_support_user=True,
    )
    return redirect(
        f"/election/{jurisdiction.election_id}/jurisdiction/{jurisdiction_id}"
    )


@api.route("/support/rounds/<round_id>", methods=["DELETE"])
@restrict_access_support
def support_undo_round_start(round_id: str):
    round = get_or_404(Round, round_id)
    election = get_or_404(Election, round.election_id)
    current_round = get_current_round(election)

    if not current_round or round.id != current_round.id:
        raise Conflict(
            "Cannot undo starting this round because it is not the current round."
        )
    if len(list(round.audit_boards)) > 0:
        raise Conflict(
            "Cannot undo starting this round because some jurisdictions have already created audit boards."
        )

    delete_round_and_corresponding_sampled_ballots(round)

    return jsonify(status="ok")


@api.route("/support/elections/<election_id>/reopen-current-round", methods=["PATCH"])
@restrict_access_support
def reopen_current_round(election_id: str):
    election = get_or_404(Election, election_id)
    current_round = get_current_round(election)

    if not current_round:
        raise Conflict("Audit hasn't started yet.")
    if not current_round.ended_at:
        raise Conflict("Round is in progress.")

    current_round.ended_at = None
    for round_contest in current_round.round_contests:
        round_contest.end_p_value = None
        round_contest.is_complete = None
        round_contest.results = []
    db_session.commit()

    return jsonify(status="ok")

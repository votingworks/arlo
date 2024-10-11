import uuid
from datetime import datetime, timezone
from flask import jsonify, request, session
from werkzeug.exceptions import Conflict, Forbidden

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..database import db_session
from ..auth import (
    check_access,
    UserType,
    restrict_access,
    get_loggedin_user,
    allow_public_access,
)
from ..util.jsonschema import JSONDict, validate
from ..activity_log import (
    CreateAudit,
    DeleteAudit,
    activity_base,
    record_activity,
)
from ..util.get_json import safe_get_json_dict

ELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "auditName": {"type": "string"},
        "auditType": {
            "type": "string",
            "enum": [audit_type.value for audit_type in AuditType],
        },
        "auditMathType": {
            "type": "string",
            "enum": [audit_math_type.value for audit_math_type in AuditMathType],
        },
        "organizationId": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    },
    "required": ["organizationId", "auditName", "auditType"],
    "additionalProperties": False,
}


def validate_new_election(election: JSONDict):
    validate(election, ELECTION_SCHEMA)

    if Election.query.filter_by(
        audit_name=election["auditName"], organization_id=election["organizationId"]
    ).first():
        raise Conflict(
            f"An audit with name '{election['auditName']}' already exists within your organization"
        )

    valid_math_types_for_audit_type = {
        AuditType.BALLOT_POLLING: [
            AuditMathType.BRAVO,
            AuditMathType.MINERVA,
            AuditMathType.PROVIDENCE,
        ],
        AuditType.BALLOT_COMPARISON: [AuditMathType.SUPERSIMPLE],
        AuditType.BATCH_COMPARISON: [AuditMathType.MACRO],
        AuditType.HYBRID: [AuditMathType.SUITE],
    }

    if (
        election["auditMathType"]
        not in valid_math_types_for_audit_type[election["auditType"]]
    ):
        raise Conflict(
            f"Audit math type '{election['auditMathType']}' cannot be used with audit type '{election['auditType']}'"
        )


@api.route("/election", methods=["POST"])
@allow_public_access  # Access control is implemented within the endpoint
def create_election():
    election = safe_get_json_dict(request)

    validate_new_election(election)

    online = {
        AuditType.BALLOT_POLLING: True,
        AuditType.BATCH_COMPARISON: False,
        AuditType.BALLOT_COMPARISON: True,
        AuditType.HYBRID: True,
    }[election["auditType"]]

    organization = get_or_404(Organization, election["organizationId"])

    election = Election(
        id=str(uuid.uuid4()),
        audit_name=election["auditName"],
        audit_type=election["auditType"],
        audit_math_type=election["auditMathType"],
        organization_id=election["organizationId"],
        online=online,
        state=organization.default_state,
    )

    check_access([UserType.AUDIT_ADMIN], election)

    db_session.add(election)

    db_session.flush()  # Ensure we can read election.organization in activity_base
    record_activity(
        CreateAudit(timestamp=election.created_at, base=activity_base(election))
    )

    db_session.commit()

    return jsonify(electionId=election.id)


@api.route("/election/<election_id>", methods=["DELETE"])
@restrict_access([UserType.AUDIT_ADMIN])
def delete_election(election: Election):
    election.deleted_at = datetime.now(timezone.utc)

    record_activity(
        DeleteAudit(timestamp=election.deleted_at, base=activity_base(election))
    )

    db_session.commit()
    return jsonify(status="ok")


@api.route("/audit_admins/<audit_admin_id>/organizations", methods=["GET"])
@allow_public_access  # Access control is implemented within the endpoint
def list_organizations_and_elections(audit_admin_id: str):
    user_type, user_key = get_loggedin_user(session)
    user = User.query.get(audit_admin_id)
    if user is None or user.email != user_key or user_type != UserType.AUDIT_ADMIN:
        raise Forbidden()

    return jsonify(
        [
            {
                "id": org.id,
                "name": org.name,
                "elections": [
                    {
                        "id": election.id,
                        "auditName": election.audit_name,
                        "electionName": election.election_name,
                        "state": election.state,
                    }
                    for election in org.elections
                    if election.deleted_at is None
                ],
            }
            for org in user.organizations
        ]
    )

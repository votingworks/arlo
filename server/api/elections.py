import uuid
from flask import jsonify, request
from werkzeug.exceptions import Conflict

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..database import db_session
from ..auth import check_access, UserType
from ..util.jsonschema import JSONDict, validate

ELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "auditName": {"type": "string"},
        "auditType": {
            "type": "string",
            "enum": [audit_type.value for audit_type in AuditType],
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


@api.route("/election", methods=["POST"])
def create_election():
    election = request.get_json()

    validate_new_election(election)

    online = {
        AuditType.BALLOT_POLLING: False,
        AuditType.BATCH_COMPARISON: False,
        AuditType.BALLOT_COMPARISON: True,
    }[election["auditType"]]

    election = Election(
        id=str(uuid.uuid4()),
        audit_name=election["auditName"],
        audit_type=election["auditType"],
        organization_id=election["organizationId"],
        online=online,
    )

    check_access([UserType.AUDIT_ADMIN], election)

    db_session.add(election)

    db_session.commit()

    return jsonify(electionId=election.id)

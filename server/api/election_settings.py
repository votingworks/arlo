from flask import jsonify, request
from werkzeug.exceptions import Conflict

from . import api
from ..auth import restrict_access, UserType
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..util.jsonschema import validate, JSONDict
from ..util.get_json import safe_get_json_dict


ELECTION_SETTINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "electionName": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "online": {"type": "boolean"},
        "randomSeed": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "riskLimit": {
            "anyOf": [
                {"type": "integer", "minimum": 1, "maximum": 20},
                {"type": "null"},
            ]
        },
        "state": {
            "anyOf": [
                {"type": "string", "enum": [state.value for state in USState]},
                {"type": "null"},
            ]
        },
        # We accept auditType and auditName on PUT only because we return them
        # on GET, so this makes it simpler for the frontend. We don't actually
        # update the auditType/auditName in this endpoint - they get set on
        # audit creation only.
        "auditType": {"type": "string"},
        "auditMathType": {"type": "string"},
        "auditName": {"type": "string"},
    },
    "additionalProperties": False,
    "required": ["electionName", "online", "randomSeed", "riskLimit", "state"],
}


def serialize_election_settings(election: Election) -> JSONDict:
    return {
        "electionName": election.election_name,
        "online": election.online,
        "randomSeed": election.random_seed,
        "riskLimit": election.risk_limit,
        "state": election.state,
        "auditType": election.audit_type,
        "auditMathType": election.audit_math_type,
        "auditName": election.audit_name,
    }


@api.route("/election/<election_id>/settings", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_election_settings(election: Election):
    return jsonify(serialize_election_settings(election))


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/settings", methods=["GET"]
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_jurisdiction_election_settings(
    election: Election,
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    return jsonify(serialize_election_settings(election))


def validate_election_settings(settings: JSONDict, election: Election):
    if len(list(election.rounds)) > 0:
        raise Conflict("Cannot update settings after audit has started.")

    validate(settings, ELECTION_SETTINGS_SCHEMA)


@api.route("/election/<election_id>/settings", methods=["PUT"])
@restrict_access([UserType.AUDIT_ADMIN])
def put_election_settings(election: Election):
    settings = safe_get_json_dict(request)
    validate_election_settings(settings, election)

    election.election_name = settings["electionName"]
    election.online = settings["online"]
    election.random_seed = settings["randomSeed"]
    election.risk_limit = settings["riskLimit"]
    election.state = settings["state"]

    db_session.add(election)
    db_session.commit()

    return jsonify(status="ok")

from flask import jsonify, request
from werkzeug.exceptions import Conflict

from . import api
from ..auth import with_election_access, with_jurisdiction_access
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..util.jsonschema import validate, JSONDict


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
    }


@api.route("/election/<election_id>/settings", methods=["GET"])
@with_election_access
def get_election_settings(election: Election):
    return jsonify(serialize_election_settings(election))


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/settings", methods=["GET"]
)
@with_jurisdiction_access
def get_jurisdiction_election_settings(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    return jsonify(serialize_election_settings(election))


def validate_election_settings(settings: JSONDict, election: Election):
    if len(list(election.rounds)) > 0:
        raise Conflict("Cannot update settings after audit has started.")

    validate(settings, ELECTION_SETTINGS_SCHEMA)


@api.route("/election/<election_id>/settings", methods=["PUT"])
@with_election_access
def put_election_settings(election: Election):
    settings = request.get_json()
    validate_election_settings(settings, election)

    election.election_name = settings["electionName"]
    election.online = settings["online"]
    election.random_seed = settings["randomSeed"]
    election.risk_limit = settings["riskLimit"]
    election.state = settings["state"]

    db_session.add(election)
    db_session.commit()

    return jsonify(status="ok")

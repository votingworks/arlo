from flask import jsonify, request
from jsonschema import validate

from arlo_server import app, db
from arlo_server.auth import require_audit_admin_for_organization
from arlo_server.models import Election, USState

from util.jsonschema import nullable, Enum, Obj, Str, Bool, Int, IntRange

GET_ELECTION_SETTINGS_RESPONSE_SCHEMA = Obj(
    electionName=nullable(Str),
    online=Bool,
    randomSeed=nullable(Str),
    riskLimit=nullable(IntRange(1, 20)),
    state=nullable(Enum([state.value for state in USState])),
)


PUT_ELECTION_SETTINGS_REQUEST_SCHEMA = GET_ELECTION_SETTINGS_RESPONSE_SCHEMA


@app.route("/election/<election_id>/settings", methods=["GET"])
def get_election_settings(election_id: str):
    election = Election.query.get_or_404(election_id)
    require_audit_admin_for_organization(election.organization_id)

    response_data = {
        "electionName": election.election_name,
        "online": election.online,
        "randomSeed": election.random_seed,
        "riskLimit": election.risk_limit,
        "state": election.state,
    }

    validate(schema=GET_ELECTION_SETTINGS_RESPONSE_SCHEMA, instance=response_data)

    return jsonify(response_data)


@app.route("/election/<election_id>/settings", methods=["PUT"])
def put_election_settings(election_id: str):
    election = Election.query.get_or_404(election_id)
    require_audit_admin_for_organization(election.organization_id)

    settings = request.get_json()
    validate(schema=PUT_ELECTION_SETTINGS_REQUEST_SCHEMA, instance=settings)

    election.election_name = settings["electionName"]
    election.online = settings["online"]
    election.random_seed = settings["randomSeed"]
    election.risk_limit = settings["riskLimit"]
    election.state = settings["state"]

    db.session.add(election)
    db.session.commit()

    return jsonify(status="ok")

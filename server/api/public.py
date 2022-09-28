from flask import jsonify, request

from . import api
from ..util.jsonschema import validate
from ..models import *  # pylint: disable=wildcard-import


ELECTION_RESULTS_CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "votes": {"type": "integer", "minimum": 0},
    },
    "additionalProperties": False,
    "required": ["name", "votes"],
}

ELECTION_RESULTS_SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": ELECTION_RESULTS_CANDIDATE_SCHEMA,
            "minItems": 2,
        },
        "numWinners": {"type": "integer", "minimum": 1},
        "totalBallotsCast": {"type": "integer", "minimum": 1},
    },
    "additionalProperties": False,
    "required": ["candidates", "numWinners", "totalBallotsCast"],
}

COMPUTE_SAMPLE_SIZES_INPUT_SCHEMA = {
    "type": "object",
    "properties": {"electionResults": ELECTION_RESULTS_SCHEMA},
    "additionalProperties": False,
    "required": ["electionResults"],
}


# Conceptually, this is a GET but we use a POST so that we can specify election results in a body.
# Specifying election results in a query param could cause us to hit URL size limits
@api.route("/public/sample-sizes", methods=["POST"])
def public_compute_sample_sizes():
    compute_sample_sizes_input = request.get_json()
    validate(compute_sample_sizes_input, COMPUTE_SAMPLE_SIZES_INPUT_SCHEMA)
    sample_sizes = {
        "ballotComparison": {},
        "ballotPolling": {},
        "batchComparison": {},
    }
    for risk_limit_percentage in list(range(0, 21)):
        sample_sizes["ballotComparison"][str(risk_limit_percentage)] = 0
        sample_sizes["ballotPolling"][str(risk_limit_percentage)] = 0
        sample_sizes["batchComparison"][str(risk_limit_percentage)] = 0
    return jsonify(sample_sizes)

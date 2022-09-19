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
    "properties": {
        "electionResults": ELECTION_RESULTS_SCHEMA,
        "riskLimitPercentage": {"type": "integer", "minimum": 0, "maximum": 20},
    },
    "additionalProperties": False,
    "required": ["electionResults", "riskLimitPercentage"],
}


@api.route("/public/sample-sizes", methods=["POST"])
def public_compute_sample_sizes():
    compute_sample_sizes_input = request.get_json()
    validate(compute_sample_sizes_input, COMPUTE_SAMPLE_SIZES_INPUT_SCHEMA)
    return jsonify(dict(ballotComparison=0, ballotPolling=0, batchComparison=0))

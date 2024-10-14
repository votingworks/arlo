import math
from typing import Any

from werkzeug.exceptions import Conflict
from flask import jsonify, request


from . import api
from ..auth.auth_helpers import allow_public_access
from ..audit_math import bravo, sampler_contest, supersimple
from ..util.jsonschema import validate
from ..models import *  # pylint: disable=wildcard-import
from ..util.get_json import safe_get_json_dict


# Leave enough buffer to support an election of galactic scale while making it hard for users to
# crash the sample size math by holding down the 0 key :D
# Keep this in sync with the client-side limit in client/src/components/PublicPages/AuditPlanner/
MAX_NUMERICAL_VALUE = 1e15

ELECTION_RESULTS_CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "votes": {"type": "integer", "minimum": 0, "maximum": MAX_NUMERICAL_VALUE},
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
        "numWinners": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_NUMERICAL_VALUE,
        },
        "totalBallotsCast": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_NUMERICAL_VALUE,
        },
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
@allow_public_access
def public_compute_sample_sizes():
    contest_for_sampler = parse_compute_sample_sizes_input(safe_get_json_dict(request))

    audit_types = ["ballotComparison", "ballotPolling", "batchComparison"]
    sample_sizes = {audit_type: {} for audit_type in audit_types}
    sample_size_functions = {
        "ballotComparison": compute_ballot_comparison_sample_size,
        "ballotPolling": compute_ballot_polling_sample_size,
        "batchComparison": compute_batch_comparison_sample_size,
    }
    for audit_type in audit_types:
        for risk_limit_percentage in list(range(0, 21)):
            sample_size_function = sample_size_functions[audit_type]
            sample_sizes[audit_type][str(risk_limit_percentage)] = sample_size_function(
                contest_for_sampler, risk_limit_percentage
            )

    return jsonify(sample_sizes)


def parse_compute_sample_sizes_input(
    compute_sample_sizes_input: Any,
) -> sampler_contest.Contest:
    validate(compute_sample_sizes_input, COMPUTE_SAMPLE_SIZES_INPUT_SCHEMA)

    election_results = compute_sample_sizes_input["electionResults"]
    candidates = election_results["candidates"]
    num_winners = election_results["numWinners"]
    total_ballots_cast = election_results["totalBallotsCast"]

    if len(set(candidate["name"] for candidate in candidates)) < len(candidates):
        raise Conflict("Candidates must have unique names")

    if all(candidate["votes"] == 0 for candidate in candidates):
        raise Conflict("At least 1 candidate must have greater than 0 votes")

    if num_winners >= len(candidates):
        raise Conflict("Number of winners must be less than number of candidates")

    contest = Contest(
        choices=[
            ContestChoice(id=candidate["name"], num_votes=candidate["votes"])
            for candidate in candidates
        ],
        num_winners=num_winners,
        total_ballots_cast=total_ballots_cast,
        votes_allowed=num_winners,
    )
    contest_for_sampler: sampler_contest.Contest = sampler_contest.from_db_contest(
        contest
    )
    return contest_for_sampler


def compute_ballot_comparison_sample_size(
    contest: sampler_contest.Contest, risk_limit_percentage: int
) -> int:
    sample_size = supersimple.get_sample_sizes(risk_limit_percentage, contest, None)
    return min(sample_size, contest.ballots)


def compute_ballot_polling_sample_size(
    contest: sampler_contest.Contest, risk_limit_percentage: int
) -> int:
    sample_size_options = bravo.get_sample_size(
        risk_limit_percentage, contest, None, None
    )
    sample_size: int = sample_size_options.get(
        "0.9",
        sample_size_options.get(
            "all-ballots", sample_size_options.get("asn", {"size": contest.ballots})
        ),
    )["size"]
    return min(sample_size, contest.ballots)


def compute_batch_comparison_sample_size(
    contest: sampler_contest.Contest, risk_limit_percentage: int
) -> int:
    is_tie = contest.diluted_margin == 0
    if is_tie or risk_limit_percentage == 0:
        return contest.ballots

    sample_size = int(
        math.ceil(-1 * math.log(risk_limit_percentage / 100) / contest.diluted_margin)
        + 2
    )
    return min(sample_size, contest.ballots)

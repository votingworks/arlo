from flask import jsonify
from collections import defaultdict
from werkzeug.exceptions import BadRequest
from typing import Dict

from arlo_server import app
from arlo_server.models import Election
from arlo_server.auth import with_election_access, UserType
from audit_math import bravo, sampler_contest


def sample_size_options(election: Election) -> dict:
    if not election.contests:
        raise BadRequest("Cannot compute sample sizes until contests are set")
    if not election.risk_limit:
        raise BadRequest("Cannot compute sample sizes until risk limit is set")

    # For now, we only support one targeted contest
    contest = next(c for c in election.contests if c.is_targeted)

    # Sum the audit results from previous rounds
    results_by_choice: Dict[str, int] = defaultdict(int)
    for result in contest.results:
        results_by_choice[result.contest_choice_id] += result.result
    results_so_far = {contest.id: results_by_choice}

    # Do the math!
    sample_sizes: dict = bravo.get_sample_size(
        election.risk_limit / 100,
        sampler_contest.from_db_contest(contest),
        results_so_far,
    )
    return sample_sizes


@app.route("/election/<election_id>/sample-sizes", methods=["GET"])
@with_election_access(UserType.AUDIT_ADMIN)
def get_sample_sizes(election: Election):
    sample_sizes = sample_size_options(election)

    # Convert the results into a slightly more regular format
    json_sizes = list(sample_sizes.values())

    return jsonify({"sampleSizes": json_sizes})

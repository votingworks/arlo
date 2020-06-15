from collections import defaultdict
from typing import Dict
from flask import jsonify
from werkzeug.exceptions import BadRequest

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..auth import with_election_access
from ..audit_math import bravo, sampler_contest


# Sum the audit results for each contest choice from all rounds so far
def cumulative_contest_results(contest: Contest) -> Dict[str, int]:
    results_by_choice: Dict[str, int] = defaultdict(int)
    for result in contest.results:
        results_by_choice[result.contest_choice_id] += result.result
    return results_by_choice


def sample_size_options(election: Election, round_one=False) -> dict:
    if not election.contests:
        raise BadRequest("Cannot compute sample sizes until contests are set")
    if not election.risk_limit:
        raise BadRequest("Cannot compute sample sizes until risk limit is set")

    # For now, we only support one targeted contest
    contest = next(c for c in election.contests if c.is_targeted)

    # Because the /sample-sizes endpoint is only used for the audit setup flow,
    # we always want it to return the sample size options for the first round.
    # So we support a flag in this function to compute the sample sizes for
    # round one specifically, even if the audit has progressed further.
    cumulative_results = (
        {choice.id: 0 for choice in contest.choices}
        if round_one
        else cumulative_contest_results(contest)
    )

    sample_sizes: dict = bravo.get_sample_size(
        election.risk_limit / 100,
        sampler_contest.from_db_contest(contest),
        cumulative_results,
    )
    return sample_sizes


@api.route("/election/<election_id>/sample-sizes", methods=["GET"])
@with_election_access
def get_sample_sizes(election: Election):
    sample_sizes = sample_size_options(election, round_one=True)

    # Convert the results into a slightly more regular format
    json_sizes = list(sample_sizes.values())

    return jsonify({"sampleSizes": json_sizes})

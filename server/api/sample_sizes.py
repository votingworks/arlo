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
    risk_limit: int = election.risk_limit  # Need this to pass typechecking

    def sample_sizes_for_contest(contest: Contest) -> dict:
        # Because the /sample-sizes endpoint is only used for the audit setup flow,
        # we always want it to return the sample size options for the first round.
        # So we support a flag in this function to compute the sample sizes for
        # round one specifically, even if the audit has progressed further.
        cumulative_results = (
            {choice.id: 0 for choice in contest.choices}
            if round_one
            else cumulative_contest_results(contest)
        )

        return bravo.get_sample_size(
            float(risk_limit) / 100,
            sampler_contest.from_db_contest(contest),
            cumulative_results,
        )

    targeted_contests = Contest.query.filter_by(
        election_id=election.id, is_targeted=True
    )
    targeted_contests_that_havent_met_risk_limit = (
        targeted_contests.all()
        if round_one
        else targeted_contests.join(RoundContest).filter_by(is_complete=False).all()
    )
    samples_sizes_for_targeted_contests = [
        sample_sizes_for_contest(contest)
        for contest in targeted_contests_that_havent_met_risk_limit
    ]
    # Choose the sample size options for the targted contest with the largest
    # sample size, since that will cover the samples needed by the other
    # targeted contests.
    # TODO update this for independently targeted contests
    return max(
        samples_sizes_for_targeted_contests,
        key=lambda sample_sizes: sample_sizes["asn"]["size"],
    )


@api.route("/election/<election_id>/sample-sizes", methods=["GET"])
@with_election_access
def get_sample_sizes(election: Election):
    sample_sizes = sample_size_options(election, round_one=True)
    json_sizes = list(sample_sizes.values())
    return jsonify({"sampleSizes": json_sizes})

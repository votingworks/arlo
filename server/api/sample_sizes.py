from collections import defaultdict
from typing import Dict
from flask import jsonify
from werkzeug.exceptions import BadRequest

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..auth import with_election_access
from ..audit_math import bravo, macro, sampler_contest


# Sum the audit results for each contest choice from all rounds so far
def cumulative_contest_results(contest: Contest) -> Dict[str, int]:
    results_by_choice: Dict[str, int] = defaultdict(int)
    for result in contest.results:
        results_by_choice[result.contest_choice_id] += result.result
    return results_by_choice


# Because the /sample-sizes endpoint is only used for the audit setup flow,
# we always want it to return the sample size options for the first round.
# So we support a flag in this function to compute the sample sizes for
# round one specifically, even if the audit has progressed further.
def sample_size_options(
    election: Election, round_one=False
) -> Dict[str, Dict[str, bravo.SampleSizeOption]]:
    if not election.contests:
        raise BadRequest("Cannot compute sample sizes until contests are set")
    if not election.risk_limit:
        raise BadRequest("Cannot compute sample sizes until risk limit is set")
    risk_limit: int = election.risk_limit  # Need this to pass typechecking

    def sample_sizes_for_contest(contest: Contest):
        if election.audit_type == AuditType.BALLOT_POLLING:
            cumulative_results = (
                {choice.id: 0 for choice in contest.choices}
                if round_one
                else cumulative_contest_results(contest)
            )

            sample_size_options = bravo.get_sample_size(
                float(risk_limit) / 100,
                sampler_contest.from_db_contest(contest),
                cumulative_results,
            )
            # Remove unnecessary "type" field from options, add "key" field
            return {
                key: {"key": key, "size": option["size"], "prob": option["prob"]}
                for key, option in sample_size_options.items()
            }

        else:
            batch_tallies = {
                # Key each batch by jurisdiction name and batch name since batch names
                # are only guaranteed unique within a jurisdiction
                (jurisdiction.name, batch_name): tally
                for jurisdiction in election.jurisdictions
                if jurisdiction.batch_tallies
                for batch_name, tally in jurisdiction.batch_tallies.items()  # type: ignore
            }
            sample_size = macro.get_sample_sizes(
                float(risk_limit) / 100,
                sampler_contest.from_db_contest(contest),
                batch_tallies,
                {},  # The cumulative results so far isn't used currently
            )
            # TODO macro should return a probability
            return {"macro": {"key": "macro", "size": sample_size, "prob": None}}

    targeted_contests = Contest.query.filter_by(
        election_id=election.id, is_targeted=True
    )
    targeted_contests_that_havent_met_risk_limit = (
        targeted_contests.all()
        if round_one
        else targeted_contests.join(RoundContest).filter_by(is_complete=False).all()
    )
    return {
        contest.id: sample_sizes_for_contest(contest)
        for contest in targeted_contests_that_havent_met_risk_limit
    }


@api.route("/election/<election_id>/sample-sizes", methods=["GET"])
@with_election_access
def get_sample_sizes(election: Election):
    sample_sizes = {
        contest_id: list(options.values())
        for contest_id, options in sample_size_options(election, round_one=True).items()
    }
    return jsonify({"sampleSizes": sample_sizes})

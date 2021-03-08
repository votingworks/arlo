from typing import Dict
from collections import Counter
from flask import jsonify
from werkzeug.exceptions import BadRequest, Conflict

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType
from ..audit_math import ballot_polling, macro, supersimple, sampler_contest
from . import rounds  # pylint: disable=cyclic-import
from .cvrs import all_cvrs_uploaded


# Because the /sample-sizes endpoint is only used for the audit setup flow,
# we always want it to return the sample size options for the first round.
# So we support a flag in this function to compute the sample sizes for
# round one specifically, even if the audit has progressed further.
def sample_size_options(
    election: Election, round_one=False
) -> Dict[str, Dict[str, ballot_polling.SampleSizeOption]]:
    if not election.contests:
        raise BadRequest("Cannot compute sample sizes until contests are set")
    if election.risk_limit is None:
        raise BadRequest("Cannot compute sample sizes until risk limit is set")

    def sample_sizes_for_contest(contest: Contest):
        assert election.risk_limit is not None
        if election.audit_type == AuditType.BALLOT_POLLING:
            sample_results = (
                None if round_one else rounds.contest_results_by_round(contest)
            )
            sample_size_options = ballot_polling.get_sample_size(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                sample_results,
                AuditMathType(election.audit_math_type),
                rounds.round_sizes(election),
            )
            # Remove unnecessary "type" field from options, add "key" field
            return {
                key: {"key": key, "size": option["size"], "prob": option["prob"]}
                for key, option in sample_size_options.items()
            }

        elif election.audit_type == AuditType.BATCH_COMPARISON:
            cumulative_batch_results = rounds.cumulative_batch_results(election)
            if round_one:
                cumulative_batch_results = {
                    batch_key: {
                        contest_id: {choice_id: 0 for choice_id in contest_results}
                        for contest_id, contest_results in batch_results.items()
                    }
                    for batch_key, batch_results in cumulative_batch_results.items()
                }
            sample_size = macro.get_sample_sizes(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                rounds.batch_tallies(election),
                cumulative_batch_results,
            )
            return {"macro": {"key": "macro", "size": sample_size, "prob": None}}

        elif election.audit_type == AuditType.BALLOT_COMPARISON:
            if not all_cvrs_uploaded(contest):
                raise Conflict("Some jurisdictions haven't uploaded their CVRs yet.")

            contest_for_sampler = sampler_contest.from_db_contest(contest)

            if round_one:
                discrepancy_counts = None
            else:
                num_previous_samples = (
                    SampledBallotDraw.query.join(Round)
                    .filter_by(election_id=election.id)
                    .count()
                )
                discrepancies = supersimple.compute_discrepancies(
                    contest_for_sampler,
                    rounds.cvrs_for_contest(contest),
                    rounds.sampled_ballot_interpretations_to_cvrs(contest),
                )
                discrepancy_counter = Counter(
                    d["counted_as"] for d in discrepancies.values()
                )
                discrepancy_counts = {
                    "sample_size": num_previous_samples,
                    "1-under": discrepancy_counter[-1],
                    "1-over": discrepancy_counter[1],
                    "2-under": discrepancy_counter[-2],
                    "2-over": discrepancy_counter[2],
                }

            sample_size = supersimple.get_sample_sizes(
                election.risk_limit, contest_for_sampler, discrepancy_counts
            )
            return {
                "supersimple": {"key": "supersimple", "size": sample_size, "prob": None}
            }

        else:
            assert election.audit_type == AuditType.HYBRID
            return {}

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
@restrict_access([UserType.AUDIT_ADMIN])
def get_sample_sizes(election: Election):
    sample_sizes = {
        contest_id: list(options.values())
        for contest_id, options in sample_size_options(election, round_one=True).items()
    }
    # If we've already started the first round, return which sample size was
    # selected for each contest so we can show the user
    selected_sample_sizes = dict(
        RoundContest.query.join(Round)
        .filter_by(election_id=election.id, round_num=1)
        .values(RoundContest.contest_id, RoundContest.sample_size)
    )
    return jsonify({"sampleSizes": sample_sizes, "selected": selected_sample_sizes})

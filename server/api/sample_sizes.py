from typing import Dict
from flask import jsonify
from werkzeug.exceptions import BadRequest

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType
from ..audit_math import bravo, macro, supersimple, sampler_contest
from . import rounds  # pylint: disable=cyclic-import
from .cvrs import set_contest_metadata_from_cvrs
from ..util.group_by import group_by


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
    risk_limit = float(election.risk_limit) / 100

    def sample_sizes_for_contest(contest: Contest):
        if election.audit_type == AuditType.BALLOT_POLLING:
            cumulative_results = (
                {choice.id: 0 for choice in contest.choices}
                if round_one
                else rounds.cumulative_contest_results(contest)
            )

            sample_size_options = bravo.get_sample_size(
                risk_limit,
                sampler_contest.from_db_contest(contest),
                cumulative_results,
            )
            # Remove unnecessary "type" field from options, add "key" field
            return {
                key: {"key": key, "size": option["size"], "prob": option["prob"]}
                for key, option in sample_size_options.items()
            }

        elif election.audit_type == AuditType.BATCH_COMPARISON:
            sample_results = rounds.cumulative_batch_results(election)
            if round_one:
                sample_results = {
                    batch_key: {
                        contest_id: {choice_id: 0 for choice_id in contest_results}
                        for contest_id, contest_results in batch_results.items()
                    }
                    for batch_key, batch_results in sample_results.items()
                }
            sample_size = macro.get_sample_sizes(
                risk_limit,
                sampler_contest.from_db_contest(contest),
                rounds.batch_tallies(election),
                sample_results,
            )
            return {"macro": {"key": "macro", "size": sample_size, "prob": None}}

        else:
            assert election.audit_type == AuditType.BALLOT_COMPARISON

            set_contest_metadata_from_cvrs(contest)
            contest_for_sampler = sampler_contest.from_db_contest(contest)

            discrepancies = supersimple.compute_discrepancies(
                contest_for_sampler,
                rounds.cvrs_for_contest(contest),
                rounds.sampled_ballot_interpretations_to_cvrs(contest),
            )
            discrepancy_groups = group_by(
                discrepancies.values(), lambda d: d["counted_as"]
            )
            discrepancy_counts = {
                "sample_size": len(discrepancies),  # TODO is this the right value?
                "1-under": len(discrepancy_groups.get(-1, [])),
                "1-over": len(discrepancy_groups.get(1, [])),
                "2-under": len(discrepancy_groups.get(-2, [])),
                "2-over": len(discrepancy_groups.get(2, [])),
            }

            sample_size = supersimple.get_sample_sizes(
                risk_limit, contest_for_sampler, discrepancy_counts
            )
            return {
                "supersimple": {"key": "supersimple", "size": sample_size, "prob": None}
            }

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
    return jsonify({"sampleSizes": sample_sizes})

import sys
from server.api.cvrs import cvr_contests_metadata
from server.api.rounds import cvrs_for_contest, sampled_ballot_interpretations_to_cvrs
from server.audit_math import sampler_contest, suite
from server.models import *  # pylint: disable=wildcard-import
from server.database import db_session


def ballot_comparison_stratum(audit: Election):
    contest = audit.contests[0]
    vote_counts = {choice.id: choice.num_votes for choice in contest.choices}
    suite_contest = sampler_contest.from_db_contest(contest)
    reported_results = cvrs_for_contest(contest)
    sample_results = sampled_ballot_interpretations_to_cvrs(contest)
    sample_size = sum(ballot["times_sampled"] for ballot in sample_results.values())
    misstatements = suite.misstatements(
        suite_contest, reported_results, sample_results,
    )
    return suite.BallotComparisonStratum(
        contest.total_ballots_cast, vote_counts, misstatements, sample_size,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python -m scripts.combine-hybrid-results <audit_id_1> <audit_id_2>"
        )
        sys.exit(1)

    audit_id_1 = sys.argv[1]
    audit_1 = Election.query.get(audit_id_1)
    if not audit_1:
        print(f"Audit not found: {audit_id_1}")
        sys.exit(1)

    audit_id_2 = sys.argv[2]
    audit_2 = Election.query.get(audit_id_2)
    if not audit_2:
        print(f"Election not found: {audit_id_2}")
        sys.exit(1)

    print(f"Audit 1: {audit_1.audit_name} ({audit_1.audit_type})")
    print(f"Audit 2: {audit_2.audit_name} ({audit_2.audit_type})")

    if audit_1.audit_type != AuditType.BALLOT_COMPARISON:
        print("Audit 1 must be ballot comparison.")
        sys.exit(1)
    if audit_2.audit_type != AuditType.BALLOT_POLLING:
        print("Audit 2 must be ballot polling.")
        sys.exit(1)
    if audit_1.contests.length != audit_2.contests.length != 1:
        print("Both audits must have exactly one contest.")
        sys.exit(1)

    # non_cvr_stratum, cvr_stratum = hybrid_contest_strata(contest)
    # p_value, is_complete = suite.compute_risk(
    #     election.risk_limit,
    #     sampler_contest.from_db_contest(contest),
    #     non_cvr_stratum,
    #     cvr_stratum,
    # )

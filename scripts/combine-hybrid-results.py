# pylint: disable=invalid-name
import sys
from server.api.rounds import (
    cvrs_for_contest,
    sampled_ballot_interpretations_to_cvrs,
    samples_not_found_by_round,
    contest_results_by_round,
    round_sizes,
)
from server.audit_math import sampler_contest, suite
from server.models import *  # pylint: disable=wildcard-import


def ballot_comparison_stratum(contest):
    # for type check
    assert contest.total_ballots_cast

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


def ballot_polling_stratum(contest, remap):
    # for type checker
    assert contest.total_ballots_cast

    vote_counts = {remap[choice.id]: choice.num_votes for choice in contest.choices}

    results_by_round = contest_results_by_round(contest)
    assert results_by_round

    sample_results = {
        round_id: {
            remap[choice_id]: result for choice_id, result in round_results.items()
        }
        for round_id, round_results in results_by_round.items()
    }

    # When a sampled ballot can't be found, count it as a vote for every loser
    for round_id, num_not_found in samples_not_found_by_round(contest).items():
        for loser in sampler_contest.from_db_contest(contest).losers:
            sample_results[round_id][loser] += num_not_found

    sample_size = sum(round_sizes(contest).values())

    return suite.BallotPollingStratum(
        contest.total_ballots_cast, vote_counts, sample_results, sample_size
    )


def combined_contests(cvr_contest, bp_contest, remap):
    contest_info_dict = {}

    cvr_candidates = cvr_contest.candidates
    bp_candidates = bp_contest.candidates
    for cand in bp_contest.candidates:
        contest_info_dict[remap[cand]] = (
            bp_candidates[cand] + cvr_candidates[remap[cand]]
        )

    contest_info_dict["numWinners"] = cvr_contest.num_winners
    contest_info_dict["votesAllowed"] = cvr_contest.votes_allowed

    contest_info_dict["ballots"] = bp_contest.ballots + cvr_contest.ballots

    return sampler_contest.Contest(cvr_contest.name, contest_info_dict)


if __name__ == "__main__":
    if len(sys.argv) != 3:
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
    # TODO: Technically they have to be the same contests too
    if len(audit_1.contests) != len(audit_2.contests):
        print("Both audits must have the same number of contests")
        sys.exit(1)

    choice_id_to_name_audit_1 = dict(
        ContestChoice.query.join(Contest)
        .filter_by(election_id=audit_1.id)
        .values(ContestChoice.id, ContestChoice.name)
    )

    choice_id_to_name_audit_2 = dict(
        ContestChoice.query.join(Contest)
        .filter_by(election_id=audit_2.id)
        .values(ContestChoice.id, ContestChoice.name)
    )

    remap = {}
    for id1 in choice_id_to_name_audit_1:
        for id2 in choice_id_to_name_audit_2:
            if choice_id_to_name_audit_1[id1] == choice_id_to_name_audit_2[id2]:
                remap[id2] = id1

    for i in range(len(audit_1.contests)):
        cvr_stratum = ballot_comparison_stratum(audit_1.contests[i])
        print(cvr_stratum)
        no_cvr_stratum = ballot_polling_stratum(audit_2.contests[i], remap)
        print(no_cvr_stratum)

        a1_sampler_contest = sampler_contest.from_db_contest(audit_1.contests[i])
        a2_sampler_contest = sampler_contest.from_db_contest(audit_2.contests[i])

        # assert a1_sampler_contest.name == a2_sampler_contest.name, f"Both audits must have the same contests! {a1_sampler_contest.name} {a2_sampler_contest.name}"

        overall_contest = combined_contests(
            a1_sampler_contest, a2_sampler_contest, remap,
        )

        # non_cvr_stratum, cvr_stratum = hybrid_contest_strata(contest)
        p_value, is_complete = suite.compute_risk(
            audit_1.risk_limit, overall_contest, no_cvr_stratum, cvr_stratum,
        )
        print(f"{a1_sampler_contest.name}: Finished? {is_complete} p-value {p_value}")

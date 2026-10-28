import math
from collections import Counter
from itertools import product
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from typing import TypedDict

from .sampler_contest import Contest, CVRS, SAMPLECVRS, CVR as CVR

l: Decimal = Decimal(0.5)  # noqa: E741
gamma: Decimal = Decimal(1.03905)  # This gamma is used in Stark's tool, AGI, and CORLA

# This sets the expected number of one-vote misstatements at 1 in 1000
r1_default: Decimal = Decimal(0.001)
s1_default: Decimal = Decimal(0.001)

# This sets the expected two-vote misstatements at 1 in 10000
r2_default: Decimal = Decimal(0.0001)
s2_default: Decimal = Decimal(0.0001)

# Chance that an uncontested contest's sample includes a vote for each winner
UNCONTESTED_P_COMPLETION = 0.95


class Discrepancy(TypedDict):
    counted_as: int
    weighted_error: Decimal


def nMin(
    alpha: Decimal, contest: Contest, o1: Decimal, o2: Decimal, u1: Decimal, u2: Decimal
) -> Decimal:
    """
    Computes a sample size parameterized by expected under and overstatements
    and the margin.
    """
    return (o1 + o2 + u1 + u2).max(
        math.ceil(
            -2
            * gamma
            * (
                alpha.ln()
                + o1 * (1 - 1 / (2 * gamma)).ln()
                + o2 * (1 - 1 / gamma).ln()
                + u1 * (1 + 1 / (2 * gamma)).ln()
                + u2 * (1 + 1 / gamma).ln()
            )
            / Decimal(contest.diluted_margin)
        ),
    )


def compute_discrepancies(
    contest: Contest, cvrs: CVRS, sample_cvr: SAMPLECVRS
) -> dict[str, Discrepancy]:
    """
    Iterates through a given sample and returns the discrepancies found.

    Inputs:
        contests       - the contests and results being audited
        cvrs           - mapping of ballot_id to votes:
                {
                    'ballot_id': {
                        'contest': {
                            'candidate1': 1,
                            'candidate2': 0,
                            ...
                        }
                    ...
                }

        sample_cvr - the CVR of the audited ballots
                {
                    'ballot_id': {
                        'times_sampled': 1,
                        'cvr': {
                            'contest': {
                                'candidate1': 1,
                                'candidate2': 0,
                                ...
                            }
                    }
                    ...
                }

    Outputs:
        discrepancies   - A mapping of ballot ids to their discrepancies. This
                          includes entries for ballots in the sample that have discrepancies
                          only. Each value is the maximum across all winner-loser
                          pairs, so the two values may come from different pairs.
                    {
                        'ballot_id': {
                            'counted_as': -1, # The maximum discrepancy in votes
                            'weighted_error': -0.0033 # The maximum discrepancy relative to the pair's margin, used for p-value calculation
                        }
                    }
    """
    discrepancies: dict[str, Discrepancy] = {}
    for ballot, ballot_sample_cvr in sample_cvr.items():
        ballot_discrepancies: list[Discrepancy] = []
        for winner, loser in product(contest.winners, contest.losers):
            ballot_discrepancy = discrepancy(
                contest,
                winner,
                loser,
                cvrs.get(ballot),
                ballot_sample_cvr["cvr"],
            )
            if ballot_discrepancy is not None:
                ballot_discrepancies.append(ballot_discrepancy)

        if len(ballot_discrepancies) > 0:
            discrepancies[ballot] = Discrepancy(
                counted_as=max(d["counted_as"] for d in ballot_discrepancies),
                weighted_error=max(d["weighted_error"] for d in ballot_discrepancies),
            )

    return discrepancies


def discrepancy(
    contest: Contest,
    winner: str,
    loser: str,
    reported: CVR | None,
    audited: CVR | None,
) -> Discrepancy | None:
    def compute_error():
        # Special cases: if ballot wasn't in CVR or ballot can't be found by
        # audit board, count it as a two-vote overstatement
        if reported is None or audited is None:
            return 2

        # Reported values outside the expected domain can't be scored
        # reliably, so count them as a two-vote overstatement.
        if any(
            str(value) not in ["0", "1", "o", "u"]
            for value in reported.get(contest.name, {}).values()
        ):
            return 2

        a_w, a_l = (
            (int(audited[contest.name][winner]), int(audited[contest.name][loser]))
            if contest.name in audited
            # If contest wasn't on the ballot according to the audit board
            else (0, 0)
        )

        # Special case for ES&S overvotes. If the audited result correctly
        # identified the overvote, return 0 error. Otherwise, return an error
        # using the standard formula, but substituting in the overvotes.
        has_overvote = "o" in reported.get(contest.name, {}).values()
        audited_votes = sum(map(int, (audited.get(contest.name, {}).values())))
        if has_overvote:
            if audited_votes > contest.votes_allowed:
                return 0
            else:
                return (1 - a_w) - (1 - a_l)

        # ES&S undervotes count as no vote for any choice.
        def reported_vote(choice: str) -> int:
            value = reported[contest.name][choice]
            return 0 if value == "u" else int(value)

        v_w, v_l = (
            (reported_vote(winner), reported_vote(loser))
            if contest.name in reported
            # If contest wasn't on the ballot according to the CVR
            else (0, 0)
        )
        return (v_w - a_w) - (v_l - a_l)

    error = compute_error()
    if error == 0:
        return None

    V_wl = contest.candidates[winner] - contest.candidates[loser]
    weighted_error = Decimal(error) / Decimal(V_wl) if V_wl > 0 else Decimal("inf")

    return Discrepancy(counted_as=error, weighted_error=weighted_error)


def get_sample_sizes(
    risk_limit: int, contest: Contest, sample_results: dict[str, int] | None
) -> int:
    """
    Computes initial sample sizes parameterized by likelihood that the
    initial sample will confirm the election result, assuming no
    discrepancies.

    Inputs:
        sample_results - if a sample has already been drawn, this will
                         contain its results, of the form:
                         {
                            'sample_size': n,
                            '1-under':     u1,
                            '1-over':      o1,
                            '2-under':     u2,
                            '2-over':      o2,
                         }

    Outputs:
        sample_size    - the sample size needed for this audit
    """
    alpha = Decimal(risk_limit) / 100
    assert alpha < 1

    if alpha == 0:
        return contest.ballots

    sample_results = sample_results or {}
    obs_o1 = Decimal(sample_results.get("1-over", 0))
    obs_o2 = Decimal(sample_results.get("2-over", 0))
    # We want to be conservative, so we will ignore understatements (i.e. errors
    # that favor the winner) which are negative.
    obs_u1 = 0
    obs_u2 = 0
    num_sampled = Decimal(sample_results.get("sample_size", 0))

    if contest.is_uncontested:
        return uncontested_sample_size(contest, int(num_sampled))

    if num_sampled:
        r1 = obs_o1 / num_sampled
        r2 = obs_o2 / num_sampled
        s1 = obs_u1 / num_sampled
        s2 = obs_u2 / num_sampled
    else:
        r1 = r1_default
        r2 = r2_default
        s1 = s1_default
        s2 = s2_default

    denom = (
        (1 - Decimal(contest.diluted_margin) / (2 * gamma)).ln()
        - r1 * (1 - 1 / (2 * gamma)).ln()
        - r2 * (1 - 1 / gamma).ln()
        - s1 * (1 + 1 / (2 * gamma)).ln()
        - s2 * (1 + 1 / gamma).ln()
    )

    if denom >= 0:
        stopping_size = contest.ballots
    else:
        n0 = math.ceil(alpha.ln() / denom)

        # Round up one-vote discrepancies.
        o1 = (r1 * n0).quantize(Decimal(1), ROUND_CEILING)
        u1 = (s1 * n0).quantize(Decimal(1), ROUND_CEILING)
        # Round normally two-vote discrepancies.
        o2 = (r2 * n0).quantize(Decimal(1), ROUND_HALF_UP)
        u2 = (s2 * n0).quantize(Decimal(1), ROUND_HALF_UP)

        estimated_stopping_size = int(nMin(alpha, contest, o1, o2, u1, u2))
        stopping_size = min(estimated_stopping_size, contest.ballots)

    return max(stopping_size - int(num_sampled), 0)


def get_sample_sizes_from_discrepancies(
    risk_limit: int,
    contest: Contest,
    discrepancies: dict[str, Discrepancy],
    num_sampled_so_far: int,
) -> int:
    """
    Computes the next round's sample size from the discrepancies found so far
    (the output of compute_discrepancies) and the number of ballots sampled so
    far.
    """
    discrepancy_counter = Counter(d["counted_as"] for d in discrepancies.values())
    return get_sample_sizes(
        risk_limit,
        contest,
        {
            "sample_size": num_sampled_so_far,
            "1-under": discrepancy_counter[-1],
            "1-over": discrepancy_counter[1],
            "2-under": discrepancy_counter[-2],
            "2-over": discrepancy_counter[2],
        },
    )


def compute_risk(
    risk_limit: int,
    contest: Contest,
    cvrs: CVRS,
    sample_cvr: SAMPLECVRS,
    discrepancies: dict[str, Discrepancy] | None = None,
) -> tuple[float, bool]:
    """
    Computes the risk-value of <sample_results> based on results in <contest>.

    Inputs:
        contests       - the contests and results being audited
        cvrs           - mapping of ballot_id to votes:
                {
                    'ballot_id': {
                        'contest': {
                            'candidate1': 1,
                            'candidate2': 0,
                            ...
                        }
                    ...
                }

        sample_cvr - the CVR of the audited ballots
                {
                    'ballot_id': {
                        'times_sampled': 1,
                        'contest': {
                            'candidate1': 1,
                            'candidate2': 0,
                            ...
                        }
                    ...
                }

        discrepancies  - optional, the result of compute_discrepancies for this
                         sample, to avoid computing it again

    Outputs:
        measurements    - the p-value of the hypotheses that the election
                          result is correct based on the sample, for each winner-loser pair.
        confirmed       - a boolean indicating whether the audit can stop
    """
    alpha = Decimal(risk_limit) / 100
    assert alpha < 1

    N = contest.ballots

    # An uncontested outcome is confirmed by finding a vote for each winner
    if contest.is_uncontested:
        if all_winners_have_audited_votes(contest, sample_cvr):
            return 0, True
        return 1, False

    p = Decimal(1.0)
    V = Decimal(contest.diluted_margin * N)

    if contest.diluted_margin == 0:
        U = Decimal("inf")
    else:
        U = 2 * gamma / Decimal(contest.diluted_margin)

    result = False

    if discrepancies is None:
        discrepancies = compute_discrepancies(contest, cvrs, sample_cvr)

    for ballot in sample_cvr:
        if ballot in discrepancies:
            # We want to be conservative, so we will ignore understatements (i.e. errors
            # that favor the winner) which are negative.
            e_r = max(discrepancies[ballot]["weighted_error"], Decimal(0))
        else:
            e_r = Decimal(0)

        if contest.diluted_margin:
            U = 2 * gamma / Decimal(contest.diluted_margin)
            denom = (2 * gamma) / V
            p_b_denom = 1 - (e_r / denom)
            if p_b_denom <= 0:
                p = Decimal("inf")
                break
            p_b = (1 - 1 / U) / p_b_denom
        else:
            # If the contest is a tie, this step results in 1 - 1/(infinity)
            # divided by 1 - e_r/infinity, i.e. 1
            p_b = Decimal(1.0)

        multiplicity = sample_cvr[ballot]["times_sampled"]
        p *= p_b**multiplicity

    if 0 < p < alpha:
        result = True

    return min(float(p), 1.0), result


def uncontested_sample_size(contest: Contest, num_sampled: int) -> int:
    """Returns the number of ballots likely to include a vote for every winner."""
    remaining = max(contest.ballots - num_sampled, 0)
    min_winner_fraction = min(contest.winners.values()) / contest.ballots
    # A winner with no reported votes can only be confirmed by a full hand tally
    if min_winner_fraction == 0:
        return remaining
    if min_winner_fraction >= 1:
        return min(1, remaining)
    size = math.ceil(
        math.log(1 - UNCONTESTED_P_COMPLETION) / math.log(1 - min_winner_fraction)
    )
    return min(size, remaining)


def all_winners_have_audited_votes(contest: Contest, sample_cvr: SAMPLECVRS) -> bool:
    """Returns whether every winner received a vote on at least one audited ballot."""
    return all(
        any(
            ballot["cvr"] is not None
            and str(ballot["cvr"].get(contest.name, {}).get(winner)) == "1"
            for ballot in sample_cvr.values()
        )
        for winner in contest.winners
    )

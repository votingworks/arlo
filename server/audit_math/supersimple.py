# pylint: disable=invalid-name
import math
from itertools import product
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from typing import Dict, Tuple, TypedDict, Optional

from .sampler_contest import Contest, CVRS, SAMPLECVRS, CVR

l: Decimal = Decimal(0.5)
gamma: Decimal = Decimal(1.03905)  # This gamma is used in Stark's tool, AGI, and CORLA

# This sets the expected number of one-vote misstatements at 1 in 1000
r1_default: Decimal = Decimal(0.001)
s1_default: Decimal = Decimal(0.001)

# This sets the expected two-vote misstatements at 1 in 10000
r2_default: Decimal = Decimal(0.0001)
s2_default: Decimal = Decimal(0.0001)


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
) -> Dict[str, Discrepancy]:
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
                          only.
                    {
                        'ballot_id': {
                            'counted_as': -1, # The maximum value for a discrepancy
                            'weighted_error': -0.0033 # Weighted error used for p-value calculation
                        }
                    }
    """
    discrepancies: Dict[str, Discrepancy] = {}
    for ballot, ballot_sample_cvr in sample_cvr.items():
        ballot_discrepancies = []
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
            discrepancies[ballot] = max(
                ballot_discrepancies, key=lambda d: d["counted_as"]
            )

    return discrepancies


def discrepancy(
    contest: Contest,
    winner: str,
    loser: str,
    reported: Optional[CVR],
    audited: Optional[CVR],
) -> Optional[Discrepancy]:
    def compute_error():
        # Special cases: if ballot wasn't in CVR or ballot can't be found by
        # audit board, count it as a two-vote overstatement
        if reported is None or audited is None:
            return 2

        a_w, a_l = (
            (int(audited[contest.name][winner]), int(audited[contest.name][loser]))
            if contest.name in audited
            # If contest wasn't on the ballot according to the audit board
            else (0, 0)
        )

        # Special case for ES&S overvotes/undervotes.
        has_overvote = "o" in reported.get(contest.name, {}).values()
        has_undervote = "u" in reported.get(contest.name, {}).values()
        audited_votes = sum(map(int, (audited.get(contest.name, {}).values())))
        # If the audited result correctly identified overvote/undervote, return
        # 0 error.  Otherwise, return an error using the standard formula, but
        # substituting in the appropriate overvotes/undervotes.
        if has_overvote:
            if audited_votes > 1:
                return 0
            else:
                return (1 - a_w) - (1 - a_l)
        if has_undervote:
            if audited_votes < 1:
                return 0
            else:
                return (0 - a_w) - (0 - a_l)

        v_w, v_l = (
            (int(reported[contest.name][winner]), int(reported[contest.name][loser]))
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
    risk_limit: int, contest: Contest, sample_results: Optional[Dict[str, int]]
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


def compute_risk(
    risk_limit: int, contest: Contest, cvrs: CVRS, sample_cvr: SAMPLECVRS
) -> Tuple[float, bool]:
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

    Outputs:
        measurements    - the p-value of the hypotheses that the election
                          result is correct based on the sample, for each winner-loser pair.
        confirmed       - a boolean indicating whether the audit can stop
    """
    alpha = Decimal(risk_limit) / 100
    assert alpha < 1

    p = Decimal(1.0)

    N = contest.ballots
    V = Decimal(contest.diluted_margin * N)

    if contest.diluted_margin == 0:
        U = Decimal("inf")
    else:
        U = 2 * gamma / Decimal(contest.diluted_margin)

    result = False

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
            p_b = (1 - 1 / U) / (1 - (e_r / denom))
        else:
            # If the contest is a tie, this step results in 1 - 1/(infinity)
            # divided by 1 - e_r/infinity, i.e. 1
            p_b = Decimal(1.0)

        multiplicity = sample_cvr[ballot]["times_sampled"]
        p *= p_b**multiplicity

    if 0 < p < alpha:
        result = True

    # Special case if the sample size equals all the ballots (i.e. a full hand tally)
    if sum(ballot["times_sampled"] for ballot in sample_cvr.values()) >= N:
        return 0, True

    return min(float(p), 1.0), result

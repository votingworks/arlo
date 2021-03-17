# pylint: disable=invalid-name
import math
from itertools import product
from decimal import Decimal, ROUND_CEILING
from typing import Dict, Tuple, TypedDict, Optional

from .sampler_contest import Contest, CVRS, SAMPLECVRS, CVR

l: Decimal = Decimal(0.5)
gamma: Decimal = Decimal(1.03905)  # This gamma is used in Stark's tool, AGI, and CORLA

# This sets the expected number of one-vote misstatements at 1 in 1000
o1: Decimal = Decimal(0.001)
u1: Decimal = Decimal(0.001)

# This sets the expected two-vote misstatements at 1 in 10000
o2: Decimal = Decimal(0.0001)
u2: Decimal = Decimal(0.0001)


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
                contest, winner, loser, cvrs.get(ballot), ballot_sample_cvr["cvr"],
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
    # Special cases: if ballot wasn't in CVR or ballot can't be found by
    # audit board, count it as a two-vote overstatement
    if reported is None or audited is None:
        error = 2
    else:
        v_w, v_l = (
            (reported[contest.name][winner], reported[contest.name][loser])
            if contest.name in reported
            # If contest wasn't on the ballot according to the CVR
            else (0, 0)
        )
        a_w, a_l = (
            (audited[contest.name][winner], audited[contest.name][loser])
            if contest.name in audited
            # If contest wasn't on the ballot according to the audit board
            else (0, 0)
        )
        error = (v_w - a_w) - (v_l - a_l)

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
        total_ballots  - the total number of ballots cast in the election
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
        r1 = o1
        r2 = o2
        s1 = u1
        s2 = u2

    denom = (
        (1 - Decimal(contest.diluted_margin) / (2 * gamma)).ln()
        - r1 * (1 - 1 / (2 * gamma)).ln()
        - r2 * (1 - 1 / gamma).ln()
        - s1 * (1 + 1 / (2 * gamma)).ln()
        - s2 * (1 + 1 / gamma).ln()
    )

    if denom >= 0:
        return contest.ballots

    n0 = math.ceil(alpha.ln() / denom)

    # Round up one-vote differences.
    r1 = (r1 * n0).quantize(Decimal(1), ROUND_CEILING)
    s1 = (s1 * n0).quantize(Decimal(1), ROUND_CEILING)

    return int(nMin(alpha, contest, r1, r2, s1, s2))


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
        p *= p_b ** multiplicity

    if 0 < p < alpha:
        result = True

    if len(sample_cvr) >= N:
        # We've done a full hand recount
        return 0, True

    return min(float(p), 1.0), result

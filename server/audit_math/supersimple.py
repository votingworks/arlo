# pylint: disable=invalid-name
import math
from decimal import Decimal, ROUND_CEILING
from typing import Dict, Tuple, TypedDict, Optional

from .sampler_contest import Contest

l: Decimal = Decimal(0.5)
gamma: Decimal = Decimal(1.03905)  # This gamma is used in Stark's tool, AGI, and CORLA

# This sets the expected number of one-vote misstatements at 1 in 1000
o1: Decimal = Decimal(0.001)
u1: Decimal = Decimal(0.001)

# This sets the expected two-vote misstatements at 1 in 10000
o2: Decimal = Decimal(0.0001)
u2: Decimal = Decimal(0.0001)

# { ballot_id: { contest_id: { choice_id: 0 | 1 }}}
CVRS = Dict[str, Dict[str, Dict[str, int]]]
CVR = Dict[str, Dict[str, int]]


class Discrepancy(TypedDict):
    counted_as: int
    weighted_error: Decimal
    discrepancy_cvr: CVRS


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
    contest: Contest, cvrs: CVRS, sample_cvr: CVRS,
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
                        'contest': {
                            'candidate1': 1,
                            'candidate2': 0,
                            ...
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
                            'discrepancy_cvr': { # a per-contest mapping of discrepancies
                                'recorded_as': {
                                    'contest': {
                                        'candidate1': 1,
                                        'candidate0': 0,
                                }},
                                'audited_as': {
                                    'contest': {
                                        'candidate1': 0,
                                        'candidate2': 0,
                                    }
                                }
                            }
                        }
                    }
    """

    discrepancies: Dict[str, Discrepancy] = {}
    for ballot in sample_cvr:
        # We want to be conservative, so we will ignore the case where there are
        # negative errors (i.e. errors that favor the winner. We can do that
        # by setting these to zero and evaluating whether an error is greater
        # than zero (i.e. positive).
        e_r = Decimal(0.0)
        e_int = 0

        found = False
        for winner in contest.winners:
            for loser in contest.losers:

                if contest.name in cvrs[ballot]:
                    v_w = cvrs[ballot][contest.name][winner]
                    v_l = cvrs[ballot][contest.name][loser]
                else:
                    v_w = 0
                    v_l = 0

                if contest.name in sample_cvr[ballot]:
                    a_w = sample_cvr[ballot][contest.name][winner]
                    a_l = sample_cvr[ballot][contest.name][loser]
                else:
                    a_w = 0
                    a_l = 0

                V_wl = contest.candidates[winner] - contest.candidates[loser]

                e = (v_w - a_w) - (v_l - a_l)

                if e:
                    # we found a discrepancy!
                    found = True
                e_weighted = Decimal(e) / Decimal(V_wl)
                if e_weighted > e_r:
                    e_r = e_weighted
                    e_int = e

        if found:
            discrepancies[ballot] = Discrepancy(
                counted_as=e_int,
                weighted_error=e_weighted,
                discrepancy_cvr={
                    "reported_as": cvrs[ballot],
                    "audited_as": sample_cvr[ballot],
                },
            )

    return discrepancies


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
    obs_u1 = Decimal(sample_results.get("1-under", 0))
    obs_o2 = Decimal(sample_results.get("2-over", 0))
    obs_u2 = Decimal(sample_results.get("2-under", 0))
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
    risk_limit: int, contest: Contest, cvrs: CVRS, sample_cvr: CVRS,
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

    U = 2 * gamma / Decimal(contest.diluted_margin)

    result = False

    discrepancies = compute_discrepancies(contest, cvrs, sample_cvr)

    for ballot in sample_cvr:
        if ballot in discrepancies:
            e_r = discrepancies[ballot]["weighted_error"]
        else:
            e_r = Decimal(0)

        denom = (2 * gamma) / V
        p_b = (1 - 1 / U) / (1 - (e_r / denom))
        p *= p_b

    if 0 < p < alpha:
        result = True

    return float(p), result

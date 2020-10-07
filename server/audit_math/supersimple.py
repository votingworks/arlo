# pylint: disable=invalid-name
import math
from typing import Dict, Tuple, Union, TypedDict

from .sampler_contest import Contest

l: float = 0.5
gamma: float = 1.03905  # This gamma is used in Stark's tool, AGI, and CORLA

# This sets the expected number of one-vote misstatements at 1 in 1000
o1: float = 0.001
u1: float = 0.001

# This sets the expected two-vote misstatements at 1 in 10000
o2: float = 0.0001
u2: float = 0.0001

# { ballot_id: { contest_id: { choice_id: 0 | 1 }}}
CVRS = Dict[str, Dict[str, Dict[str, int]]]
CVR = Dict[str, Dict[str, int]]


class Discrepancy(TypedDict):
    counted_as: int
    weighted_error: float
    cvr: CVR
    sample_cvr: CVR


def nMin(
    risk_limit: float, contest: Contest, o1: float, o2: float, u1: float, u2: float
) -> float:
    """
    Computes a sample size parameterized by expected under and overstatements
    and the margin.
    """
    return max(
        o1 + o2 + u1 + u2,
        math.ceil(
            -2
            * gamma
            * (
                math.log(risk_limit)
                + o1 * math.log(1 - 1 / (2 * gamma))
                + o2 * math.log(1 - 1 / gamma)
                + u1 * math.log(1 + 1 / (2 * gamma))
                + u2 * math.log(1 + 1 / gamma)
            )
            / contest.diluted_margin
        ),
    )


def find_discrepancies(
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
                          includes entries for all ballots in the sample, even those without
                          discrepancies.
                {
                    'ballot_id': {
                        'counted_as': -1, # The maximum value for a discrepancy
                        'weighted_error': -0.0033 # Weighted error used for p-value calculation
                        'cvr': <CVR for this ballot>,
                        'sample_cvr': <Sample CVR for this ballot>
                    }
    """

    discrepancies: Dict[str, Discrepancy] = {}
    for ballot in sample_cvr:
        e_r = 0.0
        e_int = 0

        if contest.name not in sample_cvr[ballot]:
            continue
        for winner in contest.winners:
            for loser in contest.losers:
                v_w = cvrs[ballot][contest.name][winner]
                a_w = sample_cvr[ballot][contest.name][winner]

                v_l = cvrs[ballot][contest.name][loser]
                a_l = sample_cvr[ballot][contest.name][loser]

                V_wl = contest.candidates[winner] - contest.candidates[loser]

                e = (v_w - a_w) - (v_l - a_l)
                e_weighted = e / V_wl
                if e_weighted > e_r:
                    e_r = e_weighted
                    e_int = e

        discrepancies[ballot] = Discrepancy(
            counted_as=e_int,
            weighted_error=e_weighted,
            cvr=cvrs[ballot],
            sample_cvr=sample_cvr[ballot],
        )

    return discrepancies


def get_sample_sizes(
    risk_limit: float, contest: Contest, sample_results: Dict[str, Union[int, float]]
) -> float:
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

    obs_o1 = sample_results["1-over"]
    obs_u1 = sample_results["1-under"]
    obs_o2 = sample_results["2-over"]
    obs_u2 = sample_results["2-under"]
    num_sampled = sample_results["sample_size"]

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
        math.log(1 - contest.diluted_margin / (2 * gamma))
        - r1 * math.log(1 - 1 / (2 * gamma))
        - r2 * math.log(1 - 1 / gamma)
        - s1 * math.log(1 + 1 / (2 * gamma))
        - s2 * math.log(1 + 1 / gamma)
    )

    if denom >= 0:
        return contest.ballots

    n0 = math.ceil(math.log(risk_limit) / denom)

    # Round up one-vote differences.
    r1 = math.ceil(r1 * n0)
    s1 = math.ceil(s1 * n0)

    return nMin(risk_limit, contest, r1, r2, s1, s2)


def compute_risk(
    risk_limit: float, contest: Contest, cvrs: CVRS, sample_cvr: CVRS,
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
    p = 1.0

    V = contest.diluted_margin * len(cvrs)

    U = 2 * gamma / contest.diluted_margin

    result = False

    discrepancies = find_discrepancies(contest, cvrs, sample_cvr)

    for ballot in discrepancies:
        e_r = discrepancies[ballot]["weighted_error"]

        denom = (2 * gamma) / V
        p_b = (1 - 1 / U) / (1 - (e_r / denom))
        p *= p_b

    if 0 < p < risk_limit:
        result = True

    return p, result

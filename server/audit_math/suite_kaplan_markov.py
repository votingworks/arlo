from __future__ import division, print_function
import math
import numpy as np
import numpy.random
import scipy as sp
import scipy.stats

from decimal import Decimal

def ballot_comparison_pvalue(n, o1, u1, o2, u2, reported_margin, N, null_lambda=1):
    """
    Compute the p-value for a ballot comparison audit using Kaplan-Markov

    Parameters
    ----------
    n : int
        sample size
    o1 : int
        number of ballots that overstate any
        margin by one vote but no margin by two votes
    u1 : int
        number of ballots that understate any margin by
        exactly one vote, and every margin by at least one vote
    o2 : int
        number of ballots that overstate any margin by two votes
    u2 : int
        number of ballots that understate every margin by two votes
    reported_margin : float
        the smallest reported margin *in votes* between a winning
        and losing candidate for the contest as a whole, including any other strata
    N : int
        number of votes cast in the stratum
    null_lambda : float
        fraction of the overall margin (in votes) to test for in the stratum. If the overall margin is reported_margin,
        test that the overstatement in this stratum does not exceed null_lambda*reported_margin

    Returns
    -------
    pvalue
    """


    gamma = Decimal(1.03905)  # This gamma is used in Stark's tool, AGI, and CORLA
    U_s = 2*N/reported_margin
    log_pvalue = n*np.log(1 - null_lambda/(gamma*U_s)) - \
                    o1*np.log(1 - 1/(2*gamma)) - \
                    o2*np.log(1 - 1/gamma) - \
                    u1*np.log(1 + 1/(2*gamma)) - \
                    u2*np.log(1 + 1/gamma)
    pvalue = np.exp(log_pvalue)
    return np.min([pvalue, 1])



def compute_discrepancies(
    contest: Contest, winner, loser, cvrs: CVRS, sample_cvr: SAMPLE_CVRS
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
        # Typechecker needs us to pull these out into variables
        ballot_sample_cvr = sample_cvr[ballot]["cvr"]
        ballot_cvr = cvrs[ballot]
        assert ballot_cvr is not None

        # We want to be conservative, so we will ignore the case where there are
        # negative errors (i.e. errors that favor the winner. We can do that
        # by setting these to zero and evaluating whether an error is greater
        # than zero (i.e. positive).
        e_r = Decimal(0.0)
        e_int = 0

        found = False

        # Special case: if ballot can't be found by audit board, count it as a
        # two-vote overstatement
        if ballot_sample_cvr is None:
            e_int = 2
            e_r = Decimal(e_int) / Decimal(contest.diluted_margin * contest.ballots)
            found = True

        else:
            if contest.name in ballot_cvr:
                v_w = ballot_cvr[contest.name][winner]
                v_l = ballot_cvr[contest.name][loser]
            else:
                v_w = 0
                v_l = 0

            if contest.name in ballot_sample_cvr:
                a_w = ballot_sample_cvr[contest.name][winner]
                a_l = ballot_sample_cvr[contest.name][loser]
            else:
                a_w = 0
                a_l = 0

            V_wl = contest.candidates[winner] - contest.candidates[loser]

            e = (v_w - a_w) - (v_l - a_l)

            if e != 0:
                # we found a discrepancy!
                found = True

            if V_wl == 0:
                # In this case the error is undefined
                e_weighted = Decimal("inf")
            else:
                e_weighted = Decimal(e) / Decimal(V_wl)

            if e_weighted > e_r:
                e_r = e_weighted
                e_int = e

        if found:
            discrepancies[ballot] = Discrepancy(
                counted_as=e_int,
                weighted_error=e_r,
                discrepancy_cvr={
                    "reported_as": ballot_cvr,
                    "audited_as": ballot_sample_cvr,
                },
            )

    return discrepancies


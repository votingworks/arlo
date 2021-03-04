"""
This library allows the performing of a stratified audit. For now, it works with
ballot polling and ballot comparison, plurality winner contests. The method
is SUITE, described by Ottoboni, Stark, Lindeman, and McBurnett here:
https://arxiv.org/abs/1809.04235

This code borrows heavily from code already written by Stark and Ottoboni here:
https://github.com/pbstark/CORLA18


"""
from __future__ import print_function, division

from collections import OrderedDict
from itertools import product
import math
import numpy as np
import scipy as sp
from typing import Union, Optional, Tuple, Dict, List, Any


from decimal import Decimal
from ..models import AuditMathType
from .sampler_contest import Contest, CVR, CVRS, SAMPLE_CVRS, SampleCVR
from .supersimple import Discrepancy
from . import bravo


GAMMA = 1.03905  # This GAMMA is used in Stark's tool, AGI, and CORLA

class Stratum:
    """
    A class encapsulating a stratum of ballots in an election. Each stratum is its
    own contest object, with its own margin. Strata, along with the overall
    contest object, are passed to the SUITE module when perfoming mixed-strata
    audits.
    """
    RESULTS = Union[
      Dict[Any, Dict[str, Dict[str, int]]], # batch comparison
      CVRS, # ballot comparison
      None # ballot polling
    ]

    SAMPLE_RESULTS = Union[
      Dict[Any, Dict[str, Dict[str, int]]], # batch comparison
      SAMPLE_CVRS, # ballot comparison
      Optional[Dict[str, Dict[str, int]]],# ballot polling
    ]

    contest: Contest
    math_type: AuditMathType
    results: RESULTS
    sample: SAMPLE_RESULTS
    sample_size: int


    def __init__(self,
            contest: Contest,
            math_type: AuditMathType,
            results: RESULTS,
            sample_results: SAMPLE_RESULTS,
            sample_size: int,
    ):
        self.contest = contest
        self.math_type = math_type
        self.results = results
        self.sample = sample_results
        self.sample_size = sample_size

    def compute_pvalue(self, contest, alpha, winner, loser, null_lambda) -> float:
        """
        Compute a p-value for a winner-loser pair for this strata based on its math type.
        """


        reported_margin = contest.candidates[winner] - contest.candidates[loser]
        if self.math_type == AuditMathType.BRAVO:
            # Set parameters
            popsize = self.contest.ballots

            # Set up likelihood for null and alternative hypotheses
            n = self.sample_size
            sample = bravo.compute_cumulative_sample(self.sample)
            n_w = sample[winner]
            n_l = sample[loser]
            n_u = n - n_w - n_l

            v_w = self.contest.winners[winner]
            v_l = self.contest.losers[loser]
            v_u = popsize - v_w - v_l

            null_margin = (v_w - v_l) - null_lambda*reported_margin

            assert v_w >= n_w and v_l >= n_l and v_u >= n_u, "Alternative hypothesis isn't consistent with the sample"

            alt_logLR = np.sum(np.log(v_w - np.arange(n_w))) + \
                        np.sum(np.log(v_l - np.arange(n_l))) + \
                        np.sum(np.log(v_u - np.arange(n_u)))

            null_logLR = lambda Nw: (n_w > 0)*np.sum(np.log(Nw - np.arange(n_w))) + \
                        (n_l > 0)*np.sum(np.log(Nw - null_margin - np.arange(n_l))) + \
                        (n_u > 0)*np.sum(np.log(popsize - 2*Nw + null_margin - np.arange(n_u)))

            upper_n_w_limit = (popsize - n_u + null_margin)/2
            lower_n_w_limit = np.max([n_w, n_l+null_margin])

            # For extremely small or large null_margins, the limits do not
            # make sense with the sample values.
            if upper_n_w_limit < n_w or (upper_n_w_limit - null_margin) < n_l:
                raise Exception('Null is impossible, given the sample')


            if lower_n_w_limit > upper_n_w_limit:
                lower_n_w_limit, upper_n_w_limit = upper_n_w_limit, lower_n_w_limit

            LR_derivative = lambda Nw: np.sum([1/(Nw - i) for i in range(n_w)]) + \
                        np.sum([1/(Nw - null_margin - i) for i in range(n_l)]) - \
                        2*np.sum([1/(popsize - 2*Nw + null_margin - i) for i in range(n_u)])

            # Sometimes the upper_n_w_limit is too extreme, causing illegal 0s.
            # Check and change the limit when that occurs.
            if np.isinf(null_logLR(upper_n_w_limit)) or np.isinf(LR_derivative(upper_n_w_limit)):
                upper_n_w_limit -= 1

            # Check if the maximum occurs at an endpoint: deriv has no sign change
            if LR_derivative(upper_n_w_limit)*LR_derivative(lower_n_w_limit) > 0:
                nuisance_param = upper_n_w_limit if null_logLR(upper_n_w_limit)>=null_logLR(lower_n_w_limit) else lower_n_w_limit
            # Otherwise, find the (unique) root of the derivative of the log likelihood ratio
            else:
                nuisance_param = sp.optimize.brentq(LR_derivative, lower_n_w_limit, upper_n_w_limit)
            number_invalid = popsize - nuisance_param*2 + null_margin
            logLR = alt_logLR - null_logLR(nuisance_param)
            LR = np.exp(logLR)

            return 1.0/LR if 1.0/LR < 1 else 1.0
        elif self.math_type == AuditMathType.SUPERSIMPLE:
            discrepancies = compute_discrepancies(self.contest, winner, loser, self.results, self.sample)
            o1,o2,u1,u2 = 0,0,0,0

            for ballot in discrepancies:
                e = discrepancies[ballot]["counted_as"]
                if e == -2:
                    u2 += 1
                elif e == -1:
                    u1 += 1
                elif e == 1:
                    o1 += 1
                elif e == 2:
                    o2 += 1

            U_s = 2*self.contest.ballots/reported_margin
            log_pvalue = self.sample_size*np.log(1 - null_lambda/(GAMMA*U_s)) - \
                            o1*np.log(1 - 1/(2*GAMMA)) - \
                            o2*np.log(1 - 1/GAMMA) - \
                            u1*np.log(1 + 1/(2*GAMMA)) - \
                            u2*np.log(1 + 1/GAMMA)
            pvalue = np.exp(log_pvalue)
            return np.min([pvalue, 1])
        # TODO null_margins = null_lambda?
        else: raise Exception('SUITE with batch comparison is not yet implemented')


def maximize_fisher_combined_pvalue(
        alpha: Decimal,
	contest: Contest,
	strata: List[Stratum],
        winner: str,
        loser: str
    	) -> float:
    """
    Grid search to find the maximum P-value.
    Find the smallest Fisher's combined statistic for P-values obtained
    by testing two null hypotheses at level alpha using data X=(X1, X2).
    Parameters
    ----------
    stepsize : float
        size of the grid for searching over lambda. Default is 0.05
    strata  - a list of Stratum object. Note: assume ballot polling strata is first.
    alpha : float
        Risk limit. Default is 0.05.

    Returns
    -------
    max_pvalue: float
    """
    assert len(strata)==2
    stepsize=0.05

    maximized_pvalue = 0.0
    # find range of possible lambda
    N_w1 = strata[0].contest.candidates[winner]
    N_w2 = strata[1].contest.candidates[winner]


    N_ell1 = strata[0].contest.candidates[loser]
    N_ell2 = strata[1].contest.candidates[loser]

    N_1 = strata[0].contest.ballots
    N_2 = strata[1].contest.ballots


    V = N_w1 + N_w2 - N_ell1 - N_ell2
    lambda_lower = np.amax([N_w1 - N_ell1 - N_1, V - (N_w2 - N_ell2 + N_2)] )/V
    lambda_upper =np.amin([ N_w1 - N_ell1 + N_1, V - (N_w2 - N_ell2 - N_2)] )/V

    n1 = strata[0].sample_size
    n2 = strata[1].sample_size

    n_w1 = strata[0].sample[contest.name][winner]
    n_l1 = strata[0].sample[contest.name][loser]

    V_wl = contest.candidates[winner] - contest.candidates[loser]


    Wn = n_w1; Ln = n_l1; Un = n1-n_w1-n_l1
    assert Wn>=0 and Ln>=0 and Un>=0

    T2 = lambda delta: 2*n2*np.log(1 + V_wl*delta/(2*N_2*GAMMA))
    modulus = lambda delta: 2*Wn*np.log(1 + V_wl*delta) + 2*Ln*np.log(1 + V_wl*delta) + \
            2*Un*np.log(1 + 2*V_wl*delta) + T2(delta)

    while True:
        # TODO: reconcile handling winner/loser pairs with pvalue calculation
        test_lambdas = np.arange(lambda_lower, lambda_upper+stepsize, stepsize)
        if len(test_lambdas) < 5:
            stepsize = (lambda_upper + 1 - lambda_lower)/5
            test_lambdas = np.arange(lambda_lower, lambda_upper+stepsize, stepsize)

        fisher_pvalues = np.empty_like(test_lambdas)
        for i in range(len(test_lambdas)):
            try:
                pvalue1 = np.min([1, strata[0].compute_pvalue(contest, alpha, winner, loser, 1-test_lambdas[i])])
            except:
                # If the sprt throws an error, set its pvalue to 0.
                # This is per the Stark code
                pvalue1 = 0

            pvalue2 = np.min([1, strata[1].compute_pvalue(contest, alpha, winner, loser, test_lambdas[i])])

            pvalues = [pvalue1, pvalue2]
            if np.any(np.array(pvalues)==0):
                fisher_pvalues[i] = 0
            else:
                obs = -2*np.sum(np.log(pvalues))
                fisher_pvalues[i] = 1-sp.stats.chi2.cdf(obs, df=2*len(pvalues))

        pvalue = np.max(fisher_pvalues)
        alloc_lambda = test_lambdas[np.argmax(fisher_pvalues)]

        # If p-value is over the risk limit, then there's no need to refine the
        # maximization. We have a lower bound on the maximum.
        if pvalue > alpha or modulus is None:
            maximized_pvalue = pvalue
            break

        # Use modulus of continuity for the Fisher combination function to check
        # how close this is to the true max
        fisher_fun_obs = sp.stats.chi2.ppf(1-pvalue, df=4)
        fisher_fun_alpha = sp.stats.chi2.ppf(1-alpha, df=4)
        dist = np.abs(fisher_fun_obs - fisher_fun_alpha)
        mod = modulus(stepsize)

        if mod <= dist:
            maximized_pvalue = pvalue
            break
        else:
            # We haven't found a good enough max yet, keep looking
            lambda_lower = alloc_lambda - 2*stepsize
            lambda_upper = alloc_lambda + 2*stepsize

    return maximized_pvalue


def get_sample_size(
        risk_limit: int,
        contest: Contest,
        strata: List[Stratum],
        )-> Dict: # TODO: revisit typing
    """
    Estimate the initial sample sizes for the audit.

    Inputs:
        risk_limit      - the risk limit for this audit
        contest         - the overall contest information
        strata          - A list of strata over which to perform the audit.
                          Note: we assume the ballot polling strata is first
    Outputs:
        sample_sizes    - A dictonary mapping each strata to its respective
                          sample size.
    """

    N1 = strata[0].contest.ballots
    N2 = strata[1].contest.ballots
    n = 0

    for winner,loser in product(contest.winners, contest.losers):
        N_w1 = strata[0].contest.candidates[winner]
        N_l1 = strata[0].contest.candidates[loser]

        N_w2 = strata[1].contest.candidates[winner]
        N_l2 = strata[1].contest.candidates[loser]

        n1 = strata[0].sample_size
        n2 = strata[1].sample_size

        n_ratio = N1/(N1+N2)
        n = n1+n2
        reported_margin = (N_w1+N_w2)-(N_l1+N_l2)
        expected_pvalue = 1

        n1_original = n1
        n2_original = n2


        # Find out what we've observed so far
        discrepancies = compute_discrepancies(contest, winner, loser, strata[1].results, strata[1].sample)
        u2_obs, u1_obs, o1_obs, o2_obs = 0,0,0,0

        # We augment the sample with hypothetical ballots:
        for ballot in discrepancies:
            # If the ballot already showed a discrepancy, account for it
            if ballot in discrepancies:
                e = discrepancies[ballot]["counted_as"]
                if e == -2:
                    u2_obs += 1
                elif e == -1:
                    u1_obs += 1
                elif e == 1:
                    o1_obs += 1
                elif e == 2:
                    o2_obs += 1

        o1_rate, o2_rate, u1_rate, u2_rate = 0, 0, 0, 0
        # Assume o1, o2, u1, u2 rates will be the same as what we observed in sample
        if n1_original != 0:
            o1_rate = o1_obs/n1_original
            o2_rate = o2_obs/n1_original
            u1_rate = u1_obs/n1_original
            u2_rate = u2_obs/n1_original

        def try_n(n):
            n1 = math.ceil(n_ratio * n)
            n2 = int(n - n1)

            if (n1 < n1_original) or (n2 < n2_original):
                return 1

            o1 = math.ceil(o1_rate*(n1-n1_original)) + o1_obs
            o2 = math.ceil(o2_rate*(n1-n1_original)) + o2_obs
            u1 = math.floor(u1_rate*(n1-n1_original)) + u1_obs
            u2 = math.floor(u2_rate*(n1-n1_original)) + u2_obs

            # Because this is a hypothetical sample, we create a
            # corresponding hypothetical stratum
            hyp_sample_size = strata[1].sample_size + n1
            hyp_sample = strata[1].sample

            hyp_o1 = 0
            hyp_o2 = 0
            hyp_u1 = 0
            hyp_u2 = 0

            # We augment the sample with hypothetical ballots:
            for ballot in list(strata[1].results.keys())[:n1]:
                if ballot in hyp_sample:
                    # The ballot has already been sampled, so just increment
                    hyp_sample[ballot]["times_sampled"] += 1

                    # If the ballot already showed a discrepancy, account for it
                    if ballot in discrepancies:
                        e = discrepancies[ballot]["counted_as"]
                        if e == -2:
                            hyp_u2 += 1
                        elif e == -1:
                            hyp_u1 += 1
                        elif e == 1:
                            hyp_o1 += 1
                        elif e == 2:
                            hyp_o2 += 1
                else:
                    # The ballot hasn't been sampled yet, so create a fake
                    # sample.
                    hyp_cvr = strata[1].results[ballot]

                    # If we haven't met our expected discrepancies,
                    # take care of those.
                    if hyp_cvr[contest.name][winner]:
                        # Since the vote was for the winner, we can only create
                        # over statements.
                        if hyp_o2 < o2:
                            hyp_cvr[contest.name][winner] = 0
                            hyp_cvr[contest.name][loser] = 1
                        elif hyp_o1 < o1:
                            hyp_cvr[contest.name][winner] = 0
                            hyp_cvr[contest.name][loser] = 0
                    elif hyp_cvr[contest.name][loser]:
                        # Since the vote was for the loser, we can only create
                        # over statements.
                        if hyp_u2 < u2:
                            hyp_cvr[contest.name][winner] = 1
                            hyp_cvr[contest.name][loser] = 0
                        elif hyp_u1 < u1:
                            hyp_cvr[contest.name][winner] = 0
                            hyp_cvr[contest.name][loser] = 0
                    else:
                        # The vote was for someone else, so we can do anything
                        if hyp_o2 < o2:
                            hyp_cvr[contest.name][winner] = 0
                            hyp_cvr[contest.name][loser] = 1
                        elif hyp_o1 < o1:
                            hyp_cvr[contest.name][winner] = 0
                            hyp_cvr[contest.name][loser] = 0
                        elif hyp_u2 < u2:
                            hyp_cvr[contest.name][winner] = 1
                            hyp_cvr[contest.name][loser] = 0
                        elif hyp_u1 < u1:
                            hyp_cvr[contest.name][winner] = 0
                            hyp_cvr[contest.name][loser] = 0

                    # Add our hypothetical sample to the samples
                    hyp_sample[ballot] = {"cvr": hyp_cvr}

            hyp_cvr_stratum = Stratum(
                strata[1].contest,
                strata[1].math_type,
                strata[1].results,
                hyp_sample,
                hyp_sample_size
            )

            # Set up the no-CVR stratum, assuming the sample looks like the
            # prior round
            hyp_sample_size = strata[0].sample_size
            hyp_sample = strata[0].sample

            cumulative_sample = bravo.compute_cumulative_sample(hyp_sample)

            # Add fake ballots to the hypothetical sample:
            if hyp_sample_size == 0:
                # If no ballots have been sampled, assume the sample is roughly
                # the margin
                hyp_sample['hyp_round'] = {
                    winner: (n2 * strata[0].contest.candidates[winner])/strata[0].contest.ballots,
                    loser: (n2 * strata[0].contest.candidates[loser])/strata[0].contest.ballots,
                }
            else:
                # Otherwise use the sample we've seen so far
                hyp_sample['hyp_round'] = {
                    winner: (n2 * cumulative_sample[winner])/hyp_sample_size,
                    loser: (n2 * cumulative_sample[loser])/hyp_sample_size
                }

            hyp_sample_size = strata[0].sample_size + n2

            hyp_no_cvr_stratum = Stratum(
                strata[0].contest,
                strata[0].math_type,
                strata[0].results,
                hyp_sample,
                hyp_sample_size
            )

            hyp_strata = [hyp_no_cvr_stratum, hyp_cvr_stratum]
            return maximize_fisher_combined_pvalue(risk_limit, contest, hyp_strata, winner, loser)

        # step 1: linear search, increasing n by a factor of 1.1 each time
        while (expected_pvalue > risk_limit) or (expected_pvalue is np.nan):
            n = np.ceil(1.1*n)
            if n > N1+N2:
                n1 = math.ceil(n_ratio * (N1+N2))
                n2 = int(N1 + N2 - n1)
                return (n1, n2)
            if N2 > 0:
                n1 = math.ceil(n_ratio * n)
                n2 = int(n - n1)
                if (N_w2 < int(n2*N_w2/N2) or N_l2 < int(n2*N_l2/N2)):
                    return(N1, N2)
            expected_pvalue = try_n(n)

        # step 2: bisection between n/1.1 and n
        low_n = n/1.1
        high_n = n
        mid_pvalue = 1
        while  (mid_pvalue > risk_limit) or (mid_pvalue < risk_limit_tol*risk_limit) or \
            (expected_pvalue is np.nan):
            mid_n = np.floor((low_n+high_n)/2)
            if (low_n == mid_n) or (high_n == mid_n):
                break
            mid_pvalue = try_n(mid_n)
            if mid_pvalue <= risk_limit:
                high_n = mid_n
            else:
                low_n = mid_n

        n1 = math.ceil(n_ratio * high_n)
        n2 = math.ceil(high_n - n1)


    return (n1, n2)



def compute_risk(risk_limit: int, contest: Contest, strata: List[Stratum]) -> Tuple[float, bool]:
    """
    Computes a risk measurement for a given sample, using fisher's combining
    function to combine pvalue measurements from a ballot polling and ballot
    comparison stratum. Returns the highest measured p-value for all winner-loser
    pairs.
    """
    alpha = Decimal(risk_limit)/100
    assert alpha < 1

    pvalues = []
    for winner,loser in product(contest.winners, contest.losers):
        pvalues.append(maximize_fisher_combined_pvalue(alpha, contest, strata, winner,loser))

    max_p = max(pvalues)

    return max_p, max_p <= alpha




def compute_discrepancies(
    contest: Contest, winner, loser, cvrs: CVRS, sample_cvr: SAMPLE_CVRS
) -> Dict[str, Discrepancy]:
    """
    Iterates through a given sample and returns the discrepancies found.

    Inputs:
        contests       - the contests and results being audited
        winner,loser   - the winner-loser pair to compute discrepancies for
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


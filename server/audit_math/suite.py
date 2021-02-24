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
import json
import csv
import matplotlib.pyplot as plt

from ballot_comparison import ballot_comparison_pvalue
from fishers_combination import  maximize_fisher_combined_pvalue, create_modulus
from suite_sprt import ballot_polling_sprt

from models import AuditMathType
from sampler_contest import Contest, Stratum

def maximize_fisher_combined_pvalue(
	contest: Contest,
	strata: List[Stratum],
    	stepsize=0.05, modulus=None, alpha=0.05) -> float:
    """
    Grid search to find the maximum P-value.
    Find the smallest Fisher's combined statistic for P-values obtained
    by testing two null hypotheses at level alpha using data X=(X1, X2).
    Parameters
    ----------
    stepsize : float
        size of the grid for searching over lambda. Default is 0.05
    modulus : function
        the modulus of continuity of the Fisher's combination function.
        This should be created using `create_modulus`.
        Optional (Default is None), but increases the precision of the grid search.
    alpha : float
        Risk limit. Default is 0.05.
    feasible_lambda_range : array-like
        lower and upper limits to search over lambda.
        Optional, but a smaller interval will speed up the search.

    Returns
    -------
    max_pvalue: float
    """
    assert len(strata)==2

    # find range of possible lambda
    # TODO: fix variables
    V = N_w1 + N_w2 - N_ell1 - N_ell2
    lambda_lower = np.amax([N_w1 - N_ell1 - N_1, V - (N_w2 - N_ell2 + N_2)] )/V
    lambda_upper =np.amin([ N_w1 - N_ell1 + N_1, V - (N_w2 - N_ell2 - N_2)] )/V


    # TODO: fix variables
    T2 = lambda delta: 2*n1*np.log(1 + contest.margin*delta/(2*N1*gamma))
    modulus = lambda delta: 2*Wn*np.log(1 + V_wl*delta) + 2*Ln*np.log(1 + V_wl*delta) + \
            2*Un*np.log(1 + 2*V_wl*delta) + T2(delta)

    while True:
        test_lambdas = np.arange(lambda_lower, lambda_upper+stepsize, stepsize)
        if len(test_lambdas) < 5:
            stepsize = (lambda_upper + 1 - lambda_lower)/5
            test_lambdas = np.arange(lambda_lower, lambda_upper+stepsize, stepsize)

        fisher_pvalues = np.empty_like(test_lambdas)
        for i in range(len(test_lambdas)):
            pvalue1 = np.min([1, strata[0].compute_p_value(alpha, test_lambdas[i])])
            pvalue2 = np.min([1, strata[1].compute_p_value(alpha, 1-test_lambdas[i])])
            fisher_pvalues[i] = fisher_combined_pvalue([pvalue1, pvalue2])

        pvalue = np.max(fisher_pvalues)
        alloc_lambda = test_lambdas[np.argmax(fisher_pvalues)]

        # If p-value is over the risk limit, then there's no need to refine the
        # maximization. We have a lower bound on the maximum.
        if pvalue > alpha or modulus is None:
            return pvalue

        # Use modulus of continuity for the Fisher combination function to check
        # how close this is to the true max
        fisher_fun_obs = scipy.stats.chi2.ppf(1-pvalue, df=4)
        fisher_fun_alpha = scipy.stats.chi2.ppf(1-alpha, df=4)
        dist = np.abs(fisher_fun_obs - fisher_fun_alpha)
        mod = modulus(stepsize)

        if mod <= dist:
            return pvalue
        else:
            # We haven't found a good enough max yet, keep looking
            lambda_lower = alloc_lambda - 2*stepsize
            lambda_upper = alloc_lambda + 2*stepsize

def try_n(n):

    """
    Find expected combined P-value for a total sample size n.
    """
    n1 = math.ceil(n_ratio * n)
    n2 = int(n - n1)

    # Set up the p-value function for the CVR stratum
    if n1 == 0:
        cvr_pvalue = lambda alloc: 1
    else:
        o1 = math.ceil(o1_rate*n1)
        o2 = math.ceil(o2_rate*n1)
        u1 = math.floor(u1_rate*n1)
        u2 = math.floor(u2_rate*n1)
        cvr_pvalue = lambda alloc: ballot_comparison_pvalue(n=n1, \
                        gamma=gamma, o1=o1, u1=u1, o2=o2, u2=u2, \
                        reported_margin=reported_margin, N=N1, \
                        null_lambda=alloc)

    # Set up the p-value function for the no-CVR stratum
    if n2 == 0:
        nocvr_pvalue = lambda alloc: 1
    else:
        sample = [0]*math.ceil(n2*N_l2/N2)+[1]*int(n2*N_w2/N2)
        if len(sample) < n2:
            sample += [np.nan]*(n2 - len(sample))
        nocvr_pvalue = lambda alloc: ballot_polling_sprt(sample=np.array(sample), \
                        popsize=N2, \
                        alpha=risk_limit,\
                        Vw=N_w2, Vl=N_l2, \
                        null_margin=(N_w2-N_l2) - \
                         alloc*reported_margin)['pvalue']

    if N2 == 0:
        n_w2 = 0
        n_l2 = 0
    else:
        n_w2 = int(n2*N_w2/N2)
        n_l2 = int(n2*N_l2/N2)
    bounding_fun = create_modulus(n1=n1, n2=n2,
                                  n_w2=n_w2, \
                                  n_l2=n_l2, \
                                  N1=N1, V_wl=reported_margin, gamma=gamma)
    res = maximize_fisher_combined_pvalue(N_w1=N_w1, N_l1=N_l1, N1=N1, \
                                          N_w2=N_w2, N_l2=N_l2, N2=N2, \
                                          pvalue_funs=(cvr_pvalue, \
                                           nocvr_pvalue), \
                                          stepsize=stepsize, \
                                          modulus=bounding_fun, \
                                          alpha=risk_limit)
    expected_pvalue = res['max_pvalue']
    return expected_pvalue

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
    Outputs:
        sample_sizes    - A dictonary mapping each strata to its respective
                          sample size.


    """

    # These are variables that were originally passed in. Not sure if we need them
    stepsize=0.05
    min_n=5
    risk_limit_tol=0.8
    n_ratio = n_ratio if n_ratio else N1/(N1+N2)
    n = min_n
    assert n > 0, "minimum sample size must be positive"
    assert risk_limit_tol < 1 and risk_limit_tol > 0, "bad risk limit tolerance"



    reported_margin = (N_w1+N_w2)-(N_l1+N_l2)
    expected_pvalue = 1


    # step 1: linear search, doubling n each time
    while (expected_pvalue > risk_limit) or (expected_pvalue is np.nan):
        n = 2*n
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

    # step 2: bisection between n/2 and n
    low_n = n/2
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


def estimate_escalation_n(N_w1, N_w2, N_l1, N_l2, N1, N2, n1, n2, \
                          o1_obs, o2_obs, u1_obs, u2_obs, \
                          n2l_obs, n2w_obs, \
                          o1_rate=0, o2_rate=0, u1_rate=0, u2_rate=0, \
                          n_ratio=None, \
                          risk_limit=0.05,\
                          gamma=1.03905,\
                          stepsize=0.05,\
                          risk_limit_tol=0.8,
                          ):
    """
    Estimate the initial sample sizes for the audit.

    Parameters
    ----------
    N_w1 : int
        votes for the reported winner in the ballot comparison stratum
    N_w2 : int
        votes for the reported winner in the ballot polling stratum
    N_l1 : int
        votes for the reported loser in the ballot comparison stratum
    N_l2 : int
        votes for the reported loser in the ballot polling stratum
    N1 : int
        total number of votes in the ballot comparison stratum
    N2 : int
        total number of votes in the ballot polling stratum
    n1 : int
        size of sample already drawn in the ballot comparison stratum
    n2 : int
        size of sample already drawn in the ballot polling stratum
    o1_obs : int
        observed number of ballots with 1-vote overstatements in the CVR stratum
    o2_obs : int
        observed number of ballots with 2-vote overstatements in the CVR stratum
    u1_obs : int
        observed number of ballots with 1-vote understatements in the CVR
        stratum
    u2_obs : int
        observed number of ballots with 2-vote understatements in the CVR
        stratum
    n2l_obs : int
        observed number of votes for the reported loser in the no-CVR stratum
    n2w_obs : int
        observed number of votes for the reported winner in the no-CVR stratum
    n_ratio : float
        ratio of sample allocated to each stratum.
        If None, allocate sample in proportion to ballots cast in each stratum
    risk_limit : float
        risk limit
    gamma : float
        gamma from Lindeman and Stark (2012)
    stepsize : float
        stepsize for the discrete bounds on Fisher's combining function
    risk_limit_tol : float
        acceptable percentage below the risk limit, between 0 and 1.
        Default is 0.8, meaning the estimated sample size might have
        an expected risk that is 80% of the desired risk limit
    Returns
    -------
    tuple : estimated initial sample sizes in the CVR stratum and no-CVR stratum
    """
    n_ratio = n_ratio if n_ratio else N1/(N1+N2)
    n = n1+n2
    reported_margin = (N_w1+N_w2)-(N_l1+N_l2)
    expected_pvalue = 1

    n1_original = n1
    n2_original = n2
    observed_nocvr_sample = [0]*n2l_obs + [1]*n2w_obs + \
                            [np.nan]*(n2_original-n2l_obs-n2w_obs)

    # Assume o1, o2, u1, u2 rates will be the same as what we observed in sample
    if n1_original != 0:
        o1_rate = o1_obs/n1_original
        o2_rate = o2_obs/n1_original
        u1_rate = u1_obs/n1_original
        u2_rate = u2_obs/n1_original

    if N1 == 0:
        def try_n(n):
            n = int(n)
            expected_new_sample = [0]*math.ceil((n-n2_original)*(n2l_obs/n2_original))+ \
                                  [1]*int((n-n2_original)*(n2w_obs/n2_original))
            totsample = observed_nocvr_sample+expected_new_sample
            if len(totsample) < n:
                totsample += [np.nan]*(n - len(totsample))
            totsample = np.array(totsample)
            n_w2 = np.sum(totsample == 1)
            n_l2 = np.sum(totsample == 0)

            expected_pvalue = ballot_polling_sprt( \
                            sample=totsample,\
                            popsize=N2, \
                            alpha=risk_limit,\
                            Vw=N_w2, Vl=N_l2, \
                            null_margin=0)['pvalue']
            return expected_pvalue

    elif N2 == 0:
        def try_n(n):
            o1 = math.ceil(o1_rate*(n-n1_original)) + o1_obs
            o2 = math.ceil(o2_rate*(n-n1_original)) + o2_obs
            u1 = math.floor(u1_rate*(n-n1_original)) + u1_obs
            u2 = math.floor(u2_rate*(n-n1_original)) + u2_obs
            expected_pvalue = ballot_comparison_pvalue(n=n,\
                                    gamma=1.03905, o1=o1, \
                                    u1=u1, o2=o2, u2=u2, \
                                    reported_margin=reported_margin, N=N1, \
                                    null_lambda=1)
            return expected_pvalue

    else:
        def try_n(n):
            n1 = math.ceil(n_ratio * n)
            n2 = int(n - n1)

            if (n1 < n1_original) or (n2 < n2_original):
                return 1

            # Set up the p-value function for the CVR stratum
            if n1 == 0:
                cvr_pvalue = lambda alloc: 1
            else:
                o1 = math.ceil(o1_rate*(n1-n1_original)) + o1_obs
                o2 = math.ceil(o2_rate*(n1-n1_original)) + o2_obs
                u1 = math.floor(u1_rate*(n1-n1_original)) + u1_obs
                u2 = math.floor(u2_rate*(n1-n1_original)) + u2_obs
                cvr_pvalue = lambda alloc: ballot_comparison_pvalue(n=n1,\
                                    gamma=1.03905, o1=o1, \
                                    u1=u1, o2=o2, u2=u2, \
                                    reported_margin=reported_margin, N=N1, \
                                    null_lambda=alloc)

            # Set up the p-value function for the no-CVR stratum
            if n2 == 0:
                nocvr_pvalue = lambda alloc: 1
                n_w2 = 0
                n_l2 = 0
            else:
                expected_new_sample = [0]*math.ceil((n2-n2_original)*(n2l_obs/n2_original))+ \
                                      [1]*int((n2-n2_original)*(n2w_obs/n2_original))
                totsample = observed_nocvr_sample+expected_new_sample
                if len(totsample) < n2:
                    totsample += [np.nan]*(n2 - len(totsample))
                totsample = np.array(totsample)
                n_w2 = np.sum(totsample == 1)
                n_l2 = np.sum(totsample == 0)

                nocvr_pvalue = lambda alloc: ballot_polling_sprt( \
                                sample=totsample,\
                                popsize=N2, \
                                alpha=risk_limit,\
                                Vw=N_w2, Vl=N_l2, \
                                null_margin=(N_w2-N_l2) - \
                                 alloc*reported_margin)['pvalue']

            # Compute combined p-value
            bounding_fun = create_modulus(n1=n1, n2=n2,
                                          n_w2=n_w2, \
                                          n_l2=n_l2, \
                                          N1=N1, V_wl=reported_margin, gamma=gamma)
            res = maximize_fisher_combined_pvalue(N_w1=N_w1, N_l1=N_l1, N1=N1, \
                                                  N_w2=N_w2, N_l2=N_l2, N2=N2, \
                                                  pvalue_funs=(cvr_pvalue,\
                                                    nocvr_pvalue), \
                                                  stepsize=stepsize, \
                                                  modulus=bounding_fun, \
                                                  alpha=risk_limit)
            expected_pvalue = res['max_pvalue']
            return expected_pvalue

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


################################################################################
############################## Do the audit! ###################################
################################################################################

def audit_contest(candidates, winners, losers, stratum_sizes,\
                  n1, n2, o1_obs, o2_obs, u1_obs, u2_obs, observed_poll, \
                  risk_limit, gamma, stepsize):
    """
    Use SUITE to calculate risk of each (winner, loser) pair
    given the observed samples in the CVR and no-CVR strata.

    Parameters
    ----------
    candidates : dict
        OrderedDict with candidate names as keys and
        [CVR votes, no-CVR votes, total votes] as values
    winners : list
        names of winners
    losers : list
        names of losers
    stratum_sizes : list
        list with total number of votes in the CVR and no-CVR strata
    n1 : int
        size of sample already drawn in the ballot comparison stratum
    n2 : int
        size of sample already drawn in the ballot polling stratum
    o1_obs : int
        observed number of ballots with 1-vote overstatements in the CVR stratum
    o2_obs : int
        observed number of ballots with 2-vote overstatements in the CVR stratum
    u1_obs : int
        observed number of ballots with 1-vote understatements in the CVR
        stratum
    u2_obs : int
        observed number of ballots with 2-vote understatements in the CVR
        stratum
    observed_poll : dict
        Dict with candidate names as keys and number of votes in the no-CVR
        stratum sample as values
    risk_limit : float
        risk limit
    gamma : float
        gamma from Lindeman and Stark (2012)
    stepsize : float
        stepsize for the discrete bounds on Fisher's combining function
    Returns
    -------
    dict : attained risk for each (winner, loser) pair in the contest
    """
    audit_pvalues = {}

    for k in product(winners, losers):
        N_w1 = candidates[k[0]][0]
        N_w2 = candidates[k[0]][1]
        N_l1 = candidates[k[1]][0]
        N_l2 = candidates[k[1]][1]
        n2w = observed_poll[k[0]]
        n2l = observed_poll[k[1]]
        reported_margin = (N_w1+N_w2)-(N_l1+N_l2)

        if stratum_sizes[1] == 0:
            audit_pvalues[k] = ballot_comparison_pvalue(n=n1, \
                        gamma=gamma, \
                        o1=o1_obs, u1=u1_obs, o2=o2_obs, u2=u2_obs, \
                        reported_margin=reported_margin, \
                        N=stratum_sizes[0], \
                        null_lambda=1)

        elif stratum_sizes[0] == 0:
            sam = np.array([0]*n2l+[1]*n2w+[np.nan]*(n2-n2w-n2l))
            audit_pvalues[k] = ballot_polling_sprt(\
                                sample=sam, \
                                popsize=stratum_sizes[1], \
                                alpha=risk_limit, \
                                Vw=N_w2, Vl=N_l2, \
                                null_margin=0)['pvalue']
        else:
            if n1 == 0:
                cvr_pvalue = lambda alloc: 1
            else:
                cvr_pvalue = lambda alloc: ballot_comparison_pvalue(n=n1, \
                            gamma=gamma, \
                            o1=o1_obs, u1=u1_obs, o2=o2_obs, u2=u2_obs, \
                            reported_margin=reported_margin, \
                            N=stratum_sizes[0], \
                            null_lambda=alloc)

            if n2 == 0:
                nocvr_pvalue = lambda alloc: 1
            else:
                sam = np.array([0]*n2l+[1]*n2w+[np.nan]*(n2-n2w-n2l))
                nocvr_pvalue = lambda alloc: ballot_polling_sprt(\
                                    sample=sam, \
                                    popsize=stratum_sizes[1], \
                                    alpha=risk_limit, \
                                    Vw=N_w2, Vl=N_l2, \
                                    null_margin=(N_w2-N_l2) - \
                                      alloc*reported_margin)['pvalue']
            bounding_fun = create_modulus(n1=n1, n2=n2, \
                                          n_w2=n2w, \
                                          n_l2=n2l, \
                                          N1=stratum_sizes[0], \
                                          V_wl=reported_margin, gamma=gamma)
            res = maximize_fisher_combined_pvalue(N_w1=N_w1, N_l1=N_l1,\
                             N1=stratum_sizes[0], \
                             N_w2=N_w2, N_l2=N_l2, \
                             N2=stratum_sizes[1], \
                             pvalue_funs=(cvr_pvalue, nocvr_pvalue), \
                             stepsize=stepsize, \
                             modulus=bounding_fun, \
                             alpha=risk_limit)
            audit_pvalues[k] = res['max_pvalue']

    return audit_pvalues


################################################################################
############################## Unit testing ####################################
################################################################################

def test_initial_n():
    """
    Assume N1 = N2 = 500, n1 = n2 \equiv n,
    and the margins V1 = V2 = V/2 are identical in each stratum.
    w got 60% of the vote and l got 40%.
    It's known that there are no invalid ballots or votes for other candidates.
    Assume there are no errors in the comparison stratum and the sample
    proportions in the polling stratum are 60% and 40%.

    In the polling stratum,
        $$c(\lambda) = V/2 - (1-\lambda)V = 200\lambda - 100$$
    and
        $$N_w(\lambda) = (N2 + c(\lambda))/2 = 200 + 100\lambda.$$
    Therefore the Fisher combination function is
        $$ \chi(\lambda) = -2\[ \sum_{i=1}^{np_w - 1} \log(200+100\lambda - i)
            - \sum_{i=1}^{np_w - 1} \log(300 - i) +
            \sum_{i=1}^{np_\ell - 1} \log(300-100\lambda - i)
            - \sum_{i=1}^{np_\ell - 1} \log(200 - i)
            + n\log( 1 - \frac{\lambda}{5\gamma} )\] $$
    """

    chi_5percent = scipy.stats.chi2.ppf(1-0.05, df=4)
    chi_10percent = scipy.stats.chi2.ppf(1-0.10, df=4)

    # sample sizes: n = 50 in each stratum. Not sufficient.
    chi50 = lambda lam: -2*( np.sum(np.log(200 + 100*lam - np.arange(30))) - \
        np.sum(np.log(300 - np.arange(30))) + np.sum(np.log(300 - 100*lam - \
        np.arange(20))) - np.sum(np.log(200 - np.arange(20))) + \
        50*np.log(1 - lam/(5*gamma)))

    # Valid lambda range is (-2, 3)
    approx_chisq_min = np.nanmin(list(map(chi50, np.arange(-2,3,0.05))))
    np.testing.assert_array_less(approx_chisq_min, chi_5percent)

    # sample sizes: n = 70 in each stratum. Sufficient.
    chi70 = lambda lam: -2*( np.sum(np.log(200 + 100*lam - np.arange(42))) - \
        np.sum(np.log(300 - np.arange(42))) + np.sum(np.log(300 - 100*lam - \
        np.arange(28))) - np.sum(np.log(200 - np.arange(28))) + \
        70*np.log(1 - lam/(5*gamma)))
    approx_chisq_min = np.nanmin(list(map(chi70, np.arange(-2,3,0.05))))
    np.testing.assert_array_less(chi_10percent, approx_chisq_min)
    np.testing.assert_array_less(chi_5percent, approx_chisq_min)

    n = estimate_n(N_w1 = 300, N_w2 = 300, N_l1 = 200, N_l2 = 200,\
           N1 = 500, N2 = 500, o1_rate = 0, o2_rate = 0,\
           u1_rate = 0, u2_rate = 0, n_ratio = 0.5,
           risk_limit = 0.05, gamma = 1.03905)
    np.testing.assert_equal(n[0] <= 70 and n[0] > 30, True)
    if (n[0]+n[1]) % 2 == 1:
        np.testing.assert_equal(n[0], n[1]+1)
    else:
        np.testing.assert_equal(n[0], n[1])

    # sample sizes: n = 55 in each stratum. Should be sufficient.
    chi55 = lambda lam: -2*( np.sum(np.log(200 + 100*lam - np.arange(33))) - \
        np.sum(np.log(300 - np.arange(33))) + np.sum(np.log(300 - 100*lam - \
        np.arange(22))) - np.sum(np.log(200 - np.arange(22))) + \
        55*np.log(1 - lam/(5*gamma)))
    approx_chisq_min = np.nanmin(list(map(chi55, np.arange(-2,3,0.05))))
    np.testing.assert_array_less(chi_10percent, approx_chisq_min)
    np.testing.assert_array_less(chi_5percent, approx_chisq_min)


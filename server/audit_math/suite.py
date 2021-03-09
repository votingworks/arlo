# pylint: disable=invalid-name
"""
This library allows the performing of a stratified audit. For now, it works with
ballot polling and ballot comparison, plurality winner contests. The method
is SUITE, described by Ottoboni, Stark, Lindeman, and McBurnett here:
https://arxiv.org/abs/1809.04235

This code borrows heavily from code already written by Stark and Ottoboni here:
https://github.com/pbstark/CORLA18


"""
from __future__ import print_function, division

from itertools import product
import math
from typing import Optional, Tuple, Dict
from decimal import Decimal
import numpy as np
import scipy as sp


from .sampler_contest import Contest, CVRS
from . import bravo


GAMMA = 1.03905  # This GAMMA is used in Stark's tool, AGI, and CORLA


class BallotPollingStratum:
    """
    A class encapsulating a stratum of ballots in an election. Each stratum is its
    own contest object, with its own margin. Strata, along with the overall
    contest object, are passed to the SUITE module when perfoming mixed-strata
    audits.
    """

    SAMPLE_RESULTS = Optional[Dict[str, Dict[str, int]]]  # ballot polling

    contest: Contest
    sample: SAMPLE_RESULTS
    sample_size: int

    def __init__(
        self, contest: Contest, sample_results: SAMPLE_RESULTS, sample_size: int,
    ):
        self.contest = contest
        self.sample = sample_results
        self.sample_size = sample_size

    def compute_pvalue(self, contest, winner, loser, null_lambda) -> float:
        """
        Compute a p-value for a winner-loser pair for this strata based on its math type.
        """

        reported_margin = contest.candidates[winner] - contest.candidates[loser]
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

        null_margin = (v_w - v_l) - null_lambda * reported_margin

        assert (
            v_w >= n_w and v_l >= n_l and v_u >= n_u
        ), "Alternative hypothesis isn't consistent with the sample"

        alt_logLR = (
            np.sum(np.log(v_w - np.arange(n_w)))
            + np.sum(np.log(v_l - np.arange(n_l)))
            + np.sum(np.log(v_u - np.arange(n_u)))
        )

        null_logLR = (
            lambda Nw: (n_w > 0) * np.sum(np.log(Nw - np.arange(n_w)))
            + (n_l > 0) * np.sum(np.log(Nw - null_margin - np.arange(n_l)))
            + (n_u > 0)
            * np.sum(np.log(popsize - 2 * Nw + null_margin - np.arange(n_u)))
        )

        upper_n_w_limit = int((popsize - n_u + null_margin) / 2)
        lower_n_w_limit = np.max([n_w, n_l + null_margin])

        # For extremely small or large null_margins, the limits do not
        # make sense with the sample values.
        if upper_n_w_limit < n_w or (upper_n_w_limit - null_margin) < n_l:
            raise ValueError("Null is impossible, given the sample")

        if lower_n_w_limit > upper_n_w_limit:
            lower_n_w_limit, upper_n_w_limit = upper_n_w_limit, lower_n_w_limit

        LR_derivative = (
            lambda Nw: np.sum([1 / (Nw - i) for i in range(n_w)])
            + np.sum([1 / (Nw - null_margin - i) for i in range(n_l)])
            - 2 * np.sum([1 / (popsize - 2 * Nw + null_margin - i) for i in range(n_u)])
        )

        # Sometimes the upper_n_w_limit is too extreme, causing illegal 0s.
        # Check and change the limit when that occurs.
        if np.isinf(null_logLR(upper_n_w_limit)) or np.isinf(
            LR_derivative(upper_n_w_limit)
        ):
            upper_n_w_limit -= 1

        # Check if the maximum occurs at an endpoint: deriv has no sign change
        if LR_derivative(upper_n_w_limit) * LR_derivative(lower_n_w_limit) > 0:
            nuisance_param = (
                upper_n_w_limit
                if null_logLR(upper_n_w_limit) >= null_logLR(lower_n_w_limit)
                else lower_n_w_limit
            )
        # Otherwise, find the (unique) root of the derivative of the log likelihood ratio
        else:
            nuisance_param = sp.optimize.brentq(
                LR_derivative, lower_n_w_limit, upper_n_w_limit
            )
        logLR = alt_logLR - null_logLR(nuisance_param)
        LR = np.exp(logLR)

        return 1.0 / LR if 1.0 / LR < 1 else 1.0


class BallotComparisonStratum:
    """
    A class encapsulating a stratum of ballots in an election. Each stratum is its
    own contest object, with its own margin. Strata, along with the overall
    contest object, are passed to the SUITE module when perfoming mixed-strata
    audits.
    """

    RESULTS = CVRS

    contest: Contest
    results: RESULTS
    sample_size: int

    def __init__(
        self,
        contest: Contest,
        results: RESULTS,
        misstatements: Dict[str, int],
        sample_size: int,
    ):
        self.contest = contest
        self.results = results
        self.misstatements = misstatements
        self.sample_size = sample_size

    def compute_pvalue(self, contest, winner, loser, null_lambda) -> float:

        """
        Compute a p-value for a winner-loser pair for this strata based on its math type.
        """

        reported_margin = contest.candidates[winner] - contest.candidates[loser]
        o1, o2, u1, u2 = (
            self.misstatements["o1"],
            self.misstatements["o2"],
            self.misstatements["u1"],
            self.misstatements["u2"],
        )

        U_s = 2 * self.contest.ballots / reported_margin
        log_pvalue = (
            self.sample_size * np.log(1 - null_lambda / (GAMMA * U_s))
            - o1 * np.log(1 - 1 / (2 * GAMMA))
            - o2 * np.log(1 - 1 / GAMMA)
            - u1 * np.log(1 + 1 / (2 * GAMMA))
            - u2 * np.log(1 + 1 / GAMMA)
        )
        pvalue = np.exp(log_pvalue)
        return np.min([pvalue, 1])


def get_misstatements(contest, reported_cvr, sample, winner, loser):
    o1, o2, u1, u2 = 0, 0, 0, 0
    for ballot in reported_cvr:
        if ballot not in sample:
            continue

        v_w = reported_cvr[ballot][contest.name][winner]
        v_l = reported_cvr[ballot][contest.name][loser]

        a_w = sample[ballot]["cvr"][contest.name][winner]
        a_l = sample[ballot]["cvr"][contest.name][loser]

        e = (v_w - a_w) - (v_l - a_l)

        if e == -2:
            u2 += 1
        elif e == -1:
            u1 += 1
        elif e == 1:
            o1 += 1
        elif e == 2:
            o2 += 1

    return u2, u2, o1, o2


def maximize_fisher_combined_pvalue(
    alpha: Decimal,
    contest: Contest,
    bp_stratum: BallotPollingStratum,
    cvr_stratum: BallotComparisonStratum,
    winner: str,
    loser: str,
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
    stepsize = 0.05

    maximized_pvalue = 0.0
    # find range of possible lambda
    N_w1 = bp_stratum.contest.candidates[winner]
    N_w2 = cvr_stratum.contest.candidates[winner]

    N_ell1 = bp_stratum.contest.candidates[loser]
    N_ell2 = cvr_stratum.contest.candidates[loser]

    N_1 = bp_stratum.contest.ballots
    N_2 = cvr_stratum.contest.ballots

    V = N_w1 + N_w2 - N_ell1 - N_ell2
    lambda_lower = np.amax([N_w1 - N_ell1 - N_1, V - (N_w2 - N_ell2 + N_2)]) / V
    lambda_upper = np.amin([N_w1 - N_ell1 + N_1, V - (N_w2 - N_ell2 - N_2)]) / V

    n1 = bp_stratum.sample_size
    n2 = cvr_stratum.sample_size

    n_w1 = bp_stratum.sample[contest.name][winner]
    n_l1 = bp_stratum.sample[contest.name][loser]

    V_wl = contest.candidates[winner] - contest.candidates[loser]

    Wn = n_w1
    Ln = n_l1
    Un = n1 - n_w1 - n_l1
    assert Wn >= 0 and Ln >= 0 and Un >= 0

    T2 = lambda delta: 2 * n2 * np.log(1 + V_wl * delta / (2 * N_2 * GAMMA))
    modulus = (
        lambda delta: 2 * Wn * np.log(1 + V_wl * delta)
        + 2 * Ln * np.log(1 + V_wl * delta)
        + 2 * Un * np.log(1 + 2 * V_wl * delta)
        + T2(delta)
    )

    while True:
        test_lambdas = np.arange(lambda_lower, lambda_upper + stepsize, stepsize)
        if len(test_lambdas) < 5:
            stepsize = (lambda_upper + 1 - lambda_lower) / 5
            test_lambdas = np.arange(lambda_lower, lambda_upper + stepsize, stepsize)

        fisher_pvalues = np.empty_like(test_lambdas)
        for i, test_lambda in enumerate(test_lambdas):
            try:
                pvalue1 = np.min(
                    [
                        1,
                        bp_stratum.compute_pvalue(
                            contest, winner, loser, 1 - test_lambda
                        ),
                    ]
                )
            except ValueError:
                # If the sprt throws an error, set its pvalue to 0.
                # This is per the Stark code
                pvalue1 = 0

            pvalue2 = np.min(
                [1, cvr_stratum.compute_pvalue(contest, winner, loser, test_lambda)]
            )

            pvalues = [pvalue1, pvalue2]
            if np.any(np.array(pvalues) == 0):
                fisher_pvalues[i] = 0
            else:
                obs = -2 * np.sum(np.log(pvalues))
                fisher_pvalues[i] = 1 - sp.stats.chi2.cdf(obs, df=2 * len(pvalues))

        pvalue = np.max(fisher_pvalues)
        alloc_lambda = test_lambdas[np.argmax(fisher_pvalues)]

        # If p-value is over the risk limit, then there's no need to refine the
        # maximization. We have a lower bound on the maximum.
        if pvalue > alpha or modulus is None:
            maximized_pvalue = pvalue
            break

        # Use modulus of continuity for the Fisher combination function to check
        # how close this is to the true max
        fisher_fun_obs = sp.stats.chi2.ppf(1 - pvalue, df=4)
        fisher_fun_alpha = sp.stats.chi2.ppf(1 - alpha, df=4)
        dist = np.abs(fisher_fun_obs - fisher_fun_alpha)
        mod = modulus(stepsize)

        if mod <= dist:
            maximized_pvalue = pvalue
            break

        # We haven't found a good enough max yet, keep looking
        lambda_lower = alloc_lambda - 2 * stepsize
        lambda_upper = alloc_lambda + 2 * stepsize

    return maximized_pvalue


def try_n(n, risk_limit, contest, winner, loser, bp_stratum, cvr_stratum, n_ratio):

    n1_original = cvr_stratum.sample_size
    n2_original = bp_stratum.sample_size

    o1_rate, o2_rate, u1_rate, u2_rate = 0, 0, 0, 0
    # Assume o1, o2, u1, u2 rates will be the same as what we observed in sample
    if n1_original != 0:
        o1_rate = cvr_stratum.misstatements["o1"] / n1_original
        o2_rate = cvr_stratum.misstatements["o2"] / n1_original
        u1_rate = cvr_stratum.misstatements["u1"] / n1_original
        u2_rate = cvr_stratum.misstatements["u2"] / n1_original

    n1 = math.ceil(n_ratio * n)
    n2 = int(n - n1)

    if (n1 < n1_original) or (n2 < n2_original):
        return 1

    o1 = math.ceil(o1_rate * (n1 - n1_original)) + cvr_stratum.misstatements["o1"]
    o2 = math.ceil(o2_rate * (n1 - n1_original)) + cvr_stratum.misstatements["o2"]
    u1 = math.floor(u1_rate * (n1 - n1_original)) + cvr_stratum.misstatements["u1"]
    u2 = math.floor(u2_rate * (n1 - n1_original)) + cvr_stratum.misstatements["u2"]

    # Because this is a hypothetical sample, we create a
    # corresponding hypothetical stratum
    hyp_sample_size = cvr_stratum.sample_size + n1

    hyp_misstatements = {
        "o1": o1 * (1 + n1),
        "o2": o2 * (1 + n1),
        "u1": u1 * (1 + n1),
        "u2": u2 * (1 + n1),
    }

    hyp_cvr_stratum = BallotComparisonStratum(
        cvr_stratum.contest, cvr_stratum.results, hyp_misstatements, hyp_sample_size,
    )

    # Set up the no-CVR stratum, assuming the sample looks like the
    # prior round
    hyp_sample_size = bp_stratum.sample_size
    hyp_sample = bp_stratum.sample

    cumulative_sample = bravo.compute_cumulative_sample(hyp_sample)

    # Add fake ballots to the hypothetical sample:
    if hyp_sample_size == 0:
        # If no ballots have been sampled, assume the sample is roughly
        # the margin
        hyp_sample["hyp_round"] = {
            winner: min(
                math.ceil(
                    (n2 * bp_stratum.contest.candidates[winner])
                    / bp_stratum.contest.ballots
                ),
                bp_stratum.contest.candidates[winner],
            ),
            loser: min(
                math.ceil(
                    (n2 * bp_stratum.contest.candidates[loser])
                    / bp_stratum.contest.ballots
                ),
                bp_stratum.contest.candidates[loser],
            ),
        }
    else:
        # Otherwise use the sample we've seen so far
        hyp_sample["hyp_round"] = {
            winner: min(
                math.ceil((n2 * cumulative_sample[winner]) / hyp_sample_size),
                bp_stratum.contest.candidates[winner],
            ),
            loser: min(
                math.ceil((n2 * cumulative_sample[loser]) / hyp_sample_size),
                bp_stratum.contest.candidates[loser],
            ),
        }
    hyp_sample_size += n2
    hyp_sample_size = min(bp_stratum.contest.ballots, hyp_sample_size)

    hyp_no_cvr_stratum = BallotPollingStratum(
        bp_stratum.contest, hyp_sample, hyp_sample_size
    )

    return maximize_fisher_combined_pvalue(
        risk_limit, contest, hyp_no_cvr_stratum, hyp_cvr_stratum, winner, loser
    )


def get_sample_size(
    risk_limit: int,
    contest: Contest,
    bp_stratum: BallotPollingStratum,
    cvr_stratum: BallotComparisonStratum,
) -> Dict:  # TODO: revisit typing
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

    N1 = bp_stratum.contest.ballots
    N2 = cvr_stratum.contest.ballots

    for winner, loser in product(contest.winners, contest.losers):
        N_w2 = cvr_stratum.contest.candidates[winner]
        N_l2 = cvr_stratum.contest.candidates[loser]

        n1 = bp_stratum.sample_size
        n2 = cvr_stratum.sample_size

        n_ratio = N1 / (N1 + N2)
        n = n1 + n2

        n = max(n, 1)  # make sure n is never zero
        expected_pvalue = 1

        # step 1: linear search, increasing n by a factor of 1.1 each time
        while (expected_pvalue > risk_limit) or (expected_pvalue is np.nan):
            n = np.ceil(1.1 * n)
            if n > N1 + N2:
                n1 = math.ceil(n_ratio * (N1 + N2))
                n2 = int(N1 + N2 - n1)
                return (n1, n2)
            if N2 > 0:
                n1 = math.ceil(n_ratio * n)
                n2 = int(n - n1)
                if N_w2 < int(n2 * N_w2 / N2) or N_l2 < int(n2 * N_l2 / N2):
                    return (N1, N2)
            expected_pvalue = try_n(
                n, risk_limit, contest, winner, loser, bp_stratum, cvr_stratum, n_ratio
            )

        # step 2: bisection between n/1.1 and n
        low_n = n / 1.1
        high_n = n
        mid_pvalue = 1
        # TODO: do we need this tolerance?
        # risk_limit_tol = 0.8
        while (mid_pvalue > risk_limit) or (expected_pvalue is np.nan):
            # while  (mid_pvalue > risk_limit) or (mid_pvalue < risk_limit_tol*risk_limit) or \
            #    (expected_pvalue is np.nan):
            mid_n = np.floor((low_n + high_n) / 2)
            if mid_n in [low_n, high_n]:
                break
            mid_pvalue = try_n(
                mid_n,
                risk_limit,
                contest,
                winner,
                loser,
                bp_stratum,
                cvr_stratum,
                n_ratio,
            )
            if mid_pvalue <= risk_limit:
                high_n = mid_n
            else:
                low_n = mid_n

        n1 = math.ceil(n_ratio * high_n)
        n2 = math.ceil(high_n - n1)

    return (n1, n2)


def compute_risk(
    risk_limit: int, contest: Contest, bp_stratum, cvr_stratum
) -> Tuple[float, bool]:
    """
    Computes a risk measurement for a given sample, using fisher's combining
    function to combine pvalue measurements from a ballot polling and ballot
    comparison stratum. Returns the highest measured p-value for all winner-loser
    pairs.
    """
    alpha = Decimal(risk_limit) / 100
    assert alpha < 1

    pvalues = []
    for winner, loser in product(contest.winners, contest.losers):
        pvalues.append(
            maximize_fisher_combined_pvalue(
                alpha, contest, bp_stratum, cvr_stratum, winner, loser
            )
        )

    max_p = max(pvalues)

    return max_p, max_p <= alpha

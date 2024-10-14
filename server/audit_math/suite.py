# pylint: disable=invalid-name
"""
This library allows the performing of a stratified audit. For now, it works with
ballot polling and ballot comparison, plurality winner contests. The method
is SUITE, described by Ottoboni, Stark, Lindeman, and McBurnett here:
https://arxiv.org/abs/1809.04235

This code borrows heavily from code already written by Stark and Ottoboni here:
https://github.com/pbstark/CORLA18
"""
from itertools import product
import math
from typing import Tuple, Dict, TypedDict, NamedTuple, List
from collections import Counter

from decimal import Decimal
import numpy as np
import scipy as sp


from .sampler_contest import Contest, CVRS, SAMPLECVRS
from . import bravo, supersimple


class HybridPair(NamedTuple):
    non_cvr: int
    cvr: int


GAMMA = 1.03905  # This GAMMA is used in Stark's tool, AGI, and CORLA
MIN_SAMPLE_SIZE = 5  # The smallest sample size we want to take


class BallotPollingStratum:
    """
    A class encapsulating a stratum of ballots in an election. Each stratum is its
    own contest object, with its own margin. Strata, along with the overall
    contest object, are passed to the SUITE module when perfoming mixed-strata
    audits.
    """

    SAMPLE_RESULTS = Dict[str, Dict[str, int]]  # ballot polling

    num_ballots: int
    vote_totals: Dict[str, int]
    sample: SAMPLE_RESULTS
    sample_size: int

    def __init__(
        self,
        num_ballots: int,
        vote_totals: Dict[str, int],
        sample_results: SAMPLE_RESULTS,
        sample_size: int,
    ):
        """
        initialize this stratum.

        Inputs:
            num_ballots: the total number of ballots cast in this stratum
            vote_totals: the per-candidate vote totals for this stratum, of the form
                    {
                        cand1: 700,
                        cand2: 200,
                        ...
                    }
            sample_results : the vote totals for this stratum in the sample so far, by round. E.g.,
                    {
                        "round1" : {
                            "winner1": 10,
                            "winner2": 7,
                            "loser1": 5,
                            "loser2": 2,
                            ...
                        },
                        "round2": {...},
                        ...
                    }
            sample_size: the number of ballots sampled so far
        """
        self.num_ballots = num_ballots
        self.vote_totals = vote_totals
        self.sample = sample_results
        self.sample_size = sample_size

    def compute_pvalue(
        self, reported_margin: int, winner: str, loser: str, null_lambda: float
    ) -> float:
        """
        Compute a p-value for a winner-loser pair for this stratum.


        Inputs:
            reported_margin: the total margin, in votes, between the winner and loser across all strata
            winner: the name of the winner
            loser: the name of the loser
            null_lambda: the null hypothesis lambda value from which we derive a null margin

        Outputs:
            pvalue: the pvalue from testing the hypothesis that null margin is not the acual margin
        """

        if self.sample_size == 0 or reported_margin == 0:
            return 1.0

        sample = bravo.compute_cumulative_sample(self.sample)
        n_w = sample[winner]
        n_l = sample[loser]
        n_u = self.sample_size - n_w - n_l

        v_w = self.vote_totals[winner]
        v_l = self.vote_totals[loser]
        v_u = self.num_ballots - v_w - v_l

        null_margin = (v_w - v_l) - null_lambda * reported_margin

        if not (v_w >= n_w and v_l >= n_l and v_u >= n_u):
            return 1.0

        alt_logLR = (
            np.sum(np.log(v_w - np.arange(n_w)))
            + np.sum(np.log(v_l - np.arange(n_l)))
            + np.sum(np.log(v_u - np.arange(n_u)))
        )

        def null_logLR(Nw):
            return (
                (n_w > 0) * np.sum(np.log(Nw - np.arange(n_w)))
                + (n_l > 0) * np.sum(np.log(Nw - null_margin - np.arange(n_l)))
                + (n_u > 0)
                * np.sum(
                    np.log(self.num_ballots - 2 * Nw + null_margin - np.arange(n_u))
                )
            )

        upper_n_w_limit = (self.num_ballots - n_u + null_margin) / 2.0
        lower_n_w_limit = np.max([n_w, n_l + null_margin])

        # For extremely small or large null_margins, the limits do not
        # make sense with the sample values.
        if upper_n_w_limit < n_w or (upper_n_w_limit - null_margin) < n_l:
            return 0

        def LR_derivative(Nw):
            return (
                np.sum([1 / (Nw - i) for i in range(n_w)])
                + np.sum([1 / (Nw - null_margin - i) for i in range(n_l)])
                - 2
                * np.sum(
                    [
                        1 / (self.num_ballots - 2 * Nw + null_margin - i)
                        for i in range(n_u)
                    ]
                )
            )

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
        LR = float(np.exp(logLR))  # This value is always a float, but np.exp
        # can return a vector. casting for the typechecker.
        # Note if this value overflows, the p-value becomes 0.
        return min(1.0 / LR, 1.0)


class MisstatementCounts(TypedDict):
    o1: int
    o2: int
    u1: int
    u2: int


# { (winner, loser): MistatementCounts }
MISSTATEMENTS = Dict[Tuple[str, str], MisstatementCounts]


class BallotComparisonStratum:
    """
    A class encapsulating a stratum of ballots in an election. Each stratum is its
    own contest object, with its own margin. Strata, along with the overall
    contest object, are passed to the SUITE module when perfoming mixed-strata
    audits.
    """

    num_ballots: int
    vote_totals: Dict[str, int]
    misstatements: MISSTATEMENTS
    sample_size: int

    def __init__(
        self,
        num_ballots: int,
        vote_totals: Dict[str, int],
        misstatements: MISSTATEMENTS,
        sample_size: int,
    ):
        """
        Initializes the ballot comparison stratum.

        Inputs:
            contest: contest information for this stratum, including candidate
                     vote totals and stratum size
            results: The CVRs for this stratum.
            misstatements: All of the misstatements observed so far, by winner-loser pair. E.g.,
                    {
                        (winner1, loser1): {"o1": 0, "o2": 0, "u1": 0, "u2": 0},
                        (winner1, loser2): ...,
                        ...,
                        (winner2, loser1): ...
                    }
            sample_size: the number of ballots sampled so far
        """

        self.num_ballots = num_ballots
        self.vote_totals = vote_totals
        self.misstatements = misstatements
        self.sample_size = sample_size

    def compute_pvalue(self, reported_margin, winner, loser, null_lambda) -> float:
        """
        Compute a p-value for a winner-loser pair for this strata based on its math type.

        Inputs:
            reported_margin: the alternative hypothesis margin, in ballots
            winner, loser: the winner-loser pair to evaluate the hypothesis on
            null_lambda: the Fisher's combining lambda for the null hypothesis.

        Outputs:
            pvalue - the pvalue for the hypothesis given the null_lambda
        """

        if self.sample_size == 0 or reported_margin == 0:
            return 1.0

        if self.sample_size == self.num_ballots:
            return 0.0

        o1, o2, u1, u2 = (
            self.misstatements[(winner, loser)]["o1"],
            self.misstatements[(winner, loser)]["o2"],
            self.misstatements[(winner, loser)]["u1"],
            self.misstatements[(winner, loser)]["u2"],
        )

        U_s = Decimal(2 * self.num_ballots / reported_margin)
        gamma = Decimal(GAMMA)
        multiplier = 1 - Decimal(null_lambda) / (gamma * U_s)

        # This represents an invalid alternative, because lambda is too big.
        if multiplier <= 0:
            return 1.0

        log_pvalue = (
            self.sample_size * multiplier.ln()
            - o1 * (1 - 1 / (2 * gamma)).ln()
            - o2 * (1 - 1 / gamma).ln()
            - u1 * (1 + 1 / (2 * gamma)).ln()
            - u2 * (1 + 1 / gamma).ln()
        )
        pvalue = (log_pvalue).exp()
        return float(np.min([float(pvalue), 1.0]))  # cast for the typechecker


def maximize_fisher_combined_pvalue(
    alpha: float,
    contest: Contest,
    bp_stratum: BallotPollingStratum,
    cvr_stratum: BallotComparisonStratum,
    winner: str,
    loser: str,
    stepsize: float = 0.05,
) -> float:
    """
    Grid search to find the maximum P-value.
    Find the smallest Fisher's combined statistic for P-values obtained
    by testing two null hypotheses at level alpha using data X=(X1, X2).

    This was largely taken from CORLA18.

    Inputs:
        alpha: the risk limit as a fraction
        contest: the contest being audited
        bp_stratum: a stratum object containing the ballot polling stratum
        cvr_stratum: a stratum object containing the ballot comparison stratum
        winner, loser: the winner-loser pair to maximuze the p-value over

    Outputs:
        a maximum p-value for the Fisher's combining function given the two
        strata.
    """
    maximized_pvalue = 0.0
    # find range of possible lambda
    cvr_winner_votes = cvr_stratum.vote_totals[winner]
    bp_winner_votes = bp_stratum.vote_totals[winner]

    cvr_loser_votes = cvr_stratum.vote_totals[loser]
    bp_loser_votes = bp_stratum.vote_totals[loser]

    V = cvr_winner_votes - cvr_loser_votes + bp_winner_votes - bp_loser_votes
    reported_margin = contest.candidates[winner] - contest.candidates[loser]
    assert V == reported_margin

    # The election is tied
    if V == 0:
        return 1.0

    lambda_lower = (
        np.amax(
            [
                cvr_winner_votes - cvr_loser_votes - cvr_stratum.num_ballots,
                V - (bp_winner_votes - bp_loser_votes + bp_stratum.num_ballots),
            ]
        )
        / V
    )
    lambda_upper = (
        np.amin(
            [
                cvr_winner_votes - cvr_loser_votes + cvr_stratum.num_ballots,
                V - (bp_winner_votes - bp_loser_votes - bp_stratum.num_ballots),
            ]
        )
        / V
    )

    sample = bravo.compute_cumulative_sample(bp_stratum.sample)
    bp_sample_winner_votes = sample[winner]
    bp_sample_loser_votes = sample[loser]

    Wn = bp_sample_winner_votes
    Ln = bp_sample_loser_votes
    Un = bp_stratum.sample_size - bp_sample_winner_votes - bp_sample_loser_votes
    assert Wn >= 0, f"{Wn, Ln, Un}"
    assert Ln >= 0, f"{Wn, Ln, Un}"
    assert Un >= 0, f"{Wn, Ln, Un}"

    def T2(delta):
        return (
            2
            * cvr_stratum.sample_size
            * np.log(
                1 + reported_margin * delta / (2 * cvr_stratum.num_ballots * GAMMA)
            )
        )

    def modulus(delta):
        return (
            2 * Wn * np.log(1 + reported_margin * delta)
            + 2 * Ln * np.log(1 + reported_margin * delta)
            + 2 * Un * np.log(1 + 2 * reported_margin * delta)
            + T2(delta)
        )

    while True:
        test_lambdas = np.arange(lambda_lower, lambda_upper + stepsize, stepsize)
        if len(test_lambdas) < 5:
            stepsize = (lambda_upper + 1 - lambda_lower) / 5
            test_lambdas = np.arange(lambda_lower, lambda_upper + stepsize, stepsize)

        fisher_pvalues = np.empty_like(test_lambdas)
        for i, test_lambda in enumerate(test_lambdas):
            pvalue1: float = np.min(
                [
                    1,
                    cvr_stratum.compute_pvalue(
                        reported_margin, winner, loser, test_lambda
                    ),
                ]
            )
            pvalue2: float = np.min(
                [
                    1,
                    bp_stratum.compute_pvalue(
                        reported_margin, winner, loser, 1 - test_lambda
                    ),
                ]
            )

            pvalues = [pvalue1, pvalue2]
            if np.any(np.array(pvalues) == 0):
                fisher_pvalues[i] = 0
            else:
                obs = -2 * np.sum(np.log(pvalues))
                fisher_pvalues[i] = 1 - sp.stats.chi2.cdf(obs, df=2 * len(pvalues))

        pvalue = np.max(fisher_pvalues)
        alloc_lambda: float = test_lambdas[np.argmax(fisher_pvalues)]  # type: ignore

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
        # TODO memoize the p-values we've already looked at
        # to make it faster.
        lambda_lower = alloc_lambda - 2 * stepsize
        lambda_upper = alloc_lambda + 2 * stepsize
        stepsize /= 10

    return min(maximized_pvalue, 1.0)


def try_n(
    n: int,
    alpha: float,
    contest: Contest,
    winner: str,
    loser: str,
    bp_stratum: BallotPollingStratum,
    cvr_stratum: BallotComparisonStratum,
    n_ratio: float,
) -> float:
    """
    A function that evaluates whether a certain sample size can meet the risk limit.

    Inputs:
        n - the sample size to test
        alpha - the risk limit as a fraction
        contest - the contest being audited
        winner, loser - the winner-loser pair to evaluate the risk measurement over
        bp_stratum: a stratum object containing the ballot polling stratum
        cvr_stratum: a stratum object containing the ballot comparison stratum
        n_ratio: the ratio of the size of the CVR stratum to both strata.
    Outputs:
        A Fisher's combined maximized p-value for the given sample size, contest,
        winner-loser pair, and strata.
    """
    n1_original = cvr_stratum.sample_size
    n2_original = bp_stratum.sample_size

    o1_rate, o2_rate, u1_rate, u2_rate = 0.0, 0.0, 0.0, 0.0
    # Assume o1, o2, u1, u2 rates will be the same as what we observed in sample
    if n1_original != 0:
        o1_rate = cvr_stratum.misstatements[(winner, loser)]["o1"] / n1_original
        o2_rate = cvr_stratum.misstatements[(winner, loser)]["o2"] / n1_original
        u1_rate = cvr_stratum.misstatements[(winner, loser)]["u1"] / n1_original
        u2_rate = cvr_stratum.misstatements[(winner, loser)]["u2"] / n1_original

    n1 = math.ceil(n_ratio * n)
    n2 = int(n - n1)

    if (n1 < n1_original) or (n2 < n2_original):
        return 1.0

    o1 = (
        math.ceil(o1_rate * (n - n1_original))
        + cvr_stratum.misstatements[(winner, loser)]["o1"]
    )
    o2 = (
        math.ceil(o2_rate * (n - n1_original))
        + cvr_stratum.misstatements[(winner, loser)]["o2"]
    )
    u1 = (
        math.floor(u1_rate * (n - n1_original))
        + cvr_stratum.misstatements[(winner, loser)]["u1"]
    )
    u2 = (
        math.floor(u2_rate * (n - n1_original))
        + cvr_stratum.misstatements[(winner, loser)]["u2"]
    )

    # Because this is a hypothetical sample, we create a
    # corresponding hypothetical stratum
    hyp_sample_size = n1

    hyp_misstatements: MISSTATEMENTS = {
        (winner, loser): {
            "o1": o1,
            "o2": o2,
            "u1": u1,
            "u2": u2,
        }
    }

    hyp_cvr_stratum = BallotComparisonStratum(
        cvr_stratum.num_ballots,
        cvr_stratum.vote_totals,
        hyp_misstatements,
        hyp_sample_size,
    )

    # Set up the no-CVR stratum, assuming the sample looks like the
    # prior round
    prev_sample_size = bp_stratum.sample_size
    hyp_sample: BallotPollingStratum.SAMPLE_RESULTS = {"hyp_round": {}}

    cumulative_sample = bravo.compute_cumulative_sample(bp_stratum.sample)

    # Add fake ballots to the hypothetical sample:
    if prev_sample_size == 0:
        # If no ballots have been sampled, assume the sample is roughly
        # the margin
        hyp_sample["hyp_round"] = {
            winner: min(
                int(n2 * (bp_stratum.vote_totals[winner] / bp_stratum.num_ballots)),
                bp_stratum.vote_totals[winner],
            ),
            loser: min(
                math.ceil(
                    n2 * (bp_stratum.vote_totals[loser] / bp_stratum.num_ballots)
                ),
                bp_stratum.vote_totals[loser],
            ),
        }
    else:
        # Otherwise use the sample we've seen so far
        hyp_sample["hyp_round"] = {
            winner: min(
                int(
                    (n2 - prev_sample_size)
                    * (cumulative_sample[winner] / prev_sample_size)
                ),
                bp_stratum.vote_totals[winner],
            ),
            loser: min(
                math.ceil(
                    (n2 - prev_sample_size)
                    * (cumulative_sample[loser] / prev_sample_size)
                ),
                bp_stratum.vote_totals[loser],
            ),
        }

    hyp_sample_size = n2
    hyp_sample_size = min(bp_stratum.num_ballots, hyp_sample_size)

    for rnd in bp_stratum.sample:
        hyp_sample[rnd] = bp_stratum.sample[rnd]

    hyp_no_cvr_stratum = BallotPollingStratum(
        bp_stratum.num_ballots, bp_stratum.vote_totals, hyp_sample, hyp_sample_size
    )

    return maximize_fisher_combined_pvalue(
        alpha, contest, hyp_no_cvr_stratum, hyp_cvr_stratum, winner, loser
    )


def get_sample_size_for_wl_pair(
    alpha: float,
    contest: Contest,
    bp_stratum: BallotPollingStratum,
    cvr_stratum: BallotComparisonStratum,
    winner: str,
    loser: str,
) -> Tuple[int, int]:
    n_ratio = cvr_stratum.num_ballots / (
        cvr_stratum.num_ballots + bp_stratum.num_ballots
    )
    ballots_to_sample = max(
        MIN_SAMPLE_SIZE, cvr_stratum.sample_size + bp_stratum.sample_size
    )

    expected_pvalue = 1.0

    # this allows us to exactly match CORLA18's estimate_n and estimate_escalation_n
    coefficient = 1.1
    if bp_stratum.sample_size == 0 and cvr_stratum.sample_size == 0:
        coefficient = 2.0

    # step 1: linear search, increasing n by a factor of 1.1 or 2 each time
    while expected_pvalue > alpha:
        ballots_to_sample = int(coefficient * ballots_to_sample)
        if ballots_to_sample > contest.ballots:
            cvr_ballots_to_sample = math.ceil(n_ratio * contest.ballots)
            bp_ballots_to_sample = int(contest.ballots - cvr_ballots_to_sample)
            return (cvr_ballots_to_sample, bp_ballots_to_sample)

        expected_pvalue = try_n(
            ballots_to_sample,
            alpha,
            contest,
            winner,
            loser,
            bp_stratum,
            cvr_stratum,
            n_ratio,
        )

    # step 2: bisection between n/1.1 and n
    low_n = ballots_to_sample / coefficient
    high_n = ballots_to_sample
    mid_pvalue = 1.0
    # TODO: do we need this tolerance?
    risk_limit_tol = 0.8
    while (mid_pvalue > alpha) or (mid_pvalue < risk_limit_tol * alpha):
        mid_n = int(np.floor((low_n + high_n) / 2))  # cast for typechecker
        if mid_n in [low_n, high_n]:
            break
        mid_pvalue = try_n(
            mid_n,
            alpha,
            contest,
            winner,
            loser,
            bp_stratum,
            cvr_stratum,
            n_ratio,
        )
        if mid_pvalue <= alpha:
            high_n = mid_n
        else:
            low_n = mid_n

    cvr_ballots_to_sample = int(math.ceil(n_ratio * high_n))
    bp_ballots_to_sample = int(math.ceil(high_n - cvr_ballots_to_sample))
    return (cvr_ballots_to_sample, bp_ballots_to_sample)


def get_sample_size(
    risk_limit: int,
    contest: Contest,
    bp_stratum: BallotPollingStratum,
    cvr_stratum: BallotComparisonStratum,
) -> HybridPair:
    """
    Estimate the initial sample sizes for the audit.

    Inputs:
        risk_limit      - the risk limit (as an integer percentage) for this audit
        contest         - the overall contest information
        bp_stratum: a stratum object containing the ballot polling stratum
        cvr_stratum: a stratum object containing the ballot comparison stratum
    Outputs:
        sample_sizes    - A Tuple of (cvr_strata_size, no_cvr_strata_size).
    """

    alpha = float(risk_limit) / 100

    # Note: because we are seeking to maximize the p-values in both strata,
    # the p-values are monotonic, and assessing the hypothesis that the error
    # in both strata is greater than or equal to some threshold value that
    # depends on the margin, in votes, selecting the smallest margin maximizes
    # the p-values for the first round.

    if bp_stratum.sample_size == 0 and cvr_stratum.sample_size == 0:
        worst_winner = min(  # type: ignore
            {winner: contest.candidates[winner] for winner in contest.winners},
            key=contest.candidates.get,
        )
        best_loser = max(  # type: ignore
            {loser: contest.candidates[loser] for loser in contest.losers},
            key=contest.candidates.get,
        )

        sample_size = get_sample_size_for_wl_pair(
            alpha, contest, bp_stratum, cvr_stratum, worst_winner, best_loser
        )
    else:
        sample_sizes: List[Tuple[int, int]] = []
        for winner, loser in product(contest.winners, contest.losers):
            sample_sizes.append(
                get_sample_size_for_wl_pair(
                    alpha, contest, bp_stratum, cvr_stratum, winner, loser
                )
            )

        sample_size = sorted(sample_sizes, key=sum, reverse=True)[0]

    if (
        sample_size[0] == cvr_stratum.num_ballots
        or sample_size[1] == bp_stratum.num_ballots
    ):
        raise ValueError("One or both strata need to be recounted.")

    return HybridPair(cvr=sample_size[0], non_cvr=sample_size[1])


def compute_risk(
    risk_limit: int, contest: Contest, bp_stratum, cvr_stratum
) -> Tuple[float, bool]:
    """
    Computes a risk measurement for a given sample, using fisher's combining
    function to combine pvalue measurements from a ballot polling and ballot
    comparison stratum. Returns the highest measured p-value for all winner-loser
    pairs.

    Inputs:
        risk_limit      - the risk limit (as an integer percentage) for this audit
        contest         - the overall contest information
        bp_stratum: a stratum object containing the ballot polling stratum
        cvr_stratum: a stratum object containing the ballot comparison stratum

    Outputs:
        a maximized Fisher's combined p-value over all winner-loser pairs, and
        whether the p-value meets the risk limit.

    """
    alpha = float(risk_limit) / 100
    assert alpha < 1

    pvalues = []

    exception = False
    for winner, loser in product(contest.winners, contest.losers):
        if (
            bp_stratum.sample_size >= bp_stratum.num_ballots
            and cvr_stratum.sample_size >= cvr_stratum.num_ballots
        ):
            # We did a full recount already!
            exception = True
            pvalues.append(0.0)
        elif bp_stratum.sample_size >= bp_stratum.num_ballots:
            exception = True
            pvalues.append(cvr_stratum.compute_pvalue(alpha, winner, loser, 1))
        elif cvr_stratum.sample_size >= cvr_stratum.num_ballots:
            exception = True
            pvalues.append(bp_stratum.compute_pvalue(alpha, winner, loser, 1))
        else:
            pvalues.append(
                maximize_fisher_combined_pvalue(
                    alpha, contest, bp_stratum, cvr_stratum, winner, loser
                )
            )

    max_p = max(pvalues)

    if exception:
        raise ValueError(
            "One or both strata has already been recounted. Possibly returning a p-value from the remaining stratum.",
            max_p,
            max_p <= alpha,
        )

    return max_p, max_p <= alpha


def misstatements(
    contest: Contest,
    reported_results: CVRS,
    audited_results: SAMPLECVRS,
) -> MISSTATEMENTS:
    misstatements: MISSTATEMENTS = {}
    for winner, loser in product(contest.winners, contest.losers):
        discrepancies = [
            supersimple.discrepancy(
                contest,
                winner,
                loser,
                reported_results.get(ballot),
                audited_result["cvr"],
            )
            for ballot, audited_result in audited_results.items()
        ]

        discrepancy_nums = [
            discrepancy["counted_as"]
            for discrepancy in discrepancies
            if discrepancy is not None
        ]
        misstatement_counts = Counter(discrepancy_nums)
        # We want to be conservative, so we will ignore understatements (i.e. errors
        # that favor the winner) which are negative.
        misstatements[(winner, loser)] = {
            "o1": misstatement_counts[1],
            "o2": misstatement_counts[2],
            "u1": 0,
            "u2": 0,
        }

    return misstatements

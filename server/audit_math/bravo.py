# pylint: disable=invalid-name
"""
Library for performing a BRAVO-style ballot polling risk-limiting audit,
as described by Lindeman and Stark here: https://www.usenix.org/system/files/conference/evtwote12/evtwote12-final27.pdf

Note that this library works for one contest at a time, as if each contest being
targeted is being audited completely independently.
"""
import math
from decimal import Decimal
from collections import defaultdict
import logging
from typing import Dict, Tuple, Optional, TypedDict
from scipy import stats

from .sampler_contest import Contest
from .ballot_polling_types import (
    SampleSizeOption,
    BALLOT_POLLING_ROUND_SIZES,
    BALLOT_POLLING_SAMPLE_RESULTS,
)


def get_expected_sample_size(
    alpha: Decimal, contest: Contest, cumulative_sample_results: Dict[str, int]
) -> SampleSizeOption:
    """
    Returns the expected sample size (also known as the ASN or average sample number) for a BRAVO
    audit of <contest>

    Input:
        risk_limit      - the risk-limit for this audit
        contest         - the contest to get the sample size for
        sample_results  - mapping of candidates to votes in the (cumulative)
                          sample:
                        {
                            candidate1: sampled_votes,
                            candidate2: sampled_votes,
                            ...
                        }

    Output:
        the expected sample size for the contest
    """
    if is_tie(contest):
        raise ValueError("Cannot compute ASN for a tied contest")

    winners = contest.margins["winners"]
    losers = contest.margins["losers"]

    if not losers:
        raise ValueError("Cannot compute ASN for a contest with no losers")

    T = get_test_statistics(contest.margins, cumulative_sample_results)

    class SampleSizeWinnerLoserStats(TypedDict):
        p_w: Decimal
        p_l: Decimal
        sample_w: int
        sample_l: int

    sample_size = 0
    sample_size_winner_loser_stats: Optional[SampleSizeWinnerLoserStats] = None
    for winner_name, winner_stats in winners.items():
        for loser_name, loser_stats in losers.items():
            weighted_alpha = (Decimal(1) / alpha) / T[(winner_name, loser_name)]
            p_w = Decimal(winner_stats["p_w"])
            p_l = Decimal(loser_stats["p_l"])
            if p_l == 0:
                # p_l is 0 --> s_w is 1 --> z_l is -Infinity
                # Skip this pair to avoid invalid operation errors
                continue
            s_w = p_w / (p_w + p_l)
            z_w = (2 * s_w).ln()
            z_l = (2 - 2 * s_w).ln()

            possible_sample_size = math.ceil(
                (weighted_alpha.ln() + (z_w / Decimal(2))) / (p_w * z_w + p_l * z_l)
            )
            if possible_sample_size > sample_size:
                sample_size = possible_sample_size
                sample_size_winner_loser_stats = {
                    "p_w": p_w,
                    "p_l": p_l,
                    "sample_w": cumulative_sample_results[winner_name],
                    "sample_l": cumulative_sample_results[loser_name],
                }

    if sample_size == 0:
        raise ValueError("Sample indicates the audit is over")

    probability_of_completion = (
        expected_prob(
            alpha,
            sample_size_winner_loser_stats["p_w"],
            sample_size_winner_loser_stats["p_l"],
            sample_size_winner_loser_stats["sample_w"],
            sample_size_winner_loser_stats["sample_l"],
            sample_size,
        )
        if sample_size_winner_loser_stats is not None
        # We can't meaningfully compute the probability of completion of the number of winners is
        # greater than 1
        and contest.num_winners == 1
        else None
    )

    return {
        "type": "ASN",
        "size": sample_size,
        "prob": probability_of_completion,
    }


def get_test_statistics(
    margins: Dict[str, Dict], sample_results: Dict[str, int]
) -> Dict[Tuple[str, str], Decimal]:
    """
    Computes T*, the test statistic from an existing sample.

    Inputs:
        margins        - the margins for the contest being audited
        sample_results - mapping of candidates to votes in the (cumulative)
                         sample:
                {
                    candidate1: sampled_votes,
                    candidate2: sampled_votes,
                    ...
                }

    Outputs:
        T - Mapping of (winner, loser) pairs to their test statistic based
            on sample_results
    """
    winners = margins["winners"]
    losers = margins["losers"]

    T = {}

    # Setup pair-wise Ts:
    for winner in winners:
        for loser in losers:
            T[(winner, loser)] = Decimal(1.0)

    # Handle the no-losers case
    if not losers:
        for winner in winners:
            T[(winner, "")] = Decimal(1.0)

    for cand, votes in sample_results.items():
        # Avoid a degenerate case where T is 0 and votes is also 0
        if not votes:
            continue

        if cand in winners:
            for loser in losers:
                T[(cand, loser)] *= Decimal(winners[cand]["swl"][loser] / 0.5) ** votes
        elif cand in losers:
            for winner in winners:
                T[(winner, cand)] *= (
                    Decimal((1 - winners[winner]["swl"][cand]) / 0.5) ** votes
                )

    logging.debug(f"bravo test_stats: T={T}")

    return T


def bravo_sample_sizes(
    alpha: Decimal,
    p_w: Decimal,
    p_r: Decimal,
    sample_w: int,
    sample_r: int,
    p_completion: float,
    total_ballots: int,
) -> int:
    """
    Analytic calculation for BRAVO round completion assuming the election
    outcome is correct. Written by Mark Lindeman.

    Inputs:
        risk_limit      - the risk-limit for this audit
        p_w             - the fraction of vote share for the winner
        p_r             - the fraction of vote share for the loser
        sample_w        - the number of votes for the winner that have already
                          been sampled
        sample_r        - the number of votes for the runner-up that have
                          already been sampled
        p_completion    - the desired chance of completion in one round,
                          if the outcome is correct
        total_ballots   - the total ballots cast

    Outputs:
        sample_size     - the expected sample size for the given chance
                          of completion in one round
    """
    # calculate the "two-way" share of p_w
    p_wr = p_w + p_r
    p_w2 = p_w / p_wr
    p_r2 = 1 - p_w2

    # set up the basic BRAVO math
    plus = (p_w2 / Decimal(0.5)).ln()
    minus = (p_r2 / Decimal(0.5)).ln()
    threshold = (1 / alpha).ln() - (sample_w * plus + sample_r * minus)

    # crude condition trapping:
    if threshold <= 0:
        return 0

    z = -stats.norm.ppf(p_completion)

    # The basic equation is E_x = R_x where
    # E_x: expected # of successes at the 1-p_completion quantile
    # R_x: smallest x (given n) that attains the risk limit

    # E_x = n * p_w2 + z * sqrt(n * p_w2 * p_r2)
    # R_x = (threshold - minus * n) / (plus - minus)

    # (Both sides are continuous approximations to discrete functions.)
    # We set these equal, rewrite as a quadratic in n, and take the
    # larger of the two zeros (roots).

    # These parameters are useful in simplifying the quadratic.
    d = p_w2 * p_r2
    f = threshold / (plus - minus)
    g = minus / (plus - minus) + p_w2

    # The three coefficients of the quadratic:
    q_a = g**2
    q_b = -(Decimal(z) ** 2 * d + 2 * f * g)
    q_c = f**2

    # Apply the quadratic formula.
    # We want the larger root for p_completion > 0.5, the
    # smaller root for p_completion < 0.5; they are equal
    # when p_completion = 0.
    # max here handles cases where, due to rounding error,
    # the base (content) of the radical is trivially
    # negative for p_completion very close to 0.5.
    radical = (Decimal(0).max(q_b**2 - 4 * q_a * q_c)).sqrt()

    if p_completion > 0.5:
        size = math.floor((-q_b + radical) / (2 * q_a))
    else:
        size = math.floor((-q_b - radical) / (2 * q_a))

    # This is a reasonable estimate, but is not guaranteed.
    # Get a guarantee. (Perhaps contrary to intuition, using
    # math.ceil instead of math.floor can lead to a
    # larger sample.)
    test_stat = Decimal(0)
    while test_stat.is_nan() or (
        test_stat < threshold
        # In extreme cases, the test_stat never reaches the threshold (or at least doesn't do so in
        # a reasonable amount of time). This second check prevents this loop from hanging in those
        # cases.
        and size < total_ballots
    ):
        x_c = Decimal(stats.binom.ppf(1.0 - p_completion, size, float(p_w2)))
        test_stat = x_c * plus + (size - x_c) * minus
        if test_stat.is_nan() or test_stat < threshold:
            size += 1

    # The preceding fussiness notwithstanding, we use a simple
    # adjustment to account for "other" votes beyond p_w and p_r.

    size_adj = math.ceil(size / p_wr)

    return size_adj


def expected_prob(
    alpha: Decimal, p_w: Decimal, p_r: Decimal, sample_w: int, sample_r: int, asn: int
) -> float:
    """
    Analytic calculation for BRAVO round completion of the expected value, assuming
    the election outcome is correct. Adapted from Mark Lindeman.

    Inputs:
        risk_limit      - the risk-limit for this audit
        p_w             - the fraction of vote share for the winner
        p_r             - the fraction of vote share for the loser
        sample_w        - the number of votes for the winner that have already
                          been sampled
        sample_r        - the number of votes for the runner-up that have
                          already been sampled
        asn             - the expected value

    Outputs:
        sample_size     - the expected chance of completion in one round for the
                          given expected value (asn)

    """

    # calculate the "two-way" share of p_w
    p_wr = p_w + p_r
    p_w2 = p_w / p_wr
    p_r2 = 1 - p_w2

    # set up the basic BRAVO math
    plus = (p_w2 / Decimal(0.5)).ln()
    minus = (p_r2 / Decimal(0.5)).ln()
    threshold = (1 / alpha).ln() - (sample_w * plus + sample_r * minus)

    # crude condition trapping:
    if threshold <= 0:
        return 0.0

    n = asn * p_wr
    # The basic equation is E_x = R_x where
    # E_x: expected # of successes at the 1-p_completion quantile
    # R_x: smallest x (given n) that attains the risk limit

    # E_x = n * p_w2 + z * sqrt(n * p_w2 * p_r2)
    # R_x = (threshold - minus * n) / (plus - minus)

    # (Both sides are continuous approximations to discrete functions.)
    # We set these equal, and solve for z

    R_x = (threshold - minus * n) / (plus - minus)

    z = (R_x - n * p_w2) / (n * p_w2 * p_r2).sqrt()

    # Invert the PPF used to compute z from the sample prob
    return round(float(stats.norm.cdf(float(-z))), 2)


def compute_cumulative_sample(sample_results):
    """
    Computes a cumulative sample given a round-by-round sample
    """
    cumulative_sample = defaultdict(int)
    for rd in sample_results:
        for cand in sample_results[rd]:
            cumulative_sample[cand] += sample_results[rd][cand]
    return cumulative_sample


def get_sample_size(
    risk_limit: int,
    contest: Contest,
    sample_results: Optional[BALLOT_POLLING_SAMPLE_RESULTS],
    round_sizes: Optional[BALLOT_POLLING_ROUND_SIZES],
) -> Dict[str, SampleSizeOption]:
    """
    Computes initial sample size parameterized by likelihood that the
    initial sample will confirm the election result, assuming no
    discrepancies.

    Inputs:
        risk_limit     - the risk-limit for this audit
        contest        - a sampler_contest object of the contest being audited
        sample_results - mapping of candidates to votes in the (cumulative)
                         sample:
                        {
                            candidate1: sampled_votes,
                            candidate2: sampled_votes,
                            ...
                        }

    Outputs:
        samples - dictionary mapping confirmation likelihood to sample size:
                {
                    likelihood1: sample_size,
                    likelihood2: sample_size,
                    ...
                    asn: {
                        "size": sample_size,
                        "prob": prob       # the probability the asn terminates
                                           # in one round
                    }

                }
    """
    logging.debug(
        f"bravo::get_sample_size({risk_limit=}, {contest=}, {sample_results=})"
    )

    alpha = Decimal(risk_limit) / 100
    assert alpha < 1, "The risk-limit must be less than one!"

    if alpha == 0:
        return {
            "all-ballots": {
                "type": "all-ballots",
                "size": contest.ballots,
                "prob": None,
            }
        }

    quants = [0.7, 0.8, 0.9]

    if round_sizes:
        num_sampled = sum(round_info.round_size for round_info in round_sizes.values())
        # If we've already sampled all the ballots, we should never be here
        if num_sampled >= contest.ballots:
            raise ValueError("All ballots have already been audited!")

    winners = contest.margins["winners"]
    losers = contest.margins["losers"]

    if not losers:
        raise ValueError("Contest must have candidates who did not win!")

    if is_tie(contest):
        return {
            "all-ballots": {
                "type": "all-ballots",
                "size": contest.ballots,
                "prob": None,
            }
        }

    if is_landslide(contest):
        return {
            "asn": {"type": "ASN", "size": 1, "prob": 1},
        }

    cumulative_sample = {}
    if sample_results:
        cumulative_sample = compute_cumulative_sample(sample_results)
    else:
        for candidate in contest.candidates:
            cumulative_sample[candidate] = 0

    samples: Dict[str, SampleSizeOption] = {}

    samples["asn"] = get_expected_sample_size(alpha, contest, cumulative_sample)

    if contest.num_winners != 1:
        return samples

    for quant in quants:
        sample_size = 0
        for winner_name, winner_stats in winners.items():
            for loser_name, loser_stats in losers.items():
                p_w = Decimal(winner_stats["p_w"])
                p_l = Decimal(loser_stats["p_l"])
                if p_l == 0:
                    # Skip this pair to avoid invalid operation errors
                    continue
                sample_w = cumulative_sample[winner_name]
                sample_l = cumulative_sample[loser_name]

                possible_sample_size = bravo_sample_sizes(
                    alpha, p_w, p_l, sample_w, sample_l, quant, contest.ballots
                )
                if possible_sample_size > sample_size:
                    sample_size = possible_sample_size

        if sample_size != 0:
            samples[str(quant)] = {
                "type": None,
                "size": sample_size,
                "prob": quant,
            }

    # If the computed sample size is a good chunk of the ballots, recommend
    # auditing all ballots, since this is actually less work than auditing a
    # large proportion (for large elections).
    large_election_threshold = 100000
    all_ballots_threshold = contest.ballots * 0.25
    if (
        contest.ballots > large_election_threshold
        and "0.9" in samples
        and samples["0.9"]["size"] >= all_ballots_threshold
    ):
        return {
            "all-ballots": {
                "type": "all-ballots",
                "size": contest.ballots,
                "prob": None,
            }
        }

    logging.debug(f"bravo::get_sample_size => {samples=}")

    return samples


def compute_risk(
    risk_limit: int, contest: Contest, sample_results: Dict[str, Dict[str, int]]
) -> Tuple[Dict[Tuple[str, str], float], bool]:
    """
    Computes the risk-value of <sample_results> based on results in <contest>.

    Inputs:
        risk_limit     - the risk-limit for this audit
        contest        - a sampler_contest object for the contest being measured
        sample_results - mapping of candidates to votes in the sample:
                { "round": {
                    candidate1: sampled_votes,
                    candidate2: sampled_votes,
                    ...
                }}

    Outputs:
        measurements    - the p-value of the hypotheses that the election
                          result is correct based on the sample, for each
                          winner-loser pair.
        confirmed       - a boolean indicating whether the audit can stop
    """
    logging.debug(f"bravo::compute_risk({risk_limit=}, {contest=}, {sample_results=})")

    alpha = Decimal(risk_limit) / 100
    assert alpha < 1, "The risk-limit must be less than one!"

    # Get cumulative sample results
    cumulative_sample = {}
    if sample_results:
        cumulative_sample = compute_cumulative_sample(sample_results)
    else:
        for candidate in contest.candidates:
            cumulative_sample[candidate] = 0
    T = get_test_statistics(contest.margins, cumulative_sample)

    measurements = {}

    # If we've done a full hand recount
    if sum(cumulative_sample.values()) >= contest.ballots:
        for pair in T:
            measurements[pair] = 0.0
        return measurements, True

    finished = True
    # pylint: disable=consider-using-dict-items
    for pair in T:
        raw = 1 / T[pair] if T[pair] > 0 else Decimal(1)
        measurements[pair] = min(float(raw), 1.0)

        if raw > alpha:
            finished = False
    logging.debug(f"bravo::compute_risk -> {measurements=}, {finished=}")
    return measurements, finished


def is_tie(contest: Contest) -> bool:
    winners = contest.margins["winners"]
    losers = contest.margins["losers"]

    if not losers:
        return False

    smallest_p_w = min(winner_stats["p_w"] for winner_stats in winners.values())
    largest_p_l = max(loser_stats["p_l"] for loser_stats in losers.values())
    return bool(smallest_p_w == largest_p_l)


def is_landslide(contest: Contest) -> bool:
    losers = contest.margins["losers"]

    if not losers:  # pragma: no cover
        return False

    largest_p_l = max(loser_stats["p_l"] for loser_stats in losers.values())
    return bool(largest_p_l == 0)

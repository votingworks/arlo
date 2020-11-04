# pylint: disable=invalid-name
"""
Library for performing a Minerva-style ballot polling risk-limiting audit,
as described by Zagórski et al https://arxiv.org/abs/2008.02315

Note that this library works for one contest at a time, as if each contest being
targeted is being audited completely independently.
"""
from decimal import Decimal
from collections import defaultdict
import logging
from typing import List, Dict, Tuple, Optional

from .sampler_contest import Contest
from .shim import minerva_sample_sizes, get_minerva_test_statistics  # type: ignore


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
    sample_results: Optional[Dict[str, Dict[str, int]]],
    round_sizes: Dict[int, int],
) -> Dict[str, "SampleSizeOption"]:  # type: ignore
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
                }
    """

    # import pdb; pdb.set_trace()
    # logging.warning(f"{sample.results=}")
    # from ..api.rounds import contest_results_by_round
    # logging.warning(f"{contest_results_by_round(contest)=}")

    if sample_results is None:
        prev_round_schedule = []
    else:
        # Set up some parameters we hope to get via the API
        first_round_size = 100
        prev_round_count = len(sample_results)
        prev_round_schedule = [
            first_round_size * 2 ** i for i in range(prev_round_count)
        ]
        next_round_size = first_round_size * 2 ** prev_round_count
        logging.debug(f"{prev_round_schedule=}, {next_round_size=}")
        return {"0.9": {"type": None, "size": next_round_size, "prob": 0.9}}

    alpha = Decimal(risk_limit) / 100
    assert alpha < 1, "The risk-limit must be less than one!"

    quants = [0.7, 0.8, 0.9]

    samples: Dict = {}

    # Get cumulative sample results
    cumulative_sample = {}
    if sample_results:
        cumulative_sample = compute_cumulative_sample(sample_results)
    else:
        for candidate in contest.candidates:
            cumulative_sample[candidate] = 0

    p_w = Decimal("inf")
    p_l = Decimal(0)
    best_loser = ""
    worse_winner = ""

    # For multi-winner, do nothing
    if contest.num_winners != 1:
        # FIXME: handle this some day
        # TODO: return -1 instead?
        return {"asn": {"type": "ASN", "size": -1, "prob": None}}



    margin = contest.margins
    # Get smallest p_w - p_l
    for winner in margin["winners"]:
        if margin["winners"][winner]["p_w"] < p_w:
            p_w = Decimal(margin["winners"][winner]["p_w"])
            worse_winner = winner

    for loser in margin["losers"]:
        if margin["losers"][loser]["p_l"] > p_l:
            p_l = Decimal(margin["losers"][loser]["p_l"])
            best_loser = loser

    # If we're in a single-candidate race, set sample to 0
    if not margin["losers"]:
        for quant in quants:
            samples[str(quant)] = {"type": None, "size": -1.0, "prob": quant}

        return samples

    num_ballots = contest.ballots

    # Handles ties
    if p_w == p_l:
        samples["asn"] = {
            "type": "ASN",
            "size": num_ballots,
            "prob": 1.0,
        }

        for quant in quants:
            samples[str(quant)] = {"type": None, "size": num_ballots, "prob": quant}

        return samples

    # Handle landslides
    if p_w == 1.0:
        samples["asn"] = {
            "type": "ASN",
            "size": 1,
            "prob": 1.0,
        }

        return samples

    # If we haven't seen anything yet, initialize sample_w and sample_l
    if not cumulative_sample:
        sample_w = 0
        sample_l = 0
    else:
        sample_w = cumulative_sample[worse_winner]
        sample_l = cumulative_sample[best_loser]

    for quant in quants:
        size = minerva_sample_sizes(alpha, p_w, p_l, sample_w, sample_l, quant)
        samples[str(quant)] = {"type": None, "size": size, "prob": quant}

    return samples


def collect_p_values(
        alpha: float,
        margins: Dict[str, Dict], round_schedule: List[int], sample_results: Dict[str, int]
) -> Dict[Tuple[str, str], Decimal]:
    """
    Collect risk levels for each pair of candidates.

    Inputs:
        alpha          - risk limit
        margins        - the margins for the contest being audited
        round_schedule - the sizes of each round
        sample_results - mapping of candidates to votes in each round

    Outputs:
        T - Mapping of (winner, loser) pairs to their test statistic based
            on sample_results
    """

    winners = margins["winners"]
    losers = margins["losers"]

    risks = {}

    for winner in winners:
        for loser in losers:
            risks[(winner, loser)] = Decimal(1.0)

    # Handle the no-losers case
    if not losers:
        for winner in winners:
            risks[(winner, "")] = Decimal(1.0)

    for winner, winner_res in winners.items():
        for loser, loser_res in losers.items():
            res = get_minerva_test_statistics(
                alpha,
                winner_res["p_w"],
                loser_res["p_l"],
                sample_results[winner],
                sample_results[loser],
            )
            logging.debug(
                f"minerva test_stats {res=} for: {winner_res['p_w']=}, {loser_res['p_l']=}, {sample_results[winner]=}, {sample_results[loser]=})"
            )
            risks[(winner, loser)] = 1.0 if res is None else 1.0 / res

    logging.debug(f"minerva test_stats return: {risks=}")
    return risks


def compute_risk(
    risk_limit: float,
    contest: Contest,
    sample_results: Dict[str, Dict[str, int]],
    round_sizes: Dict[int, int],
    risk_limit: float, contest: Contest, sample_results: Dict[str, Dict[str, int]]
) -> Tuple[Dict[Tuple[str, str], float], bool]:
    """
    Computes the risk-value of <sample_results> based on results in <contest>.

    Inputs:
        risk_limit     - the risk-limit for this audit - integer percentage
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
    # import pdb; pdb.set_trace()

    alpha = risk_limit / 100
    assert 0.0 < alpha < 1.0, "The risk-limit must be greater than zero and less than one!"

    # Set up some parameters we hope to get via the API
    first_round_size = 100
    prev_round_count = len(sample_results)
    prev_round_schedule = [first_round_size * 2 ** i for i in range(prev_round_count)]
    logging.debug(f"{prev_round_schedule=}")

    # Get cumulative sample results
    cumulative_sample = {}
    if sample_results:
        cumulative_sample = compute_cumulative_sample(sample_results)
    else:
        for candidate in contest.candidates:
            cumulative_sample[candidate] = 0
    risks = collect_p_values(alpha, contest.margins, prev_round_schedule, cumulative_sample)

    measurements = {}
    finished = True
    for pair in risks:
        raw = 1 / risks[pair]
        measurements[pair] = float(raw)

        if raw > alpha:
            finished = False

    return measurements, finished

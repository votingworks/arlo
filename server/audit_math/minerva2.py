"""
Library for performing a Minerva2 / PROVIDENCE ballot polling risk-limiting audit,
as described by Broadrick et al https://arxiv.org/abs/2210.08717
"""
import logging
from typing import Dict

from r2b2.minerva2 import Minerva2
from r2b2.contest import Contest as R2B2_Contest, ContestType

from .sampler_contest import Contest
from .ballot_polling_types import SampleSizeOption


def make_r2b2_contest(arlo_contest: Contest):
    reported_winners = arlo_contest.winners.keys()
    return R2B2_Contest(
        arlo_contest.ballots,
        arlo_contest.candidates,
        arlo_contest.num_winners,
        reported_winners,
        ContestType.PLURALITY,
    )


def get_sample_size(
    risk_limit: int,
    contest: Contest,
    sample_results: Dict[str, Dict[str, str]],
    round_sizes: Dict[int, int],
) -> Dict[str, SampleSizeOption]:
    """
    Computes sample size for the next round, parameterized by likelihood that the
    sample will confirm the election result, assuming accurate results.

    Inputs:
        risk_limit:     maximum risk as an integer percentage
        contest:        a sampler_contest object of the contest being audited
        sample_results: map round ids to mapping of candidates to incremental votes
        round_sizes:    map round ids to incremental round sizes

    Outputs:
        samples:        dictionary mapping confirmation likelihood to next sample size

    >>> c3 = make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    >>> get_sample_size(10, c3, None, [])
    {'0.7': {'type': None, 'size': 134, 'prob': 0.7}, '0.8': {'type': None, 'size': 166, 'prob': 0.8}, '0.9': {'type': None, 'size': 215, 'prob': 0.9}}
    >>> get_sample_size(20, c3, None, [])
    {'0.7': {'type': None, 'size': 87, 'prob': 0.7}, '0.8': {'type': None, 'size': 110, 'prob': 0.8}, '0.9': {'type': None, 'size': 156, 'prob': 0.9}}
    >>> get_sample_size(10, c3, make_sample_results(c3, [[55, 40, 3]]), {1: 100})
    {'0.9': {'type': None, 'size': 225, 'prob': 0.9}}
    """

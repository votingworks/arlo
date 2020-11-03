"""
An implementation of Minerva
"""
# TODO: remove the following once we are using the arguments
# pylint: disable=unused-argument
from typing import Dict, Tuple, Optional

from .sampler_contest import Contest


def get_sample_size(
    risk_limit: int,
    contest: Contest,
    sample_results: Optional[Dict[str, Dict[str, int]]],
    round_sizes: Dict[int, int],
) -> Dict[str, "SampleSizeOption"]:  # type: ignore

    return {}


def compute_risk(
    risk_limit: float,
    contest: Contest,
    sample_results: Dict[str, Dict[str, int]],
    round_sizes: Dict[int, int],
) -> Tuple[Dict[Tuple[str, str], float], bool]:

    return {("", ""): 0.0}, False

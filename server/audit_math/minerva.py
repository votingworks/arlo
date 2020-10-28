"""
An implementation of Minerva
"""
from typing import Dict, Tuple

from .sampler_contest import Contest

def get_sample_size(
    risk_limit: int, contest: Contest, sample_results: Dict[str, Dict[str, int]]
) -> Dict[str, "SampleSizeOption"]:  # type: ignore

    return {}


def compute_risk(
    risk_limit: float, contest: Contest, sample_results: Dict[str, Dict[str, int]]
) -> Tuple[Dict[Tuple[str, str], float], bool]:

    return {('', ''): 0.0}, False

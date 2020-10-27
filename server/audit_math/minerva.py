"""
An implementation of Minerva
"""

from .sampler_contest import Contest

def get_sample_size(
    risk_limit: int, contest: Contest, sample_results: Dict[str, int]
) -> Dict[str, "SampleSizeOption"]:  # type: ignore

    return {}


def compute_risk(
    risk_limit: float, contest: Contest, sample_results: Dict[str, int]
) -> Tuple[Dict[Tuple[str, str], float], bool]:

    return None, False

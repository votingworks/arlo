"""
This is a wrapper class to accomodate using more than one test statistics for
ballot polling audits.
"""
from typing import Dict, Tuple, Optional
from typing_extensions import Literal, TypedDict
from ..models import BallotPollingType
from .sampler_contest import Contest
from . import bravo


class SampleSizeOption(TypedDict):
    type: Optional[Literal["ASN"]]
    size: int
    prob: Optional[float]


def get_sample_size(
    risk_limit: int, contest: Contest, sample_results: Dict[str, int], mathtype: str
) -> Dict[str, SampleSizeOption]:

    if mathtype == BallotPollingType.BRAVO:
        return bravo.get_sample_size(risk_limit, contest, sample_results)
    else:
        return bravo.get_sample_size(risk_limit, contest, sample_results)


def compute_risk(
    risk_limit: int, contest: Contest, sample_results: Dict[str, int], mathtype: str
) -> Tuple[Dict[Tuple[str, str], float], bool]:

    if mathtype == BallotPollingType.BRAVO:
        return bravo.compute_risk(risk_limit, contest, sample_results)
    else:
        return bravo.compute_risk(risk_limit, contest, sample_results)

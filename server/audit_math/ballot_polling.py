"""
This is a wrapper class to accomodate using more than one test statistics for
ballot polling audits.
"""
from typing import Dict, Tuple, Optional
from typing_extensions import Literal, TypedDict
from ..models import BallotPollingType
from .sampler_contest import Contest
from . import bravo, minerva


class SampleSizeOption(TypedDict):
    type: Optional[Literal["ASN"]]
    size: int
    prob: Optional[float]


def get_sample_size(
    risk_limit: int,
    contest: Contest,
    sample_results: Optional[Dict[str, Dict[str, int]]],
    round_sizes: Dict[int, int],
    math_type: BallotPollingType,
) -> Dict[str, SampleSizeOption]:
    """
    Compute sample size using the specified math.

    Inputs:
        - risk_limit: The integer percentage risk-limit entered by the user
        - contest: The contest we're auditing
        - sample_results: the sample results by round
        - mathtype: which math to use (Minerva or BRAVO at the moment)
    Outputs:
        - A sample size dictionary containing sample sizes for different
          finishing probabilities
    """

    if math_type == BallotPollingType.MINERVA:
        return minerva.get_sample_size(risk_limit, contest, sample_results, round_sizes)
    else:
        # Default to BRAVO math
        return bravo.get_sample_size(risk_limit, contest, sample_results)


def compute_risk(
    risk_limit: int,
    contest: Contest,
    sample_results: Dict[str, Dict[str, int]],
    round_sizes: Dict[int, int],
    math_type: BallotPollingType,
) -> Tuple[Dict[Tuple[str, str], float], bool]:

    if math_type == BallotPollingType.MINERVA:
        return minerva.compute_risk(risk_limit, contest, sample_results, round_sizes)
    else:
        # Default to BRAVO
        return bravo.compute_risk(risk_limit, contest, sample_results)

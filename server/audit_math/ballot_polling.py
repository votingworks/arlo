"""
This is a wrapper class to accomodate using more than one test statistics for
ballot polling audits.
"""

from typing import Dict, Tuple, Optional

from ..models import AuditMathType
from .sampler_contest import Contest
from . import bravo, minerva, providence
from .ballot_polling_types import (
    SampleSizeOption,
    BALLOT_POLLING_ROUND_SIZES,
    BALLOT_POLLING_SAMPLE_RESULTS,
)


def get_sample_size(
    risk_limit: int,
    contest: Contest,
    sample_results: Optional[BALLOT_POLLING_SAMPLE_RESULTS],
    math_type: AuditMathType,
    round_sizes: Optional[BALLOT_POLLING_ROUND_SIZES],
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

    if math_type == AuditMathType.MINERVA:
        return minerva.get_sample_size(risk_limit, contest, sample_results, round_sizes)
    elif math_type == AuditMathType.PROVIDENCE:
        return providence.get_sample_size(
            risk_limit, contest, sample_results, round_sizes
        )
    else:
        # Default to BRAVO math
        return bravo.get_sample_size(risk_limit, contest, sample_results, round_sizes)


def compute_risk(
    risk_limit: int,
    contest: Contest,
    sample_results: BALLOT_POLLING_SAMPLE_RESULTS,
    samples_not_found: Dict[str, int],
    math_type: AuditMathType,
    round_sizes: BALLOT_POLLING_ROUND_SIZES,
) -> Tuple[Dict[Tuple[str, str], float], bool]:
    sample_results = {  # Make a copy so we don't mutate the original results
        round_id: dict(round_results)
        for round_id, round_results in sample_results.items()
    }
    # When a sampled ballot can't be found, count it as a vote for every loser
    for round_id, num_not_found in samples_not_found.items():
        for loser in contest.losers:
            sample_results[round_id][loser] += num_not_found

    if math_type == AuditMathType.MINERVA:
        return minerva.compute_risk(
            risk_limit, contest, sample_results, round_sizes
        )  # pragma: no cover
    elif math_type == AuditMathType.PROVIDENCE:
        return providence.compute_risk(risk_limit, contest, sample_results, round_sizes)
    else:
        # Default to BRAVO
        return bravo.compute_risk(risk_limit, contest, sample_results)

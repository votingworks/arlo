from typing import Dict, NamedTuple, Optional
from .sampler_contest import Contest

# pylint: disable=unused-argument

# CVR: { contest_id: { choice_id: 0 | 1 }}
# CVRS: { ballot_id: CVR }
CVR = Dict[str, Dict[str, int]]
CVRS = Dict[str, Optional[CVR]]

RESULTS = CVRS


class HybridPair(NamedTuple):
    non_cvr: int
    cvr: int


class BallotPollingStratum:
    """
    A class encapsulating a stratum of ballots in an election. Each stratum is its
    own contest object, with its own margin. Strata, along with the overall
    contest object, are passed to the SUITE module when perfoming mixed-strata
    audits.
    """

    SAMPLE_RESULTS = Optional[Dict[str, Dict[str, int]]]  # ballot polling

    contest: Contest
    sample: SAMPLE_RESULTS
    sample_size: int

    def __init__(
        self, contest: Contest, sample_results: SAMPLE_RESULTS, sample_size: int,
    ):
        self.contest = contest
        self.sample = sample_results
        self.sample_size = sample_size


class BallotComparisonStratum:
    """
    A class encapsulating a stratum of ballots in an election. Each stratum is its
    own contest object, with its own margin. Strata, along with the overall
    contest object, are passed to the SUITE module when perfoming mixed-strata
    audits.
    """

    contest: Contest
    results: RESULTS
    sample_size: int

    def __init__(
        self,
        contest: Contest,
        results: RESULTS,
        misstatements: Dict[str, int],
        sample_size: int,
    ):
        self.contest = contest
        self.results = results
        self.misstatements = misstatements
        self.sample_size = sample_size


def get_misstatements(contest, reported_cvr, sample, winner, loser):
    return {}


def get_sample_size(
    risk_limit: int,
    contest: Contest,
    non_cvr_stratum: BallotPollingStratum,
    cvr_stratum: BallotComparisonStratum,
):
    return {
        "asn": {"size": HybridPair(cvr=1, non_cvr=2), "prob": 0.5},
        "0.7": {"size": HybridPair(cvr=3, non_cvr=4), "prob": 0.7},
        "0.8": {"size": HybridPair(cvr=5, non_cvr=6), "prob": 0.8},
        "0.9": {"size": HybridPair(cvr=7, non_cvr=8), "prob": 0.9},
    }

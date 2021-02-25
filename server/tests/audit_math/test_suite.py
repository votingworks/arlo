# pylint: disable=invalid-name
from decimal import Decimal
import math
import pytest

from ...audit_math import suite_sprt
from ...audit_math.sampler_contest import Contest, Stratum
from ...models import AuditMathType

SEED = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
RISK_LIMIT = 10
ALPHA = Decimal(0.05)

@pytest.fixture
def contests():
    contests = {}

    for contest in sprt_contests:
        contests[contest]  = Contest(contest, sprt_contests[contest])

    return contests

@pytest.fixture
def strata(contests):
    strata = {}

    for stratum in sprt_strata:
        strata[stratum] = Stratum(
                            contests[stratum], # this only works because there's one stratum
                            AuditMathType.BRAVO,
                            None,
                            sprt_strata[stratum]["sample"],
                            sprt_strata[stratum]["sample_size"]
                        )

    return strata

def test_sprt_functionality(contests, strata):

    for contest in contests:
        pvalue = suite_sprt.ballot_polling_sprt(
                    ALPHA,
                    contests[contest],
                    strata[contest],
                    {('winner','loser'): 0}
                )[('winner', 'loser')]
        expected_pvalue = expected_sprt_pvalues[contest][('winner', 'loser')]
        delta = Decimal(0.00005)
        assert abs(pvalue - expected_pvalue) < delta, contest


@pytest.fixture
def analytic_contests():
    contests = {}

    for contest in analytic_sprt_contests:
        contests[contest]  = Contest(contest, analytic_sprt_contests[contest])

    return contests

@pytest.fixture
def analytic_strata(analytic_contests):
    strata = {}

    for stratum in analytic_sprt_strata:
        strata[stratum] = Stratum(
                            analytic_contests[stratum], # this only works because there's one stratum
                            AuditMathType.BRAVO,
                            None,
                            analytic_sprt_strata[stratum]["sample"],
                            analytic_sprt_strata[stratum]["sample_size"]
                        )

    return strata

def test_sprt_analytic_example(analytic_contests, analytic_strata):
    for contest in analytic_contests:
        pvalue = suite_sprt.ballot_polling_sprt(
                    ALPHA,
                    analytic_contests[contest],
                    analytic_strata[contest],
                    {('winner','loser'): 0}
                )[('winner', 'loser')]
        expected_pvalue = expected_analytic_sprt_pvalues[contest][('winner', 'loser')]
        delta = Decimal(0.00005)
        assert abs(pvalue - expected_pvalue) < delta, contest


def test_edge_cases(analytic_contests, analytic_strata):
    with pytest.raises(Exception, match=r"Null is impossible, given the sample"):
        pvalue = suite_sprt.ballot_polling_sprt(
                    ALPHA,
                    analytic_contests['contest1'],
                    analytic_strata['contest1'],
                    {('winner','loser'): 7}
                )[('winner', 'loser')]
        delta = Decimal(0.00005)
        assert abs(pvalue - 1) < delta, 'contest1'




sprt_contests = {
    'contest1': {
        "winner": 500,
        "loser": 450,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1
    },
    'contest2': {
        "winner": 600,
        "loser": 400,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1
    },
    'contest3': {
        "winner": 500,
        "loser": 450,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1
    },
    'contest4': {
        "winner": 500,
        "loser": 450,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1
    },
}


analytic_sprt_contests = {
    'contest1': {
        "winner": 5,
        "loser": 4,
        "ballots": 10,
        "numWinners": 1,
        "votesAllowed": 1
    },
    'contest2': {
        "winner": 6,
        "loser": 4,
        "ballots": 10,
        "numWinners": 1,
        "votesAllowed": 1
    },
    'contest3': {
        "winner": 6,
        "loser": 4,
        "ballots": 10,
        "numWinners": 1,
        "votesAllowed": 1
    },
}

sprt_strata = {
    "contest1": {
        "sample_size": 100,
        "sample": {
            "round1": {
                "winner": 50,
                "loser": 50
            }
        }
    },
    "contest2": {
        "sample_size": 100,
        "sample": {
            "round1": {
                "winner": 60,
                "loser": 40
            }
        }
    },
    "contest3": {
        "sample_size": 250,
        "sample": {
            "round1": {
                "winner": 110,
                "loser": 100
            }
        }
    },
    "contest4": {
        "sample_size": 100,
        "sample": {
            "round1": {
                "winner": 40,
                "loser": 60
            }
        }
    },
}


analytic_sprt_strata = {
    "contest1": {
        "sample_size": 4,
        "sample": {
            "round1": {
                "winner": 2,
                "loser": 2
            }
        }
    },
    "contest2": {
        "sample_size": 4,
        "sample": {
            "round1": {
                "winner": 3,
                "loser": 1
            }
        }
    },
    "contest3": {
        "sample_size": 3,
        "sample": {
            "round1": {
                "winner": 2,
                "loser": 1
            }
        }
    },
}

expected_sprt_pvalues = {
    'contest1': {('winner','loser'): 1},
    'contest2': {('winner','loser'): 0.10693399},
    'contest3': {('winner','loser'): 1},
    'contest4': {('winner','loser'): 1},
}
expected_analytic_sprt_pvalues = {
    'contest1': {('winner','loser'): 1},
    'contest2': {('winner','loser'): 0.625},
    'contest3': {('winner','loser'): 0.83333333},
}

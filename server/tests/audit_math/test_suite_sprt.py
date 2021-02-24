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

'''
def test_sprt_analytic_example():
    sample = [0, 0, 1, 1]
    population = [0]*5 + [1]*5
    popsize = len(population)
    res = ballot_polling_sprt(sample, popsize, alpha=0.05, Vw=5, Vl=4, number_invalid=0)
    np.testing.assert_almost_equal(res['LR'], 0.6)
    np.testing.assert_almost_equal(res['Nu_used'], 0)
    res2 = ballot_polling_sprt(sample, popsize, alpha=0.05, Vw=5, Vl=4)
    np.testing.assert_almost_equal(res2['LR'], 0.6, decimal=2)
    np.testing.assert_almost_equal(res2['Nu_used'], 0)

    sample = [0, 1, 1, 1]
    res = ballot_polling_sprt(sample, popsize, alpha=0.05, Vw=6, Vl=4, number_invalid=0)
    np.testing.assert_almost_equal(res['LR'], 1.6)
    res2 = ballot_polling_sprt(sample, popsize, alpha=0.05, Vw=6, Vl=4)
    np.testing.assert_almost_equal(res2['LR'], 1.6, decimal=2)
    np.testing.assert_almost_equal(res2['Nu_used'], 0, decimal=2)

    sample = [0, 1, 1]
    res = ballot_polling_sprt(sample, popsize, alpha=0.05, Vw=6, Vl=4, number_invalid=0)
    np.testing.assert_almost_equal(res['LR'], 1.2)
    res2 = ballot_polling_sprt(sample, popsize, alpha=0.05, Vw=6, Vl=4)
    np.testing.assert_almost_equal(res2['LR'], 1.2, decimal=2)
    np.testing.assert_almost_equal(res2['Nu_used'], 0, decimal=2)


def test_edge_cases():
    sample = [0, 0, 1, 1]
    population = [0]*5 + [1]*5
    popsize = len(population)

    # if nuisance_param < 0 or nuisance_param > popsize
    res = ballot_polling_sprt(sample, popsize, alpha=0.05, Vw=6, Vl=4, number_invalid=12)
    np.testing.assert_almost_equal(res['decision'], 'Number invalid is incompatible with the null and the data')

    # if nuisance_param < Wn or (nuisance_param - null_margin) < Ln \
    #    or number_invalid < Un:
    res = ballot_polling_sprt(sample, popsize, alpha=0.05, Vw=6, Vl=4, number_invalid=7)
    np.testing.assert_almost_equal(res['decision'], 'Number invalid is incompatible with the null and the data')

    # if upper_Nw_limit < Wn or (upper_Nw_limit - null_margin) < Ln:
    res = ballot_polling_sprt(sample, popsize, alpha=0.05, Vw=6, Vl=4, null_margin=7)
    np.testing.assert_almost_equal(res['decision'], 'Null is impossible, given the sample')
'''



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

expected_sprt_pvalues = {
    'contest1': {('winner','loser'): 1},
    'contest2': {('winner','loser'): 0.10693399},
    'contest3': {('winner','loser'): 1},
    'contest4': {('winner','loser'): 1},
}

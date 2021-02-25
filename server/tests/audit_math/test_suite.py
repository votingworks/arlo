# pylint: disable=invalid-name
from decimal import Decimal
import math
import pytest

from ...models import AuditMathType
from ...audit_math.sampler_contest import Contest
from ...audit_math.suite import Stratum
from ...audit_math import supersimple

SEED = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
RISK_LIMIT = 10
ALPHA = Decimal(0.1)

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
        pvalue = strata[contest].compute_pvalue(
                    ALPHA,
                    'winner',
                    'loser',
                    0
                )
        expected_pvalue = expected_sprt_pvalues[contest]
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
        pvalue = analytic_strata[contest].compute_pvalue(
                    ALPHA,
                    'winner',
                    'loser',
                    0
                )
        expected_pvalue = expected_analytic_sprt_pvalues[contest]
        delta = Decimal(0.00005)
        assert abs(pvalue - expected_pvalue) < delta, contest


def test_edge_cases(analytic_contests, analytic_strata):
    with pytest.raises(Exception, match=r"Null is impossible, given the sample"):
        pvalue = analytic_strata['contest1'].compute_pvalue(
                    ALPHA,
                    'winner',
                    'loser',
                    7
                )
        delta = Decimal(0.00005)
        assert abs(pvalue - 1) < delta, 'contest1'


@pytest.fixture
def cvrs():
    cvr = {}
    for i in range(100000):
        if i < 60000:
            contest_a_res = {"winner": 1, "loser": 0}
        else:
            contest_a_res = {"winner": 0, "loser": 1}

        cvr[i] = {"Contest A": contest_a_res}

        if i < 30000:
            cvr[i]["Contest B"] = {"winner": 1, "loser": 0}
        elif 30000 < i < 60000:
            cvr[i]["Contest B"] = {"winner": 0, "loser": 1}

        if i < 18000:
            cvr[i]["Contest C"] = {"winner": 1, "loser": 0}
        elif 18000 < i < 36000:
            cvr[i]["Contest C"] = {"winner": 0, "loser": 1}

        if i < 8000:
            cvr[i]["Contest D"] = {"winner": 1, "loser": 0}
        elif 8000 < i < 14000:
            cvr[i]["Contest D"] = {"winner": 0, "loser": 1}

        if i < 10000:
            cvr[i]["Contest E"] = {"winner": 1, "loser": 0}


    yield cvr


@pytest.fixture
def cvr_contests():
    contests = {}

    for contest in ss_contests:
        contests[contest] = Contest(contest, ss_contests[contest])

    yield contests

@pytest.fixture
def cvr_strata(cvr_contests, cvrs):
    strata = {}
    for contest in cvr_contests:
        stratum = Stratum(cvr_contests[contest],
                          AuditMathType.SUPERSIMPLE,
                          cvrs,
                          None,
                          0)
        strata[contest] = stratum

    return strata


def test_cvr_compute_risk(cvr_strata, cvr_contests):

    for contest in cvr_contests:
        sample_cvr = {}
        sample_size = supersimple.get_sample_sizes(RISK_LIMIT, cvr_contests[contest], None)

        # No discrepancies
        for i in range(sample_size):
            sample_cvr[i] = {
                "times_sampled": 1,
                "cvr": {
                    "Contest A": {"winner": 1, "loser": 0},
                    "Contest B": {"winner": 1, "loser": 0},
                    "Contest C": {"winner": 1, "loser": 0},
                    "Contest D": {"winner": 1, "loser": 0},
                    "Contest E": {"winner": 1, "loser": 0},
                },
            }

        stratum = cvr_strata[contest]
        stratum.sample = sample_cvr
        stratum.sample_size = sample_size
        p_value = stratum.compute_pvalue(ALPHA, "winner", "loser", 1)
        expected_p = expected_p_values["no_discrepancies"][contest]
        diff = abs(p_value - expected_p)

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )
        assert p_value <= ALPHA, "Audit should have finished but didn't"

        '''
        to_sample = {
            "sample_size": sample_size,
            "1-under": 0,
            "1-over": 0,
            "2-under": 0,
            "2-over": 0,
        }

        next_sample_size = supersimple.get_sample_sizes(
            RISK_LIMIT, contests[contest], to_sample
        )
        assert (
            next_sample_size == no_next_sample[contest]
        ), "Number of ballots left to sample is not correct!"
        '''

        # Test one-vote overstatement
        sample_cvr[0] = {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": 0, "loser": 0},
                "Contest B": {"winner": 0, "loser": 0},
                "Contest C": {"winner": 0, "loser": 0},
                "Contest D": {"winner": 0, "loser": 0},
                "Contest E": {"winner": 0, "loser": 0},
            },
        }

        stratum.sample = sample_cvr
        stratum.sample_size = sample_size
        p_value = stratum.compute_pvalue(ALPHA, "winner", "loser", 1)
        expected_p = expected_p_values["one_vote_over"][contest]
        diff = abs(p_value - expected_p)
        finished = p_value <= ALPHA

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )
        if contest in ["Contest E", "Contest F"]:
            assert finished, "Audit should have finished but didn't"
        else:
            assert not finished, "Audit shouldn't have finished but did!"

        '''
        to_sample = {
            "sample_size": sample_size,
            "1-under": 0,
            "1-over": 1,
            "2-under": 0,
            "2-over": 0,
        }

        next_sample_size = supersimple.get_sample_sizes(
            RISK_LIMIT, contests[contest], to_sample
        )
        assert (
            next_sample_size == o1_next_sample[contest]
        ), "Number of ballots left to sample is not correct in contest {}!".format(
            contest
        )
        '''
        # Test two-vote overstatement
        sample_cvr[0] = {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": 0, "loser": 1},
                "Contest B": {"winner": 0, "loser": 1},
                "Contest C": {"winner": 0, "loser": 1},
                "Contest D": {"winner": 0, "loser": 1},
                "Contest E": {"winner": 0, "loser": 1},
            },
        }

        stratum.sample = sample_cvr
        stratum.sample_size = sample_size
        p_value = stratum.compute_pvalue(ALPHA, "winner", "loser", 1)
        expected_p = expected_p_values["two_vote_over"][contest]
        diff = abs(p_value - expected_p)
        finished = p_value <= ALPHA

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )

        if contest in ["Contest F"]:
            assert finished, "Audit should have finished but didn't"
        else:
            assert not finished, "Audit shouldn't have finished but did!"

        '''
        to_sample = {
            "sample_size": sample_size,
            "1-under": 0,
            "1-over": 0,
            "2-under": 0,
            "2-over": 1,
        }

        next_sample_size = supersimple.get_sample_sizes(
            RISK_LIMIT, contests[contest], to_sample
        )
        assert (
            next_sample_size == o2_next_sample[contest]
        ), "Number of ballots left to sample is not correct in contest {}!".format(
            contest
        )
        '''


expected_p_values = {
    "no_discrepancies": {
        "Contest A": 0.06507,
        "Contest B": 0.06973,
        "Contest C": 0.06740,
        "Contest D": 0.07048,
        "Contest E": 0.01950,
        "Contest F": 0.05013,
    },
    "one_vote_over": {
        "Contest A": 0.12534,
        "Contest B": 0.13441,
        "Contest C": 0.12992,
        "Contest D": 0.13585,
        "Contest E": 0.03758,
        "Contest F": 0.05013,
    },
    "two_vote_over": {
        "Contest A": 1.0,
        "Contest B": 1.0,
        "Contest C": 1.0,
        "Contest D": 1.0,
        "Contest E": 0.51877,
        "Contest F": 0.05013,
    },
}



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
    'contest1':  1,
    'contest2':  0.10693399,
    'contest3':  1,
    'contest4':  1,
}
expected_analytic_sprt_pvalues = {
    'contest1': 1,
    'contest2': 0.625,
    'contest3': 0.83333333,
}

ss_contests = {
    "Contest A": {
        "winner": 60000,
        "loser": 40000,
        "ballots": 100000,
        "numWinners": 1,
        "votesAllowed": 1,
    },
    "Contest B": {
        "winner": 30000,
        "loser": 24000,
        "ballots": 60000,
        "numWinners": 1,
        "votesAllowed": 1,
    },
    "Contest C": {
        "winner": 18000,
        "loser": 12600,
        "ballots": 36000,
        "numWinners": 1,
        "votesAllowed": 1,
    },
    "Contest D": {
        "winner": 8000,
        "loser": 6000,
        "ballots": 15000,
        "numWinners": 1,
        "votesAllowed": 1,
    },
    "Contest E": {
        "winner": 10000,
        "loser": 0,
        "ballots": 10000,
        "numWinners": 1,
        "votesAllowed": 1,
    },
    "Contest F": {
        "winner": 10,
        "loser": 4,
        "ballots": 15,
        "numWinners": 1,
        "votesAllowed": 1,
    },
}

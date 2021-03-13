# pylint: disable=invalid-name
from decimal import Decimal
import pytest

from ...audit_math.sampler_contest import Contest
from ...audit_math.suite import (
    BallotPollingStratum,
    BallotComparisonStratum,
    compute_risk,
    get_sample_size,
)
from ...audit_math import supersimple

SEED = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
RISK_LIMIT = 10
ALPHA = Decimal(0.1)



@pytest.fixture
def strata():
    strata = {}

    for stratum in sprt_strata:
        strata[stratum] = BallotPollingStratum(
            sprt_ballots,
            sprt_contests[stratum],
            sprt_strata[stratum]["sample"],
            sprt_strata[stratum]["sample_size"],
        )

    return strata


def test_sprt_functionality(strata):

    for contest in strata:
        margin = strata[contest].vote_totals["winner"] - strata[contest].vote_totals["loser"]
        pvalue = strata[contest].compute_pvalue(margin, "winner", "loser", 1)
        expected_pvalue = expected_sprt_pvalues[contest]
        delta = Decimal(0.00005)
        assert abs(pvalue - expected_pvalue) < delta, contest



@pytest.fixture
def analytic_strata():
    strata = {}

    for stratum in analytic_sprt_strata:
        strata[stratum] = BallotPollingStratum(
            analytic_sprt_ballots,
            analytic_sprt_contests[stratum],
            analytic_sprt_strata[stratum]["sample"],
            analytic_sprt_strata[stratum]["sample_size"],
        )

    return strata


def test_sprt_analytic_example(analytic_strata):
    for contest in analytic_strata:
        margin = analytic_strata[contest].vote_totals["winner"] - analytic_strata[contest].vote_totals["loser"]
        pvalue = analytic_strata[contest].compute_pvalue(
            margin, "winner", "loser", 1
        )
        expected_pvalue = expected_analytic_sprt_pvalues[contest]
        delta = Decimal(0.00005)
        assert abs(pvalue - expected_pvalue) < delta, contest


def test_edge_cases(analytic_strata):
    with pytest.raises(Exception, match=r"Null is impossible, given the sample"):
        margin = analytic_strata["contest1"].vote_totals["winner"] - analytic_strata["contest1"].vote_totals["loser"]
        pvalue = analytic_strata["contest1"].compute_pvalue(
            margin, "winner", "loser", 8
        )
        delta = Decimal(0.00005)
        assert abs(pvalue - 1) < delta, "contest1"


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
def cvr_strata(cvrs):
    strata = {}
    for contest in ss_contests:
        num_ballots = ss_ballots[contest]
        vote_totals = ss_contests[contest]
        stratum = BallotComparisonStratum(num_ballots, vote_totals, cvrs, {}, 0)
        strata[contest] = stratum

    return strata


def test_cvr_compute_risk(cvr_strata):

    for contest in cvr_strata:
        sample_size = true_sample_sizes[contest]

        # No discrepancies
        misstatements = {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }

        stratum = cvr_strata[contest]
        stratum.misstatements = misstatements
        stratum.sample_size = sample_size
        reported_margin = ss_contests[contest]["winner"] - ss_contests[contest]["loser"]
        p_value = stratum.compute_pvalue(reported_margin, "winner", "loser", 1)
        expected_p = expected_p_values["no_discrepancies"][contest]
        diff = abs(p_value - expected_p)

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )
        assert p_value <= ALPHA, "Audit should have finished but didn't"

        # Test one-vote overstatement
        misstatements = {
            "o1": 1,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }

        stratum = cvr_strata[contest]
        stratum.misstatements = misstatements
        stratum.sample_size = sample_size
        p_value = stratum.compute_pvalue(reported_margin, "winner", "loser", 1)
        expected_p = expected_p_values["one_vote_over"][contest]
        diff = abs(p_value - expected_p)
        finished = p_value <= ALPHA

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )
        if contest in ["Contest E"]:
            assert finished, "Audit should have finished but didn't"
        else:
            assert not finished, "Audit shouldn't have finished but did!"

        # Test two-vote overstatement
        misstatements = {
            "o1": 0,
            "o2": 1,
            "u1": 0,
            "u2": 0,
        }

        stratum = cvr_strata[contest]
        stratum.misstatements = misstatements
        stratum.sample_size = sample_size
        p_value = stratum.compute_pvalue(reported_margin, "winner", "loser", 1)
        expected_p = expected_p_values["two_vote_over"][contest]
        diff = abs(p_value - expected_p)
        finished = p_value <= ALPHA

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )

        assert not finished, "Audit shouldn't have finished but did!"


def test_fishers_combined():
    """
    This test was derived from the fisher's combination notebook in the CORLA repo, found
    here: https://github.com/pbstark/CORLA18/blob/master/code/fisher_combined_pvalue.ipynb
    """
    contest_dict = {
        "winner": 5300,
        "loser": 5100,
        "ballots": 11000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    cvr_stratum_vote_totals= {
        "winner": 4550,
        "loser": 4950,
    }

    cvr_stratum_ballots =  10000

    cvrs = {}
    for i in range(4550):
        cvrs[i] = {"ex1": {"winner": 1, "loser": 0}}
    for i in range(4550, 9500):
        cvrs[i] = {"ex1": {"winner": 0, "loser": 1}}
    for i in range(9500, 10000):
        cvrs[i] = {"ex1": {"winner": 0, "loser": 0}}

    # We sample 500 ballots from the cvr strata, and find no discrepancies
    misstatements = {
        "o1": 0,
        "o2": 0,
        "u1": 0,
        "u2": 0,
    }

    # Create our CVR strata
    cvr_strata = BallotComparisonStratum(
        cvr_stratum_ballots, cvr_stratum_vote_totals, cvrs, misstatements, sample_size=500
    )

    # Compute its p-value and check, with a lambda of 0.3
    expected_pvalue = 0.23557770396261943
    pvalue = cvr_strata.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    no_cvr_stratum_vote_totals= {
        "winner": 750,
        "loser": 150,
    }
    no_cvr_stratum_ballots = 1000


    # In the no-cvr strata, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_sample = {"ex1": {"winner": 187, "loser": 37}}

    # create our ballot polling strata
    no_cvr_strata = BallotPollingStratum(no_cvr_stratum_ballots, no_cvr_stratum_vote_totals, no_cvr_sample, sample_size=250)

    # Compute its p-value and check, with a lambda of 0.7
    expected_pvalue = 0.006068185147942991
    pvalue = no_cvr_strata.compute_pvalue(reported_margin, "winner", "loser", 0.7)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    pvalue, res = compute_risk(5, contest, no_cvr_strata, cvr_strata)
    expected_pvalue = 0.07049896663377597
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.000001, "Got {}".format(pvalue)
    assert not res


def test_get_sample_size():

    contest_dict = {
        "winner":1011000,
        "loser":989000,
        "ballots": 2000000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)

    cvr_stratum_vote_totals = {
        "winner": 960000,
        "loser": 940000,
    }
    cvr_stratum_num_ballots = 1900000


    cvrs = {}
    for i in range(960000):
        cvrs[i] = {"ex1": {"winner": 1, "loser": 0}}
    for i in range(960000, 1900000):
        cvrs[i] = {"ex1": {"winner": 0, "loser": 1}}

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        "o1": 0,
        "o2": 0,
        "u1": 0,
        "u2": 0,
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_num_ballots, cvr_stratum_vote_totals, cvrs, misstatements, sample_size=0
    )

    no_cvr_stratum_vote_totals = {
        "winner": 51000,
        "loser": 49000,
    }
    no_cvr_stratum_num_ballots = 100000


    # In the no-cvr stratum, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_sample = {"ex1": {"winner": 0, "loser": 0}}

    # create our ballot polling stratum
    no_cvr_stratum = BallotPollingStratum(no_cvr_stratum_num_ballots, no_cvr_stratum_vote_totals
            , no_cvr_sample, sample_size=0)

    expected_sample_size = (3800,200)

    assert expected_sample_size == get_sample_size(
        5, contest, no_cvr_stratum, cvr_stratum
    )


expected_p_values = {
    "no_discrepancies": {
        "Contest A": 0.06507,
        "Contest B": 0.06973,
        "Contest C": 0.06740,
        "Contest D": 0.07048,
        "Contest E": 0.01950,
    },
    "one_vote_over": {
        "Contest A": 0.12534,
        "Contest B": 0.13441,
        "Contest C": 0.12992,
        "Contest D": 0.13585,
        "Contest E": 0.03758,
    },
    "two_vote_over": {
        "Contest A": 1.0,
        "Contest B": 1.0,
        "Contest C": 1.0,
        "Contest D": 1.0,
        "Contest E": 0.51877,
    },
}


sprt_contests = {
    "contest1": {
        "winner": 500,
        "loser": 450,
    },
    "contest2": {
        "winner": 600,
        "loser": 400,
    },
    "contest3": {
        "winner": 500,
        "loser": 450,
    },
    "contest4": {
        "winner": 500,
        "loser": 450,
    },
}

sprt_ballots = 1000


analytic_sprt_contests = {
    "contest1": {
        "winner": 5,
        "loser": 4,
    },
    "contest2": {
        "winner": 6,
        "loser": 4,
    },
    "contest3": {
        "winner": 6,
        "loser": 4,
    },
}
analytic_sprt_ballots = 10

sprt_strata = {
    "contest1": {"sample_size": 100, "sample": {"round1": {"winner": 50, "loser": 50}}},
    "contest2": {"sample_size": 100, "sample": {"round1": {"winner": 60, "loser": 40}}},
    "contest3": {
        "sample_size": 250,
        "sample": {"round1": {"winner": 110, "loser": 100}},
    },
    "contest4": {"sample_size": 100, "sample": {"round1": {"winner": 40, "loser": 60}}},
}


analytic_sprt_strata = {
    "contest1": {"sample_size": 4, "sample": {"round1": {"winner": 2, "loser": 2}}},
    "contest2": {"sample_size": 4, "sample": {"round1": {"winner": 3, "loser": 1}}},
    "contest3": {"sample_size": 3, "sample": {"round1": {"winner": 2, "loser": 1}}},
}

expected_sprt_pvalues = {
    "contest1": 1,
    "contest2": 0.10693399,
    "contest3": 1,
    "contest4": 1,
}
expected_analytic_sprt_pvalues = {
    "contest1": 1,
    "contest2": 0.625,
    "contest3": 0.83333333,
}

ss_ballots = {
    "Contest A": 100000,
    "Contest B": 60000,
    "Contest C": 36000,
    "Contest D": 15000,
    "Contest E": 10000,

}

ss_contests = {
    "Contest A": {
        "winner": 60000,
        "loser": 40000,
    },
    "Contest B": {
        "winner": 30000,
        "loser": 24000,
    },
    "Contest C": {
        "winner": 18000,
        "loser": 12600,
    },
    "Contest D": {
        "winner": 8000,
        "loser": 6000,
    },
    "Contest E": {
        "winner": 10000,
        "loser": 0,
    },
}

true_sample_sizes = {
    "Contest A": 27,
    "Contest B": 54,
    "Contest C": 36,
    "Contest D": 40,
    "Contest E": 6,
    "Contest F": 14,
    "Two-winner Contest": 27,
}

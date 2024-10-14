# pylint: disable=invalid-name,consider-using-dict-items,consider-using-f-string
from decimal import Decimal
from itertools import product
import pytest


from ...audit_math.sampler_contest import Contest
from ...audit_math.suite import (
    BallotPollingStratum,
    BallotComparisonStratum,
    compute_risk,
    get_sample_size,
    HybridPair,
    maximize_fisher_combined_pvalue,
    try_n,
    misstatements,
)

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
        margin = (
            strata[contest].vote_totals["winner"] - strata[contest].vote_totals["loser"]
        )
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
        margin = (
            analytic_strata[contest].vote_totals["winner"]
            - analytic_strata[contest].vote_totals["loser"]
        )
        pvalue = analytic_strata[contest].compute_pvalue(margin, "winner", "loser", 1)
        expected_pvalue = expected_analytic_sprt_pvalues[contest]
        delta = Decimal(0.00005)
        assert abs(pvalue - expected_pvalue) < delta, contest


def test_edge_cases(analytic_strata):
    margin = (
        analytic_strata["contest1"].vote_totals["winner"]
        - analytic_strata["contest1"].vote_totals["loser"]
    )
    pvalue = analytic_strata["contest1"].compute_pvalue(margin, "winner", "loser", 8)
    assert pvalue == 0


@pytest.fixture
def cvr_strata():
    strata = {}
    for contest in ss_contests:
        num_ballots = ss_ballots[contest]
        vote_totals = ss_contests[contest]
        stratum = BallotComparisonStratum(num_ballots, vote_totals, {}, 0)
        strata[contest] = stratum

    return strata


def test_cvr_compute_risk(cvr_strata):

    for contest in cvr_strata:
        sample_size = true_sample_sizes[contest]

        # No discrepancies
        misstatements = {
            ("winner", "loser"): {
                "o1": 0,
                "o2": 0,
                "u1": 0,
                "u2": 0,
            }
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
            ("winner", "loser"): {
                "o1": 1,
                "o2": 0,
                "u1": 0,
                "u2": 0,
            }
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
            ("winner", "loser"): {
                "o1": 0,
                "o2": 1,
                "u1": 0,
                "u2": 0,
            }
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

    cvr_stratum_vote_totals = {
        "winner": 4550,
        "loser": 4950,
    }

    cvr_stratum_ballots = 10000

    # We sample 500 ballots from the cvr strata, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR strata
    cvr_strata = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=500,
    )

    # Compute its p-value and check, with a lambda of 0.3
    expected_pvalue = 0.23557770396261943
    pvalue = cvr_strata.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    no_cvr_stratum_vote_totals = {
        "winner": 750,
        "loser": 150,
    }
    no_cvr_stratum_ballots = 1000

    # In the no-cvr strata, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_sample = {"ex1": {"winner": 187, "loser": 37}}

    # create our ballot polling strata
    no_cvr_strata = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        no_cvr_sample,
        sample_size=250,
    )

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
        "winner": 1011000,
        "loser": 989000,
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

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_num_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
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
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_num_ballots,
        no_cvr_stratum_vote_totals,
        no_cvr_sample,
        sample_size=0,
    )

    expected_sample_size = HybridPair(cvr=3800, non_cvr=200)

    assert expected_sample_size == get_sample_size(
        5, contest, no_cvr_stratum, cvr_stratum
    )


def test_winner_loses_no_cvr():

    contest_dict = {
        "winner": 5300,
        "loser": 5100,
        "ballots": 11000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    no_cvr_stratum_vote_totals = {
        "winner": 4550,
        "loser": 4950,
    }

    no_cvr_sample = {"ex1": {"winner": 227, "loser": 247}}
    no_cvr_stratum_ballots = 10000
    # create our ballot polling strata
    no_cvr_strata = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        no_cvr_sample,
        sample_size=500,
    )
    # Compute its p-value and check, with a lambda of 0.7
    expected_pvalue = 0.9670403493064489
    pvalue = no_cvr_strata.compute_pvalue(reported_margin, "winner", "loser", 0.7)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Create our CVR strata
    cvr_stratum_vote_totals = {
        "winner": 750,
        "loser": 150,
    }
    cvr_stratum_ballots = 1000

    # We sample 250 ballots from the cvr strata, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }
    cvr_strata = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=250,
    )

    # Compute its p-value and check, with a lambda of 0.3
    expected_pvalue = 0.0006592649872177509
    pvalue = cvr_strata.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    # Now get the combined pvalue
    pvalue, res = compute_risk(5, contest, no_cvr_strata, cvr_strata)
    expected_pvalue = 0.9961600910311891
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.000001, "Got {}".format(pvalue)
    assert not res


def test_close_contest_many_undervotes():
    contest_dict = {
        "winner": 2200,
        "loser": 2150,
        "ballots": 11000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    cvr_stratum_vote_totals = {
        "winner": 1750,
        "loser": 1750,
    }

    cvr_stratum_ballots = 10000

    # We sample 500 ballots from the cvr strata, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR strata
    cvr_strata = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=500,
    )

    # Compute its p-value and check, with a lambda of 0.3
    expected_pvalue = 0.6969532708975282
    pvalue = cvr_strata.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    no_cvr_stratum_vote_totals = {
        "winner": 450,
        "loser": 400,
    }
    no_cvr_stratum_ballots = 1000

    # In the no-cvr strata, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_sample = {"ex1": {"winner": 112, "loser": 100}}

    # create our ballot polling strata
    no_cvr_strata = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        no_cvr_sample,
        sample_size=250,
    )

    # Compute its p-value and check, with a lambda of 0.7
    expected_pvalue = 0.8106977731409347
    pvalue = no_cvr_strata.compute_pvalue(reported_margin, "winner", "loser", 0.7)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    pvalue, res = compute_risk(5, contest, no_cvr_strata, cvr_strata)
    expected_pvalue = 0.9250601803054523
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.000001, "Got {}".format(pvalue)
    assert not res


def test_wide_margin():
    contest_dict = {
        "winner": 990,
        "loser": 10,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    cvr_stratum_vote_totals = {
        "winner": 940,
        "loser": 10,
    }

    cvr_stratum_ballots = 950

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    no_cvr_stratum_vote_totals = {
        "winner": 50,
        "loser": 0,
    }
    no_cvr_stratum_ballots = 50

    # create our ballot polling stratum
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        {},
        sample_size=0,
    )

    # Now try getting a sample size
    expected_sample_size = HybridPair(cvr=10, non_cvr=0)

    assert expected_sample_size == get_sample_size(
        5, contest, no_cvr_stratum, cvr_stratum
    )

    # Take some silly samples

    # Compute CVR stratum p-value and check, with a lambda of 0.3
    cvr_stratum.sample_size = 500
    expected_pvalue = 0.0
    pvalue = cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    # In the no-cvr stratum, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_stratum.sample = {"ex1": {"winner": 49, "loser": 0}}
    no_cvr_stratum.sample_size = 49
    pvalue = no_cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.7)
    expected_pvalue = 0.0
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    pvalue, res = compute_risk(5, contest, no_cvr_stratum, cvr_stratum)
    expected_pvalue = 0.0
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.000001, "Got {}".format(pvalue)
    assert res


def test_wrong_outcome():
    contest_dict = {
        "winner": 990,
        "loser": 10,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    cvr_stratum_vote_totals = {
        "winner": 940,
        "loser": 10,
    }

    cvr_stratum_ballots = 950

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 100,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    no_cvr_stratum_vote_totals = {
        "winner": 50,
        "loser": 0,
    }
    no_cvr_stratum_ballots = 50

    # create our ballot polling stratum
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        {},
        sample_size=0,
    )

    # Take some silly samples

    # Compute CVR stratum p-value and check, with a lambda of 0.3
    cvr_stratum.sample_size = 500
    expected_pvalue = 1.0
    pvalue = cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    # In the no-cvr stratum, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_stratum.sample = {"ex1": {"winner": 0, "loser": 49}}
    no_cvr_stratum.sample_size = 49
    # Compute its p-value and check, with a lambda of 0.7
    pvalue = no_cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.7)
    expected_pvalue = 1.0
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    pvalue, res = compute_risk(5, contest, no_cvr_stratum, cvr_stratum)
    expected_pvalue = 1.0
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.000001, "Got {}".format(pvalue)
    assert not res


def test_escalation():
    contest_dict = {
        "winner": 600,
        "loser": 400,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    cvr_stratum_vote_totals = {
        "winner": 400,
        "loser": 300,
    }

    cvr_stratum_ballots = 700

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    no_cvr_stratum_vote_totals = {
        "winner": 200,
        "loser": 100,
    }
    no_cvr_stratum_ballots = 300

    # create our ballot polling stratum
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        {},
        sample_size=0,
    )

    expected_sample_size = HybridPair(cvr=56, non_cvr=24)

    assert expected_sample_size == get_sample_size(
        5, contest, no_cvr_stratum, cvr_stratum
    )

    # Take some silly samples

    # Compute CVR stratum p-value and check, with a lambda of 0.3
    cvr_stratum.sample_size = 56
    expected_pvalue = 0.0945345798479189
    pvalue = cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    # In the no-cvr stratum, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_stratum.sample = {"round1": {"winner": 14, "loser": 10}}
    no_cvr_stratum.sample_size = 24
    # Compute its p-value and check, with a lambda of 0.7
    pvalue = no_cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.7)
    expected_pvalue = 0.4540875636833894
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    pvalue, res = compute_risk(5, contest, no_cvr_stratum, cvr_stratum)
    expected_pvalue = 0.21456844367035688
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.000001, "Got {}".format(pvalue)
    assert not res

    # Now get another sample

    expected_sample_size = HybridPair(cvr=101, non_cvr=43)

    assert expected_sample_size == get_sample_size(
        5, contest, no_cvr_stratum, cvr_stratum
    )

    # Take another sample

    cvr_stratum.misstatements = {
        ("winner", "loser"): {
            "o1": 4,
            "o2": 1,
            "u1": 0,
            "u2": 0,
        }
    }
    cvr_stratum.sample_size = 101
    expected_pvalue = 1.0
    pvalue = cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, f"Incorrect pvalue: {pvalue}!"

    # In the no-cvr stratum, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_stratum.sample = {
        "round1": {"winner": 14, "loser": 10},
        "round2": {"winner": 18, "loser": 1},
    }
    no_cvr_stratum.sample_size = 43
    # Compute its p-value and check, with a lambda of 0.7
    pvalue = no_cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.7)
    expected_pvalue = 9.572332760803416e-05
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    pvalue, res = compute_risk(5, contest, no_cvr_stratum, cvr_stratum)
    expected_pvalue = 0.00912863118679208
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.000001, "Got {}".format(pvalue)
    assert res


def test_really_close_race():
    contest_dict = {
        "winner": 502,
        "loser": 498,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    cvr_stratum_vote_totals = {
        "winner": 351,
        "loser": 349,
    }

    cvr_stratum_ballots = 700

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    no_cvr_stratum_vote_totals = {
        "winner": 151,
        "loser": 149,
    }
    no_cvr_stratum_ballots = 300

    # create our ballot polling stratum
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        {},
        sample_size=0,
    )

    with pytest.raises(ValueError, match=r"One or both strata need to be recounted"):
        get_sample_size(5, contest, no_cvr_stratum, cvr_stratum)

    # Take some silly samples

    # Compute CVR stratum p-value and check, with a lambda of 0.3
    cvr_stratum.sample_size = 699
    expected_pvalue = 0.561657191343699
    pvalue = cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    # In the no-cvr stratum, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_stratum.sample = {"round1": {"winner": 151, "loser": 148}}
    no_cvr_stratum.sample_size = 299
    # Compute its p-value and check, with a lambda of 0.7
    pvalue = no_cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.7)
    expected_pvalue = 0.0
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    pvalue, res = compute_risk(5, contest, no_cvr_stratum, cvr_stratum)
    expected_pvalue = 0.40032246260273263
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.000001, "Got {}".format(pvalue)

    assert not res


def test_multi_winner():
    contest_dict = {
        "Bageman": 500,
        "Booth": 125,
        "Bullen": 2625,
        "Clinton": 1789,
        "Cummings": 123,
        "Deaver": 3051,
        "Fox": 2088,
        "Foutz": 127,
        "Guccione": 1680,
        "Hoskins": 150,
        "Jorgensen": 2112,
        "Turner": 468,
        "Vece": 127,
        "ballots": 8402,
        "numWinners": 2,
        "votesAllowed": 2,
    }

    contest = Contest("ex1", contest_dict)
    cvr_stratum_vote_totals = {
        "Bageman": 396,
        "Booth": 3,
        "Bullen": 2484,
        "Clinton": 1580,
        "Cummings": 50,
        "Deaver": 2519,
        "Fox": 1978,
        "Foutz": 16,
        "Guccione": 1580,
        "Hoskins": 50,
        "Jorgensen": 2012,
        "Turner": 358,
        "Vece": 16,
    }
    cvr_stratum_ballots = 6542

    misstatements = {}
    for winner, loser in product(contest.winners, contest.losers):
        # We sample 500 ballots from the cvr stratum, and find no discrepancies
        misstatements[(winner, loser)] = {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    no_cvr_stratum_vote_totals = {
        "Bageman": 104,
        "Booth": 122,
        "Bullen": 141,
        "Clinton": 209,
        "Cummings": 73,
        "Deaver": 532,
        "Fox": 110,
        "Foutz": 111,
        "Guccione": 100,
        "Hoskins": 100,
        "Jorgensen": 100,
        "Turner": 110,
        "Vece": 111,
    }
    no_cvr_stratum_ballots = 1860

    # create our ballot polling stratum
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        {},
        sample_size=0,
    )

    expected_sample_size = HybridPair(cvr=164, non_cvr=46)

    assert expected_sample_size == get_sample_size(
        5, contest, no_cvr_stratum, cvr_stratum
    )


def test_multi_candidate():
    contest_dict = {
        "winner": 600,
        "loser": 300,
        "loser2": 100,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    cvr_stratum_vote_totals = {
        "winner": 400,
        "loser": 200,
        "loser2": 100,
    }

    cvr_stratum_ballots = 700

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        },
        ("winner", "loser2"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        },
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    no_cvr_stratum_vote_totals = {"winner": 200, "loser": 100, "loser2": 0}
    no_cvr_stratum_ballots = 300

    # create our ballot polling stratum
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        {},
        sample_size=0,
    )

    expected_sample_size = HybridPair(cvr=33, non_cvr=14)

    assert expected_sample_size == get_sample_size(
        5, contest, no_cvr_stratum, cvr_stratum
    )

    # Take some silly samples

    # Compute CVR stratum p-value and check, with a lambda of 0.3
    cvr_stratum.sample_size = 33
    expected_pvalue = 0.1215302377137314
    pvalue = cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    # In the no-cvr stratum, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_stratum.sample = {"round1": {"winner": 10, "loser": 4, "loser2": 0}}
    no_cvr_stratum.sample_size = 14
    # Compute its p-value and check, with a lambda of 0.7
    pvalue = no_cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.7)
    expected_pvalue = 0.00820155391878346
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    pvalue, res = compute_risk(5, contest, no_cvr_stratum, cvr_stratum)
    expected_pvalue = 0.015691091068564367
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.0001, "Got {}".format(pvalue)
    assert res


def test_tie():
    contest_dict = {
        "winner": 500,
        "loser": 500,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    cvr_stratum_vote_totals = {
        "winner": 350,
        "loser": 350,
    }

    cvr_stratum_ballots = 700

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    no_cvr_stratum_vote_totals = {
        "winner": 150,
        "loser": 150,
    }
    no_cvr_stratum_ballots = 300

    # create our ballot polling stratum
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        {},
        sample_size=0,
    )

    with pytest.raises(ValueError, match=r"One or both strata need to be recounted"):
        get_sample_size(5, contest, no_cvr_stratum, cvr_stratum)

    # Take some silly samples

    # Compute CVR stratum p-value and check, with a lambda of 0.3
    cvr_stratum.sample_size = 56
    expected_pvalue = 1.0
    pvalue = cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.3)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    # In the no-cvr stratum, we sample 250 ballots and find 187 votes for the winner
    # and 37 for the loser
    no_cvr_stratum.sample = {"round1": {"winner": 150, "loser": 149}}
    no_cvr_stratum.sample_size = 249
    # Compute its p-value and check, with a lambda of 0.7
    pvalue = no_cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.7)
    expected_pvalue = 1.0
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    pvalue, res = compute_risk(5, contest, no_cvr_stratum, cvr_stratum)
    expected_pvalue = 1.0
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.000001, "Got {}".format(pvalue)
    assert not res


def test_tiny_election():
    contest_dict = {
        "winner": 10,
        "loser": 0,
        "ballots": 10,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)

    no_cvr_stratum_vote_totals = {
        "winner": 6,
        "loser": 0,
    }
    no_cvr_stratum_ballots = 6
    no_cvr_sample = {"round1": {"winner": 0, "loser": 0}}

    # create our ballot polling strata
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        no_cvr_sample,
        sample_size=0,
    )

    cvr_stratum_vote_totals = {
        "winner": 4,
        "loser": 0,
    }

    cvr_stratum_ballots = 4

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    expected_sample_size = HybridPair(cvr=3, non_cvr=3)

    assert expected_sample_size == get_sample_size(
        5, contest, no_cvr_stratum, cvr_stratum
    )

    no_cvr_stratum.sample = {"round1": {"winner": 2, "loser": 0}}
    no_cvr_stratum.sample_size = 2

    cvr_stratum.sample_size = 3
    pvalue = maximize_fisher_combined_pvalue(
        0.05, contest, no_cvr_stratum, cvr_stratum, "winner", "loser", 1.0
    )
    # Compute its p-value and check, with a lambda of 0.7
    expected_pvalue = 0.13732787993505824
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)


def test_invalid_try_n():
    contest_dict = {
        "winner": 10,
        "loser": 0,
        "ballots": 10,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)

    no_cvr_stratum_vote_totals = {
        "winner": 6,
        "loser": 0,
    }
    no_cvr_stratum_ballots = 7
    no_cvr_sample = {"round1": {"winner": 0, "loser": 0}}

    # create our ballot polling strata
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        no_cvr_sample,
        sample_size=0,
    )

    cvr_stratum_vote_totals = {
        "winner": 4,
        "loser": 0,
    }

    cvr_stratum_ballots = 4

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    no_cvr_stratum.sample = {"round1": {"winner": 2, "loser": 0}}
    no_cvr_stratum.sample_size = 2
    cvr_stratum.sample_size = 3

    # This tests if we ask for a sample size that is smaller
    # than the sample we've already taken.
    ret = try_n(
        2, 0.05, contest, "winner", "loser", no_cvr_stratum, cvr_stratum, 4 / 11
    )

    assert ret == 1.0, f"{ret}"


def test_misstatements():
    contest_data = {
        "winner": 16,
        "loser": 10,
        "ballots": 26,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("Jonah Test", contest_data)

    cvr = {}

    for i in range(contest_data["ballots"]):
        if i < contest_data["winner"]:
            cvr[i] = {"Jonah Test": {"winner": 1, "loser": 0}}
        else:
            cvr[i] = {"Jonah Test": {"winner": 0, "loser": 1}}

    sample_cvr = {}
    for ballot in range(18):
        sample_cvr[ballot] = {
            "times_sampled": 1,
            "cvr": {
                "Jonah Test": {
                    "winner": cvr[ballot]["Jonah Test"]["winner"],
                    "loser": cvr[ballot]["Jonah Test"]["loser"],
                }
            },
        }
    # Two of our winning ballots were actually blank
    sample_cvr[0]["cvr"]["Jonah Test"] = {"winner": 0, "loser": 0}
    sample_cvr[1]["cvr"]["Jonah Test"] = {"winner": 0, "loser": 0}

    expected = {("winner", "loser"): {"o1": 2, "o2": 0, "u1": 0, "u2": 0}}
    assert misstatements(contest, cvr, sample_cvr) == expected

    # Create a two-vote understatement.
    sample_cvr[0]["cvr"]["Jonah Test"] = {"winner": 0, "loser": 1}
    expected = {("winner", "loser"): {"o1": 1, "o2": 1, "u1": 0, "u2": 0}}
    assert misstatements(contest, cvr, sample_cvr) == expected

    # create one- and two-vote understatements. These should be ignored.
    sample_cvr[16]["cvr"]["Jonah Test"] = {"winner": 0, "loser": 0}
    sample_cvr[17]["cvr"]["Jonah Test"] = {"winner": 1, "loser": 0}
    expected = {("winner", "loser"): {"o1": 1, "o2": 1, "u1": 0, "u2": 0}}
    assert misstatements(contest, cvr, sample_cvr) == expected


def test_cvr_recount():
    contest_dict = {
        "winner": 510,
        "loser": 490,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    no_cvr_stratum_vote_totals = {
        "winner": 1,
        "loser": 0,
    }
    no_cvr_stratum_ballots = 1
    no_cvr_sample = {"round1": {"winner": 0, "loser": 0}}

    # create our ballot polling strata
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        no_cvr_sample,
        sample_size=0,
    )

    cvr_stratum_vote_totals = {
        "winner": 509,
        "loser": 490,
    }

    cvr_stratum_ballots = 999

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    cvr_stratum.sample_size = 999

    expected_pvalue = 0.0
    pvalue = cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.9)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    no_cvr_stratum.sample = {"round1": {"winner": 0, "loser": 0}}
    no_cvr_stratum.sample_size = 0
    expected_pvalue = 1
    pvalue = no_cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.1)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    with pytest.raises(
        ValueError,
        match=r"One or both strata has already been recounted. Possibly returning a p-value from the remaining stratum.",
    ) as error:
        compute_risk(10, contest, no_cvr_stratum, cvr_stratum)

        pvalue, res = error.args[1], error.args[2]
        expected_pvalue = 0.005819346812076758
        diff = abs(expected_pvalue - pvalue)
        assert diff < 0.000001, "Got {}".format(pvalue)
        assert not res


def test_bp_recount():
    contest_dict = {
        "winner": 510,
        "loser": 490,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    no_cvr_stratum_vote_totals = {
        "winner": 1,
        "loser": 0,
    }
    no_cvr_stratum_ballots = 1
    no_cvr_sample = {"round1": {"winner": 0, "loser": 0}}

    # create our ballot polling strata
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        no_cvr_sample,
        sample_size=0,
    )

    cvr_stratum_vote_totals = {
        "winner": 509,
        "loser": 490,
    }

    cvr_stratum_ballots = 999

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    cvr_stratum.sample_size = 591

    expected_pvalue = 0.005819346812076758
    pvalue = cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.9)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    no_cvr_stratum.sample = {"round1": {"winner": 1, "loser": 0}}
    no_cvr_stratum.sample_size = 1
    expected_pvalue = 0
    pvalue = no_cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.1)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    with pytest.raises(
        ValueError,
        match=r"One or both strata has already been recounted. Possibly returning a p-value from the remaining stratum.",
    ) as error:
        compute_risk(10, contest, no_cvr_stratum, cvr_stratum)

        pvalue, res = error.args[1], error.args[2]
        expected_pvalue = 0.005819346812076758
        diff = abs(expected_pvalue - pvalue)
        assert diff < 0.000001, "Got {}".format(pvalue)
        assert not res


def test_full_recount():
    contest_dict = {
        "winner": 510,
        "loser": 490,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("ex1", contest_dict)
    reported_margin = contest_dict["winner"] - contest_dict["loser"]

    no_cvr_stratum_vote_totals = {
        "winner": 1,
        "loser": 0,
    }
    no_cvr_stratum_ballots = 1
    no_cvr_sample = {"round1": {"winner": 0, "loser": 0}}

    # create our ballot polling strata
    no_cvr_stratum = BallotPollingStratum(
        no_cvr_stratum_ballots,
        no_cvr_stratum_vote_totals,
        no_cvr_sample,
        sample_size=0,
    )

    cvr_stratum_vote_totals = {
        "winner": 509,
        "loser": 490,
    }

    cvr_stratum_ballots = 999

    # We sample 500 ballots from the cvr stratum, and find no discrepancies
    misstatements = {
        ("winner", "loser"): {
            "o1": 0,
            "o2": 0,
            "u1": 0,
            "u2": 0,
        }
    }

    # Create our CVR stratum
    cvr_stratum = BallotComparisonStratum(
        cvr_stratum_ballots,
        cvr_stratum_vote_totals,
        misstatements,
        sample_size=0,
    )

    cvr_stratum.sample_size = 999

    expected_pvalue = 0.0
    pvalue = cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.9)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue!"

    no_cvr_stratum.sample = {"round1": {"winner": 1, "loser": 0}}
    no_cvr_stratum.sample_size = 1
    expected_pvalue = 0.0
    pvalue = no_cvr_stratum.compute_pvalue(reported_margin, "winner", "loser", 0.1)
    diff = abs(expected_pvalue - pvalue)
    assert diff < 0.00001, "Incorrect pvalue: {}!".format(pvalue)

    # Now get the combined pvalue
    with pytest.raises(
        ValueError,
        match=r"One or both strata has already been recounted. Possibly returning a p-value from the remaining stratum.",
    ) as error:
        compute_risk(10, contest, no_cvr_stratum, cvr_stratum)

        pvalue, res = error.args[1], error.args[2]
        expected_pvalue = 0.0
        diff = abs(expected_pvalue - pvalue)
        assert diff < 0.000001, "Got {}".format(pvalue)
        assert not res


def test_ess_misstatements():
    contest = Contest(
        "Two Losers",
        {
            "winner": 1000,
            "loser1": 0,
            "loser2": 500,
            "ballots": 1500,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )
    reported_results = {
        "ballot-0": {"Two Losers": {"winner": "o", "loser1": "o", "loser2": "o"}},
        "ballot-1": {"Two Losers": {"winner": "u", "loser1": "u", "loser2": "u"}},
        "ballot-2": {"Two Losers": {"winner": "1", "loser1": "0", "loser2": "0"}},
    }

    # Correct results
    audited_results = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {"Two Losers": {"winner": "1", "loser1": "0", "loser2": "1"}},
        },
        "ballot-1": {
            "times_sampled": 1,
            "cvr": {"Two Losers": {"winner": "0", "loser1": "0", "loser2": "0"}},
        },
        "ballot-2": {
            "times_sampled": 1,
            "cvr": {"Two Losers": {"winner": "1", "loser1": "0", "loser2": "0"}},
        },
    }
    assert misstatements(contest, reported_results, audited_results) == {
        ("winner", "loser1"): {"o1": 0, "o2": 0, "u1": 0, "u2": 0},
        ("winner", "loser2"): {"o1": 0, "o2": 0, "u1": 0, "u2": 0},
    }

    # Overstatements
    audited_results = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {"Two Losers": {"winner": "0", "loser1": "1", "loser2": "0"}},
        },
        "ballot-1": {
            "times_sampled": 1,
            "cvr": {"Two Losers": {"winner": "0", "loser1": "0", "loser2": "1"}},
        },
        "ballot-2": {
            "times_sampled": 1,
            "cvr": {"Two Losers": {"winner": "0", "loser1": "1", "loser2": "0"}},
        },
    }
    assert misstatements(contest, reported_results, audited_results) == {
        ("winner", "loser1"): {"o1": 1, "o2": 1, "u1": 0, "u2": 0},
        ("winner", "loser2"): {"o1": 2, "o2": 0, "u1": 0, "u2": 0},
    }

    # Missing ballots/contests not on ballot
    audited_results = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": None,
        },
        "ballot-1": {"times_sampled": 1, "cvr": {}},
    }
    assert misstatements(contest, reported_results, audited_results) == {
        ("winner", "loser1"): {"o1": 0, "o2": 1, "u1": 0, "u2": 0},
        ("winner", "loser2"): {"o1": 0, "o2": 1, "u1": 0, "u2": 0},
    }


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

# pylint: disable=invalid-name
from decimal import Decimal
import pytest

from ...audit_math import supersimple
from ...audit_math.sampler_contest import Contest

seed = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
ALPHA = Decimal(0.1)
RISK_LIMIT = 10


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
def contests():
    contests = {}

    for contest in ss_contests:
        contests[contest] = Contest(contest, ss_contests[contest])

    yield contests


def test_compute_diluted_margin(contests):
    for contest, expected in true_dms.items():
        computed = contests[contest].diluted_margin
        assert (
            computed == expected
        ), "Diluted margin computation incorrect: got {}, expected {} in contest {}".format(
            computed, expected, contest
        )


def test_find_no_discrepancies(contests, cvrs):

    # Test no discrepancies
    sample_cvr = {
        0: {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": 1, "loser": 0},
                "Contest B": {"winner": 1, "loser": 0},
                "Contest C": {"winner": 1, "loser": 0},
                "Contest D": {"winner": 1, "loser": 0},
                "Contest E": {"winner": 1, "loser": 0},
            },
        }
    }

    for contest in contests:
        discrepancies = supersimple.compute_discrepancies(
            contests[contest], cvrs, sample_cvr
        )
        assert not discrepancies


def test_find_one_discrepancy(contests, cvrs):

    # Test one discrepancy
    sample_cvr = {
        0: {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": 0, "loser": 0},
                "Contest B": {"winner": 1, "loser": 0},
                "Contest C": {"winner": 1, "loser": 0},
                "Contest D": {"winner": 1, "loser": 0},
                "Contest E": {"winner": 1, "loser": 0},
            },
        }
    }

    for contest in contests:
        discrepancies = supersimple.compute_discrepancies(
            contests[contest], cvrs, sample_cvr
        )
        if contest == "Contest A":
            assert discrepancies[0]["counted_as"] == 1
            assert discrepancies[0]["weighted_error"] == Decimal(1) / Decimal(20000)
            assert (
                discrepancies[0]["discrepancy_cvr"]["reported_as"][contest]
                != discrepancies[0]["discrepancy_cvr"]["audited_as"][contest]
            )
        else:
            assert not discrepancies


def test_race_not_in_cvr_discrepancy(contests, cvrs):

    sample_cvr = {
        0: {
            "times_sampled": 1,
            "cvr": {
                "Contest F": {
                    "winner": 0,
                    "loser": 1,
                },  # The audit board found a race not in the CVR
            },
        }
    }

    discrepancies = supersimple.compute_discrepancies(
        contests["Contest F"], cvrs, sample_cvr
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 1
    assert discrepancies[0]["weighted_error"] == Decimal(1) / Decimal(6)
    assert "Contest F" not in discrepancies[0]["discrepancy_cvr"]["reported_as"]


def test_race_not_in_sample_discrepancy(contests, cvrs):

    sample_cvr = {
        0: {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": 0, "loser": 0},
                "Contest B": {"winner": 1, "loser": 0},
                "Contest C": {"winner": 1, "loser": 0},
                "Contest E": {"winner": 1, "loser": 0},
            },
        }
    }

    discrepancies = supersimple.compute_discrepancies(
        contests["Contest D"], cvrs, sample_cvr
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 1
    assert discrepancies[0]["weighted_error"] == Decimal(1) / Decimal(2000)
    assert "Contest D" not in discrepancies[0]["discrepancy_cvr"]["audited_as"]


def test_get_sample_sizes(contests):
    for contest in contests:
        computed = supersimple.get_sample_sizes(RISK_LIMIT, contests[contest], None)
        expected = true_sample_sizes[contest]  # From Stark's tool

        assert (
            computed == expected
        ), "Sample size computation incorrect: got {}, expected {} in contest {}".format(
            computed, expected, contest
        )


def test_compute_risk(contests, cvrs):

    for contest in contests:
        sample_cvr = {}
        sample_size = supersimple.get_sample_sizes(RISK_LIMIT, contests[contest], None)

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

        p_value, finished = supersimple.compute_risk(
            RISK_LIMIT, contests[contest], cvrs, sample_cvr
        )

        expected_p = expected_p_values["no_discrepancies"][contest]
        diff = abs(p_value - expected_p)

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )
        assert finished, "Audit should have finished but didn't"

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

        p_value, finished = supersimple.compute_risk(
            RISK_LIMIT, contests[contest], cvrs, sample_cvr
        )

        expected_p = expected_p_values["one_vote_over"][contest]
        diff = abs(p_value - expected_p)

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )
        if contest in ["Contest E", "Contest F"]:
            assert finished, "Audit should have finished but didn't"
        else:
            assert not finished, "Audit shouldn't have finished but did!"

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

        p_value, finished = supersimple.compute_risk(
            RISK_LIMIT, contests[contest], cvrs, sample_cvr
        )
        expected_p = expected_p_values["two_vote_over"][contest]
        diff = abs(p_value - expected_p)

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )

        if contest in ["Contest F"]:
            assert finished, "Audit should have finished but didn't"
        else:
            assert not finished, "Audit shouldn't have finished but did!"

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


def test_tied_contest():
    contest_data = {
        "winner": 50000,
        "loser": 50000,
        "ballots": 100000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("Tied Contest", contest_data)

    cvr = {}

    for i in range(contest_data["ballots"]):
        if i < contest_data["ballots"] / 2:
            cvr[i] = {"Tied Contest": {"winner": 1, "loser": 0}}
        else:
            cvr[i] = {"Tied Contest": {"winner": 0, "loser": 1}}

    sample_results = {
        "sample_size": 0,
        "1-under": 0,
        "1-over": 0,
        "2-under": 0,
        "2-over": 0,
    }

    sample_size = supersimple.get_sample_sizes(RISK_LIMIT, contest, sample_results)

    assert sample_size == contest_data["ballots"]

    sample_cvr = {
        0: {"times_sampled": 1, "cvr": {"Tied Contest": {"winner": 1, "loser": 0}}}
    }

    # Ensure that anything short of a full recount doesn't finish
    p, res = supersimple.compute_risk(RISK_LIMIT, contest, cvr, sample_cvr)

    assert p > ALPHA
    assert not res

    # Do a full hand recount with no discrepancies
    sample_cvr = {}
    for ballot in cvr:
        sample_cvr[ballot] = {"times_sampled": 1, "cvr": cvr[ballot]}

    p, res = supersimple.compute_risk(RISK_LIMIT, contest, cvr, sample_cvr)

    assert not p
    assert res


def test_snapshot_test():
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

    sample_results = {
        "sample_size": 0,
        "1-under": 0,
        "1-over": 0,
        "2-under": 0,
        "2-over": 0,
    }

    _ = supersimple.get_sample_sizes(RISK_LIMIT, contest, sample_results)

    sample_cvr = {}
    for ballot in range(18):
        sample_cvr[ballot] = {"times_sampled": 1, "cvr": cvr[ballot]}

    # Two of our winning ballots were actually blank
    sample_cvr[0]["cvr"]["Jonah Test"] = {"winner": 0, "loser": 0}
    sample_cvr[1]["cvr"]["Jonah Test"] = {"winner": 0, "loser": 0}

    p, res = supersimple.compute_risk(RISK_LIMIT, contest, cvr, sample_cvr)

    expected_p = 0.1201733
    assert abs(expected_p - p) < 0.0001
    assert not res

    # now draw 9 more ballots without any discrepancies
    sample_cvr = {}
    for ballot in cvr:
        sample_cvr[ballot] = {"times_sampled": 1, "cvr": cvr[ballot]}
    sample_cvr[0]["cvr"]["Jonah Test"] = {"winner": 0, "loser": 0}
    sample_cvr[1]["cvr"]["Jonah Test"] = {"winner": 0, "loser": 0}

    p, res = supersimple.compute_risk(RISK_LIMIT, contest, cvr, sample_cvr)

    assert res
    assert p < 0.000000001


def test_multiplicity():
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

    sample_results = {
        "sample_size": 0,
        "1-under": 0,
        "1-over": 0,
        "2-under": 0,
        "2-over": 0,
    }

    _ = supersimple.get_sample_sizes(RISK_LIMIT, contest, sample_results)

    sample_cvr = {}
    for ballot in range(18):
        sample_cvr[ballot] = {"times_sampled": 1, "cvr": cvr[ballot]}
    # Two of our winning ballots were actually blank
    sample_cvr[0]["cvr"]["Jonah Test"] = {"winner": 0, "loser": 0}
    sample_cvr[1]["cvr"]["Jonah Test"] = {"winner": 0, "loser": 0}

    p, res = supersimple.compute_risk(RISK_LIMIT, contest, cvr, sample_cvr)

    expected_p = 0.1201733
    assert abs(expected_p - p) < 0.0001
    assert not res

    # now draw those same ballots again
    for i in sample_cvr:
        sample_cvr[i]["cvr"]["times_sampled"] = 2

    p, res = supersimple.compute_risk(RISK_LIMIT, contest, cvr, sample_cvr)

    assert not res
    assert p != 0  # This wasn't a recount


true_dms = {
    "Contest A": 0.2,
    "Contest B": 0.1,
    "Contest C": 0.15,
    "Contest D": 2 / 15,
    "Contest E": 1,
}

true_sample_sizes = {
    "Contest A": 27,
    "Contest B": 54,
    "Contest C": 36,
    "Contest D": 40,
    "Contest E": 6,
    "Contest F": 14,
}

no_next_sample = {
    "Contest A": 24,
    "Contest B": 48,
    "Contest C": 32,
    "Contest D": 36,
    "Contest E": 5,
    "Contest F": 12,
}

o1_next_sample = {
    "Contest A": 38,
    "Contest B": 76,
    "Contest C": 51,
    "Contest D": 57,
    "Contest E": 7,
    "Contest F": 16,
}

o2_next_sample = {
    "Contest A": 100000,
    "Contest B": 60000,
    "Contest C": 36000,
    "Contest D": 15000,
    "Contest E": 6,
    "Contest F": 15,
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
        "Contest A": 1.73150,
        "Contest B": 1.85538,
        "Contest C": 1.79346,
        "Contest D": 1.87524,
        "Contest E": 0.51877,
        "Contest F": 0.05013,
    },
}

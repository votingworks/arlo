# pylint: disable=invalid-name
import pytest

from ...audit_math import supersimple
from ...audit_math.sampler_contest import Contest

seed = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
risk_limit = 0.1


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
        elif 18000 < i < 30600:
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
            "Contest A": {"winner": 1, "loser": 0},
            "Contest B": {"winner": 1, "loser": 0},
            "Contest C": {"winner": 1, "loser": 0},
            "Contest D": {"winner": 1, "loser": 0},
            "Contest E": {"winner": 1, "loser": 0},
        }
    }

    for contest in contests:
        discrepancies = supersimple.find_discrepancies(
            contests[contest], cvrs, sample_cvr
        )

        assert discrepancies[0]["counted_as"] == 0
        assert discrepancies[0]["weighted_error"] == 0
        assert discrepancies[0]["cvr"] == discrepancies[0]["sample_cvr"]


def test_find_one_discrepancy(contests, cvrs):

    # Test no discrepancies
    sample_cvr = {
        0: {
            "Contest A": {"winner": 0, "loser": 0},
            "Contest B": {"winner": 1, "loser": 0},
            "Contest C": {"winner": 1, "loser": 0},
            "Contest D": {"winner": 1, "loser": 0},
            "Contest E": {"winner": 1, "loser": 0},
        }
    }

    for contest in contests:
        discrepancies = supersimple.find_discrepancies(
            contests[contest], cvrs, sample_cvr
        )
        if contest == "Contest A":
            assert discrepancies[0]["counted_as"] == 1
            assert discrepancies[0]["weighted_error"] == 1 / 20000
            assert (
                discrepancies[0]["cvr"][contest]
                != discrepancies[0]["sample_cvr"][contest]
            )
        else:
            assert discrepancies[0]["counted_as"] == 0
            assert discrepancies[0]["weighted_error"] == 0
            assert (
                discrepancies[0]["cvr"][contest]
                == discrepancies[0]["sample_cvr"][contest]
            )


def test_get_sample_sizes(contests):
    sample_results = {
        "sample_size": 0,
        "1-under": 0,
        "1-over": 0,
        "2-under": 0,
        "2-over": 0,
    }

    for contest in contests:
        computed = supersimple.get_sample_sizes(
            risk_limit, contests[contest], sample_results
        )
        expected = true_sample_sizes[contest]  # From Stark's tool

        assert (
            computed == expected
        ), "Sample size computation incorrect: got {}, expected {} in contest {}".format(
            computed, expected, contest
        )


def test_compute_risk(contests, cvrs):

    for contest in contests:
        to_sample = {
            "sample_size": 0,
            "1-under": 0,
            "1-over": 0,
            "2-under": 0,
            "2-over": 0,
        }
        sample_cvr = {}
        sample_size = supersimple.get_sample_sizes(
            risk_limit, contests[contest], to_sample
        )

        for i in range(sample_size):
            sample_cvr[i] = {
                "Contest A": {"winner": 1, "loser": 0},
                "Contest B": {"winner": 1, "loser": 0},
                "Contest C": {"winner": 1, "loser": 0},
                "Contest D": {"winner": 1, "loser": 0},
                "Contest E": {"winner": 1, "loser": 0},
            }

        _, finished = supersimple.compute_risk(
            risk_limit, contests[contest], cvrs, sample_cvr
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
            risk_limit, contests[contest], to_sample
        )
        assert (
            next_sample_size == no_next_sample[contest]
        ), "Number of ballots left to sample is not correct!"

        # Test one-vote overstatement
        sample_cvr[0] = {
            "Contest A": {"winner": 0, "loser": 0},
            "Contest B": {"winner": 0, "loser": 0},
            "Contest C": {"winner": 0, "loser": 0},
            "Contest D": {"winner": 0, "loser": 0},
            "Contest E": {"winner": 0, "loser": 0},
        }

        _, finished = supersimple.compute_risk(
            risk_limit, contests[contest], cvrs, sample_cvr
        )
        assert not finished, "Audit shouldn't have finished but did!"

        to_sample = {
            "sample_size": sample_size,
            "1-under": 0,
            "1-over": 1,
            "2-under": 0,
            "2-over": 0,
        }

        next_sample_size = supersimple.get_sample_sizes(
            risk_limit, contests[contest], to_sample
        )
        assert (
            next_sample_size == o1_next_sample[contest]
        ), "Number of ballots left to sample is not correct in contest {}!".format(
            contest
        )

        # Test two-vote overstatement
        sample_cvr[0] = {
            "Contest A": {"winner": 0, "loser": 1},
            "Contest B": {"winner": 0, "loser": 1},
            "Contest C": {"winner": 0, "loser": 1},
            "Contest D": {"winner": 0, "loser": 1},
            "Contest E": {"winner": 0, "loser": 1},
        }

        _, finished = supersimple.compute_risk(
            risk_limit, contests[contest], cvrs, sample_cvr
        )
        assert not finished, "Audit shouldn't have finished but did!"

        to_sample = {
            "sample_size": sample_size,
            "1-under": 0,
            "1-over": 0,
            "2-under": 0,
            "2-over": 1,
        }

        next_sample_size = supersimple.get_sample_sizes(
            risk_limit, contests[contest], to_sample
        )
        assert (
            next_sample_size == o2_next_sample[contest]
        ), "Number of ballots left to sample is not correct in contest {}!".format(
            contest
        )


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
}

no_next_sample = {
    "Contest A": 24,
    "Contest B": 48,
    "Contest C": 32,
    "Contest D": 36,
    "Contest E": 5,
}

o1_next_sample = {
    "Contest A": 38,
    "Contest B": 76,
    "Contest C": 51,
    "Contest D": 57,
    "Contest E": 7,
}

o2_next_sample = {
    "Contest A": 100000,
    "Contest B": 60000,
    "Contest C": 36000,
    "Contest D": 15000,
    "Contest E": 6,
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
}

from decimal import Decimal
import pytest

from ...audit_math import macro
from ...audit_math.sampler_contest import Contest

SEED = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
RISK_LIMIT = 25
ALPHA = 0.25

macro_contests = {
    "Contest A": {
        "winner": 60000,
        "loser": 54000,
        "ballots": 120000,
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
}


@pytest.fixture
def contests():
    contests = {}

    for contest in macro_contests:
        contests[contest] = Contest(contest, macro_contests[contest])

    return contests


@pytest.fixture
def batches():

    batches = {}
    for i in range(200):
        batches["Batch {}".format(i)] = {
            "Contest A": {"winner": 200, "loser": 180, "ballots": 400, "numWinners": 1},
        }

        batches["Batch {} AV".format(i)] = {
            "Contest A": {"winner": 100, "loser": 90, "ballots": 200, "numWinners": 1},
        }

    for i in range(100):
        batches["Batch {}".format(i)]["Contest B"] = {
            "winner": 200,
            "loser": 160,
            "ballots": 400,
            "numWinners": 1,
        }
        batches["Batch {} AV".format(i)]["Contest B"] = {
            "winner": 100,
            "loser": 80,
            "ballots": 200,
            "numWinners": 1,
        }

    for i in range(30):
        batches["Batch {}".format(i)]["Contest C"] = {
            "winner": 200,
            "loser": 140,
            "ballots": 400,
            "numWinners": 1,
        }
        batches["Batch {} AV".format(i)]["Contest C"] = {
            "winner": 100,
            "loser": 70,
            "ballots": 200,
            "numWinners": 1,
        }

    for i in range(100, 130):
        batches["Batch {}".format(i)]["Contest C"] = {
            "winner": 200,
            "loser": 140,
            "ballots": 400,
            "numWinners": 1,
        }
        batches["Batch {} AV".format(i)]["Contest C"] = {
            "winner": 100,
            "loser": 70,
            "ballots": 200,
            "numWinners": 1,
        }

    return batches


def test_max_error(contests, batches):

    # this is kind of a hacky way to do this but ¯\_(ツ)_/¯
    expected_ups = {"Contest A": {}, "Contest B": {}, "Contest C": {}}
    for i in range(200):
        expected_ups["Contest A"]["Batch {}".format(i)] = 0.0700
        expected_ups["Contest A"]["Batch {} AV".format(i)] = 0.035
        expected_ups["Contest B"]["Batch {}".format(i)] = 0
        expected_ups["Contest B"]["Batch {} AV".format(i)] = 0
        expected_ups["Contest C"]["Batch {}".format(i)] = 0
        expected_ups["Contest C"]["Batch {} AV".format(i)] = 0

    for i in range(100):
        expected_ups["Contest B"]["Batch {}".format(i)] = 0.0733
        expected_ups["Contest B"]["Batch {} AV".format(i)] = 0.0367

    for i in range(30):
        expected_ups["Contest C"]["Batch {}".format(i)] = 0.0852
        expected_ups["Contest C"]["Batch {} AV".format(i)] = 0.0426

    for i in range(100, 130):
        expected_ups["Contest C"]["Batch {}".format(i)] = 0.0852
        expected_ups["Contest C"]["Batch {} AV".format(i)] = 0.0426

    for contest in contests:
        for batch in batches:
            expected_up = Decimal(expected_ups[contest][batch])
            computed_up = macro.compute_max_error(batches[batch], contests[contest])

            delta = abs(computed_up - expected_up)
            assert (
                delta < 0.001
            ), "Got an incorrect maximum possible overstatement: {} should be {}".format(
                computed_up, expected_up
            )


def test_get_sample_sizes(contests, batches):
    expected_first_round = {
        "Contest A": 29,
        "Contest B": 15,
        "Contest C": 10,
    }

    sample = {}
    for contest in contests:
        computed = macro.get_sample_sizes(
            RISK_LIMIT, contests[contest], batches, sample
        )

        assert (
            expected_first_round[contest] == computed
        ), "First round sample expected {}, got {}".format(
            expected_first_round[contest], computed
        )

    # Add 31 batches to the sample that is correct
    for i in range(31):
        sample["Batch {}".format(i)] = {
            "Contest A": {"winner": 200, "loser": 180,},
            "Contest B": {"winner": 200, "loser": 160,},
            "Contest C": {"winner": 200, "loser": 140,},
        }

    expected_second_round = {
        "Contest A": 26,
        "Contest B": 12,
        "Contest C": 7,
    }

    for contest in contests:
        computed = macro.get_sample_sizes(
            RISK_LIMIT, contests[contest], batches, sample
        )

        assert (
            expected_second_round[contest] == computed
        ), "Second round sample expected {}, got {}".format(
            expected_second_round[contest], computed
        )

    # Now add in some errors
    # draws with taint of 0.04047619
    for i in range(100, 106):
        sample["Batch {}".format(i)] = {
            "Contest A": {"winner": 190, "loser": 190,},
            "Contest C": {"winner": 200, "loser": 140,},
        }

    expected_third_round = {
        "Contest A": 25,
        "Contest B": 12,
        "Contest C": 6,
    }

    for contest in contests:
        computed = macro.get_sample_sizes(
            RISK_LIMIT, contests[contest], batches, sample
        )

        assert (
            expected_third_round[contest] == computed
        ), "Third round sample expected {}, got {}".format(
            expected_third_round[contest], computed
        )


def test_compute_risk(contests, batches):

    sample = {}

    # Draws with taint of 0
    for i in range(31):
        sample["Batch {}".format(i)] = {
            "Contest A": {"winner": 200, "loser": 180,},
            "Contest B": {"winner": 200, "loser": 160,},
            "Contest C": {"winner": 200, "loser": 140,},
        }

    # draws with taint of 0.04047619
    for i in range(100, 106):
        sample["Batch {}".format(i)] = {
            "Contest A": {"winner": 190, "loser": 190,},
            "Contest C": {"winner": 200, "loser": 140,},
        }

    for contest in contests:
        computed_p, result = macro.compute_risk(
            RISK_LIMIT, contests[contest], batches, sample
        )

        expected_p = 0.247688222

        delta = abs(expected_p - computed_p)

        assert delta < 10 ** -2, "Incorrect p-value: Got {}, expected {}".format(
            computed_p, expected_p
        )

        assert result, "Audit did not terminate but should have"


def test_tied_contest():

    contest_data = {
        "winner": 50000,
        "loser": 50000,
        "ballots": 100000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("Tied Contest", contest_data)

    batches = {}
    for i in range(100):
        batches[i] = {
            "Tied Contest": {
                "winner": 500,
                "loser": 500,
                "ballots": 1000,
                "numWinners": 1,
            }
        }

    sample_results = {}

    sample_size = macro.get_sample_sizes(RISK_LIMIT, contest, batches, sample_results)

    assert sample_size == len(batches)

    sample_results = {
        0: {
            "Tied Contest": {
                "winner": 500,
                "loser": 500,
                "ballots": 1000,
                "numWinners": 1,
            }
        }
    }

    computed_p, res = macro.compute_risk(RISK_LIMIT, contest, batches, sample_results)

    assert computed_p > ALPHA
    assert not res

    # Now do a full hand recount
    computed_p, res = macro.compute_risk(RISK_LIMIT, contest, batches, batches)

    assert not computed_p
    assert res

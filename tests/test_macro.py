import pytest
import math
import numpy as np

from audits import sampler, macro
from audits.sampler_contest import Contest

seed = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"

risk_limit = 0.25

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

    yield contests


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

    yield batches


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
            expected_up = expected_ups[contest][batch]
            computed_up = macro.compute_max_error(batches[batch], contests[contest])

            delta = abs(computed_up - expected_up)
            assert (
                delta < 0.001
            ), "Got an incorrect maximum possible overstatement: {} should be {}".format(
                computed_up, expected_up
            )


def test_compute_U(contests, batches):

    # Values from Stark
    expected_Us = {
        "Contest A": 21.0,
        "Contest B": 11.0,
        "Contest C": 7.666667,
    }

    for contest in expected_Us:
        computed = round(macro.compute_U(batches, contests[contest]), 6)

        assert (
            computed == expected_Us[contest]
        ), "U computation was incorrect for contest {}! Expected{}, got {}".format(
            contest, expected_Us[contest], computed
        )


def test_compute_risk(contests, batches):

    sample = {}

    # Draws with taint of 0
    for i in range(31):
        sample["Batch {}".format(i)] = {
            "Contest A": {"winner": 200, "loser": 180,},
            "Contest B": {"winner": 200, "loser": 160,},
            "Contest C": {"winner": 170, "loser": 170,},
        }

    # draws with taint of 0.047619 for Contest A,  for the others
    for i in range(100, 106):
        sample["Batch {}".format(i)] = {
            "Contest A": {"winner": 190, "loser": 190,},
            "Contest C": {"winner": 200, "loser": 140,},
        }

    expected_ps = {
        "Contest A": 0.22035947,
        "Contest B": 0.052098685,
        "Contest C": 0.432327595,
    }

    expected_results = {"Contest A": True, "Contest B": True, "Contest C": False}

    for contest in contests:
        computed_p, result = macro.compute_risk(
            risk_limit, contests[contest], batches, sample
        )

        expected_p = expected_ps[contest]

        delta = abs(expected_p - computed_p)

        assert (
            delta < 10 ** -6
        ), "Incorrect p-value: Got {}, expected {} in contest {}".format(
            computed_p, expected_p, contest
        )

        if expected_results[contest]:
            assert result, "Audit on {} did not terminate but should have".format(
                contest
            )
        else:
            assert not result, "Audit terminated but should't have"

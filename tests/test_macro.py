import pytest
import math
import numpy as np

from sampler import Sampler


@pytest.fixture
def sampler():
    seed = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"

    risk_limit = 0.25
    contests = {
        "Contest A": {
            "winner": 60000,
            "loser": 54000,
            "ballots": 120000,
            "numWinners": 1,
        },
        "Contest B": {
            "winner": 30000,
            "loser": 24000,
            "ballots": 60000,
            "numWinners": 1,
        },
        "Contest C": {
            "winner": 18000,
            "loser": 12600,
            "ballots": 36000,
            "numWinners": 1,
        },
    }

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

    yield Sampler("MACRO", seed, risk_limit, contests, batches)


def test_max_error(sampler):

    # this is kind of a hacky way to do this but ¯\_(ツ)_/¯
    expected_ups = {}
    for i in range(200):
        expected_ups["Batch {}".format(i)] = 0.0700
        expected_ups["Batch {} AV".format(i)] = 0.035

    for i in range(100):
        expected_ups["Batch {}".format(i)] = 0.0733
        expected_ups["Batch {} AV".format(i)] = 0.0367

    for i in range(30):
        expected_ups["Batch {}".format(i)] = 0.0852
        expected_ups["Batch {} AV".format(i)] = 0.0426

    for i in range(100, 130):
        expected_ups["Batch {}".format(i)] = 0.0852
        expected_ups["Batch {} AV".format(i)] = 0.0426

    for batch in sampler.batch_results:
        expected_up = expected_ups[batch]
        computed_up = sampler.audit.compute_max_error(
            batch, sampler.contests, sampler.margins
        )

        delta = abs(computed_up - expected_up)
        assert (
            delta < 0.001
        ), "Got an incorrect maximum possible overstatement: {} should be {}".format(
            computed_up, expected_up
        )


def test_get_sample_sizes(sampler):
    expected = 31
    computed = sampler.get_sample_sizes({})
    assert (
        computed == expected
    ), "Failed to compute sample sized: got {}, expected {}".format(computed, expected)


def test_compute_risk(sampler):

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
            "Contest B": {"winner": 200, "loser": 160,},
            "Contest C": {"winner": 200, "loser": 140,},
        }

    computed_p, result = sampler.audit.compute_risk(
        sampler.contests, sampler.margins, sample
    )

    expected_p = 0.247688222

    delta = abs(expected_p - computed_p)

    assert delta < 10 ** -4, "Incorrect p-value: Got {}, expected {}".format(
        computed_p, expected_p
    )

    assert result, "Audit did not terminate but should have"

# pylint: disable=invalid-name,consider-using-dict-items,consider-using-f-string
from decimal import Decimal
from typing import Dict
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


def test_max_error(contests, batches) -> None:

    # this is kind of a hacky way to do this but ¯\_(ツ)_/¯
    expected_ups: Dict = {
        "Contest A": {},
        "Contest B": {},
        "Contest C": {},
    }
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


def test_get_sizes_extra_contests(contests, batches) -> None:
    name = "test2"

    info_dict = {
        "cand1": 400,
        "cand2": 100,
        "ballots": 500,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    other_contest = Contest(name, info_dict)
    contests[name] = other_contest

    for batch in batches:
        if "AV" in batch:
            continue
        pct = int(batch.split(" ")[-1])
        if pct < 10:
            batches[batch]["test2"] = {"cand1": 40, "cand2": 10, "ballots": 50}

    expected_first_round = {
        "Contest A": 30,
        "Contest B": 16,
        "Contest C": 11,
        name: 4,
    }

    # This should give us zeros for error
    sample: Dict = {}
    sample_ticket_numbers: Dict = {}
    for contest in contests:
        computed = macro.get_sample_sizes(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
        )

        assert (
            expected_first_round[contest] == computed
        ), "First round sample expected {}, got {}".format(
            expected_first_round[contest], computed
        )


def test_get_sample_sizes(contests, batches) -> None:
    expected_first_round = {
        "Contest A": 30,
        "Contest B": 16,
        "Contest C": 11,
    }

    sample: Dict = {}
    sample_ticket_numbers: Dict = {}
    for contest in contests:
        computed = macro.get_sample_sizes(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
        )

        assert (
            expected_first_round[contest] == computed
        ), "First round sample expected {}, got {}".format(
            expected_first_round[contest], computed
        )

    # Add 4 discrepancy-free batches to the sample
    for i in range(4):
        sample["Batch {}".format(i)] = {
            "Contest A": {
                "winner": 200,
                "loser": 180,
            },
            "Contest B": {
                "winner": 200,
                "loser": 160,
            },
            "Contest C": {
                "winner": 200,
                "loser": 140,
            },
        }
        sample_ticket_numbers[str(i)] = "Batch {}".format(i)

    expected_second_round = {
        "Contest A": 26,
        "Contest B": 12,
        "Contest C": 7,
    }

    for contest in contests:
        computed = macro.get_sample_sizes(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
        )

        assert (
            expected_second_round[contest] == computed
        ), "Second round sample expected {}, got {}".format(
            expected_second_round[contest], computed
        )

    # Now add in some errors with taint for A equal to reported margin
    #    -- so sample size should not change.
    # B is not in sample -> sample size should not change.
    # taints of 0 for C -> sample size decreases by number of batches.
    for i in range(4, 9):
        sample["Batch {}".format(i)] = {
            "Contest A": {
                "winner": 190,
                "loser": 190,
            },
            "Contest C": {
                "winner": 200,
                "loser": 140,
            },
        }
        sample_ticket_numbers[str(i)] = "Batch {}".format(i)

    expected_third_round = {
        "Contest A": 26,
        "Contest B": 12,
        "Contest C": 2,
    }

    for contest in contests:
        computed = macro.get_sample_sizes(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
        )

        assert (
            expected_third_round[contest] == computed
        ), "Third round sample expected {}, got {}".format(
            expected_third_round[contest], computed
        )

    # The "2" for C is conservative: audit should end after ome more 0-taint batch
    contest = "Contest C"
    sample["Batch 9"] = {
        contest: {
            "winner": 200,
            "loser": 140,
        }
    }
    sample_ticket_numbers["9"] = "Batch 9"
    computed = macro.get_sample_sizes(
        RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
    )

    assert computed == 0, "Fourth round sample expected 0, got {}".format(computed)


def test_full_recount(contests, batches) -> None:
    # Do a full recount:
    sample = batches
    sample_ticket_numbers = {str(i): batch for i, batch in enumerate(batches)}
    for contest in contests:

        with pytest.raises(ValueError, match=r"All ballots have already been counted!"):
            macro.get_sample_sizes(
                RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
            )

        computed_p, result = macro.compute_risk(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
        )

        assert computed_p == 0.0, "Incorrect p-value: Got {}, expected {}".format(
            computed_p, 0.0
        )

        assert result, "Audit did not terminate but should have"


def test_full_recount_with_replacement(contests, batches) -> None:
    # Do a full recount where all of the batches were sampled multiple times
    sample = batches
    sample_ticket_numbers = {
        str(i): batch
        for i, batch in enumerate(list(batches.keys()) + list(batches.keys()))
    }
    for contest in contests:

        with pytest.raises(ValueError, match=r"All ballots have already been counted!"):
            macro.get_sample_sizes(
                RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
            )

        computed_p, result = macro.compute_risk(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
        )

        assert computed_p == 0.0, "Incorrect p-value: Got {}, expected {}".format(
            computed_p, 0.0
        )

        assert result, "Audit did not terminate but should have"


def test_almost_done() -> None:
    info_dict = {
        "winner": 600,
        "loser": 400,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("test1", info_dict)

    # One batch
    batches = {"Batch 1": {"test1": {"winner": 600, "loser": 400}}}

    sample = {"Batch 1": {"test1": {"winner": 500, "loser": 500}}}
    sample_ticket_numbers = {"1": "Batch 1"}

    with pytest.raises(ValueError, match=r"All ballots have already been counted!"):
        macro.get_sample_sizes(
            RISK_LIMIT, contest, batches, sample, sample_ticket_numbers
        )


def test_worst_case() -> None:
    info_dict = {
        "winner": 1000,
        "loser": 0,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("test1", info_dict)

    # One batch
    batches = {
        "Batch 1": {
            "test1": {"winner": 500, "loser": 0, "ballots": 500, "numWinner": 1}
        },
        "Batch 2": {
            "test1": {"winner": 500, "loser": 0, "ballots": 500, "numWinner": 1}
        },
    }

    sample = {"Batch 1": {"test1": {"winner": 0, "loser": 500}}}
    sample_ticket_numbers = {"1": "Batch 1"}

    assert macro.compute_risk(
        RISK_LIMIT, contest, batches, sample, sample_ticket_numbers
    ) == (
        Decimal(1.0),
        False,
    )


def test_compute_risk(contests, batches) -> None:

    sample = {}
    sample_ticket_numbers = {}

    # Contest A: margin = 0.05, U = 21
    # Contest B: margin = 0.1, U = 11
    # Contest C: margin = 0.15, U = 23/3 = 7.666...

    # Draws with taint of 0
    for i in range(30):
        sample["Batch {}".format(i)] = {
            "Contest A": {
                "winner": 200,
                "loser": 180,
            },
            "Contest B": {
                "winner": 200,
                "loser": 160,
            },
            "Contest C": {
                "winner": 200,
                "loser": 140,
            },
        }
        sample_ticket_numbers[str(i)] = "Batch {}".format(i)

    # draws with taint of 0.04047619 (proportional to margin) for A, which
    # neither increase nor decrease the p value
    for i in range(100, 106):
        sample["Batch {}".format(i)] = {
            "Contest A": {
                "winner": 190,
                "loser": 190,
            },
            "Contest C": {
                "winner": 200,
                "loser": 140,
            },
        }
        sample_ticket_numbers[str(i)] = "Batch {}".format(i)

    # base multiplier for 0 taint is 1 - 1/U
    # (but last 6 batches don't affect A or B)
    expected_ps = {
        "Contest A": (20 / 21) ** 30,
        "Contest B": (10 / 11) ** 30,
        "Contest C": (20 / 23) ** 36,
    }

    for contest in contests:
        computed_p, result = macro.compute_risk(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
        )

        expected_p = expected_ps[contest]

        delta = abs(expected_p - computed_p)

        assert delta < 10**-4, "Incorrect p-value: Got {}, expected {}".format(
            computed_p, expected_p
        )

        assert result, "Audit did not terminate but should have"

    # Now test that duplication works (ensure unique ticket names)
    # (p value for A is unchanged, p value for C decreases)
    for i in range(100, 103):
        sample["Batch {}".format(i)] = {
            "Contest A": {
                "winner": 190,
                "loser": 190,
            },
            "Contest C": {
                "winner": 200,
                "loser": 140,
            },
        }
        sample_ticket_numbers[str(i + 6)] = "Batch {}".format(i)

    expected_ps = {
        "Contest A": (20 / 21) ** 30,
        "Contest B": (10 / 11) ** 30,
        "Contest C": (20 / 23) ** 39,
    }

    for contest in contests:
        computed_p, result = macro.compute_risk(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
        )

        expected_p = expected_ps[contest]

        delta = abs(expected_p - computed_p)

        assert delta < 10**-4, "Incorrect p-value: Got {}, expected {}".format(
            computed_p, expected_p
        )

        assert result, "Audit did not terminate but should have"


def test_tied_contest() -> None:

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
        batches[str(i)] = {
            "Tied Contest": {
                "winner": 500,
                "loser": 500,
                "ballots": 1000,
                "numWinners": 1,
            }
        }

    sample_results: Dict = {}
    sample_ticket_numbers: Dict = {}

    sample_size = macro.get_sample_sizes(
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers
    )

    assert sample_size == len(batches)

    sample_results = {
        "0": {
            "Tied Contest": {
                "winner": 500,
                "loser": 500,
                "ballots": 1000,
                "numWinners": 1,
            }
        }
    }
    sample_ticket_numbers = {"1": "0"}

    computed_p, res = macro.compute_risk(
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers
    )

    assert computed_p > ALPHA
    assert not res

    # Now do a full hand recount
    sample_ticket_numbers = {str(i): batch for i, batch in enumerate(batches.keys())}
    computed_p, res = macro.compute_risk(
        RISK_LIMIT, contest, batches, batches, sample_ticket_numbers
    )

    assert not computed_p
    assert res


def test_close_contest() -> None:
    contest_data = {
        "winner": 200,
        "loser": 198,
        "ballots": 400,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("Tied Contest", contest_data)

    batches = {}
    batches["1"] = {
        "Tied Contest": {
            "winner": 100,
            "loser": 0,
            "ballots": 100,
            "numWinners": 1,
        }
    }
    batches["2"] = {
        "Tied Contest": {
            "winner": 100,
            "loser": 0,
            "ballots": 100,
            "numWinners": 1,
        }
    }
    batches["3"] = {
        "Tied Contest": {
            "winner": 0,
            "loser": 100,
            "ballots": 100,
            "numWinners": 1,
        }
    }
    batches["4"] = {
        "Tied Contest": {
            "winner": 0,
            "loser": 98,
            "ballots": 100,
            "numWinners": 1,
        }
    }

    sample_results: Dict = {}
    sample_ticket_numbers: Dict = {}

    sample_size = macro.get_sample_sizes(
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers
    )

    assert sample_size == len(batches)

    sample_results = {
        "1": {
            "Tied Contest": {
                "winner": 100,
                "loser": 0,
                "ballots": 100,
                "numWinners": 1,
            }
        }
    }
    sample_ticket_numbers = {"1": "1"}

    computed_p, res = macro.compute_risk(
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers
    )

    assert computed_p > ALPHA
    assert not res

    # Now do a full hand recount
    sample_ticket_numbers = {str(i): batch for i, batch in enumerate(batches.keys())}
    computed_p, res = macro.compute_risk(
        RISK_LIMIT, contest, batches, batches, sample_ticket_numbers
    )

    assert not computed_p
    assert res

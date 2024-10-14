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
    for contest in contests:
        computed = macro.get_sample_sizes(
            RISK_LIMIT, contests[contest], batches, sample
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
    sample_ticket_numbers = {}
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
        "Contest A": 27,
        "Contest B": 13,
        "Contest C": 8,
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
        "Contest B": 13,
        "Contest C": 7,
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


def test_full_recount(contests, batches) -> None:
    # Do a full recount:
    sample = batches
    sample_ticket_numbers = {str(i): batch for i, batch in enumerate(batches)}
    for contest in contests:

        with pytest.raises(ValueError, match=r"All ballots have already been counted!"):
            macro.get_sample_sizes(RISK_LIMIT, contests[contest], batches, sample)

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
            macro.get_sample_sizes(RISK_LIMIT, contests[contest], batches, sample)

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

    with pytest.raises(ValueError, match=r"All ballots have already been counted!"):
        macro.get_sample_sizes(RISK_LIMIT, contest, batches, sample)


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

    # Draws with taint of 0
    for i in range(31):
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

    # draws with taint of 0.04047619
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

    for contest in contests:
        computed_p, result = macro.compute_risk(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
        )

        expected_p = 0.247688222

        delta = abs(expected_p - computed_p)

        assert delta < 10**-2, "Incorrect p-value: Got {}, expected {}".format(
            computed_p, expected_p
        )

        assert result, "Audit did not terminate but should have"

    # Now test that duplication works
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
        sample_ticket_numbers[str(i)] = "Batch {}".format(i)

    for contest in contests:
        computed_p, result = macro.compute_risk(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers
        )

        expected_p = 0.247688222

        delta = abs(expected_p - computed_p)

        assert delta < 10**-2, "Incorrect p-value: Got {}, expected {}".format(
            computed_p, expected_p
        )

        assert result, "Audit did not terminate but should have"


def test_compute_risk_uses_sample_order(contests, batches) -> None:
    sample = {}
    sample_ticket_numbers = {}

    # Draws with taint of 0
    for i in range(30):
        sample["Batch {}".format(i)] = {
            "Contest A": {
                "winner": 200,
                "loser": 180,
            },
        }
        sample_ticket_numbers[str(i).zfill(3)] = "Batch {}".format(i)

    # Draws with taint of 0.0952
    for i in range(100, 110):
        sample["Batch {}".format(i)] = {
            "Contest A": {
                "winner": 180,
                "loser": 200,
            },
        }
        sample_ticket_numbers[str(i).zfill(3)] = "Batch {}".format(i)

    # In the original sample order, we should reach the risk limit before
    # hitting the tainted draws
    computed_p, result = macro.compute_risk(
        RISK_LIMIT, contests["Contest A"], batches, sample, sample_ticket_numbers
    )
    expected_p = 0.247688222
    delta = abs(expected_p - computed_p)
    assert delta < 10**-2, "Incorrect p-value: Got {}, expected {}".format(
        computed_p, expected_p
    )
    assert result, "Audit did not terminate but should have"

    # Now reorder the sample so the tainted draws come first - the taint should
    # be too large to ever hit the risk limit
    sample_ticket_numbers = {
        str(len(sample_ticket_numbers) - i).zfill(3): batch
        for i, batch in enumerate(sample_ticket_numbers.values())
    }
    computed_p, result = macro.compute_risk(
        RISK_LIMIT, contests["Contest A"], batches, sample, sample_ticket_numbers
    )
    expected_p = 0.386
    delta = abs(expected_p - computed_p)
    assert delta < 10**-2, "Incorrect p-value: Got {}, expected {}".format(
        computed_p, expected_p
    )
    assert not result, "Audit terminated but shouldn't have"


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

    sample_size = macro.get_sample_sizes(RISK_LIMIT, contest, batches, sample_results)

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

    sample_size = macro.get_sample_sizes(RISK_LIMIT, contest, batches, sample_results)

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

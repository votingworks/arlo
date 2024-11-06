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
            computed_up = macro.compute_max_error(batches[batch], contests[contest], 0)

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
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers, []
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
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers, []
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
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers, []
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
        **expected_second_round,
        "Contest C": expected_second_round["Contest C"] - 5,
    }

    for contest in contests:
        computed = macro.get_sample_sizes(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers, []
        )

        assert (
            expected_third_round[contest] == computed
        ), "Third round sample expected {}, got {}".format(
            expected_third_round[contest], computed
        )

    # The "2" for C is conservative: audit should end after one more 0-taint batch
    contest = "Contest C"
    sample["Batch 9"] = {
        contest: {
            "winner": 200,
            "loser": 140,
        }
    }
    sample_ticket_numbers["9"] = "Batch 9"
    computed = macro.get_sample_sizes(
        RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers, []
    )

    assert computed == 0, "Fourth round sample expected 0, got {}".format(computed)


def test_full_recount(contests, batches) -> None:
    # Do a full recount:
    sample = batches
    sample_ticket_numbers = {str(i): batch for i, batch in enumerate(batches)}
    for contest in contests:

        with pytest.raises(ValueError, match=r"All ballots have already been counted!"):
            macro.get_sample_sizes(
                RISK_LIMIT,
                contests[contest],
                batches,
                sample,
                sample_ticket_numbers,
                [],
            )

        computed_p, result = macro.compute_risk(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers, []
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
                RISK_LIMIT,
                contests[contest],
                batches,
                sample,
                sample_ticket_numbers,
                [],
            )

        computed_p, result = macro.compute_risk(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers, []
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
            RISK_LIMIT, contest, batches, sample, sample_ticket_numbers, []
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
        RISK_LIMIT, contest, batches, sample, sample_ticket_numbers, []
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

    # 30 draws with taint of 0
    num_clean_batches = 30
    for i in range(num_clean_batches):
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

    # 6 draws with taint of 0.04047619 (proportional to margin) for A, which
    # neither increase nor decrease the p value. (These start at 100 because
    # of how Contest C is assigned to batches in the fixture.)
    num_tainted_batches = 6
    for i in range(100, 100 + num_tainted_batches):
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
        "Contest A": (20 / 21) ** num_clean_batches,
        "Contest B": (10 / 11) ** num_clean_batches,
        "Contest C": (20 / 23) ** (num_clean_batches + num_tainted_batches),
    }

    for contest in contests:
        computed_p, result = macro.compute_risk(
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers, []
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
            RISK_LIMIT, contests[contest], batches, sample, sample_ticket_numbers, []
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
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers, []
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
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers, []
    )

    assert computed_p > ALPHA
    assert not res

    # Now do a full hand recount
    sample_ticket_numbers = {str(i): batch for i, batch in enumerate(batches.keys())}
    computed_p, res = macro.compute_risk(
        RISK_LIMIT, contest, batches, batches, sample_ticket_numbers, []
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
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers, []
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
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers, []
    )

    assert computed_p > ALPHA
    assert not res

    # Now do a full hand recount
    sample_ticket_numbers = {str(i): batch for i, batch in enumerate(batches.keys())}
    computed_p, res = macro.compute_risk(
        RISK_LIMIT, contest, batches, batches, sample_ticket_numbers, []
    )

    assert not computed_p
    assert res


def test_combined_batches_no_discrepancies():
    contest_data = {
        "winner": 110,
        "loser": 90,
        "ballots": 200,
        "numWinners": 1,
        "votesAllowed": 1,
    }
    contest = Contest("Combined Batches Contest", contest_data)

    batches = {}
    batches["Batch 1"] = {
        contest.name: {
            "winner": 30,
            "loser": 20,
            "ballots": 50,
        }
    }
    batches["Batch 2"] = {
        contest.name: {
            "winner": 10,
            "loser": 40,
            "ballots": 50,
        }
    }
    batches["Batch 3"] = {
        contest.name: {
            "winner": 40,
            "loser": 0,
            "ballots": 40,
        }
    }
    batches["Batch 4"] = {
        contest.name: {
            "winner": 30,
            "loser": 30,
            "ballots": 60,
        }
    }

    sample_size = macro.get_sample_sizes(RISK_LIMIT, contest, batches, {}, {}, [])
    assert sample_size == len(batches)

    combined_batch_1_and_2_results = {
        contest.name: {
            "winner": batches["Batch 1"][contest.name]["winner"]
            + batches["Batch 2"][contest.name]["winner"],
            "loser": batches["Batch 1"][contest.name]["loser"]
            + batches["Batch 2"][contest.name]["loser"],
        }
    }
    sample_results = {
        "Batch 1": combined_batch_1_and_2_results,
        "Batch 2": combined_batch_1_and_2_results,
        "Batch 3": batches["Batch 3"],
    }
    sample_ticket_numbers = {
        "1": "Batch 1",
        "2": "Batch 2",
        "3": "Batch 3",
    }
    combined_batches = [{"Batch 1", "Batch 2"}]

    computed_p, res = macro.compute_risk(
        RISK_LIMIT,
        contest,
        batches,
        sample_results,
        sample_ticket_numbers,
        combined_batches,
    )
    U = macro.compute_U(batches, contest)
    expected_taint = 0
    expected_p = ((1 - 1 / U) / (1 - expected_taint)) ** len(sample_results)
    assert computed_p == float(expected_p)
    assert res is (expected_p < ALPHA)


def test_combined_batches_one_discrepancy():
    contest_data = {
        "winner": 110,
        "loser": 90,
        "ballots": 200,
        "numWinners": 1,
        "votesAllowed": 1,
    }
    contest = Contest("Combined Batches Contest", contest_data)

    batches = {}
    batches["Batch 1"] = {
        contest.name: {
            "winner": 30,
            "loser": 20,
            "ballots": 50,
        }
    }
    batches["Batch 2"] = {
        contest.name: {
            "winner": 10,
            "loser": 40,
            "ballots": 50,
        }
    }
    batches["Batch 3"] = {
        contest.name: {
            "winner": 40,
            "loser": 0,
            "ballots": 40,
        }
    }
    batches["Batch 4"] = {
        contest.name: {
            "winner": 30,
            "loser": 30,
            "ballots": 60,
        }
    }

    sample_size = macro.get_sample_sizes(RISK_LIMIT, contest, batches, {}, {}, [])
    assert sample_size == len(batches)

    discrepancy_votes = 2
    combined_batch_1_and_2_results = {
        contest.name: {
            "winner": batches["Batch 1"][contest.name]["winner"]
            + batches["Batch 2"][contest.name]["winner"],
            "loser": batches["Batch 1"][contest.name]["loser"]
            + batches["Batch 2"][contest.name]["loser"]
            + discrepancy_votes,
        }
    }
    sample_results = {
        "Batch 1": combined_batch_1_and_2_results,
        "Batch 2": combined_batch_1_and_2_results,
        "Batch 3": batches["Batch 3"],
    }
    sample_ticket_numbers = {
        "1": "Batch 1",
        "2": "Batch 2",
        "3": "Batch 3",
    }
    combined_batches = [{"Batch 1", "Batch 2"}]

    computed_p, res = macro.compute_risk(
        RISK_LIMIT,
        contest,
        batches,
        sample_results,
        sample_ticket_numbers,
        combined_batches,
    )
    U = macro.compute_U(batches, contest)
    max_error_batch_1 = (
        batches["Batch 1"][contest.name]["winner"]
        - batches["Batch 1"][contest.name]["loser"]
        + batches["Batch 1"][contest.name]["ballots"]
    )
    max_error_batch_2 = (
        batches["Batch 2"][contest.name]["winner"]
        - batches["Batch 2"][contest.name]["loser"]
        + batches["Batch 2"][contest.name]["ballots"]
    )
    expected_taint_batch_1 = discrepancy_votes / max_error_batch_1
    expected_taint_batch_2 = discrepancy_votes / max_error_batch_2
    numerator = 1 - 1 / U
    expected_p = (
        (numerator / (1 - Decimal(expected_taint_batch_1)))
        * (numerator / (1 - Decimal(expected_taint_batch_2)))
        * ((numerator / 1) ** (len(sample_results) - 2))
    )
    assert computed_p == float(expected_p)
    assert res is (expected_p < ALPHA)


def test_combined_batches_sampled_and_unsampled():
    contest_data = {
        "winner": 120,
        "loser": 80,
        "third": 50,
        "ballots": 250,
        "numWinners": 1,
        "votesAllowed": 1,
    }
    contest = Contest("Combined Batches Contest", contest_data)

    batches = {}
    batches["Batch 1"] = {
        contest.name: {
            "winner": 30,
            "loser": 20,
            "third": 0,
            "ballots": 50,
        }
    }
    batches["Batch 2"] = {
        contest.name: {
            "winner": 0,
            "loser": 40,
            "third": 10,
            "ballots": 50,
        }
    }
    batches["Batch 3"] = {
        contest.name: {
            "winner": 60,
            "loser": 10,
            "third": 30,
            "ballots": 100,
        }
    }
    batches["Batch 4"] = {
        contest.name: {
            "winner": 30,
            "loser": 10,
            "third": 10,
            "ballots": 50,
        }
    }

    sample_size = macro.get_sample_sizes(RISK_LIMIT, contest, batches, {}, {}, [])
    assert sample_size == len(batches)

    discrepancy_votes = 3
    combined_batch_1_and_4_results = {
        contest.name: {
            "winner": batches["Batch 1"][contest.name]["winner"]
            + batches["Batch 4"][contest.name]["winner"],
            "loser": batches["Batch 1"][contest.name]["loser"]
            + batches["Batch 4"][contest.name]["loser"]
            + discrepancy_votes,
            "third": batches["Batch 1"][contest.name]["third"]
            + batches["Batch 4"][contest.name]["third"],
        }
    }

    sample_results = {
        "Batch 1": combined_batch_1_and_4_results,
        "Batch 2": batches["Batch 2"],
        "Batch 3": batches["Batch 3"],
    }
    sample_ticket_numbers = {
        "1": "Batch 1",
        "2": "Batch 2",
        "3": "Batch 3",
    }
    combined_batches = [{"Batch 1", "Batch 4"}]

    computed_p, res = macro.compute_risk(
        RISK_LIMIT,
        contest,
        batches,
        sample_results,
        sample_ticket_numbers,
        combined_batches,
    )
    U = macro.compute_U(batches, contest)
    max_error_batch_1 = (
        batches["Batch 1"][contest.name]["winner"]
        - batches["Batch 1"][contest.name]["loser"]
        + batches["Batch 1"][contest.name]["ballots"]
    )
    expected_taint_batch_1 = discrepancy_votes / max_error_batch_1
    numerator = 1 - 1 / U
    expected_p = (numerator / (1 - Decimal(expected_taint_batch_1))) * (
        (numerator / 1) ** (len(sample_results) - 1)
    )
    assert computed_p == float(expected_p)
    assert res is (expected_p < ALPHA)


def test_pending_ballots(snapshot):
    num_pending_ballots = 2
    contest_data = {
        "winner": 200,
        "loser": 100,
        "third": 50,
        # Total ballots cast is calculated from ballot manifests, so doesn't
        # include pending ballots
        "ballots": 350,
        "numWinners": 1,
        "votesAllowed": 1,
        "pendingBallots": num_pending_ballots,
    }

    contest = Contest("Contest", contest_data)
    contest_without_pending_ballots = Contest(
        "Contest", {**contest_data, "pendingBallots": None}
    )

    batches = {}
    batches["Batch 1"] = {
        contest.name: {
            "winner": 60,
            "loser": 40,
            "third": 0,
            "ballots": 100,
        }
    }
    batches["Batch 2"] = {
        contest.name: {
            "winner": 0,
            "loser": 60,
            "third": 40,
            "ballots": 100,
        }
    }
    batches["Batch 3"] = {
        contest.name: {
            "winner": 90,
            "loser": 0,
            "third": 10,
            "ballots": 100,
        }
    }
    batches["Batch 4"] = {
        contest.name: {
            "winner": 50,
            "loser": 0,
            "third": 0,
            "ballots": 50,
        }
    }

    # With pending ballots, we want to increase the max possible error (U) so
    # that our calculations are more conservative.
    U = macro.compute_U(batches, contest)
    U_without_pending = macro.compute_U(batches, contest_without_pending_ballots)
    assert U > U_without_pending
    snapshot.assert_match(U)

    sample_size = macro.get_sample_sizes(RISK_LIMIT, contest, batches, {}, {}, [])
    assert sample_size == len(batches)

    # Don't actually do a full recount so we can assess a computed p-value,
    # rather than an automatic 0 p-value
    num_sampled_batches = len(batches) - 1
    # No discrepancies
    sample_results = dict(list(batches.items())[:num_sampled_batches])
    sample_ticket_numbers = {
        str(i): batch_name for i, batch_name in enumerate(sample_results.keys())
    }

    computed_p, res = macro.compute_risk(
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers, []
    )

    expected_p = ((1 - 1 / U) / 1) ** num_sampled_batches
    assert computed_p == float(expected_p)
    assert res is (expected_p < ALPHA)
    snapshot.assert_match(computed_p)

    # 1 discrepancy
    discrepancy_votes = 2
    sample_results = {
        **sample_results,
        "Batch 3": {
            contest.name: {
                **sample_results["Batch 3"][contest.name],
                "winner": sample_results["Batch 3"][contest.name]["winner"],
                "loser": sample_results["Batch 3"][contest.name]["loser"]
                + discrepancy_votes,
            }
        },
    }

    computed_p, res = macro.compute_risk(
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers, []
    )

    max_error_batch_3 = (
        batches["Batch 3"][contest.name]["winner"]
        - batches["Batch 3"][contest.name]["loser"]
        + batches["Batch 3"][contest.name]["ballots"]
    )
    taint_batch_3 = discrepancy_votes / max_error_batch_3
    expected_p = (((1 - 1 / U) / 1) ** (num_sampled_batches - 1)) * (
        (1 - 1 / U) / (1 - Decimal(taint_batch_3))
    )
    assert computed_p == float(expected_p)
    assert res is (expected_p < ALPHA)
    snapshot.assert_match(computed_p)


def test_unauditable_ballots(snapshot):
    contest_data = {
        "winner": 200,
        "loser": 100,
        "third": 50,
        "ballots": 350,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("Contest", contest_data)

    # Create batches that remove votes from the loser for any unauditable
    # ballots. That way we can test that these votes are treated as votes for
    # the loser.
    def create_batches(num_unauditable_ballots: int):
        batches = {}
        batches["Batch 1"] = {
            contest.name: {
                "winner": 60,
                "loser": 40 - num_unauditable_ballots / 2,
                "third": 0,
                "ballots": 100 - num_unauditable_ballots / 2,
            }
        }
        batches["Batch 2"] = {
            contest.name: {
                "winner": 0,
                "loser": 60 - num_unauditable_ballots / 2,
                "third": 40,
                "ballots": 100 - num_unauditable_ballots / 2,
            }
        }
        batches["Batch 3"] = {
            contest.name: {
                "winner": 90,
                "loser": 0,
                "third": 10,
                "ballots": 100,
            }
        }
        batches["Batch 4"] = {
            contest.name: {
                "winner": 50,
                "loser": 0,
                "third": 0,
                "ballots": 50,
            }
        }
        return batches

    batches = create_batches(1)
    batches_without_unauditable_ballots = create_batches(0)

    U = macro.compute_U(batches, contest)
    U_without_unauditable_ballots = macro.compute_U(
        batches_without_unauditable_ballots, contest
    )
    assert U > U_without_unauditable_ballots
    snapshot.assert_match(
        dict(U=U, U_without_unauditable_ballots=U_without_unauditable_ballots)
    )

    sample_size = macro.get_sample_sizes(RISK_LIMIT, contest, batches, {}, {}, [])
    assert sample_size == len(batches)

    # Don't actually do a full recount so we can assess a computed p-value,
    # rather than an automatic 0 p-value
    num_sampled_batches = len(batches) - 1
    # No discrepancies
    sample_results = dict(list(batches.items())[:num_sampled_batches])
    sample_results_without_unauditable_ballots = dict(
        list(batches_without_unauditable_ballots.items())[:num_sampled_batches]
    )
    sample_ticket_numbers = {
        str(i): batch_name for i, batch_name in enumerate(sample_results.keys())
    }

    computed_p, _ = macro.compute_risk(
        RISK_LIMIT, contest, batches, sample_results, sample_ticket_numbers, []
    )
    computed_p_without_unauditable_ballots, _ = macro.compute_risk(
        RISK_LIMIT,
        contest,
        batches_without_unauditable_ballots,
        sample_results_without_unauditable_ballots,
        sample_ticket_numbers,
        [],
    )
    assert computed_p > computed_p_without_unauditable_ballots
    expected_p = ((1 - 1 / U) / 1) ** num_sampled_batches
    assert computed_p == float(expected_p)
    snapshot.assert_match(
        dict(
            computed_p=computed_p,
            computed_p_without_unauditable_ballots=computed_p_without_unauditable_ballots,
        )
    )

# pylint: disable=invalid-name,consider-using-dict-items,consider-using-f-string
from decimal import Decimal
import pytest

from ...audit_math import supersimple
from ...audit_math.sampler_contest import CVRS, SAMPLECVRS, Contest

seed = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
ALPHA = Decimal(0.1)
RISK_LIMIT = 10


@pytest.fixture
def cvrs():
    cvr = {}
    for i in range(100000):
        if i < 60000:
            contest_a_res = {"winner": "1", "loser": "0"}
        else:
            contest_a_res = {"winner": "0", "loser": "1"}

        cvr[f"ballot-{i}"] = {"Contest A": contest_a_res}

        if i < 30000:
            cvr[f"ballot-{i}"]["Contest B"] = {"winner": "1", "loser": "0"}
        elif 30000 <= i < 60000:
            cvr[f"ballot-{i}"]["Contest B"] = {"winner": "0", "loser": "1"}

        if i < 18000:
            cvr[f"ballot-{i}"]["Contest C"] = {"winner": "1", "loser": "0"}
        elif 18000 <= i < 36000:
            cvr[f"ballot-{i}"]["Contest C"] = {"winner": "0", "loser": "1"}

        if i < 8000:
            cvr[f"ballot-{i}"]["Contest D"] = {"winner": "1", "loser": "0"}
        elif 8000 <= i < 14000:
            cvr[f"ballot-{i}"]["Contest D"] = {"winner": "0", "loser": "1"}

        if i < 10000:
            cvr[f"ballot-{i}"]["Contest E"] = {"winner": "1", "loser": "0"}

        if i < 300:
            cvr[f"ballot-{i}"]["Two-winner Contest"] = {
                "winner1": "0",
                "winner2": "1",
                "loser": "0",
            }
        elif 300 <= i < 900:
            cvr[f"ballot-{i}"]["Two-winner Contest"] = {
                "winner1": "1",
                "winner2": "0",
                "loser": "0",
            }
        elif i < 1000:
            cvr[f"ballot-{i}"]["Two-winner Contest"] = {
                "winner1": "0",
                "winner2": "0",
                "loser": "1",
            }

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
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": "1", "loser": "0"},
                "Contest B": {"winner": "1", "loser": "0"},
                "Contest C": {"winner": "1", "loser": "0"},
                "Contest D": {"winner": "1", "loser": "0"},
                "Contest E": {"winner": "1", "loser": "0"},
                "Two-winner Contest": {"winner1": "0", "winner2": "1", "loser": "0"},
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
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": "0", "loser": "0"},
                "Contest B": {"winner": "1", "loser": "0"},
                "Contest C": {"winner": "1", "loser": "0"},
                "Contest D": {"winner": "1", "loser": "0"},
                "Contest E": {"winner": "1", "loser": "0"},
                "Two-winner Contest": {"winner1": "0", "winner2": "0", "loser": "0"},
            },
        }
    }

    for contest in contests:
        discrepancies = supersimple.compute_discrepancies(
            contests[contest], cvrs, sample_cvr
        )
        if contest == "Contest A":
            assert discrepancies["ballot-0"]["counted_as"] == 1
            assert discrepancies["ballot-0"]["weighted_error"] == Decimal(1) / Decimal(
                20000
            )
        elif contest == "Two-winner Contest":
            assert discrepancies["ballot-0"]["counted_as"] == 1
            assert discrepancies["ballot-0"]["weighted_error"] == Decimal(1) / Decimal(
                200
            )

        else:
            assert not discrepancies


def test_negative_discrepancies(contests, cvrs):
    sample_cvr = {
        "ballot-60000": {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {
                    "winner": "1",
                    "loser": "0",
                },  # One of the reported loser ballots was actually a winner ballot
            },
        }
    }

    discrepancies = supersimple.compute_discrepancies(
        contests["Contest A"], cvrs, sample_cvr
    )

    assert discrepancies
    assert discrepancies["ballot-60000"]["counted_as"] == -2
    assert discrepancies["ballot-60000"]["weighted_error"] == Decimal(-2) / Decimal(
        20000
    )


def test_two_vote_overstatement_discrepancies(contests, cvrs):
    sample_cvr = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {
                    "winner": "0",
                    "loser": "1",
                },  # One of the reported winner ballots was actually a loser ballot
            },
        }
    }

    discrepancies = supersimple.compute_discrepancies(
        contests["Contest A"], cvrs, sample_cvr
    )

    assert discrepancies
    assert discrepancies["ballot-0"]["counted_as"] == 2
    assert discrepancies["ballot-0"]["weighted_error"] == Decimal(2) / Decimal(20000)


def test_race_not_in_cvr_discrepancy(contests, cvrs):

    sample_cvr = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {
                "Contest F": {
                    "winner": "0",
                    "loser": "1",
                },  # The audit board found a race not in the CVR
            },
        }
    }

    discrepancies = supersimple.compute_discrepancies(
        contests["Contest F"], cvrs, sample_cvr
    )

    assert discrepancies
    assert discrepancies["ballot-0"]["counted_as"] == 1
    assert discrepancies["ballot-0"]["weighted_error"] == Decimal(1) / Decimal(6)


def test_race_not_in_sample_discrepancy(contests, cvrs):

    sample_cvr = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": "0", "loser": "0"},
                "Contest B": {"winner": "1", "loser": "0"},
                "Contest C": {"winner": "1", "loser": "0"},
                "Contest E": {"winner": "1", "loser": "0"},
            },
        }
    }

    discrepancies = supersimple.compute_discrepancies(
        contests["Contest D"], cvrs, sample_cvr
    )

    assert discrepancies
    assert discrepancies["ballot-0"]["counted_as"] == 1
    assert discrepancies["ballot-0"]["weighted_error"] == Decimal(1) / Decimal(2000)


def test_ballot_not_found_discrepancy(contests, cvrs):
    sample_cvr = {"ballot-0": {"times_sampled": 1, "cvr": None}}

    discrepancies = supersimple.compute_discrepancies(
        contests["Contest D"], cvrs, sample_cvr
    )

    assert discrepancies
    assert discrepancies["ballot-0"]["counted_as"] == 2
    assert discrepancies["ballot-0"]["weighted_error"] == Decimal(2) / Decimal(2000)


def test_ballot_not_in_cvr(contests):
    cvrs = {}
    sample_cvr = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {"Contest D": {"winner": "1", "loser": "0"}},
        }
    }

    discrepancies = supersimple.compute_discrepancies(
        contests["Contest D"], cvrs, sample_cvr
    )

    assert discrepancies
    assert discrepancies["ballot-0"]["counted_as"] == 2
    assert discrepancies["ballot-0"]["weighted_error"] == Decimal(2) / Decimal(2000)


def test_ballot_not_in_cvr_and_not_found(contests):
    cvrs = {}
    sample_cvr = {"ballot-0": {"times_sampled": 1, "cvr": None}}

    discrepancies = supersimple.compute_discrepancies(
        contests["Contest D"], cvrs, sample_cvr
    )

    assert discrepancies
    assert discrepancies["ballot-0"]["counted_as"] == 2
    assert discrepancies["ballot-0"]["weighted_error"] == Decimal(2) / Decimal(2000)


def test_ess_discrepancies(contests) -> None:
    cvrs: CVRS = {
        "ballot-0": {"Contest A": {"winner": "o", "loser": "o"}},
        "ballot-1": {"Contest A": {"winner": "u", "loser": "u"}},
        "ballot-2": {"Contest A": {"winner": "1", "loser": "0"}},
    }

    # Correct auditing
    sample_cvr: SAMPLECVRS = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "1", "loser": "1"}},
        },
        "ballot-1": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "0", "loser": "0"}},
        },
        "ballot-2": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "1", "loser": "0"}},
        },
    }
    discrepancies = supersimple.compute_discrepancies(
        contests["Contest A"], cvrs, sample_cvr
    )
    assert discrepancies == {}

    # Votes for the loser
    sample_cvr = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "0", "loser": "1"}},
        },
        "ballot-1": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "0", "loser": "1"}},
        },
        "ballot-2": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "0", "loser": "1"}},
        },
    }
    discrepancies = supersimple.compute_discrepancies(
        contests["Contest A"], cvrs, sample_cvr
    )
    assert discrepancies == {
        "ballot-0": supersimple.Discrepancy(
            counted_as=1, weighted_error=Decimal(1) / Decimal(20000)
        ),
        "ballot-1": supersimple.Discrepancy(
            counted_as=1, weighted_error=Decimal(1) / Decimal(20000)
        ),
        "ballot-2": supersimple.Discrepancy(
            counted_as=2, weighted_error=Decimal(1) / Decimal(10000)
        ),
    }

    # Votes for the winner
    sample_cvr = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "1", "loser": "0"}},
        },
        "ballot-1": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "1", "loser": "0"}},
        },
        "ballot-2": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "1", "loser": "0"}},
        },
    }
    discrepancies = supersimple.compute_discrepancies(
        contests["Contest A"], cvrs, sample_cvr
    )
    assert discrepancies == {
        "ballot-0": supersimple.Discrepancy(
            counted_as=-1, weighted_error=Decimal(-1) / Decimal(20000)
        ),
        "ballot-1": supersimple.Discrepancy(
            counted_as=-1, weighted_error=Decimal(-1) / Decimal(20000)
        ),
    }

    # Reversed overvotes/undervotes
    sample_cvr = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "0", "loser": "0"}},
        },
        "ballot-1": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "1", "loser": "1"}},
        },
        "ballot-2": {
            "times_sampled": 1,
            "cvr": {"Contest A": {"winner": "1", "loser": "0"}},
        },
    }
    discrepancies = supersimple.compute_discrepancies(
        contests["Contest A"], cvrs, sample_cvr
    )
    assert discrepancies == {}

    # Missing ballots/contest not on ballot
    cvrs = {
        **cvrs,
        "ballot-0": None,
        "ballot-3": {},
    }
    sample_cvr = {
        "ballot-0": {"times_sampled": 1, "cvr": {}},
        "ballot-1": {"times_sampled": 1, "cvr": None},
        "ballot-3": {"times_sampled": 1, "cvr": {}},
    }
    discrepancies = supersimple.compute_discrepancies(
        contests["Contest A"], cvrs, sample_cvr
    )
    assert discrepancies == {
        "ballot-0": supersimple.Discrepancy(
            counted_as=2, weighted_error=Decimal(2) / Decimal(20000)
        ),
        "ballot-1": supersimple.Discrepancy(
            counted_as=2, weighted_error=Decimal(2) / Decimal(20000)
        ),
    }

    # More than two candidates
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
    cvrs = {
        "ballot-0": {"Two Losers": {"winner": "o", "loser1": "o", "loser2": "o"}},
        "ballot-1": {"Two Losers": {"winner": "u", "loser1": "u", "loser2": "u"}},
        "ballot-2": {"Two Losers": {"winner": "1", "loser1": "0", "loser2": "0"}},
    }
    sample_cvr = {
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
    discrepancies = supersimple.compute_discrepancies(contest, cvrs, sample_cvr)
    assert discrepancies == {}

    # Partial overvotes/undervotes (in the case where one jurisdiction's CVR
    # records an overvote/undervote, but there are other choices merged in from
    # other jurisdictions' CVRs, those other choices would have a vote 0)
    cvrs = {
        "ballot-0": {"Two Losers": {"winner": "o", "loser1": "o", "loser2": "0"}},
        "ballot-1": {"Two Losers": {"winner": "u", "loser1": "u", "loser2": "0"}},
    }
    sample_cvr = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {"Two Losers": {"winner": "0", "loser1": "0", "loser2": "1"}},
        },
        "ballot-1": {
            "times_sampled": 1,
            "cvr": {"Two Losers": {"winner": "0", "loser1": "0", "loser2": "1"}},
        },
    }
    discrepancies = supersimple.compute_discrepancies(contest, cvrs, sample_cvr)
    assert discrepancies == {
        "ballot-0": supersimple.Discrepancy(
            counted_as=1, weighted_error=Decimal(1) / Decimal(500)
        ),
        "ballot-1": supersimple.Discrepancy(
            counted_as=1, weighted_error=Decimal(1) / Decimal(500)
        ),
    }


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
            sample_cvr[f"ballot-{i}"] = {
                "times_sampled": 1,
                "cvr": {
                    "Contest A": {"winner": "1", "loser": "0"},
                    "Contest B": {"winner": "1", "loser": "0"},
                    "Contest C": {"winner": "1", "loser": "0"},
                    "Contest D": {"winner": "1", "loser": "0"},
                    "Contest E": {"winner": "1", "loser": "0"},
                    "Two-winner Contest": {
                        "winner1": "0",
                        "winner2": "1",
                        "loser": "0",
                    },
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
            "1-under": "0",
            "1-over": "0",
            "2-under": "0",
            "2-over": "0",
        }

        next_sample_size = supersimple.get_sample_sizes(
            RISK_LIMIT, contests[contest], to_sample
        )
        assert next_sample_size == 0

        # Test one-vote overstatement
        sample_cvr["ballot-0"] = {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": "0", "loser": "0"},
                "Contest B": {"winner": "0", "loser": "0"},
                "Contest C": {"winner": "0", "loser": "0"},
                "Contest D": {"winner": "0", "loser": "0"},
                "Contest E": {"winner": "0", "loser": "0"},
                "Two-winner Contest": {"winner1": "0", "winner2": "0", "loser": "0"},
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
            "1-under": "0",
            "1-over": "1",
            "2-under": "0",
            "2-over": "0",
        }

        next_sample_size = supersimple.get_sample_sizes(
            RISK_LIMIT, contests[contest], to_sample
        )
        assert (
            next_sample_size == o1_stopping_size[contest] - sample_size
        ), "Number of ballots left to sample is not correct in contest {}!".format(
            contest
        )

        # Test two-vote overstatement
        sample_cvr["ballot-0"] = {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": "0", "loser": "1"},
                "Contest B": {"winner": "0", "loser": "1"},
                "Contest C": {"winner": "0", "loser": "1"},
                "Contest D": {"winner": "0", "loser": "1"},
                "Contest E": {"winner": "0", "loser": "1"},
                "Two-winner Contest": {"winner1": "0", "winner2": "0", "loser": "1"},
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
            "1-under": "0",
            "1-over": "0",
            "2-under": "0",
            "2-over": "1",
        }

        next_sample_size = supersimple.get_sample_sizes(
            RISK_LIMIT, contests[contest], to_sample
        )
        assert (
            next_sample_size == o2_stopping_size[contest] - sample_size
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
            cvr[f"ballot-{i}"] = {"Tied Contest": {"winner": "1", "loser": "0"}}
        else:
            cvr[f"ballot-{i}"] = {"Tied Contest": {"winner": "0", "loser": "1"}}

    sample_results = {
        "sample_size": "0",
        "1-under": "0",
        "1-over": "0",
        "2-under": "0",
        "2-over": "0",
    }

    sample_size = supersimple.get_sample_sizes(RISK_LIMIT, contest, sample_results)

    assert sample_size == contest_data["ballots"]

    sample_cvr = {
        "ballot-0": {
            "times_sampled": 1,
            "cvr": {"Tied Contest": {"winner": "1", "loser": "0"}},
        }
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


def test_supersimple_full_hand_tally():
    # Simulate a sample drawn with replacement where the sample size is equal to
    # the total ballots cast but the number of unique ballots drawn is less
    contest = Contest(
        "Full Hand Tally",
        {
            "choice_1": 5,
            "choice_2": 4,
            "ballots": 10,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )
    cvr = {
        "ballot-1": {"choice_1": "1", "choice_2": "0"},
        "ballot-2": {"choice_1": "1", "choice_2": "0"},
        "ballot-3": {"choice_1": "1", "choice_2": "0"},
        "ballot-4": {"choice_1": "1", "choice_2": "0"},
        "ballot-5": {"choice_1": "1", "choice_2": "0"},
        "ballot-6": {"choice_1": "0", "choice_2": "1"},
        "ballot-7": {"choice_1": "0", "choice_2": "1"},
        "ballot-8": {"choice_1": "0", "choice_2": "1"},
        "ballot-9": {"choice_1": "0", "choice_2": "1"},
        "ballot-10": {"choice_1": "0", "choice_2": "0"},
    }
    sample_cvr = {
        "ballot-1": {"times_sampled": 2, "cvr": {"choice_1": "1", "choice_2": "0"}},
        "ballot-2": {"times_sampled": 2, "cvr": {"choice_1": "1", "choice_2": "0"}},
        "ballot-6": {"times_sampled": 2, "cvr": {"choice_1": "0", "choice_2": "1"}},
        "ballot-7": {"times_sampled": 2, "cvr": {"choice_1": "0", "choice_2": "1"}},
        "ballot-8": {"times_sampled": 2, "cvr": {"choice_1": "0", "choice_2": "1"}},
    }
    p, res = supersimple.compute_risk(RISK_LIMIT, contest, cvr, sample_cvr)

    assert p == 0
    assert res is True


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
            cvr[f"ballot-{i}"] = {"Jonah Test": {"winner": "1", "loser": "0"}}
        else:
            cvr[f"ballot-{i}"] = {"Jonah Test": {"winner": "0", "loser": "1"}}

    sample_results = {
        "sample_size": "0",
        "1-under": "0",
        "1-over": "0",
        "2-under": "0",
        "2-over": "0",
    }

    _ = supersimple.get_sample_sizes(RISK_LIMIT, contest, sample_results)

    sample_cvr = {}
    for ballot in range(18):
        sample_cvr[f"ballot-{ballot}"] = {
            "times_sampled": 1,
            "cvr": cvr[f"ballot-{ballot}"],
        }

    # Two of our winning ballots were actually blank
    sample_cvr["ballot-0"]["cvr"]["Jonah Test"] = {"winner": "0", "loser": "0"}
    sample_cvr["ballot-1"]["cvr"]["Jonah Test"] = {"winner": "0", "loser": "0"}

    p, res = supersimple.compute_risk(RISK_LIMIT, contest, cvr, sample_cvr)

    expected_p = 0.1201733
    assert abs(expected_p - p) < 0.0001
    assert not res

    # now draw 9 more ballots without any discrepancies
    sample_cvr = {}
    for ballot in cvr:
        sample_cvr[ballot] = {"times_sampled": 1, "cvr": cvr[ballot]}
    sample_cvr["ballot-0"]["cvr"]["Jonah Test"] = {"winner": "0", "loser": "0"}
    sample_cvr["ballot-1"]["cvr"]["Jonah Test"] = {"winner": "0", "loser": "0"}

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
            cvr[f"ballot-{i}"] = {"Jonah Test": {"winner": "1", "loser": "0"}}
        else:
            cvr[f"ballot-{i}"] = {"Jonah Test": {"winner": "0", "loser": "1"}}

    sample_results = {
        "sample_size": "0",
        "1-under": "0",
        "1-over": "0",
        "2-under": "0",
        "2-over": "0",
    }

    _ = supersimple.get_sample_sizes(RISK_LIMIT, contest, sample_results)

    sample_cvr = {}
    for ballot in range(18):
        sample_cvr[f"ballot-{ballot}"] = {
            "times_sampled": 1,
            "cvr": cvr[f"ballot-{ballot}"],
        }
    # Two of our winning ballots were actually blank
    sample_cvr["ballot-0"]["cvr"]["Jonah Test"] = {"winner": "0", "loser": "0"}
    sample_cvr["ballot-1"]["cvr"]["Jonah Test"] = {"winner": "0", "loser": "0"}

    p, res = supersimple.compute_risk(RISK_LIMIT, contest, cvr, sample_cvr)

    expected_p = 0.1201733
    assert abs(expected_p - p) < 0.0001
    assert not res

    # now draw those same ballots again
    for ballot in sample_cvr:
        sample_cvr[ballot]["cvr"]["times_sampled"] = 2

    p, res = supersimple.compute_risk(RISK_LIMIT, contest, cvr, sample_cvr)

    assert not res
    assert p != 0  # This wasn't a recount


def test_supersimple_sample_size_zero_risk_limit():
    contest_data = {
        "winner": 15,
        "loser": 10,
        "ballots": 30,
        "numWinners": 1,
        "votesAllowed": 1,
    }
    contest = Contest("Test Contest", contest_data)
    assert supersimple.get_sample_sizes(0, contest, None) == contest.ballots


true_dms = {
    "Contest A": 0.2,
    "Contest B": 0.1,
    "Contest C": 0.15,
    "Contest D": 2 / 15,
    "Contest E": 1,
    "Two-winner Contest": 0.2,
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


o1_stopping_size = {
    "Contest A": 38,
    "Contest B": 76,
    "Contest C": 51,
    "Contest D": 57,
    "Contest E": 7,
    "Contest F": 15,  # nMin yields 16, but contest only has 15 total votes
    "Two-winner Contest": 38,
}

o2_stopping_size = {
    "Contest A": 100000,
    "Contest B": 60000,
    "Contest C": 36000,
    "Contest D": 15000,
    "Contest E": 33,
    "Contest F": 15,
    "Two-winner Contest": 1000,
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
    "Two-winner Contest": {
        "winner1": 600,
        "winner2": 300,
        "loser": 100,
        "ballots": 1000,
        "numWinners": 2,
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
        "Two-winner Contest": 0.06508,
    },
    "one_vote_over": {
        "Contest A": 0.12534,
        "Contest B": 0.13441,
        "Contest C": 0.12992,
        "Contest D": 0.13585,
        "Contest E": 0.03758,
        "Contest F": 0.05013,
        "Two-winner Contest": 0.12534,
    },
    "two_vote_over": {
        "Contest A": 1.0,
        "Contest B": 1.0,
        "Contest C": 1.0,
        "Contest D": 1.0,
        "Contest E": 0.51877,
        "Contest F": 0.05013,
        "Two-winner Contest": 1.0,
    },
}

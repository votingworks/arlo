# pylint: disable=invalid-name,consider-using-dict-items,consider-using-f-string
from decimal import Decimal
from typing import cast
import json
import pytest
import numpy as np

from ...audit_math import supersimple
from ...audit_math.sampler_contest import Contest, SAMPLECVRS, CVR
from ...audit_math.raire import compute_raire_assertions
from ...audit_math.raire_utils import NEBAssertion, NENAssertion

from .test_raire_utils import make_neb_assertion
from ...audit_math import supersimple_raire

ALPHA = Decimal(0.1)
RISK_LIMIT = 10


# Testing for now...
def asn_func(m):
    return 1 / m if m > 0 else np.inf


@pytest.fixture
def cvrs():
    cvr = {}
    for i in range(100000):
        if i < 60000:
            contest_a_res = {"winner": 1, "loser": 2}
        else:
            contest_a_res = {"winner": 2, "loser": 1}

        cvr[i] = {"Contest A": contest_a_res}

        if i < 30000:
            cvr[i]["Contest B"] = {"winner": 1, "loser": 2}
        elif 30000 <= i < 54000:
            cvr[i]["Contest B"] = {"winner": 2, "loser": 1}

        if i < 18000:
            cvr[i]["Contest C"] = {"winner": 1, "loser": 2}
        elif 18000 <= i < 30600:
            cvr[i]["Contest C"] = {"winner": 2, "loser": 1}

        if i < 8000:
            cvr[i]["Contest D"] = {"winner": 1, "loser": 2}
        elif 8000 <= i < 14000:
            cvr[i]["Contest D"] = {"winner": 2, "loser": 1}

        if i < 10000:
            cvr[i]["Contest E"] = {"winner": 1, "loser": 2}

    yield cvr


@pytest.fixture
def contests():
    contests = {}

    for contest in ss_contests:
        contests[contest] = Contest(contest, ss_contests[contest])

    yield contests


@pytest.fixture()
def assertions(contests, cvrs):
    assertions = {}
    for contest in contests:
        assertions[contest] = [
            make_neb_assertion(contests[contest], cvrs, asn_func, "winner", "loser", [])
        ]
    return assertions


def test_find_no_discrepancies(contests, cvrs, assertions):

    # Test no discrepancies
    sample_cvr = {
        0: {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": 1, "loser": 2},
                "Contest B": {"winner": 1, "loser": 2},
                "Contest C": {"winner": 1, "loser": 2},
                "Contest D": {"winner": 1, "loser": 2},
                "Contest E": {"winner": 1, "loser": 2},
            },
        }
    }

    for contest in contests:
        for assertion in assertions[contest]:
            discrepancies = supersimple_raire.compute_discrepancies(
                cvrs, sample_cvr, assertion
            )
            assert not discrepancies


def test_find_one_discrepancy(contests, cvrs, assertions):

    # Test one discrepancy
    sample_cvr = {
        0: {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": 0, "loser": 0},
                "Contest B": {"winner": 1, "loser": 2},
                "Contest C": {"winner": 1, "loser": 2},
                "Contest D": {"winner": 1, "loser": 2},
                "Contest E": {"winner": 1, "loser": 2},
            },
        }
    }

    for contest in contests:
        for assertion in assertions[contest]:
            discrepancies = supersimple_raire.compute_discrepancies(
                cvrs, sample_cvr, assertion
            )

            if contest == "Contest A":
                assert discrepancies[0]["counted_as"] == 1
                assert discrepancies[0]["weighted_error"] == Decimal(1) / Decimal(20000)
            else:
                assert not discrepancies


def test_negative_discrepancies(cvrs, assertions):
    sample_cvr = {
        60000: {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {
                    "winner": 1,
                    "loser": 2,
                },  # One of the reported loser ballots was actually a winner ballot
            },
        }
    }

    discrepancies = supersimple_raire.compute_discrepancies(
        cvrs, sample_cvr, assertions["Contest A"][0]
    )

    assert discrepancies
    assert discrepancies[60000]["counted_as"] == -2
    assert discrepancies[60000]["weighted_error"] == Decimal(-2) / Decimal(20000)


def test_two_vote_overstatement_discrepancies(cvrs, assertions):
    sample_cvr = {
        0: {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {
                    "winner": 2,
                    "loser": 1,
                },  # One of the reported winner ballots was actually a loser ballot
            },
        }
    }

    contest = "Contest A"
    discrepancies = supersimple_raire.compute_discrepancies(
        cvrs, sample_cvr, assertions[contest][0]
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 2
    assert discrepancies[0]["weighted_error"] == Decimal(2) / Decimal(20000)


def test_race_not_in_cvr_discrepancy(cvrs, assertions):

    sample_cvr = {
        14000: {
            "times_sampled": 1,
            "cvr": {
                "Contest D": {
                    "winner": 0,
                    "loser": 1,
                },  # The audit board found a race not in the CVR
            },
        }
    }

    discrepancies = supersimple_raire.compute_discrepancies(
        cvrs, sample_cvr, assertions["Contest D"][0]
    )

    assert discrepancies
    assert discrepancies[14000]["counted_as"] == 1
    assert discrepancies[14000]["weighted_error"] == Decimal(1) / Decimal(2000)


def test_race_not_in_sample_discrepancy(cvrs, assertions):

    sample_cvr = {
        0: {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": 0, "loser": 0},
                "Contest B": {"winner": 1, "loser": 2},
                "Contest C": {"winner": 1, "loser": 2},
                "Contest E": {"winner": 1, "loser": 2},
            },
        }
    }

    discrepancies = supersimple_raire.compute_discrepancies(
        cvrs, sample_cvr, assertions["Contest D"][0]
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 1
    assert discrepancies[0]["weighted_error"] == Decimal(1) / Decimal(2000)


def test_ballot_not_found_discrepancy(cvrs, assertions):
    sample_cvr = {0: {"times_sampled": 1, "cvr": None}}

    discrepancies = supersimple_raire.compute_discrepancies(
        cvrs, sample_cvr, assertions["Contest D"][0]
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 2
    assert discrepancies[0]["weighted_error"] == Decimal(2) / Decimal(2000)


def test_ballot_not_in_cvr(cvrs, assertions):
    sample_cvr = {
        15000: {"times_sampled": 1, "cvr": {"Contest D": {"winner": 1, "loser": 2}}}
    }

    discrepancies = supersimple_raire.compute_discrepancies(
        cvrs, sample_cvr, assertions["Contest D"][0]
    )

    assert discrepancies
    assert discrepancies[15000]["counted_as"] == -1
    assert discrepancies[15000]["weighted_error"] == Decimal(-1) / Decimal(2000)


def test_ballot_not_in_cvr_and_not_found(assertions):
    cvrs = {}
    sample_cvr = {0: {"times_sampled": 1, "cvr": None}}

    discrepancies = supersimple_raire.compute_discrepancies(
        cvrs, sample_cvr, assertions["Contest D"][0]
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 2
    assert discrepancies[0]["weighted_error"] == Decimal("inf")


def test_fptp(contests, cvrs, assertions):
    # RAIRE should give us identical results to a first-past-the-post election if
    # there are only two candidates

    for contest in contests:

        computed_assertions = compute_raire_assertions(
            contests[contest], cvrs, asn_func, 0
        )

        if contest == "Contest F":
            assert not computed_assertions
        else:
            expected_assertions = assertions[contest]
            assert computed_assertions == expected_assertions, f"Failed for {contest}"

        sample_cvr = {}
        sample_size = supersimple_raire.get_sample_sizes(
            RISK_LIMIT, contests[contest], cvrs, None, assertions[contest]
        )

        # No discrepancies
        for i in range(sample_size):
            sample_cvr[i] = {
                "times_sampled": 1,
                "cvr": {
                    "Contest A": {"winner": 1, "loser": 2},
                    "Contest B": {"winner": 1, "loser": 2},
                    "Contest C": {"winner": 1, "loser": 2},
                    "Contest D": {"winner": 1, "loser": 2},
                    "Contest E": {"winner": 1, "loser": 2},
                },
            }

        p_value, finished = supersimple_raire.compute_risk(
            RISK_LIMIT, contests[contest], cvrs, sample_cvr, computed_assertions
        )

        expected_p = expected_p_values["no_discrepancies"][contest]
        diff = abs(p_value - expected_p)

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )
        if contest != "Contest F":
            assert finished, f"Audit of {contest} should have finished but didn't"

        to_sample = {
            assertion: {
                "sample_size": sample_size,
                "1-under": 0,
                "1-over": 0,
                "2-under": 0,
                "2-over": 0,
            }
            for assertion in assertions[contest]
        }

        next_sample_size = supersimple_raire.get_sample_sizes(
            RISK_LIMIT, contests[contest], cvrs, to_sample, assertions[contest]
        )
        assert next_sample_size == 0

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

        p_value, finished = supersimple_raire.compute_risk(
            RISK_LIMIT, contests[contest], cvrs, sample_cvr, computed_assertions
        )

        expected_p = expected_p_values["one_vote_over"][contest]
        diff = abs(p_value - expected_p)

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )
        if contest in ["Contest E"]:
            assert finished, "Audit should have finished but didn't"
        elif contest != "Contest F":
            assert (
                not finished
            ), f"Audit of {contest} shouldn't have finished but did {p_value}!"

        to_sample = {
            assertion: {
                "sample_size": sample_size,
                "1-under": 0,
                "1-over": 1,
                "2-under": 0,
                "2-over": 0,
            }
            for assertion in assertions[contest]
        }

        next_sample_size = supersimple_raire.get_sample_sizes(
            RISK_LIMIT, contests[contest], cvrs, to_sample, assertions[contest]
        )
        assert (
            next_sample_size == o1_stopping_size[contest] - sample_size
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

        p_value, finished = supersimple_raire.compute_risk(
            RISK_LIMIT, contests[contest], cvrs, sample_cvr, computed_assertions
        )
        expected_p = expected_p_values["two_vote_over"][contest]
        diff = abs(p_value - expected_p)

        assert (
            diff < 0.001
        ), "Incorrect p-value. Expected {}, got {} in contest {}".format(
            expected_p, p_value, contest
        )

        if contest != "Contest F":
            assert not finished, "Audit shouldn't have finished but did!"

        to_sample = {
            assertion: {
                "sample_size": sample_size,
                "1-under": 0,
                "1-over": 0,
                "2-under": 0,
                "2-over": 1,
            }
            for assertion in assertions[contest]
        }

        next_sample_size = supersimple_raire.get_sample_sizes(
            RISK_LIMIT, contests[contest], cvrs, to_sample, assertions[contest]
        )
        assert (
            next_sample_size == o2_stopping_size[contest] - sample_size
        ), "Number of ballots left to sample is not correct in contest {}!".format(
            contest
        )


def parse_shangrla_sample(input_file: str) -> SAMPLECVRS:
    cvrs = {}
    with open(input_file, "r", encoding="utf8") as datafile:
        sample_data = json.load(datafile)
        ballots = sample_data["ballots"]

        for ballot in ballots:
            if ballot["id"] not in cvrs:
                # For typechevker...
                cvrs[ballot["id"]] = {
                    "cvr": ballot["votes"],
                    "times_sampled": 1,
                }
            else:
                cvrs[ballot["id"]]["times_sampled"] += 1

    return cast(SAMPLECVRS, cvrs)


def test_get_sample_sizes_fptp(contests, cvrs, assertions):
    for contest in contests:
        computed = supersimple_raire.get_sample_sizes(
            RISK_LIMIT, contests[contest], cvrs, None, assertions[contest]
        )
        expected = true_sample_sizes[contest]  # From Stark's tool

        assert (
            computed == expected
        ), "Sample size computation incorrect: got {}, expected {} in contest {}".format(
            computed, expected, contest
        )


def test_normalize_cvr():

    expected: CVR = {"contest": {"Alice": 1, "Bob": 2, "Charlie": 0}}

    # Idempotent for correct cvrs
    assert expected == supersimple_raire.normalize_cvr(
        {"contest": {"Alice": 1, "Bob": 2, "Charlie": 0}}
    )

    # Correctly fixes gaps
    assert expected == supersimple_raire.normalize_cvr(
        {"contest": {"Alice": 2, "Bob": 4, "Charlie": 0}}
    )


def test_discrepancy_validation():

    # No discrepancy
    reported: CVR = {"contest": {"Alice": 1, "Bob": 2, "Charlie": 0}}
    audited: CVR = {"contest": {"Alice": 1, "Bob": 2, "Charlie": 0}}

    assertion = NEBAssertion("contest", "Alice", "Bob")
    margin = Decimal(1000)

    assert not supersimple_raire.discrepancy(reported, audited, assertion, margin)

    # This should still be equivalent to reported
    audited = {"contest": {"Alice": 1, "Bob": 2, "Charlie": 3}}

    assert not supersimple_raire.discrepancy(reported, audited, assertion, margin)

    # This should also still be equivalent to reported
    audited = {"contest": {"Alice": 1, "Bob": 0, "Charlie": 0}}

    assert not supersimple_raire.discrepancy(reported, audited, assertion, margin)

    # So should this, since assertion only deals with Alice and Bob, and this
    # overvote should make this CVR equiavlent to the prior auditd CVR.
    audited = {"contest": {"Alice": 1, "Bob": 2, "Charlie": 2}}

    assert not supersimple_raire.discrepancy(reported, audited, assertion, margin)

    # This CVR is equivalent to a first-place vote for Bob, as Alice and Charlie are
    # over-voted. Thus, it's a one-vote overstatement
    audited = {"contest": {"Alice": 1, "Bob": 2, "Charlie": 1}}

    expected = {"counted_as": 1, "weighted_error": 1 / margin}

    assert (
        supersimple_raire.discrepancy(reported, audited, assertion, margin) == expected
    )

    # Test decrementing
    audited = {"contest": {"Alice": 2, "Bob": 3, "Charlie": 4}}

    assert not supersimple_raire.discrepancy(reported, audited, assertion, margin)

    # Test skipping
    audited = {"contest": {"Alice": 1, "Bob": 3, "Charlie": 4}}
    assertion = NEBAssertion("contest", "Bob", "Charlie")

    assert not supersimple_raire.discrepancy(reported, audited, assertion, margin)


def test_simple_irv_election():
    contest = Contest(
        "synth",
        {
            "Alice": 600,
            "Bob": 300,
            "Charlie": 100,
            "ballots": 1000,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )

    cvrs = {}

    for i in range(1000):
        if i < 300:
            cvrs[i] = {"synth": {"Alice": 1, "Bob": 2, "Charlie": 3}}
        elif 300 <= i < 600:
            cvrs[i] = {"synth": {"Alice": 1, "Bob": 3, "Charlie": 2}}
        elif 600 <= i < 800:
            cvrs[i] = {"synth": {"Alice": 3, "Bob": 1, "Charlie": 2}}
        elif 800 <= i < 900:
            cvrs[i] = {"synth": {"Alice": 2, "Bob": 1, "Charlie": 3}}
        elif 900 <= i < 975:
            cvrs[i] = {"synth": {"Alice": 2, "Bob": 3, "Charlie": 1}}
        else:
            cvrs[i] = {"synth": {"Alice": 3, "Bob": 2, "Charlie": 1}}

    # check that we get the right assertions
    expected_assertions = []
    expected_assertions.append(NEBAssertion(contest.name, "Alice", "Bob"))
    expected_assertions.append(NEBAssertion(contest.name, "Alice", "Charlie"))

    computed_assertions = compute_raire_assertions(contest, cvrs, asn_func, 0)

    assert computed_assertions == expected_assertions

    # Check sample sizes
    expected_sample_size = 25
    assert (
        supersimple_raire.get_sample_sizes(5, contest, cvrs, {}, computed_assertions)
        == expected_sample_size
    )

    # Now test with no discrepancies
    expected_p = 0.038205645
    sample_cvrs = {}
    for i in range(23):
        sample_cvrs[i] = {"cvr": cvrs[i], "times_sampled": 1}

    for assertion in computed_assertions:
        discrepancies = supersimple_raire.compute_discrepancies(
            cvrs, sample_cvrs, assertion
        )
        assert not discrepancies

    p_value, finished = supersimple_raire.compute_risk(
        5, contest, cvrs, sample_cvrs, computed_assertions
    )

    diff = abs(p_value - expected_p)

    assert diff < 10**-4, f"Got unexpected p-value {p_value}, expected {expected_p}"
    assert finished

    # Test with one two-vote discrepancy
    sample_cvrs[0] = {
        "cvr": {"synth": {"Alice": 2, "Bob": 1, "Charlie": 3}},
        "times_sampled": 1,
    }

    expected_p = 1.0
    for assertion in computed_assertions:
        discrepancies = supersimple_raire.compute_discrepancies(
            cvrs, sample_cvrs, assertion
        )
        assert len(discrepancies) == 1
        if assertion == expected_assertions[0]:
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=2, weighted_error=Decimal(2) / Decimal(275)
            )
        elif assertion == expected_assertions[1]:
            # This is counted as a one-vote overstatement because of the way NEBAssertions count votes for the loser
            # Note that the margin between Alice and Charlie is (600 firs place
            # for A + 300 second place)  - (100 first place for C + 500 second place)
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=1, weighted_error=Decimal(1) / Decimal(300)
            )

    p_value, finished = supersimple_raire.compute_risk(
        5, contest, cvrs, sample_cvrs, computed_assertions
    )

    diff = abs(p_value - expected_p)

    assert diff < 10**-4, f"Got unexpected p-value {p_value}, expected {expected_p}"
    assert not finished

    # Test with a one-vote discrepancy
    sample_cvrs[0] = {
        "cvr": {"synth": {"Alice": 0, "Bob": 0, "Charlie": 0}},
        "times_sampled": 1,
    }

    expected_p = 0.073643586
    for assertion in computed_assertions:
        discrepancies = supersimple_raire.compute_discrepancies(
            cvrs, sample_cvrs, assertion
        )
        assert len(discrepancies) == 1
        if assertion == expected_assertions[0]:
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=1, weighted_error=Decimal(1) / Decimal(275)
            )
        elif assertion == expected_assertions[1]:
            # This is counted as a one-vote overstatement because of the way NEBAssertions count votes for the loser
            # Note that the margin between Alice and Charlie is (600 firs place
            # for A + 300 second place)  - (100 first place for C + 500 second place)
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=1, weighted_error=Decimal(1) / Decimal(300)
            )

    p_value, finished = supersimple_raire.compute_risk(
        5, contest, cvrs, sample_cvrs, computed_assertions
    )

    diff = abs(p_value - expected_p)

    assert diff < 10**-4, f"Got unexpected p-value {p_value}, expected {expected_p}"
    assert not finished


@pytest.mark.skip(reason="Takes too long to run, doesn't impact coverage")
def test_raire_example_1():
    # Election taken from the RAIRE paper (Example 1). "Dara" wins.
    contest = Contest(
        "synth",
        {
            "Alice": 26000,
            "Bob": 10000,
            "Charlie": 9000,
            "Dara": 15000,
            "ballots": 60000,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )

    contest.winners = ["Dara"]

    cvrs = {}

    for i in range(60000):
        if i < 4000:
            cvrs[i] = {"synth": {"Alice": 0, "Bob": 1, "Charlie": 2, "Dara": 0}}
        elif 4000 <= i < 24000:
            cvrs[i] = {"synth": {"Alice": 1, "Bob": 0, "Charlie": 0, "Dara": 0}}
        elif 24000 <= i < 33000:
            cvrs[i] = {"synth": {"Alice": 0, "Bob": 0, "Charlie": 1, "Dara": 2}}
        elif 33000 <= i < 39000:
            cvrs[i] = {"synth": {"Alice": 0, "Bob": 1, "Charlie": 2, "Dara": 3}}
        elif 39000 <= i < 54000:
            cvrs[i] = {"synth": {"Alice": 2, "Bob": 3, "Charlie": 0, "Dara": 1}}
        else:
            cvrs[i] = {"synth": {"Alice": 1, "Bob": 0, "Charlie": 2, "Dara": 0}}

    # check that we get the right assertions
    expected_assertions = []
    expected_assertions.append(
        NENAssertion(contest.name, "Dara", "Alice", set(["Bob", "Charlie"]))
    )
    expected_assertions.append(NEBAssertion(contest.name, "Dara", "Bob"))
    expected_assertions.append(NEBAssertion(contest.name, "Alice", "Charlie"))
    expected_assertions.append(NEBAssertion(contest.name, "Alice", "Bob"))

    computed_assertions = compute_raire_assertions(contest, cvrs, asn_func, 0)

    assert computed_assertions == expected_assertions

    # Check sample sizes (computed with Stark's tool for the eventual
    # two-candidate contest between Alice and Dara)
    expected_sample_size = 102
    assert (
        supersimple_raire.get_sample_sizes(5, contest, cvrs, {}, computed_assertions)
        == expected_sample_size
    )

    # Now test with no discrepancies
    expected_p = 0.035941685
    sample_cvrs = {}
    for i in range(expected_sample_size):
        sample_cvrs[i] = {"cvr": cvrs[i], "times_sampled": 1}

    for assertion in computed_assertions:
        discrepancies = supersimple_raire.compute_discrepancies(
            cvrs, sample_cvrs, assertion
        )
        assert not discrepancies

    p_value, finished = supersimple_raire.compute_risk(
        5, contest, cvrs, sample_cvrs, computed_assertions
    )

    diff = abs(p_value - expected_p)

    assert diff < 10**-4, f"Got unexpected p-value {p_value}, expected {expected_p}"
    assert finished

    # Test with one two-vote discrepancy
    sample_cvrs[39000] = {
        "cvr": {"synth": {"Alice": 1, "Bob": 3, "Charlie": 0, "Dara": 2}},
        "times_sampled": 1,
    }

    # Note that we actually added a ballot for our discrepancy, so this p-value
    # is lower than the by-hand 0.956343344 as the sample now contains 103 ballots.
    expected_p = 0.925663294
    for assertion in computed_assertions:
        discrepancies = supersimple_raire.compute_discrepancies(
            cvrs, sample_cvrs, assertion
        )
        assert len(discrepancies) == 1
        if assertion == expected_assertions[0]:
            assert discrepancies[39000] == supersimple.Discrepancy(
                counted_as=2, weighted_error=Decimal(2) / Decimal(4000)
            )
        elif assertion == expected_assertions[1]:
            assert discrepancies[39000] == supersimple.Discrepancy(
                counted_as=1, weighted_error=Decimal(1) / Decimal(5000)
            )
        elif assertion == expected_assertions[2]:
            assert discrepancies[39000] == supersimple.Discrepancy(
                counted_as=-1,
                weighted_error=Decimal(-1)
                / Decimal(7000),  # 26000 for Alice - 19000 for Charlie
            )
        elif assertion == expected_assertions[3]:
            assert discrepancies[39000] == supersimple.Discrepancy(
                counted_as=-1,
                weighted_error=Decimal(-1)
                / Decimal(16000),  # 26k for Alice, 10k for Bob
            )

    p_value, finished = supersimple_raire.compute_risk(
        5, contest, cvrs, sample_cvrs, computed_assertions
    )

    diff = abs(p_value - expected_p)

    assert diff < 10**-4, f"Got unexpected p-value {p_value}, expected {expected_p}"
    assert not finished


@pytest.mark.skip(reason="Takes too long to run, doesn't impact coverage")
def test_raire_example_5():
    # Election taken from the RAIRE paper (Example 1). "Dara" wins.
    contest = Contest(
        "synth",
        {
            "Alice": 10000,
            "Bob": 6000,
            "Charlie": 5000,
            "Dara": 500,
            "Edmund": 499,
            "ballots": 21999,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )

    contest.winners = ["Alice"]

    cvrs = {}

    for i in range(21999):
        if i < 10000:
            cvrs[i] = {
                "synth": {"Alice": 1, "Bob": 0, "Charlie": 0, "Dara": 0, "Edmund": 0}
            }
        elif 10000 <= i < 16000:
            cvrs[i] = {
                "synth": {"Alice": 0, "Bob": 1, "Charlie": 0, "Dara": 0, "Edmund": 0}
            }
        elif 16000 <= i < 19000:
            cvrs[i] = {
                "synth": {"Alice": 0, "Bob": 2, "Charlie": 1, "Dara": 0, "Edmund": 0}
            }
        elif 19000 <= i < 21000:
            cvrs[i] = {
                "synth": {"Alice": 2, "Bob": 0, "Charlie": 1, "Dara": 0, "Edmund": 0}
            }
        elif 21000 <= i < 21500:
            cvrs[i] = {
                "synth": {"Alice": 0, "Bob": 0, "Charlie": 0, "Dara": 1, "Edmund": 0}
            }
        else:
            cvrs[i] = {
                "synth": {"Alice": 0, "Bob": 0, "Charlie": 0, "Dara": 0, "Edmund": 1}
            }

    # check that we get the right assertions
    expected_assertions = []
    expected_assertions.append(
        NENAssertion(contest.name, "Alice", "Bob", set(["Dara", "Charlie", "Edmund"]))
    )
    expected_assertions.append(NEBAssertion(contest.name, "Alice", "Charlie"))
    expected_assertions.append(NEBAssertion(contest.name, "Alice", "Dara"))
    expected_assertions.append(NEBAssertion(contest.name, "Alice", "Edmund"))

    computed_assertions = compute_raire_assertions(contest, cvrs, asn_func, 0)

    assert computed_assertions == expected_assertions

    # Check sample sizes (computed with Stark's tool for the eventual
    # two-candidate contest between Alice and Bob)
    expected_sample_size = 50
    assert (
        supersimple_raire.get_sample_sizes(5, contest, cvrs, {}, computed_assertions)
        == expected_sample_size
    )

    # Now test with no discrepancies
    expected_p = 0.033583176
    sample_cvrs = {}
    for i in range(expected_sample_size):
        sample_cvrs[i] = {"cvr": cvrs[i], "times_sampled": 1}

    for assertion in computed_assertions:
        discrepancies = supersimple_raire.compute_discrepancies(
            cvrs, sample_cvrs, assertion
        )
        assert not discrepancies

    p_value, finished = supersimple_raire.compute_risk(
        5, contest, cvrs, sample_cvrs, computed_assertions
    )

    diff = abs(p_value - expected_p)

    assert diff < 10**-4, f"Got unexpected p-value {p_value}, expected {expected_p}"
    assert finished

    # Test with one two-vote discrepancy
    sample_cvrs[0] = {
        "cvr": {"synth": {"Alice": 0, "Bob": 1, "Charlie": 0, "Dara": 0, "Edmund": 0}},
        "times_sampled": 1,
    }

    expected_p = 0.893587672
    for assertion in computed_assertions:
        discrepancies = supersimple_raire.compute_discrepancies(
            cvrs, sample_cvrs, assertion
        )
        assert len(discrepancies) == 1
        if assertion == expected_assertions[0]:
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=2, weighted_error=Decimal(2) / Decimal(3000)
            )
        elif assertion == expected_assertions[1]:
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=1, weighted_error=Decimal(1) / Decimal(5000)
            )
        elif assertion == expected_assertions[2]:
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=1, weighted_error=Decimal(1) / Decimal(9500)
            )
        elif assertion == expected_assertions[3]:
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=1,
                weighted_error=Decimal(1) / Decimal(9501),  # 26k for Alice, 10k for Bob
            )

    p_value, finished = supersimple_raire.compute_risk(
        5, contest, cvrs, sample_cvrs, computed_assertions
    )

    diff = abs(p_value - expected_p)

    assert diff < 10**-4, f"Got unexpected p-value {p_value}, expected {expected_p}"
    assert not finished


@pytest.mark.skip(reason="Takes too long to run, doesn't impact coverage")
def test_raire_example_12():
    # Election taken from the RAIRE paper (Example 12). "Alice" wins.
    contest = Contest(
        "synth",
        {
            "Alice": 10000,
            "Bob": 6500,
            "Charlie": 5500,
            "Dara": 5000,
            "ballots": 27000,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )

    cvrs = {}

    for i in range(27000):
        if i < 5000:
            cvrs[i] = {"synth": {"Alice": 1, "Bob": 2, "Charlie": 3, "Dara": 0}}
        elif 5000 <= i < 10000:
            cvrs[i] = {"synth": {"Alice": 1, "Bob": 3, "Charlie": 2, "Dara": 0}}
        elif 10000 <= i < 15000:
            cvrs[i] = {"synth": {"Alice": 3, "Bob": 1, "Charlie": 2, "Dara": 0}}
        elif 15000 <= i < 16500:
            cvrs[i] = {"synth": {"Alice": 2, "Bob": 1, "Charlie": 3, "Dara": 0}}
        elif 16500 <= i < 21500:
            cvrs[i] = {"synth": {"Alice": 3, "Bob": 2, "Charlie": 1, "Dara": 0}}
        elif 21500 <= i < 22000:
            cvrs[i] = {"synth": {"Alice": 2, "Bob": 3, "Charlie": 1, "Dara": 0}}
        else:
            cvrs[i] = {"synth": {"Alice": 2, "Bob": 0, "Charlie": 0, "Dara": 1}}

    # check that we get the right assertions
    expected_assertions = []
    expected_assertions.append(
        NENAssertion(contest.name, "Alice", "Bob", set(["Dara", "Charlie"]))
    )
    expected_assertions.append(NEBAssertion(contest.name, "Alice", "Dara"))
    expected_assertions.append(
        NENAssertion(contest.name, "Alice", "Charlie", set(["Bob", "Dara"]))
    )
    expected_assertions.append(
        NENAssertion(contest.name, "Alice", "Charlie", set(["Dara"]))
    )

    computed_assertions = compute_raire_assertions(contest, cvrs, asn_func, 0)

    assert computed_assertions == expected_assertions

    # Check sample sizes (computed with Stark's tool for the eventual
    # two-candidate contest between Alice and Bob)
    expected_sample_size = 46
    assert (
        supersimple_raire.get_sample_sizes(5, contest, cvrs, {}, computed_assertions)
        == expected_sample_size
    )

    # Now test with no discrepancies
    expected_p = 0.033302856
    sample_cvrs = {}
    for i in range(expected_sample_size):
        sample_cvrs[i] = {"cvr": cvrs[i], "times_sampled": 1}

    for assertion in computed_assertions:
        discrepancies = supersimple_raire.compute_discrepancies(
            cvrs, sample_cvrs, assertion
        )
        assert not discrepancies

    p_value, finished = supersimple_raire.compute_risk(
        5, contest, cvrs, sample_cvrs, computed_assertions
    )

    diff = abs(p_value - expected_p)

    assert diff < 10**-4, f"Got unexpected p-value {p_value}, expected {expected_p}"
    assert finished

    # Test with one two-vote discrepancy
    sample_cvrs[0] = {
        "cvr": {"synth": {"Alice": 0, "Bob": 1, "Charlie": 0, "Dara": 0, "Edmund": 0}},
        "times_sampled": 1,
    }

    expected_p = 0.886128865
    for assertion in computed_assertions:
        discrepancies = supersimple_raire.compute_discrepancies(
            cvrs, sample_cvrs, assertion
        )
        assert len(discrepancies) == 1
        if assertion == expected_assertions[0]:
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=2, weighted_error=Decimal(2) / Decimal(4000)
            )
        elif assertion == expected_assertions[1]:
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=1, weighted_error=Decimal(1) / Decimal(5000)
            )
        elif assertion == expected_assertions[2]:
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=1, weighted_error=Decimal(1) / Decimal(6000)
            )
        elif assertion == expected_assertions[3]:
            assert discrepancies[0] == supersimple.Discrepancy(
                counted_as=1,
                weighted_error=Decimal(1) / Decimal(9500),
            )

    p_value, finished = supersimple_raire.compute_risk(
        5, contest, cvrs, sample_cvrs, computed_assertions
    )

    diff = abs(p_value - expected_p)

    assert diff < 10**-4, f"Got unexpected p-value {p_value}, expected {expected_p}"
    assert not finished


def test_raire_example_broken():
    # Election taken from the RAIRE paper (Example 12). "Alice" wins.
    contest = Contest(
        "synth",
        {
            "Alice": 10000,
            "Bob": 6500,
            "Charlie": 5500,
            "Dara": 5000,
            "ballots": 27000,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )

    cvrs = {}

    for i in range(27000):
        if i < 5000:
            cvrs[i] = {"synth": {"Alice": 1, "Bob": 2, "Charlie": 3, "Dara": 0}}
        if 5000 <= i < 10000:
            cvrs[i] = {"synth": {"Alice": 1, "Bob": 3, "Charlie": 2, "Dara": 0}}
        elif 10000 <= i < 15000:
            cvrs[i] = {"synth": {"Alice": 3, "Bob": 1, "Charlie": 2, "Dara": 0}}
        elif 15000 <= i < 16500:
            cvrs[i] = {"synth": {"Alice": 2, "Bob": 1, "Charlie": 3, "Dara": 0}}
        elif 16500 <= i < 21500:
            cvrs[i] = {"synth": {"Alice": 3, "Bob": 2, "Charlie": 1, "Dara": 0}}
        elif 21500 <= i < 22000:
            cvrs[i] = {"synth": {"Alice": 2, "Bob": 3, "Charlie": 1, "Dara": 0}}
        else:
            cvrs[i] = {"synth": {"Alice": 2, "Bob": 0, "Charlie": 0, "Dara": 1}}

    # check that we get the right assertions
    assert not compute_raire_assertions(contest, cvrs, asn_func, 0)


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
        "Contest F": 0.0,  # Full recount
    },
    "one_vote_over": {
        "Contest A": 0.12534,
        "Contest B": 0.13441,
        "Contest C": 0.12992,
        "Contest D": 0.13585,
        "Contest E": 0.03758,
        "Contest F": 0.0,  # Full recount
    },
    "two_vote_over": {
        "Contest A": 1.0,
        "Contest B": 1.0,
        "Contest C": 1.0,
        "Contest D": 1.0,
        "Contest E": 0.51877,
        "Contest F": 0.0,  # Full recount
    },
}

o1_stopping_size = {
    "Contest A": 38,
    "Contest B": 76,
    "Contest C": 51,
    "Contest D": 57,
    "Contest E": 7,
    "Contest F": 15,  # nMin yields 16, but contest only has 15 total votes
}

o2_stopping_size = {
    "Contest A": 100000,
    "Contest B": 60000,
    "Contest C": 36000,
    "Contest D": 15000,
    "Contest E": 6,
    "Contest F": 15,
}

true_sample_sizes = {
    "Contest A": 27,
    "Contest B": 54,
    "Contest C": 36,
    "Contest D": 40,
    "Contest E": 6,
    "Contest F": 15,
    "Two-winner Contest": 27,
}

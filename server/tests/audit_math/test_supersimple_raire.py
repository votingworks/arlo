# pylint: disable=invalid-name
from decimal import Decimal
import pytest
import json
import numpy as np

from ...audit_math import supersimple
from ...audit_math.sampler_contest import Contest, SAMPLECVRS
from ...audit_math.raire import compute_raire_assertions

from .test_raire_utils import make_neb_assertion
from .test_raire import parse_raire_input
from ...audit_math import supersimple_raire

seed = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
ALPHA = Decimal(0.1)
RISK_LIMIT = 10

# Testing for now...
asn_func = lambda m: 1 / m if m > 0 else np.inf


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
        elif 30000 < i < 60000:
            cvr[i]["Contest B"] = {"winner": 2, "loser": 1}

        if i < 18000:
            cvr[i]["Contest C"] = {"winner": 1, "loser": 2}
        elif 18000 < i < 36000:
            cvr[i]["Contest C"] = {"winner": 2, "loser": 1}

        if i < 8000:
            cvr[i]["Contest D"] = {"winner": 1, "loser": 2}
        elif 8000 < i < 14000:
            cvr[i]["Contest D"] = {"winner": 2, "loser": 1}

        if i < 10000:
            cvr[i]["Contest E"] = {"winner": 1, "loser": 2}

        if i < 300:
            cvr[i]["Two-winner Contest"] = {"winner1": 0, "winner2": 1, "loser": 0}
        elif 300 < i < 900:
            cvr[i]["Two-winner Contest"] = {"winner1": 1, "winner2": 0, "loser": 0}
        elif i < 1000:
            cvr[i]["Two-winner Contest"] = {"winner1": 0, "winner2": 0, "loser": 1}

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
        if contest == "Two-winner Contest":
            assertions[contest] = [
                make_neb_assertion(
                    contests[contest], cvrs, asn_func, "winner2", "loser", []
                ),
                make_neb_assertion(
                    contests[contest], cvrs, asn_func, "winner1", "loser", []
                ),
            ]

        else:
            assertions[contest] = [
                make_neb_assertion(
                    contests[contest], cvrs, asn_func, "winner", "loser", []
                )
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
                "Two-winner Contest": {"winner1": 0, "winner2": 1, "loser": 0},
            },
        }
    }

    for contest in contests:
        for assertion in assertions[contest]:
            discrepancies = supersimple_raire.compute_discrepancies(
                contests[contest], cvrs, sample_cvr, assertion
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
                "Two-winner Contest": {"winner1": 0, "winner2": 1, "loser": 0},
            },
        }
    }

    for contest in contests:
        for assertion in assertions[contest]:
            discrepancies = supersimple_raire.compute_discrepancies(
                contests[contest], cvrs, sample_cvr, assertion
            )

            if contest == "Contest A":
                assert discrepancies[0]["counted_as"] == 1
                assert discrepancies[0]["weighted_error"] == Decimal(1) / Decimal(20000)
            else:
                assert not discrepancies


def test_negative_discrepancies(contests, cvrs, assertions):
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
        contests["Contest A"], cvrs, sample_cvr, assertions["Contest A"][0]
    )

    assert discrepancies
    assert discrepancies[60000]["counted_as"] == -2
    assert discrepancies[60000]["weighted_error"] == Decimal(-2) / Decimal(20000)


def test_two_vote_overstatement_discrepancies(contests, cvrs, assertions):
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
        contests[contest], cvrs, sample_cvr, assertions[contest][0]
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 2
    assert discrepancies[0]["weighted_error"] == Decimal(2) / Decimal(20000)


def test_race_not_in_cvr_discrepancy(contests, cvrs, assertions):

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

    discrepancies = supersimple_raire.compute_discrepancies(
        contests["Contest F"], cvrs, sample_cvr, assertions["Contest F"][0]
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 1
    assert discrepancies[0]["weighted_error"] == Decimal(1) / Decimal(6)


def test_race_not_in_sample_discrepancy(contests, cvrs, assertions):

    sample_cvr = {
        0: {
            "times_sampled": 1,
            "cvr": {
                "Contest A": {"winner": 0, "loser": 0},
                "Contest B": {"winner": 1, "loser": 2},
                "Contest C": {"winner": 1, "loser": 2},
                "Contest E": {"winner": 1, "loser": 2},
                "Two-winner Contest": {"winner1": 0, "winner2": 1, "loser": 0},
            },
        }
    }

    discrepancies = supersimple_raire.compute_discrepancies(
        contests["Contest D"], cvrs, sample_cvr, assertions["Contest D"][0]
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 1
    assert discrepancies[0]["weighted_error"] == Decimal(1) / Decimal(2000)


def test_ballot_not_found_discrepancy(contests, cvrs, assertions):
    sample_cvr = {0: {"times_sampled": 1, "cvr": None}}

    discrepancies = supersimple_raire.compute_discrepancies(
        contests["Contest D"], cvrs, sample_cvr, assertions["Contest D"][0]
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 2
    assert discrepancies[0]["weighted_error"] == Decimal(2) / Decimal(2000)


def test_ballot_not_in_cvr(contests, assertions):
    cvrs = {}
    sample_cvr = {
        0: {"times_sampled": 1, "cvr": {"Contest D": {"winner": 1, "loser": 2}}}
    }

    discrepancies = supersimple_raire.compute_discrepancies(
        contests["Contest D"], cvrs, sample_cvr, assertions["Contest D"][0]
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 2
    assert discrepancies[0]["weighted_error"] == Decimal(2) / Decimal(2000)


def test_ballot_not_in_cvr_and_not_found(contests, assertions):
    cvrs = {}
    sample_cvr = {0: {"times_sampled": 1, "cvr": None}}

    discrepancies = supersimple_raire.compute_discrepancies(
        contests["Contest D"], cvrs, sample_cvr, assertions["Contest D"][0]
    )

    assert discrepancies
    assert discrepancies[0]["counted_as"] == 2
    assert discrepancies[0]["weighted_error"] == Decimal(2) / Decimal(2000)


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
        sample_size = supersimple.get_sample_sizes(RISK_LIMIT, contests[contest], None)

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
                    "Two-winner Contest": {"winner1": 0, "winner2": 1, "loser": 0},
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
            "sample_size": sample_size,
            "1-under": 0,
            "1-over": 0,
            "2-under": 0,
            "2-over": 0,
        }

        next_sample_size = supersimple.get_sample_sizes(
            RISK_LIMIT, contests[contest], to_sample
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
                "Two-winner Contest": {"winner1": 0, "winner2": 0, "loser": 0},
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
        if contest in ["Contest E", "Two-winner Contest"]:
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
                "Two-winner Contest": {"winner1": 0, "winner2": 0, "loser": 1},
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
            next_sample_size == o2_stopping_size[contest] - sample_size
        ), "Number of ballots left to sample is not correct in contest {}!".format(
            contest
        )

def parse_shangrla_sample(input_file: str) -> SAMPLECVRS:
    cvrs = {}
    with open(input_file, 'r') as datafile:
        sample_data = json.load(datafile)
        ballots = sample_data['ballots']

        for ballot in ballots:
            cvrs[ballot["id"]] = {
                 "cvr": ballot["votes"],
                 "times_sampled": 1,
            }

    return cvrs



def test_sfda_2019():
    """
    This test case is based on data found in the SHANGRLA repository:
    https://github.com/pbstark/SHANGRLA/tree/main/Code/Data
    """
    expected_p = 0.13530010921921345

    contests, cvrs, winners = parse_raire_input('server/tests/audit_math/raire_data/sfda19/SFDA2019_PrelimReport12VBMJustDASheets.raire')

    contest = Contest('339', contests['339'])

    contest.winners = {"15": contest.candidates["15"]}

    sample_cvr = parse_shangrla_sample('server/tests/audit_math/raire_data/sfda19/mvr_prepilot_test.json')

    computed_assertions = compute_raire_assertions(
            contest, cvrs, asn_func, 0
    )


    p_value, finished = supersimple_raire.compute_risk(
        RISK_LIMIT, contest, cvrs, sample_cvr, computed_assertions
    )

    diff = abs(p_value - expected_p)

    assert diff < 10**-4, f"Got unexpected p-value {p_value}, expected {expected_p}"
    assert not finished





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
        "Contest F": 0.0,  # Full recount
        "Two-winner Contest": 0.06508,
    },
    "one_vote_over": {
        "Contest A": 0.12534,
        "Contest B": 0.13441,
        "Contest C": 0.12992,
        "Contest D": 0.13585,
        "Contest E": 0.03758,
        "Contest F": 0.0,  # Full recount
        "Two-winner Contest": 0.08059,
    },
    "two_vote_over": {
        "Contest A": 1.0,
        "Contest B": 1.0,
        "Contest C": 1.0,
        "Contest D": 1.0,
        "Contest E": 0.51877,
        "Contest F": 0.0,  # Full recount
        "Two-winner Contest": 0.10581,
    },
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
    "Contest E": 6,
    "Contest F": 15,
    "Two-winner Contest": 1000,
}

# pylint: disable=invalid-name
from decimal import Decimal
import math
import pytest

from ...audit_math import bravo
from ...audit_math.sampler_contest import Contest

SEED = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
RISK_LIMIT = 10
ALPHA = Decimal(0.1)


@pytest.fixture
def contests():
    contests = {}

    for contest in bravo_contests:
        contests[contest] = Contest(contest, bravo_contests[contest])

    return contests


def test_expected_sample_sizes(contests):
    # Test expected sample sizes computation

    true_asns = {
        "test1": 119,
        "test2": 22,
        "test3": -1,
        "test4": -1,
        "test5": 1000,
        "test6": 238,
        "test7": 101,
        "test8": 34,
        "test9": -1,
        "test10": 48,
        "test11": -1,
        "test12": 119,
    }

    for contest in true_asns:
        cumulative_sample = {}
        for candidate in contests[contest].candidates:
            cumulative_sample[candidate] = 0
        computed = bravo.get_expected_sample_sizes(
            ALPHA, contests[contest], cumulative_sample
        )
        expected = true_asns[contest]

        assert (
            expected == computed
        ), "get_expected_sample_sizes failed in {}: got {}, expected {}".format(
            contest, computed, expected
        )


def test_expected_sample_sizes_second_round(contests):
    # Test expected sample sizes computation

    true_asns = {
        "test1": -12,
        "test2": 42,
        "test3": -1,
        "test4": -1,
        "test5": 1000,
        "test6": -2,
        "test7": -28,
        "test8": 14,
        "test9": -1,
        "test10": -52,
        "test11": -1,
    }

    for contest in true_asns:
        expected = true_asns[contest]
        computed = bravo.get_expected_sample_sizes(
            ALPHA, contests[contest], round1_sample_results[contest]["round1"]
        )

        assert (
            expected == computed
        ), "get_expected_sample_sizes failed in {}: got {}, expected {}".format(
            contest, computed, expected
        )


def test_bravo_sample_sizes():
    # Test bravo sample simulator
    # Test without sample
    expected_size1 = 1599
    r0_sample_win = 0
    r0_sample_rup = 0

    computed_size1 = math.ceil(
        bravo.bravo_sample_sizes(
            alpha=ALPHA,
            p_w=Decimal(0.4),
            p_r=Decimal(0.32),
            sample_w=r0_sample_win,
            sample_r=r0_sample_rup,
            p_completion=0.9,
        )
    )
    delta = expected_size1 - computed_size1

    assert delta == 0, "bravo_sample_sizes failed: got {}, expected {}".format(
        computed_size1, expected_size1
    )

    expected_size1 = 6067

    computed_size1 = math.ceil(
        bravo.bravo_sample_sizes(
            alpha=ALPHA,
            p_w=Decimal(0.36),
            p_r=Decimal(0.32),
            sample_w=r0_sample_win,
            sample_r=r0_sample_rup,
            p_completion=0.9,
        )
    )
    delta = expected_size1 - computed_size1

    assert delta == 0, "bravo_sample_sizes failed: got {}, expected {}".format(
        computed_size1, expected_size1
    )

    expected_size1 = 2476

    computed_size1 = math.ceil(
        bravo.bravo_sample_sizes(
            alpha=ALPHA,
            p_w=Decimal(0.36),
            p_r=Decimal(0.32),
            sample_w=r0_sample_win,
            sample_r=r0_sample_rup,
            p_completion=0.6,
        )
    )
    delta = expected_size1 - computed_size1

    assert delta == 0, "bravo_sample_sizes failed: got {}, expected {}".format(
        computed_size1, expected_size1
    )

    expected_size1 = 5657

    computed_size1 = math.ceil(
        bravo.bravo_sample_sizes(
            alpha=ALPHA,
            p_w=Decimal(0.52),
            p_r=Decimal(0.47),
            sample_w=r0_sample_win,
            sample_r=r0_sample_rup,
            p_completion=0.9,
        )
    )
    delta = expected_size1 - computed_size1

    assert delta == 0, "bravo_sample_sizes failed: got {}, expected {}".format(
        computed_size1, expected_size1
    )


def test_bravo_sample_sizes_round1_finish():
    # Guarantee that the audit should have finished
    r0_sample_win = 10000
    r0_sample_rup = 0
    expected_size1 = 0

    computed_size1 = math.ceil(
        bravo.bravo_sample_sizes(
            ALPHA,
            p_w=Decimal(0.52),
            p_r=Decimal(0.47),
            sample_w=r0_sample_win,
            sample_r=r0_sample_rup,
            p_completion=0.9,
        )
    )
    delta = expected_size1 - computed_size1

    assert delta == 0, "bravo_sample_sizes failed: got {}, expected {}".format(
        computed_size1, expected_size1
    )


def test_bravo_sample_sizes_round1_incomplete():
    expected_size1 = 2636
    r0_sample_win = 2923
    r0_sample_rup = 2735

    computed_size1 = math.ceil(
        bravo.bravo_sample_sizes(
            ALPHA,
            p_w=Decimal(0.52),
            p_r=Decimal(0.47),
            sample_w=r0_sample_win,
            sample_r=r0_sample_rup,
            p_completion=0.9,
        )
    )
    delta = expected_size1 - computed_size1

    assert delta == 0, "bravo_sample_sizes failed: got {}, expected {}".format(
        computed_size1, expected_size1
    )


def test_get_sample_size(contests):

    for contest in contests:
        computed = bravo.get_sample_size(
            RISK_LIMIT, contests[contest], round0_sample_results[contest]
        )

        expected = true_sample_sizes[contest]

        assert (
            computed.keys() == expected.keys()
        ), "{} get_sample_sizes returning the wrong keys! got {}, expected {}".format(
            contest, computed.keys(), expected.keys()
        )

        assert (
            computed["asn"]["size"] == expected["asn"]["size"]
        ), "{} get_sample_sizes returning the wrong ASN! got {}, expected {}".format(
            contest, computed["asn"]["size"], expected["asn"]["size"]
        )

        if expected["asn"]["prob"]:
            assert (
                round(computed["asn"]["prob"], 2) == expected["asn"]["prob"]
            ), "{} get_sample_sizes returning the wrong ASN probs! got {}, expected {}".format(
                contest, round(computed["asn"]["prob"], 2), expected["asn"]["prob"]
            )

        else:
            assert not computed["asn"][
                "prob"
            ], "Returned ASN probability when there shouldn't be one!"

        for item in computed:
            assert (
                computed[item]["type"] == expected[item]["type"]
                and computed[item]["size"] == expected[item]["size"]
                and (
                    round(computed[item]["prob"], 2) == expected[item]["prob"]
                    if expected[item]["prob"]
                    else not computed[item]["prob"]
                )
            ), "get_sample_size failed! got {}, expected {}".format(
                computed[item], expected[item]
            )


def test_bravo_expected_prob():
    # Test bravo sample simulator
    # Test without sample
    expected_prob1 = 0.52
    r0_sample_win = 0
    r0_sample_rup = 0

    computed_prob1 = round(
        bravo.expected_prob(
            ALPHA,
            p_w=Decimal(0.6),
            p_r=Decimal(0.4),
            sample_w=r0_sample_win,
            sample_r=r0_sample_rup,
            asn=119,
        ),
        2,
    )
    delta = expected_prob1 - computed_prob1

    assert delta == 0, "bravo_simulator failed: got {}, expected {}".format(
        computed_prob1, expected_prob1
    )


def test_compute_risk(contests):
    # Test computing sample
    expected_Ts = {
        "test1": {("cand1", "cand2"): 0.07},
        "test2": {("cand1", "cand2"): 10.38, ("cand1", "cand3"): 0,},
        "test3": {("cand1", ""): 1},
        "test4": {("cand1", ""): 0},
        "test5": {("cand1", "cand2"): 0},
        "test6": {("cand1", "cand2"): 0.08, ("cand1", "cand3"): 0.08,},
        "test7": {("cand1", "cand3"): 0.01, ("cand2", "cand3"): 0.04,},
        "test8": {("cand1", "cand3"): 0.0, ("cand2", "cand3"): 0.22,},
        "test9": {("cand1", ""): 1, ("cand2", ""): 1,},
        "test10": {("cand1", "cand3"): 0, ("cand2", "cand3"): 0.01,},
        "test11": {("cand1", "cand2"): 1},
        "test12": {("cand1", "cand2"): 0.07, ("cand1", "cand3"): 0,},
        "test_small_third_candidate": {
            ("cand1", "cand2"): 0.000561,
            ("cand1", "cand3"): 0,
        },
        "test_ga_presidential": {
            ("Biden", "Trump"): 2.035688053599178e-09,
            ("Biden", "Jorgensen"): 0.0,
            ("Biden", "Write-in"): 0.0,
            ("Biden", "Overvote"): 0.0,
            ("Biden", "Undervote/Blank"): 0.0,
        },
    }

    expected_decisions = {
        "test1": True,
        "test2": False,
        "test3": False,
        "test4": True,
        "test5": True,
        "test6": True,
        "test7": True,
        "test8": False,
        "test9": False,
        "test10": True,
        "test11": False,
        "test12": True,
        "test_small_third_candidate": True,
        "test_ga_presidential": True,
    }

    for contest in contests.values():
        sample = round1_sample_results[contest.name]
        T, decision = bravo.compute_risk(RISK_LIMIT, contest, sample)
        expected_T = expected_Ts[contest.name]
        for pair in expected_T:
            diff = T[pair] - expected_T[pair]
            assert (
                abs(diff) < 0.01
            ), "Risk compute for {} failed! Expected {}, got {}".format(
                contest.name, expected_Ts[contest.name][pair], T[pair]
            )

        expected_decision = expected_decisions[contest.name]
        assert (
            decision == expected_decision
        ), "Risk decision for {} failed! Expected {}, got{}".format(
            contest.name, expected_decision, decision
        )


def test_compute_risk_empty(contests):
    # Test computing risk limit with no sample
    expected_Ts = {
        "test1": {("cand1", "cand2"): 1},
        "test2": {("cand1", "cand2"): 1, ("cand1", "cand3"): 1,},
        "test3": {("cand1", ""): 1},
        "test4": {("cand1", ""): 1},
        "test5": {("cand1", "cand2"): 1},
        "test6": {("cand1", "cand2"): 1, ("cand1", "cand3"): 1,},
        "test7": {("cand1", "cand3"): 1, ("cand2", "cand3"): 1,},
        "test8": {("cand1", "cand3"): 1, ("cand2", "cand3"): 1,},
        "test9": {("cand1", ""): 1, ("cand2", ""): 1,},
        "test10": {("cand1", "cand3"): 1, ("cand2", "cand3"): 1,},
        "test11": {("cand1", "cand2"): 1,},
        "test12": {("cand1", "cand2"): 1, ("cand1", "cand3"): 1,},
        "test_small_third_candidate": {("cand1", "cand2"): 1, ("cand1", "cand3"): 1,},
        "test_ga_presidential": {
            ("Biden", "Trump"): 1,
            ("Biden", "Jorgensen"): 1,
            ("Biden", "Write-in"): 1,
            ("Biden", "Overvote"): 1,
            ("Biden", "Undervote/Blank"): 1,
        },
    }

    expected_decisions = {
        "test1": False,
        "test2": False,
        "test3": False,
        "test4": False,
        "test5": False,
        "test6": False,
        "test7": False,
        "test8": False,
        "test9": False,
        "test10": False,
        "test11": False,
        "test12": False,
        "test_small_third_candidate": False,
        "test_ga_presidential": False,
    }

    for contest in contests.values():
        sample = round0_sample_results[contest.name]
        T, decision = bravo.compute_risk(RISK_LIMIT, contest, sample)
        expected_T = expected_Ts[contest.name]
        for pair in expected_T:
            diff = T[pair] - expected_T[pair]
            assert (
                abs(diff) < 0.01
            ), "Risk compute for {} failed! Expected {}, got {}".format(
                contest.name, expected_Ts[contest.name][pair], T[pair]
            )

        expected_decision = expected_decisions[contest.name]
        assert (
            decision == expected_decision
        ), "Risk decision for {} failed! Expected {}, got{}".format(
            contest.name, expected_decision, decision
        )


def test_tied_contest():
    contest_data = {
        "cand1": 500,
        "cand2": 500,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    contest = Contest("Tied Contest", contest_data)

    sample_results = {}

    sample_options = bravo.get_sample_size(RISK_LIMIT, contest, sample_results)

    assert 0.7 not in sample_options
    assert 0.8 not in sample_options
    assert 0.9 not in sample_options
    assert sample_options["asn"]["size"] == contest.ballots
    assert sample_options["asn"]["prob"] == 1.0

    computed_p, res = bravo.compute_risk(RISK_LIMIT, contest, sample_results)

    assert computed_p[("cand1", "cand2")] > ALPHA
    assert not res

    # Now do a full hand recount
    sample_results = {"round1": {"cand1": 501, "cand2": 499,}}

    computed_p, res = bravo.compute_risk(RISK_LIMIT, contest, sample_results)

    assert computed_p[("cand1", "cand2")] == 0
    assert res


bravo_contests = {
    "test1": {
        "cand1": 600,
        "cand2": 400,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    },
    "test2": {
        "cand1": 600,
        "cand2": 200,
        "cand3": 100,
        "ballots": 900,
        "votesAllowed": 1,
        "numWinners": 1,
    },
    "test3": {"cand1": 100, "ballots": 100, "votesAllowed": 1, "numWinners": 1},
    "test4": {"cand1": 100, "ballots": 100, "votesAllowed": 1, "numWinners": 1},
    "test5": {
        "cand1": 500,
        "cand2": 500,
        "ballots": 1000,
        "votesAllowed": 1,
        "numWinners": 1,
    },
    "test6": {
        "cand1": 300,
        "cand2": 200,
        "cand3": 200,
        "ballots": 1000,
        "votesAllowed": 1,
        "numWinners": 1,
    },
    "test7": {
        "cand1": 300,
        "cand2": 200,
        "cand3": 100,
        "ballots": 700,
        "votesAllowed": 1,
        "numWinners": 2,
    },
    "test8": {
        "cand1": 300,
        "cand2": 300,
        "cand3": 100,
        "ballots": 700,
        "votesAllowed": 1,
        "numWinners": 2,
    },
    "test9": {
        "cand1": 300,
        "cand2": 200,
        "ballots": 700,
        "votesAllowed": 1,
        "numWinners": 2,
    },
    "test10": {
        "cand1": 600,
        "cand2": 300,
        "cand3": 100,
        "ballots": 1000,
        "votesAllowed": 1,
        "numWinners": 2,
    },
    "test11": {
        "cand1": 1000,
        "cand2": 0,
        "ballots": 1000,
        "votesAllowed": 1,
        "numWinners": 1,
    },
    "test12": {
        "cand1": 600,
        "cand2": 400,
        "cand3": 0,
        "ballots": 1000,
        "votesAllowed": 1,
        "numWinners": 1,
    },
    "test_small_third_candidate": {
        "cand1": 10000,
        "cand2": 9000,
        "cand3": 200,
        "ballots": 20000,
        "votesAllowed": 1,
        "numWinners": 1,
    },
    "test_ga_presidential": {
        "Trump": 2457924,
        "Biden": 2471981,
        "Jorgensen": 62058,
        "Write-in": 457,
        "Overvote": 0,
        "Undervote/Blank": 0,
        "ballots": 4992420,
        "votesAllowed": 1,
        "numWinners": 1,
    },
}

# Useful test data
round0_sample_results = {
    "test1": None,
    "test2": None,
    "test3": None,
    "test4": None,
    "test5": None,
    "test6": None,
    "test7": None,
    "test8": None,
    "test9": None,
    "test10": None,
    "test11": None,
    "test12": None,
    "test_small_third_candidate": None,
    "test_ga_presidential": None,
}

round1_sample_results = {
    "test1": {"round1": {"cand1": 72, "cand2": 47}},
    "test2": {"round1": {"cand1": 25, "cand2": 18, "cand3": 5,}},
    "test3": {"round1": {"cand1": 0}},
    "test4": {"round1": {"cand1": 100}},
    "test5": {"round1": {"cand1": 500, "cand2": 500,}},
    "test6": {"round1": {"cand1": 72, "cand2": 48, "cand3": 48}},
    "test7": {"round1": {"cand1": 30, "cand2": 25, "cand3": 10}},
    "test8": {"round1": {"cand1": 72, "cand2": 55, "cand3": 30}},
    "test9": {"round1": {"cand1": 1, "cand2": 1,}},
    "test10": {"round1": {"cand1": 60, "cand2": 30, "cand3": 10}},
    "test11": {"round1": {"cand1": 0, "cand2": 0}},
    "test12": {"round1": {"cand1": 72, "cand2": 47, "cand3": 0}},
    "test_small_third_candidate": {
        "round1": {"cand1": 1200, "cand2": 1000, "cand3": 10}
    },
    "test_ga_presidential": {
        "round1": {
            "Trump": 2457924,
            "Biden": 2471971,  # Take 10 away to make the sample "fewer" ballots
            "Jorgensen": 62058,
            "Write-in": 457,
            "Overvote": 0,
            "Undervote/Blank": 0,
        }
    },
}

true_sample_sizes = {
    "test1": {
        "asn": {"type": "ASN", "size": 119, "prob": 0.52},
        "0.7": {"type": None, "size": 184, "prob": 0.7},
        "0.8": {"type": None, "size": 244, "prob": 0.8},
        "0.9": {"type": None, "size": 351, "prob": 0.9},
    },
    "test2": {
        "asn": {"type": "ASN", "size": 22, "prob": 0.55},
        "0.7": {"type": None, "size": 32, "prob": 0.7},
        "0.8": {"type": None, "size": 41, "prob": 0.8},
        "0.9": {"type": None, "size": 57, "prob": 0.9},
    },
    "test3": {"asn": {"type": "ASN", "size": 1, "prob": 1.0},},
    "test4": {"asn": {"type": "ASN", "size": 1, "prob": 1.0},},
    "test5": {
        "asn": {"type": "ASN", "size": 1000, "prob": 1},
        "0.7": {"type": None, "size": 1000, "prob": 0.7},
        "0.8": {"type": None, "size": 1000, "prob": 0.8},
        "0.9": {"type": None, "size": 1000, "prob": 0.9},
    },
    "test6": {
        "asn": {"type": "ASN", "size": 238, "prob": 0.52},
        "0.7": {"type": None, "size": 368, "prob": 0.7},
        "0.8": {"type": None, "size": 488, "prob": 0.8},
        "0.9": {"type": None, "size": 702, "prob": 0.9},
    },
    "test7": {"asn": {"type": "ASN", "size": 101, "prob": None,},},
    "test8": {"asn": {"type": "ASN", "size": 34, "prob": None,},},
    "test9": {"asn": {"type": "ASN", "size": -1, "prob": None,},},
    "test10": {"asn": {"type": "ASN", "size": 48, "prob": None,},},
    "test11": {"asn": {"type": "ASN", "size": 1, "prob": 1.0,},},
    "test12": {
        "asn": {"type": "ASN", "size": 119, "prob": 0.52},
        "0.7": {"type": None, "size": 184, "prob": 0.7},
        "0.8": {"type": None, "size": 244, "prob": 0.8},
        "0.9": {"type": None, "size": 351, "prob": 0.9},
    },
    "test_small_third_candidate": {
        "asn": {"type": "ASN", "size": 1769, "prob": 0.5},
        "0.7": {"type": None, "size": 2837, "prob": 0.7},
        "0.8": {"type": None, "size": 3760, "prob": 0.8},
        "0.9": {"type": None, "size": 5426, "prob": 0.9},
    },
    "test_ga_presidential": {
        "asn": {"type": "ASN", "size": 573956, "prob": 0.5},
        "0.7": {"type": None, "size": 930691, "prob": 0.7},
        "0.8": {"type": None, "size": 1233334, "prob": 0.8},
        "0.9": {"type": None, "size": 1780697, "prob": 0.9},
    },
}

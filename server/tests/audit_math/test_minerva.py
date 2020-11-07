# pylint: disable=invalid-name
import pytest

from ...audit_math import minerva
from ...audit_math.sampler_contest import Contest


@pytest.fixture
def contests():
    contests = {}

    for contest in bravo_contests:
        contests[contest] = Contest(contest, bravo_contests[contest])

    return contests


# FIXME improve these tests.  Note also doctests in minerva.py module.


def test_get_sample_size():
    c3 = minerva.make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    res = minerva.get_sample_size(10, c3, None, [])
    assert res == {
        "0.7": {"type": None, "size": 134, "prob": 0.7},
        "0.8": {"type": None, "size": 166, "prob": 0.8},
        "0.9": {"type": None, "size": 215, "prob": 0.9},
    }

    c3 = minerva.make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    res = minerva.get_sample_size(10, c3, None, [])
    assert res == {
        "0.7": {"type": None, "size": 134, "prob": 0.7},
        "0.8": {"type": None, "size": 166, "prob": 0.8},
        "0.9": {"type": None, "size": 215, "prob": 0.9},
    }

    d1 = minerva.make_arlo_contest({"a": 600, "b": 200, "c": 100})
    res = minerva.get_sample_size(10, d1, None, [])
    assert res == {
        "0.7": {"type": None, "size": 20, "prob": 0.7},
        "0.8": {"type": None, "size": 25, "prob": 0.8},
        "0.9": {"type": None, "size": 35, "prob": 0.9},
    }

    d2 = minerva.make_arlo_contest({"a": 100, "b": 1})
    res = minerva.get_sample_size(10, d2, None, [])
    assert res == {
        "0.7": {"type": None, "size": 4, "prob": 0.7},
        "0.8": {"type": None, "size": 4, "prob": 0.8},
        "0.9": {"type": None, "size": 4, "prob": 0.9},
    }

    d3 = minerva.make_arlo_contest({"a": 500, "b": 500})
    res = minerva.get_sample_size(10, d3, None, [])
    assert res == {
        "0.7": {"type": None, "size": 1000, "prob": 0.7},
        "0.8": {"type": None, "size": 1000, "prob": 0.8},
        "0.9": {"type": None, "size": 1000, "prob": 0.9},
    }

    d4 = minerva.make_arlo_contest({"a": 300, "b": 200, "c": 200, "_undervote_": 300})
    res = minerva.get_sample_size(10, d4, None, [])
    assert res == {
        "0.7": {"type": None, "size": 222, "prob": 0.7},
        "0.8": {"type": None, "size": 276, "prob": 0.8},
        "0.9": {"type": None, "size": 358, "prob": 0.9},
    }

    d5 = minerva.make_arlo_contest({"a": 300})
    res = minerva.get_sample_size(10, d5, None, [])
    assert res == {
        "0.7": {"type": None, "size": -1, "prob": 0.7},
        "0.8": {"type": None, "size": -1, "prob": 0.8},
        "0.9": {"type": None, "size": -1, "prob": 0.9},
    }


def test_get_sample_size_landslide():
    d2 = minerva.make_arlo_contest({"a": 100, "b": 0})
    res = minerva.get_sample_size(10, d2, None, [])
    assert res == {"asn": {"type": "ASN", "size": 4, "prob": 1.0}}


def test_compute_risk():
    c3 = minerva.make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    res = minerva.compute_risk(
        10, c3, minerva.make_sample_results(c3, [[56, 40, 3]]), {1: 100, 2: 150}
    )
    assert res == ({("winner", "loser"): 0.0933945799801079}, True)


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
}

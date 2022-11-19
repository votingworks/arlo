# pylint: disable=invalid-name
import logging
import pytest

from pytest import approx
from ...audit_math import minerva
from ...audit_math.sampler_contest import Contest


@pytest.fixture
def contests():
    contests = {}

    for contest in bravo_contests:
        contests[contest] = Contest(contest, bravo_contests[contest])

    return contests


# TODO regularize tests via parameterization
# Note also doctests in minerva.py module.


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
    assert res == {
        "0.7": {"type": None, "size": 4, "prob": 0.7},
        "0.8": {"type": None, "size": 4, "prob": 0.8},
        "0.9": {"type": None, "size": 4, "prob": 0.9},
    }


def test_get_sample_size_landslide_other_risks():
    d2 = minerva.make_arlo_contest({"a": 100, "b": 0})
    res = minerva.get_sample_size(10, d2, None, [])
    assert res == {
        "0.7": {"type": None, "size": 4, "prob": 0.7},
        "0.8": {"type": None, "size": 4, "prob": 0.8},
        "0.9": {"type": None, "size": 4, "prob": 0.9},
    }

    assert d2.margins == {
        'winners': {
            'a': {'p_w': 1, 's_w': 1, 'swl': {'b': 1}}
        },
        'losers': {
            'b': {'p_l': 0, 's_l': 0}
        }
    }

    d2 = minerva.make_arlo_contest({"a": 100, "b": 0, "c": 0})
    res = minerva.get_sample_size(10, d2, None, [])
    assert res == {
        "0.7": {"type": None, "size": 5, "prob": 0.7},
        "0.8": {"type": None, "size": 5, "prob": 0.8},
        "0.9": {"type": None, "size": 5, "prob": 0.9},
    }

    assert d2.margins == {
        'winners': {
            'a': {'p_w': 1, 's_w': 1, 'swl': {'b': 1, 'c': 1}}
        },
        'losers': {
            'b': {'p_l': 0, 's_l': 0},
            'c': {'p_l': 0, 's_l': 0}
        }
    }

    d2 = minerva.make_arlo_contest({"a": 100, "b": 0})
    res = minerva.get_sample_size(5, d2, None, [])
    assert res == {
        "0.7": {"type": None, "size": 5, "prob": 0.7},
        "0.8": {"type": None, "size": 5, "prob": 0.8},
        "0.9": {"type": None, "size": 5, "prob": 0.9},
    }

    assert d2.margins == {
        'winners': {
            'a': {'p_w': 1, 's_w': 1, 'swl': {'b': 1}}
        },
        'losers': {
            'b': {'p_l': 0, 's_l': 0}
        }
    }

    d2 = minerva.make_arlo_contest({"a": 1000, "b": 0})
    res = minerva.get_sample_size(1, d2, None, [])
    assert res == {
        "0.7": {"type": None, "size": 7, "prob": 0.7},
        "0.8": {"type": None, "size": 7, "prob": 0.8},
        "0.9": {"type": None, "size": 7, "prob": 0.9},
    }
    assert d2.margins == {
        'winners': {
            'a': {'p_w': 1, 's_w': 1, 'swl': {'b': 1}}
        },
        'losers': {
            'b': {'p_l': 0, 's_l': 0}
        }
    }


def test_get_sample_size_landslide_low_votes(caplog):
    caplog.set_level(logging.WARN)
    d2 = minerva.make_arlo_contest({"a": 10, "b": 0})
    res = minerva.get_sample_size(1, d2, None, [])
    assert [record.levelname for record in caplog.records].count("WARNING") > 0

def test_get_sample_size_big():
    # Binary search result, just over approximation threshold of 1.5% margin
    c = minerva.make_arlo_contest({"a": 5076, "b": 4925})
    res = minerva.get_sample_size(10, c, None, [])
    assert res == {
        "0.7": {"type": None, "size": 17663, "prob": 0.7},
        "0.8": {"type": None, "size": 22233, "prob": 0.8},
        "0.9": {"type": None, "size": 30319, "prob": 0.9},
    }


def test_get_sample_size_bigger_approx():
    # 0.4% margin, fast, approximate results from v0.7.9 of Athena
    # Binary search numbers are 250632, 315749, 430133 instead
    # and take 2 minutes on an Intel(R) Xeon(R) CPU X3450 @ 2.67GHz:
    #  time python -m athena --type minerva -n t -b 502 498 -p .9 .8 .7 --approx 0.001
    c = minerva.make_arlo_contest({"a": 502000, "b": 498000})
    res = minerva.get_sample_size(10, c, None, [])
    assert res == {
        "0.7": {"type": None, "size": 250047, "prob": 0.7},
        "0.8": {"type": None, "size": 315475, "prob": 0.8},
        "0.9": {"type": None, "size": 429778, "prob": 0.9},
    }


def test_get_sample_size_second_round():
    c = minerva.make_arlo_contest({"a": 502000, "b": 498000})
    res = minerva.get_sample_size(10, c, None, [])
    assert res == {
        "0.7": {"type": None, "size": 250047, "prob": 0.7},
        "0.8": {"type": None, "size": 315475, "prob": 0.8},
        "0.9": {"type": None, "size": 429778, "prob": 0.9},
    }

    sample = {"r1": {"a": 10, "b": 10}}

    assert minerva.get_sample_size(20, c, sample, {1: 20}) == {
        "0.9": {"type": None, "size": 45, "prob": 0.9}
    }


def test_compute_risk_2r():
    c = minerva.make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    res = minerva.compute_risk(
        10,
        c,
        minerva.make_sample_results(c, [[40, 40, 3], [70, 30, 10]]),
        {1: 83, 2: 200},
    )
    assert res == ({("winner", "loser"): approx(0.006382031505998192)}, True)


def test_get_sample_size_2win():
    d2 = minerva.make_arlo_contest(
        {"a": 400, "b": 400, "c": 200, "d": 100}, num_winners=2
    )
    res = minerva.get_sample_size(10, d2, None, [])
    assert res == {
        "0.7": {"prob": 0.7, "size": 79, "type": None},
        "0.8": {"prob": 0.8, "size": 87, "type": None},
        "0.9": {"prob": 0.9, "size": 114, "type": None},
    }


def test_collect_risks():
    c3 = minerva.make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    res = minerva.collect_risks(
        0.1, c3, [120], minerva.make_sample_results(c3, [[56, 40, 3]])
    )
    assert res == {("winner", "loser"): approx(0.0933945799801079)}
    res = minerva.collect_risks(
        0.1, c3, [83], minerva.make_sample_results(c3, [[40, 40, 3]])
    )
    assert res == {("winner", "loser"): pytest.approx(0.5596434615209632)}
    with pytest.raises(ValueError, match="Incorrect number of valid ballots entered"):
        minerva.collect_risks(
            0.1, c3, [82], minerva.make_sample_results(c3, [[40, 40, 3]])
        )


def test_compute_risk_delta():
    c = minerva.make_arlo_contest(
        {
            "Warnock": 1613896,
            "Loeffler": 1270718,
            "Collins": 978667,
            "Write-ins": 132,
            "_undervote_": 1041608,
        },
        num_winners=2,
    )
    res = minerva.compute_risk(
        10, c, minerva.make_sample_results(c, [[384, 276, 234, 1]]), {1: 923}
    )
    assert res == ({("winner", "loser"): approx(0.039858047805999164)}, True)


def test_compute_risk_2win():
    c = minerva.make_arlo_contest(
        {"a": 400, "b": 400, "c": 200, "d": 100}, num_winners=2
    )
    res = minerva.compute_risk(
        10, c, minerva.make_sample_results(c, [[40, 40, 18, 2]]), {1: 100}
    )
    assert res == ({("winner", "loser"): approx(0.0064653703790821795)}, True)


def test_compute_risk_2win_2():
    c = minerva.make_arlo_contest(
        {"a": 400, "b": 400, "c": 200, "d": 100}, num_winners=2
    )
    res = minerva.compute_risk(
        10, c, minerva.make_sample_results(c, [[30, 30, 30, 10]]), {1: 100}
    )
    assert res == ({("winner", "loser"): approx(0.552702598296842)}, False)


def test_compute_risk_2win_2_2r():
    c = minerva.make_arlo_contest(
        {"a": 400, "b": 400, "c": 200, "d": 100}, num_winners=2
    )
    res = minerva.compute_risk(
        10,
        c,
        minerva.make_sample_results(c, [[30, 30, 30, 10], [50, 50, 25, 25]]),
        {1: 100, 2: 150},
    )
    assert res == ({("winner", "loser"): approx(0.083535346859948)}, True)


def test_compute_risk():
    c3 = minerva.make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    res = minerva.compute_risk(
        10, c3, minerva.make_sample_results(c3, [[56, 40, 3]]), {1: 100, 2: 150}
    )
    assert res == ({("winner", "loser"): approx(0.0933945799801079)}, True)
    res = minerva.compute_risk(
        10, c3, minerva.make_sample_results(c3, [[40, 40, 3]]), {1: 100, 2: 150}
    )
    assert res == ({("winner", "loser"): approx(0.5596434615209632)}, False)


def test_compute_risk_close_narrow():
    "Check an audit with tight and wide margins, ala issue #778"

    c = minerva.make_arlo_contest(
        {"a": 5100000, "b": 4900000, "c": 100, "_undervote_": 100000}
    )
    res = minerva.compute_risk(
        10, c, minerva.make_sample_results(c, [[5100, 4990, 1]]), {1: 10091}
    )
    assert res == ({("winner", "loser"): 0.16896200607848647}, False)


def test_compute_risk_close_narrow_2():
    "Continue to 2nd round"

    c = minerva.make_arlo_contest(
        {"a": 5100000, "b": 4900000, "c": 100, "_undervote_": 100000}
    )
    res = minerva.compute_risk(
        10,
        c,
        minerva.make_sample_results(c, [[5100, 4990, 1], [5100, 4900, 0]]),
        {1: 10091, 2: 10000},
    )
    assert res == ({("winner", "loser"): approx(0.03907953348498701)}, True)


@pytest.mark.skip(reason="Takes over a minute to run.")
def test_compute_risk_close_narrow_3():
    "test 100,000 samples in 2nd round"

    c = minerva.make_arlo_contest(
        {"a": 5100000, "b": 4900000, "c": 100, "_undervote_": 100000}
    )
    res = minerva.compute_risk(
        10,
        c,
        minerva.make_sample_results(c, [[50100, 49900, 1], [51000, 49000, 0]]),
        {1: 100001, 2: 100000},
    )
    assert res == ({("winner", "loser"): 0.0016102827517693026}, True)


# @pytest.mark.skip(reason="To be addressed in future version of Athena package")
def test_compute_risk_too_low():
    "Check an audit with such a small p-value that it might become NaN. Fails in 0.7.1"

    c = minerva.make_arlo_contest({"a": 2453876, "b": 2358432, "_undervote_": 114911})
    res = minerva.compute_risk(
        10, c, minerva.make_sample_results(c, [[17605, 0]]), {1: 17605}
    )
    assert res == ({("winner", "loser"): 0.0}, True)


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

from r2b2.minerva2 import Minerva2
from r2b2.contest import Contest as rContest, ContestType
from pytest import approx, raises

from ...audit_math import minerva2, minerva, ballot_polling
from ...models import AuditMathType

ALPHA = 0.1
RISK_LIMIT = 10


def test_make_r2b2_contest():
    arlo = minerva.make_arlo_contest({"a": 500, "b": 200, "c": 50})
    r2b2_contest = minerva2.make_r2b2_contest(arlo)

    assert arlo.ballots == r2b2_contest.contest_ballots
    for k in arlo.candidates:
        assert arlo.candidates[k] == r2b2_contest.tally[k]


# Credit to the r2b2 team for some of these tests, using some of the values they
# have in their tests just to verify that I'm getting similar responses.
def test_get_sample_size():
    arlo1 = minerva.make_arlo_contest({"a": 60000, "b": 40000})
    arlo2 = minerva.make_arlo_contest({"a": 51000, "b": 49000})
    arlo3 = minerva.make_arlo_contest({"a": 5040799, "b": 10000000 - 5040799})
    assert minerva2.get_sample_size(RISK_LIMIT, arlo1, None, None)["0.9"]["size"] == 173
    assert (
        minerva2.get_sample_size(RISK_LIMIT, arlo2, None, None)["0.9"]["size"] == 17270
    )
    assert (
        minerva2.get_sample_size(RISK_LIMIT, arlo3, None, None)["0.9"]["size"] == 103467
    )


def test_get_sample_size_multi_candidate():
    arlo1 = minerva.make_arlo_contest({"a": 60000, "b": 40000, "c": 10000})
    arlo2 = minerva.make_arlo_contest({"a": 51000, "b": 49000, "c": 10000})
    arlo3 = minerva.make_arlo_contest(
        {"a": 5040799, "b": 10000000 - 5040799, "c": 1000000}
    )
    assert minerva2.get_sample_size(RISK_LIMIT, arlo1, None, None)["0.9"]["size"] == 191
    assert (
        minerva2.get_sample_size(RISK_LIMIT, arlo2, None, None)["0.9"]["size"] == 18997
    )
    assert (
        minerva2.get_sample_size(RISK_LIMIT, arlo3, None, None)["0.9"]["size"] == 113814
    )


def test_get_sample_size_2win():
    contest = minerva.make_arlo_contest(
        {"a": 400, "b": 400, "c": 200, "d": 100}, num_winners=2
    )
    res = minerva2.get_sample_size(10, contest, None, [])
    assert res == {
        "0.7": {"prob": 0.7, "size": 76, "type": None},
        "0.8": {"prob": 0.8, "size": 87, "type": None},
        "0.9": {"prob": 0.9, "size": 118, "type": None},
    }
    sample_results = {"1": {"a": 30, "b": 30, "c": 20, "d": 20}}
    round_schedule = {1: ("1", 100)}
    res = minerva2.get_sample_size(10, contest, sample_results, round_schedule)
    assert res == {
        "0.7": {"prob": 0.7, "size": 297, "type": None},
        "0.8": {"prob": 0.8, "size": 315, "type": None},
        "0.9": {"prob": 0.9, "size": 319, "type": None},
    }


def test_get_sample_size_multiple_rounds():
    contest1 = rContest(
        100000, {"A": 60000, "B": 40000}, 1, ["A"], ContestType.MAJORITY
    )
    minerva1 = Minerva2(ALPHA, 1.0, contest1)
    minerva1.execute_round(100, {"A": 54, "B": 46})
    r2b2_result = minerva1.next_sample_size()
    arlo = minerva.make_arlo_contest({"A": 60000, "B": 40000})
    sample_results = {"1": {"A": 54, "B": 100 - 54}}
    round_schedule = {1: ("1", 100)}
    arlo_result = minerva2.get_sample_size(
        RISK_LIMIT, arlo, sample_results, round_schedule
    )["0.9"]["size"]
    assert r2b2_result == arlo_result

    minerva1.execute_round(200, {"A": 113, "B": 200 - 113})
    r2b2_result = minerva1.next_sample_size()
    sample_results["2"] = {"A": 113 - 54, "B": 200 - 113 - (100 - 54)}
    round_schedule[2] = ("2", 100)
    arlo_result = minerva2.get_sample_size(
        RISK_LIMIT, arlo, sample_results, round_schedule
    )["0.9"]["size"]
    assert r2b2_result == arlo_result


def test_compute_risk():
    contest1 = rContest(
        100000, {"A": 60000, "B": 40000}, 1, ["A"], ContestType.MAJORITY
    )
    minerva1 = Minerva2(ALPHA, 1.0, contest1)
    minerva1.execute_round(100, {"A": 54, "B": 100 - 54})
    arlo = minerva.make_arlo_contest({"A": 60000, "B": 40000})
    sample_results = {"1": {"A": 54, "B": 100 - 54}}
    round_schedule = {1: ("1", 100)}
    risk = minerva2.compute_risk(RISK_LIMIT, arlo, sample_results, round_schedule)
    ballot_polling_risk = ballot_polling.compute_risk(
        RISK_LIMIT, arlo, sample_results, {}, AuditMathType.MINERVA2, round_schedule
    )
    assert ballot_polling_risk == risk
    assert minerva1.get_risk_level() == risk[0][("winner", "loser")]

    with raises(
        ValueError, match="The risk-limit must be greater than zero and less than 100!"
    ):
        risk = minerva2.compute_risk(1000, arlo, sample_results, round_schedule)


def test_compute_risk_2win():
    contest = minerva.make_arlo_contest(
        {"a": 400, "b": 400, "c": 200, "d": 100}, num_winners=2
    )
    res = minerva2.compute_risk(
        10,
        contest,
        minerva.make_sample_results(contest, [[40, 40, 18, 2]]),
        {1: ("r0", 100)},
    )
    assert res == ({("winner", "loser"): approx(0.0064653703790821795)}, True)
    res = minerva2.compute_risk(
        10,
        contest,
        minerva.make_sample_results(contest, [[30, 30, 30, 10]]),
        {1: ("r0", 100)},
    )
    assert res == ({("winner", "loser"): approx(0.552702598296842)}, False)


def test_compute_risk_multi_round():
    contest = minerva.make_arlo_contest({"A": 450, "B": 400})
    sample_results = {"1": {"A": 54, "B": 100 - 54}}
    round_schedule = {1: ("1", 100)}
    sample_results["2"] = {"A": 55, "B": 100 - 55}
    round_schedule[2] = ("2", 100)
    res = minerva2.compute_risk(10, contest, sample_results, round_schedule)
    assert res == ({("winner", "loser"): 0.3614293635757271}, False)
    # TODO: Look into this, does the risk make sense?

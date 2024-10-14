# pylint: disable=consider-using-dict-items
from r2b2.minerva2 import Minerva2 as Providence
from r2b2.contest import Contest as rContest, ContestType
import pytest

from ...audit_math import bravo, minerva, ballot_polling, providence
from ...audit_math.ballot_polling_types import RoundInfo
from ...models import AuditMathType

ALPHA = 0.1
RISK_LIMIT = 10


def test_make_r2b2_contest():
    arlo = minerva.make_arlo_contest({"a": 500, "b": 200, "c": 50})
    r2b2_contest = providence.make_r2b2_contest(arlo)

    assert arlo.ballots == r2b2_contest.contest_ballots
    for k in arlo.candidates:
        assert arlo.candidates[k] == r2b2_contest.tally[k]


# Credit to the r2b2 team for some of these tests, using some of the values they
# have in their tests just to verify that I'm getting similar responses.
def test_get_sample_size():
    arlo1 = minerva.make_arlo_contest({"a": 60000, "b": 40000})
    arlo2 = minerva.make_arlo_contest({"a": 51000, "b": 49000})
    arlo3 = minerva.make_arlo_contest({"a": 5040799, "b": 10000000 - 5040799})
    assert (
        providence.get_sample_size(RISK_LIMIT, arlo1, None, None)["0.9"]["size"] == 173
    )
    assert (
        providence.get_sample_size(RISK_LIMIT, arlo2, None, None)["0.9"]["size"]
        == 17270
    )
    assert (
        providence.get_sample_size(RISK_LIMIT, arlo3, None, None)["0.9"]["size"]
        == 103467
    )


def test_get_sample_size_multi_candidate():
    arlo1 = minerva.make_arlo_contest({"a": 60000, "b": 40000, "c": 10000})
    arlo2 = minerva.make_arlo_contest({"a": 51000, "b": 49000, "c": 10000})
    arlo3 = minerva.make_arlo_contest(
        {"a": 5040799, "b": 10000000 - 5040799, "c": 1000000}
    )
    assert (
        providence.get_sample_size(RISK_LIMIT, arlo1, None, None)["0.9"]["size"] == 191
    )
    assert (
        providence.get_sample_size(RISK_LIMIT, arlo2, None, None)["0.9"]["size"]
        == 18997
    )
    assert (
        providence.get_sample_size(RISK_LIMIT, arlo3, None, None)["0.9"]["size"]
        == 113814
    )


def test_get_sample_size_2win():
    contest = minerva.make_arlo_contest(
        {"a": 400, "b": 400, "c": 200, "d": 100}, num_winners=2
    )
    res = providence.get_sample_size(10, contest, None, [])
    assert res == {
        "0.7": {"prob": 0.7, "size": 76, "type": None},
        "0.8": {"prob": 0.8, "size": 87, "type": None},
        "0.9": {"prob": 0.9, "size": 118, "type": None},
    }
    sample_results = {"1": {"a": 30, "b": 30, "c": 20, "d": 20}}
    round_schedule = {1: RoundInfo("1", 100)}
    res = providence.get_sample_size(10, contest, sample_results, round_schedule)
    assert res == {
        "0.7": {"prob": 0.7, "size": 297, "type": None},
        "0.8": {"prob": 0.8, "size": 315, "type": None},
        "0.9": {"prob": 0.9, "size": 319, "type": None},
    }


def test_get_sample_size_multiple_rounds():
    contest1 = rContest(
        100000, {"A": 60000, "B": 40000}, 1, ["A"], ContestType.MAJORITY
    )
    providence_audit_1 = Providence(ALPHA, 1.0, contest1)
    providence_audit_1.execute_round(100, {"A": 54, "B": 46})
    r2b2_result = providence_audit_1.next_sample_size()
    arlo = minerva.make_arlo_contest({"A": 60000, "B": 40000})
    sample_results = {"1": {"A": 54, "B": 100 - 54}}
    round_schedule = {1: RoundInfo("1", 100)}
    arlo_result = providence.get_sample_size(
        RISK_LIMIT, arlo, sample_results, round_schedule
    )["0.9"]["size"]
    assert r2b2_result == arlo_result

    providence_audit_1.execute_round(200, {"A": 113, "B": 200 - 113})
    r2b2_result = providence_audit_1.next_sample_size()
    sample_results["2"] = {"A": 113 - 54, "B": 200 - 113 - (100 - 54)}
    round_schedule[2] = RoundInfo("2", 100)
    arlo_result = providence.get_sample_size(
        RISK_LIMIT, arlo, sample_results, round_schedule
    )["0.9"]["size"]
    assert r2b2_result == arlo_result


def test_compute_risk():
    contest1 = rContest(
        100000, {"A": 60000, "B": 40000}, 1, ["A"], ContestType.MAJORITY
    )
    providence_audit_1 = Providence(ALPHA, 1.0, contest1)
    providence_audit_1.execute_round(100, {"A": 54, "B": 100 - 54})
    arlo = minerva.make_arlo_contest({"A": 60000, "B": 40000})
    sample_results = {"1": {"A": 54, "B": 100 - 54}}
    round_schedule = {1: RoundInfo("1", 100)}
    risk = providence.compute_risk(RISK_LIMIT, arlo, sample_results, round_schedule)
    ballot_polling_risk = ballot_polling.compute_risk(
        RISK_LIMIT, arlo, sample_results, {}, AuditMathType.PROVIDENCE, round_schedule
    )
    assert ballot_polling_risk == risk
    assert providence_audit_1.get_risk_level() == risk[0][("winner", "loser")]

    with pytest.raises(
        ValueError, match="The risk-limit must be greater than zero and less than 100!"
    ):
        risk = providence.compute_risk(1000, arlo, sample_results, round_schedule)


def test_compute_risk_2win():
    contest = minerva.make_arlo_contest(
        {"a": 400, "b": 400, "c": 200, "d": 100}, num_winners=2
    )
    res = providence.compute_risk(
        10,
        contest,
        minerva.make_sample_results(contest, [[40, 40, 18, 2]]),
        {1: RoundInfo("r0", 100)},
    )
    assert res == ({("winner", "loser"): pytest.approx(0.0064653703790821795)}, True)
    res = providence.compute_risk(
        10,
        contest,
        minerva.make_sample_results(contest, [[30, 30, 30, 10]]),
        {1: RoundInfo("r0", 100)},
    )
    assert res == ({("winner", "loser"): pytest.approx(0.552702598296842)}, False)


def test_compute_risk_multi_round():
    contest = minerva.make_arlo_contest({"A": 450, "B": 400})
    sample_results = {"1": {"A": 54, "B": 100 - 54}}
    round_schedule = {1: RoundInfo("1", 100)}
    sample_results["2"] = {"A": 55, "B": 100 - 55}
    round_schedule[2] = RoundInfo("2", 100)
    res = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    assert res == ({("winner", "loser"): pytest.approx(0.3614293635757271)}, False)


def test_compare_minervas():
    contest = minerva.make_arlo_contest({"A": 450, "B": 400})
    sample_results = {"1": {"A": 54, "B": 100 - 54}}
    round_schedule = {1: RoundInfo("1", 100)}
    m_1 = minerva.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    m_2 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    # Providence's round 1 stopping condition is equivalent to Minerva, so risks should be the same.
    assert m_1 == m_2

    sample_results["2"] = {"A": 55, "B": 100 - 55}
    round_schedule[2] = RoundInfo("2", 100)
    m_1 = minerva.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    m_2 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    assert m_1[0][("winner", "loser")] < m_2[0][("winner", "loser")]


def test_compare_bravo():
    contest = minerva.make_arlo_contest({"A": 450, "B": 400})
    sample_results = {"1": {"A": 54, "B": 100 - 54}}
    round_schedule = {1: RoundInfo("1", 100)}
    m_1 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    b_1 = bravo.compute_risk(RISK_LIMIT, contest, sample_results)
    assert m_1[0][("winner", "loser")] < b_1[0][("A", "B")]
    sample_results["2"] = {"A": 55, "B": 100 - 55}
    round_schedule[2] = RoundInfo("2", 100)
    m_1 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    b_1 = bravo.compute_risk(RISK_LIMIT, contest, sample_results)
    assert m_1[0][("winner", "loser")] < b_1[0][("A", "B")]
    sample_results["3"] = {"A": 8, "B": 2}
    round_schedule[3] = RoundInfo("3", 10)
    m_1 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    b_1 = bravo.compute_risk(RISK_LIMIT, contest, sample_results)
    assert m_1[0][("winner", "loser")] < b_1[0][("A", "B")]
    sample_results["4"] = {"A": 36, "B": 14}
    round_schedule[4] = RoundInfo("4", 50)
    m_1 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    b_1 = bravo.compute_risk(RISK_LIMIT, contest, sample_results)
    assert m_1[0][("winner", "loser")] < b_1[0][("A", "B")]


def test_abnormal_rounds():
    contest = minerva.make_arlo_contest({"A": 500, "B": 100})
    sample_results = {"1": {"A": 0, "B": 100}}
    round_schedule = {1: RoundInfo("1", 100)}
    m_2 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    assert not m_2[1]
    sample_results["2"] = {"A": 500, "B": 0}
    round_schedule[2] = RoundInfo("2", 500)
    m_2 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    assert m_2[1]

    contest = minerva.make_arlo_contest({"A": 5000, "B": 1000, "C": 1000, "D": 1000})
    sample_results = {"1": {"A": 1000, "B": 1000, "C": 1000, "D": 1000}}
    round_schedule = {1: RoundInfo("1", 4000)}
    m_2 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    assert not m_2[1]
    sample_results = {"1": {"A": 1000, "B": 0, "C": 0, "D": 0}}
    round_schedule = {1: RoundInfo("1", 1000)}
    m_2 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    assert m_2[1]


@pytest.mark.skip(
    reason="Both minerva's don't report the race as finished, should this be fixed?"
)
def test_tight_margins_full_count():
    contest = minerva.make_arlo_contest({"A": 101, "B": 100})
    sample_results = {"1": {"A": 0, "B": 100}}
    round_schedule = {1: RoundInfo("1", 100)}
    m_2 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    assert not m_2[1]
    sample_results["2"] = {"A": 101, "B": 0}
    round_schedule[2] = RoundInfo("2", 101)
    m_2 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    assert m_2[1]

    contest = minerva.make_arlo_contest({"A": 1001, "B": 1000, "C": 1000, "D": 1000})
    sample_results = {"1": {"A": 1001, "B": 1000, "C": 1000, "D": 1000}}
    round_schedule = {1: RoundInfo("1", 4001)}
    m_2 = providence.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    m_1 = minerva.compute_risk(RISK_LIMIT, contest, sample_results, round_schedule)
    assert m_2[1]
    assert m_1[1]

from r2b2.minerva2 import Minerva2
from r2b2.contest import Contest as rContest, ContestType

from ...audit_math import minerva2, minerva

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


# TODO: IDEA
# Look into how these functions are called (get_sample_size and compute_risk). I
# suspect that when someone's running arlo, they're pretty much just running one
# election at a time. If that's the case, it should be reasonable to have
# minerva2.py track existing elections and pick up where they were left off.
# We shouldn't have too many minerva2 instances running around in memory, and if
# we do we can just get rid of them and remake them later? Need to think through
# how this ought to work


def test_get_sample_size_multiple_rounds():
    contest1 = rContest(
        100000, {"A": 60000, "B": 40000}, 1, ["A"], ContestType.MAJORITY
    )
    minerva1 = Minerva2(ALPHA, 1.0, contest1)
    minerva1.compute_min_winner_ballots(minerva1.sub_audits["A-B"], 100)
    minerva1.sample_ballots["A"].append(54)
    minerva1.sample_ballots["B"].append(100 - 54)
    r2b2_result = minerva1.next_sample_size()
    arlo = minerva.make_arlo_contest({"A": 60000, "B": 40000})
    sample_results = {1: {"A": 54, "B": 100 - 54}}
    round_schedule = {1: 100}
    arlo_result = minerva2.get_sample_size(
        RISK_LIMIT, arlo, sample_results, round_schedule
    )["0.9"]["size"]
    assert r2b2_result == arlo_result

    minerva1.compute_min_winner_ballots(minerva1.sub_audits["A-B"], 200)
    minerva1.sample_ballots["A"].append(113)
    minerva1.sample_ballots["B"].append(200 - 113)
    r2b2_result = minerva1.next_sample_size()
    sample_results[2] = {"A": 113, "B": 200 - 113}
    round_schedule[2] = 200
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
    sample_results = {1: {"A": 54, "B": 100 - 54}}
    round_schedule = {1: 100}
    risk = minerva2.compute_risk(RISK_LIMIT, arlo, sample_results, round_schedule)
    assert minerva1.get_risk_level() == risk[0][("winner", "loser")]

import pytest

from pytest import approx
from ...audit_math import minerva2, minerva
from ...audit_math.sampler_contest import Contest


# TODO regularize tests via parameterization
# Note also doctests in minerva.py module.


def test_make_r2b2_contest():
    arlo = minerva.make_arlo_contest({"a": 500, "b": 200, "c": 50})
    r2b2_contest = minerva2.make_r2b2_contest(arlo)

    assert arlo.ballots == r2b2_contest.contest_ballots
    for k in arlo.candidates:
        assert arlo.candidates[k] == r2b2_contest.tally[k]

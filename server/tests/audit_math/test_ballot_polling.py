# pylint: disable=invalid-name
from decimal import Decimal
import pytest

from ...audit_math import bravo, minerva, ballot_polling
from ...audit_math.sampler_contest import Contest
from ...models import AuditMathType

SEED = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
RISK_LIMIT = 10
ALPHA = Decimal(0.1)


@pytest.fixture
def contests():
    contests = {}

    for contest in bravo_contests:
        contests[contest] = Contest(contest, bravo_contests[contest])

    return contests


def test_get_sample_sizes(contests):
    for contest in contests:
        bravo_sample_size = bravo.get_sample_size(
            RISK_LIMIT, contests[contest], None, None
        )

        assert bravo_sample_size == ballot_polling.get_sample_size(
            RISK_LIMIT, contests[contest], None, AuditMathType.BRAVO, None
        )

        minerva_sample_size = minerva.get_sample_size(
            RISK_LIMIT, contests[contest], None, None
        )
        assert minerva_sample_size == ballot_polling.get_sample_size(
            RISK_LIMIT, contests[contest], None, AuditMathType.MINERVA, None
        )


def test_compute_risk(contests):
    for contest in contests:
        sample = round1_sample_results[contest]

        bravo_test_stat, bravo_decision = bravo.compute_risk(
            RISK_LIMIT, contests[contest], sample
        )

        computed_stat, computed_decision = ballot_polling.compute_risk(
            RISK_LIMIT, contests[contest], sample, AuditMathType.BRAVO, {1: 119}
        )

        assert (bravo_test_stat, bravo_decision) == (computed_stat, computed_decision)

        # Test the default case
        computed_stat, computed_decision = ballot_polling.compute_risk(
            RISK_LIMIT, contests[contest], sample, AuditMathType.SUPERSIMPLE, {1: 119}
        )

        assert (bravo_test_stat, bravo_decision) == (computed_stat, computed_decision)

        minerva_test_stat, minerva_decision = minerva.compute_risk(
            RISK_LIMIT, contests[contest], sample, {1: 119}
        )

        computed_stat, computed_decision = ballot_polling.compute_risk(
            RISK_LIMIT, contests[contest], sample, AuditMathType.MINERVA, {1: 119}
        )

        assert (minerva_test_stat, minerva_decision) == (
            computed_stat,
            computed_decision,
        )


round1_sample_results = {
    "test1": {"round1": {"cand1": 72, "cand2": 47}},
}

bravo_contests = {
    "test1": {
        "cand1": 600,
        "cand2": 400,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    },
}

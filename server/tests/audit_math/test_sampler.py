import random
import pytest
from ...audit_math import sampler
from ...audit_math.sampler_contest import Contest

SEED = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
RISK_LIMIT = 0.1


@pytest.fixture
def macro_batches():
    batches = {}

    # 10 batches will have max error of .08
    for i in range(10):
        batches["pct {}".format(i)] = {
            "test1": {"cand1": 40, "cand2": 10, "ballots": 50}
        }
        # 10 batches will have max error of .04
    for i in range(11, 20):
        batches["pct {}".format(i)] = {
            "test1": {"cand1": 20, "cand2": 30, "ballots": 50}
        }

    return batches


@pytest.fixture
def macro_contest():
    name = "test1"

    info_dict = {
        "cand1": 600,
        "cand2": 400,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    return Contest(name, info_dict)


def test_draw_sample(snapshot):
    # Test getting a sample
    manifest = {
        "pct 1": 25,
        "pct 2": 25,
        "pct 3": 25,
        "pct 4": 25,
    }

    sample = sampler.draw_sample(SEED, manifest, 20, 0)
    snapshot.assert_match(sample)


def test_draw_more_samples(snapshot):
    # Test getting a sample
    manifest = {
        "pct 1": 25,
        "pct 2": 25,
        "pct 3": 25,
        "pct 4": 25,
    }

    sample = sampler.draw_sample(SEED, manifest, 10, 0)
    snapshot.assert_match(sample)

    sample = sampler.draw_sample(SEED, manifest, 10, num_sampled=10)
    snapshot.assert_match(sample)


def test_draw_macro_sample(macro_batches, macro_contest, snapshot):
    # Test getting a sample
    sample = sampler.draw_ppeb_sample(
        SEED, macro_contest, 10, 0, batch_results=macro_batches
    )
    snapshot.assert_match(sample)


def test_draw_more_macro_sample(macro_batches, macro_contest, snapshot):
    # Test getting a sample
    sample = sampler.draw_ppeb_sample(
        SEED, macro_contest, 5, 0, batch_results=macro_batches,
    )
    snapshot.assert_match(sample)

    sample = sampler.draw_ppeb_sample(
        SEED, macro_contest, 5, num_sampled=5, batch_results=macro_batches
    )
    snapshot.assert_match(sample)


def random_manifest():
    rand = random.Random(12345)
    return {f"pct {n}": rand.randint(1, 10) for n in range(rand.randint(1, 10))}


def test_ballot_labels():
    for _ in range(100):
        manifest = random_manifest()
        sample = sampler.draw_sample(SEED, manifest, 100, 0)
        for (_, (batch, ballot_number), _) in sample:
            assert 1 <= ballot_number <= manifest[batch]

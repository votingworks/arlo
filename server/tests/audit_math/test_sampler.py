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
def close_macro_batches():
    batches = {}

    batches["pct {}".format(1)] = {"test1": {"cand1": 100, "cand2": 0, "ballots": 100}}
    batches["pct {}".format(2)] = {"test1": {"cand1": 100, "cand2": 0, "ballots": 100}}
    batches["pct {}".format(3)] = {"test1": {"cand1": 0, "cand2": 100, "ballots": 100}}
    batches["pct {}".format(4)] = {"test1": {"cand1": 0, "cand2": 98, "ballots": 100}}
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


@pytest.fixture
def close_macro_contest():
    name = "recount"

    info_dict = {
        "cand1": 200,
        "cand2": 198,
        "ballots": 400,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    return Contest(name, info_dict)


def test_draw_sample(snapshot):
    # Test getting a sample
    manifest = {
        "pct 1": list(range(1, 26)),
        "pct 2": list(range(1, 26)),
        "pct 3": list(range(1, 26)),
        "pct 4": list(range(1, 26)),
    }

    sample = sampler.draw_sample(SEED, manifest, 20, 0)
    snapshot.assert_match(sample)


def test_draw_more_samples(snapshot):
    # Test getting a sample
    manifest = {
        "pct 1": list(range(1, 26)),
        "pct 2": list(range(1, 26)),
        "pct 3": list(range(1, 26)),
        "pct 4": list(range(1, 26)),
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


def test_macro_recount_sample(close_macro_batches, close_macro_contest, snapshot):

    sample = sampler.draw_ppeb_sample(
        SEED, close_macro_contest, 5, 0, batch_results=close_macro_batches,
    )
    snapshot.assert_match(sample)

    # Now do a full recount
    sample = sampler.draw_ppeb_sample(
        SEED,
        close_macro_contest,
        1000,
        num_sampled=5,
        batch_results=close_macro_batches,
    )
    snapshot.assert_match(sample)


def test_draw_macro_multiple_contests(macro_batches, snapshot):
    name = "test2"

    info_dict = {
        "cand1": 400,
        "cand2": 100,
        "ballots": 500,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    other_contest = Contest(name, info_dict)

    for batch in macro_batches:
        pct = int(batch.split(" ")[-1])
        if pct < 10:
            macro_batches[batch]["test2"] = {"cand1": 40, "cand2": 10, "ballots": 50}

    # By including a contest that isn't contained in every batch, those batches
    # will get a maximum possible error (U) of zero for that contest.
    sample = sampler.draw_ppeb_sample(
        SEED, other_contest, 10, 0, batch_results=macro_batches
    )
    snapshot.assert_match(sample)


def random_manifest():
    rand = random.Random(12345)
    return {
        f"pct {n}": list(range(1, rand.randint(2, 11)))
        for n in range(rand.randint(1, 10))
    }


def test_ballot_labels():
    for _ in range(100):
        manifest = random_manifest()
        sample = sampler.draw_sample(SEED, manifest, 100, 0)
        for (_, (batch, ballot_number), _) in sample:
            assert 1 <= ballot_number <= max(manifest[batch])

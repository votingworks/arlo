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


def test_draw_sample():
    # Test getting a sample
    manifest = {
        "pct 1": 25,
        "pct 2": 25,
        "pct 3": 25,
        "pct 4": 25,
    }

    sample = sampler.draw_sample(SEED, manifest, 20, 0)

    for i, item in enumerate(sample):
        expected = expected_sample[i]
        assert item == expected, "Draw sample failed: got {}, expected {}".format(
            item, expected
        )


def test_draw_more_samples():
    # Test getting a sample
    manifest = {
        "pct 1": 25,
        "pct 2": 25,
        "pct 3": 25,
        "pct 4": 25,
    }

    samp_size = 10
    sample = sampler.draw_sample(SEED, manifest, 10, 0)
    assert samp_size == len(sample), "Received sample of size {}, expected {}".format(
        samp_size, len(sample)
    )

    for i, item in enumerate(sample):
        expected = expected_first_sample[i]
        assert item == expected, "Draw sample failed: got {}, expected {}".format(
            item, expected
        )

    samp_size = 10
    sample = sampler.draw_sample(SEED, manifest, 10, num_sampled=10)
    assert samp_size == len(sample), "Received sample of size {}, expected {}".format(
        samp_size, len(sample)
    )
    for i, item in enumerate(sample):
        expected = expected_second_sample[i]
        assert item == expected, "Draw sample failed: got {}, expected {}".format(
            item, expected
        )


def test_draw_macro_sample(macro_batches, macro_contest):
    # Test getting a sample
    sample = sampler.draw_ppeb_sample(
        SEED, macro_contest, 10, 0, batch_results=macro_batches
    )

    for i, item in enumerate(sample):
        expected = expected_macro_sample[i]
        assert item == expected, "Draw sample failed: got {}, expected {}".format(
            item, expected
        )


def test_draw_more_macro_sample(macro_batches, macro_contest):
    # Test getting a sample
    samp_size = 5
    sample = sampler.draw_ppeb_sample(
        SEED, macro_contest, samp_size, 0, batch_results=macro_batches,
    )
    assert samp_size == len(sample), "Received sample of size {}, expected {}".format(
        samp_size, len(sample)
    )

    for i, item in enumerate(sample):
        expected = expected_first_macro_sample[i]
        assert item == expected, "Draw sample failed: got {}, expected {}".format(
            item, expected
        )

    samp_size = 5
    sample = sampler.draw_ppeb_sample(
        SEED, macro_contest, samp_size, num_sampled=5, batch_results=macro_batches
    )
    assert samp_size == len(sample), "Received sample of size {}, expected {}".format(
        samp_size, len(sample)
    )
    for i, item in enumerate(sample):
        expected = expected_second_macro_sample[i]
        assert item == expected, "Draw sample failed: got {}, expected {}".format(
            item, expected
        )


def random_manifest():
    rand = random.Random(12345)
    return {f"pct {n}": rand.randint(1, 10) for n in range(rand.randint(1, 10))}


def test_ballot_labels():
    for _ in range(100):
        manifest = random_manifest()
        sample = sampler.draw_sample(SEED, manifest, 100, 0)
        for (_, (batch, ballot_number), _) in sample:
            assert 1 <= ballot_number <= manifest[batch]


expected_sample = [
    ("0.000617786129909912", ("pct 2", 3), 1),
    ("0.002991631653037245", ("pct 3", 24), 1),
    ("0.012057030610635061", ("pct 1", 25), 1),
    ("0.017930028930651931", ("pct 4", 19), 1),
    ("0.025599454926985137", ("pct 3", 15), 1),
    ("0.045351055354441163", ("pct 1", 7), 1),
    ("0.063913979803461405", ("pct 1", 8), 1),
    ("0.064553852798863609", ("pct 1", 22), 1),
    ("0.078998835671540970", ("pct 1", 20), 1),
    ("0.090240829778172783", ("pct 3", 12), 1),
    ("0.096136506157297637", ("pct 1", 20), 2),
    ("0.104280162683637014", ("pct 4", 17), 1),
    ("0.108948480696023984", ("pct 1", 25), 2),
    ("0.111195681310332785", ("pct 1", 4), 1),
    ("0.114438612046531251", ("pct 4", 3), 1),
    ("0.130457464320709301", ("pct 2", 1), 1),
    ("0.133484785501449819", ("pct 1", 12), 1),
    ("0.134519219670087860", ("pct 3", 20), 1),
    ("0.135840440920085144", ("pct 3", 10), 1),
    ("0.138772253094235762", ("pct 4", 20), 1),
]

expected_macro_sample = [
    ("0.003875995", "pct 16", 1),
    ("0.011835450", "pct 2", 1),
    ("0.022865957", "pct 2", 2),
    ("0.035732442", "pct 3", 1),
    ("0.125751540", "pct 2", 3),
    ("0.136070319", "pct 18", 1),
    ("0.150306323", "pct 6", 1),
    ("0.176060218", "pct 4", 1),
    ("0.183200120", "pct 13", 1),
    ("0.191343085", "pct 18", 2),
]

expected_first_sample = [
    ("0.000617786129909912", ("pct 2", 3), 1),
    ("0.002991631653037245", ("pct 3", 24), 1),
    ("0.012057030610635061", ("pct 1", 25), 1),
    ("0.017930028930651931", ("pct 4", 19), 1),
    ("0.025599454926985137", ("pct 3", 15), 1),
    ("0.045351055354441163", ("pct 1", 7), 1),
    ("0.063913979803461405", ("pct 1", 8), 1),
    ("0.064553852798863609", ("pct 1", 22), 1),
    ("0.078998835671540970", ("pct 1", 20), 1),
    ("0.090240829778172783", ("pct 3", 12), 1),
]

expected_second_sample = [
    ("0.096136506157297637", ("pct 1", 20), 2),
    ("0.104280162683637014", ("pct 4", 17), 1),
    ("0.108948480696023984", ("pct 1", 25), 2),
    ("0.111195681310332785", ("pct 1", 4), 1),
    ("0.114438612046531251", ("pct 4", 3), 1),
    ("0.130457464320709301", ("pct 2", 1), 1),
    ("0.133484785501449819", ("pct 1", 12), 1),
    ("0.134519219670087860", ("pct 3", 20), 1),
    ("0.135840440920085144", ("pct 3", 10), 1),
    ("0.138772253094235762", ("pct 4", 20), 1),
]

expected_first_macro_sample = [
    ("0.003875995", "pct 16", 1),
    ("0.011835450", "pct 2", 1),
    ("0.022865957", "pct 2", 2),
    ("0.035732442", "pct 3", 1),
    ("0.125751540", "pct 2", 3),
]

expected_second_macro_sample = [
    ("0.136070319", "pct 18", 1),
    ("0.150306323", "pct 6", 1),
    ("0.176060218", "pct 4", 1),
    ("0.183200120", "pct 13", 1),
    ("0.191343085", "pct 18", 2),
]

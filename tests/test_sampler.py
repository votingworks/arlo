import pytest
from audits import sampler
from audits.sampler_contest import Contest

seed = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
risk_limit = 0.1


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

    yield batches


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

    yield Contest(name, info_dict)


def test_draw_sample():
    # Test getting a sample
    manifest = {
        "pct 1": 25,
        "pct 2": 25,
        "pct 3": 25,
        "pct 4": 25,
    }

    sample = sampler.draw_sample(seed, bravo_contests, manifest, 20)

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
    sample = sampler.draw_sample(seed, bravo_contests, manifest, 10)
    assert samp_size == len(sample), "Received sample of size {}, expected {}".format(
        samp_size, len(sample)
    )

    for i, item in enumerate(sample):
        expected = expected_first_sample[i]
        assert item == expected, "Draw sample failed: got {}, expected {}".format(
            item, expected
        )

    samp_size = 10
    sample = sampler.draw_sample(seed, bravo_contests, manifest, 10, num_sampled=10)
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
        seed, macro_contest, {}, 10, batch_results=macro_batches
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
        seed, macro_contest, {}, samp_size, batch_results=macro_batches
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
        seed, macro_contest, {}, samp_size, num_sampled=5, batch_results=macro_batches
    )
    assert samp_size == len(sample), "Received sample of size {}, expected {}".format(
        samp_size, len(sample)
    )
    for i, item in enumerate(sample):
        expected = expected_second_macro_sample[i]
        assert item == expected, "Draw sample failed: got {}, expected {}".format(
            item, expected
        )


bravo_contests = {
    "test1": {"cand1": 600, "cand2": 400, "ballots": 1000, "numWinners": 1},
    "test2": {
        "cand1": 600,
        "cand2": 200,
        "cand3": 100,
        "ballots": 900,
        "numWinners": 1,
    },
    "test3": {"cand1": 100, "ballots": 100, "numWinners": 1},
    "test4": {"cand1": 100, "ballots": 100, "numWinners": 1},
    "test5": {"cand1": 500, "cand2": 500, "ballots": 1000, "numWinners": 1},
    "test6": {
        "cand1": 300,
        "cand2": 200,
        "cand3": 200,
        "ballots": 1000,
        "numWinners": 1,
    },
    "test7": {
        "cand1": 300,
        "cand2": 200,
        "cand3": 100,
        "ballots": 700,
        "numWinners": 2,
    },
    "test8": {
        "cand1": 300,
        "cand2": 300,
        "cand3": 100,
        "ballots": 700,
        "numWinners": 2,
    },
    "test9": {"cand1": 300, "cand2": 200, "ballots": 700, "numWinners": 2},
    "test10": {
        "cand1": 600,
        "cand2": 300,
        "cand3": 100,
        "ballots": 1000,
        "numWinners": 2,
    },
}

expected_sample = [
    ("0.000617786", ("pct 2", 3), 1),
    ("0.002991631", ("pct 3", 24), 1),
    ("0.017930028", ("pct 4", 19), 1),
    ("0.025599454", ("pct 3", 15), 1),
    ("0.045351055", ("pct 1", 7), 1),
    ("0.063913979", ("pct 1", 8), 1),
    ("0.064553852", ("pct 1", 22), 1),
    ("0.078998835", ("pct 1", 20), 1),
    ("0.090240829", ("pct 3", 12), 1),
    ("0.096136506", ("pct 1", 20), 2),
    ("0.104280162", ("pct 4", 17), 1),
    ("0.111195681", ("pct 1", 4), 1),
    ("0.114438612", ("pct 4", 3), 1),
    ("0.130457464", ("pct 2", 1), 1),
    ("0.133484785", ("pct 1", 12), 1),
    ("0.134519219", ("pct 3", 20), 1),
    ("0.135840440", ("pct 3", 10), 1),
    ("0.138772253", ("pct 4", 20), 1),
    ("0.145377629", ("pct 2", 9), 1),
    ("0.146681466", ("pct 1", 20), 3),
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
    ("0.000617786", ("pct 2", 3), 1),
    ("0.002991631", ("pct 3", 24), 1),
    ("0.017930028", ("pct 4", 19), 1),
    ("0.025599454", ("pct 3", 15), 1),
    ("0.045351055", ("pct 1", 7), 1),
    ("0.063913979", ("pct 1", 8), 1),
    ("0.064553852", ("pct 1", 22), 1),
    ("0.078998835", ("pct 1", 20), 1),
    ("0.090240829", ("pct 3", 12), 1),
    ("0.096136506", ("pct 1", 20), 2),
]

expected_second_sample = [
    ("0.104280162", ("pct 4", 17), 1),
    ("0.111195681", ("pct 1", 4), 1),
    ("0.114438612", ("pct 4", 3), 1),
    ("0.130457464", ("pct 2", 1), 1),
    ("0.133484785", ("pct 1", 12), 1),
    ("0.134519219", ("pct 3", 20), 1),
    ("0.135840440", ("pct 3", 10), 1),
    ("0.138772253", ("pct 4", 20), 1),
    ("0.145377629", ("pct 2", 9), 1),
    ("0.146681466", ("pct 1", 20), 3),
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

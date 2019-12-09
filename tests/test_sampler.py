import pytest
import math
import numpy as np

from sampler import Sampler

@pytest.fixture
def sampler():
    seed = '12345678901234567890abcdefghijklmnopqrstuvwxyz😊'

    risk_limit = .1
    contests = {
        'test1': {
            'cand1': 600,
            'cand2': 400,
            'ballots': 1000,
            'numWinners': 1
        },
        'test2': {
            'cand1': 600,
            'cand2': 200,
            'cand3': 100,
            'ballots': 900,
            'numWinners': 1
        },
        'test3': {
            'cand1': 100,
            'ballots': 100,
            'numWinners': 1
        },
        'test4': {
            'cand1': 100,
            'ballots': 100,
            'numWinners': 1
        },
        'test5': {
            'cand1' : 500,
            'cand2': 500,
            'ballots': 1000,
            'numWinners': 1
        },
        'test6': {
            'cand1': 300,
            'cand2': 200,
            'cand3': 200,
            'ballots': 1000,
            'numWinners': 1
        },
        'test7': {
            'cand1': 300,
            'cand2': 200,
            'cand3': 100,
            'ballots': 700,
            'numWinners': 2
        },
        'test7': {
            'cand1': 300,
            'cand2': 200,
            'cand3': 100,
            'ballots': 700,
            'numWinners': 2

        },
        'test8': {
            'cand1': 300,
            'cand2': 300,
            'cand3': 100,
            'ballots': 700,
            'numWinners': 2

        },
        'test9': {
            'cand1': 300,
            'cand2': 200,
            'ballots': 700,
            'numWinners': 2
        },
        'test10': {
            'cand1': 600,
            'cand2': 300,
            'cand3': 100,
            'ballots': 1000,
            'numWinners': 2
        },
    }



    yield Sampler('BRAVO', seed, risk_limit, contests)


def test_macro_error():
    with pytest.raises(Exception) as e:
        Sampler('MACRO', 0, 0, {})
        
        assert 'Must have batch-level results to use MACRO' in e.value

def test_draw_sample(sampler):
    # Test getting a sample
    manifest = {
        'pct 1': 25,
        'pct 2': 25,
        'pct 3': 25,
        'pct 4': 25,
    }

    sample = sampler.draw_sample(manifest, 20)

    for i, item in enumerate(sample):
        expected = expected_sample[i]
        assert item == expected, 'Draw sample failed: got {}, expected {}'.format(item, expected)


def test_draw_more_samples(sampler):
    # Test getting a sample
    manifest = {
        'pct 1': 25,
        'pct 2': 25,
        'pct 3': 25,
        'pct 4': 25,
    }

    samp_size = 10
    sample = sampler.draw_sample(manifest, 10)
    assert samp_size == len(sample), 'Received sample of size {}, expected {}'.format(samp_size, len(sample))

    for i, item in enumerate(sample):
        expected = expected_first_sample[i]
        assert item == expected, 'Draw sample failed: got {}, expected {}'.format(item, expected)

    samp_size = 10
    sample = sampler.draw_sample(manifest, 10, 10)
    assert samp_size == len(sample), 'Received sample of size {}, expected {}'.format(samp_size, len(sample))
    for i, item in enumerate(sample):
        expected = expected_second_sample[i]
        assert item == expected, 'Draw sample failed: got {}, expected {}'.format(item, expected)

        

expected_sample = [
    ('pct 1', 4),
    ('pct 1', 7),
    ('pct 1', 8),
    ('pct 1', 12),
    ('pct 1', 20),
    ('pct 1', 20),
    ('pct 1', 20),
    ('pct 1', 22),
    ('pct 2', 1),
    ('pct 2', 3),
    ('pct 2', 9),
    ('pct 3', 10),
    ('pct 3', 12),
    ('pct 3', 15),
    ('pct 3', 20),
    ('pct 3', 24),
    ('pct 4', 3),
    ('pct 4', 17),
    ('pct 4', 19),
    ('pct 4', 20)
]

expected_first_sample = [
    ('pct 1', 7),
    ('pct 1', 8),
    ('pct 1', 20),
    ('pct 1', 20),
    ('pct 1', 22),
    ('pct 2', 3),
    ('pct 3', 12),
    ('pct 3', 15),
    ('pct 3', 24),
    ('pct 4', 19)
]

expected_second_sample = [
    ('pct 1', 4),
    ('pct 1', 12),
    ('pct 1', 20),
    ('pct 2', 1),
    ('pct 2', 9),
    ('pct 3', 10),
    ('pct 3', 20),
    ('pct 4', 3),
    ('pct 4', 17),
    ('pct 4', 20)
]

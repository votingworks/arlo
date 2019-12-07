import pytest
import math
import numpy as np

from sampler import Sampler

@pytest.fixture
def bravo_sampler():
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

@pytest.fixture
def macro_sampler():
    seed = '12345678901234567890abcdefghijklmnopqrstuvwxyz😊'

    risk_limit = .1
    contests = {
        'test1': {
            'cand1': 600,
            'cand2': 400,
            'ballots': 1000,
            'numWinners': 1
        },
    }

    batches = {}

    # 10 batches will have max error of .08
    for i in range(10):
        batches['pct {}'.format(i)] = {
            'test1': {
                'cand1': 40,
                'cand2': 10,
                'ballots': 50
            }
        }
        # 10 batches will have max error of .04
    for i in range(11, 20):
        batches['pct {}'.format(i)] = {
            'test1': {
                'cand1': 20,
                'cand2': 30,
                'ballots': 50
            }
        }

    yield Sampler('MACRO', seed, risk_limit, contests, batches)

def test_macro_error():
    with pytest.raises(Exception) as e:
        Sampler('MACRO', 0, 0, {})
        
        assert 'Must have batch-level results to use MACRO' in e.value

def test_draw_sample(bravo_sampler):
    # Test getting a sample
    manifest = {
        'pct 1': 25,
        'pct 2': 25,
        'pct 3': 25,
        'pct 4': 25,
    }

    sample = bravo_sampler.draw_sample(manifest, 20)

    for i, item in enumerate(sample):
        expected = expected_sample[i]
        assert item == expected, 'Draw sample failed: got {}, expected {}'.format(item, expected)


def test_draw_more_samples(bravo_sampler):
    # Test getting a sample
    manifest = {
        'pct 1': 25,
        'pct 2': 25,
        'pct 3': 25,
        'pct 4': 25,
    }

    samp_size = 10
    sample = bravo_sampler.draw_sample(manifest, 10)
    assert samp_size == len(sample), 'Received sample of size {}, expected {}'.format(samp_size, len(sample))

    for i, item in enumerate(sample):
        expected = expected_first_sample[i]
        assert item == expected, 'Draw sample failed: got {}, expected {}'.format(item, expected)

    samp_size = 10
    sample = bravo_sampler.draw_sample(manifest, 10, 10)
    assert samp_size == len(sample), 'Received sample of size {}, expected {}'.format(samp_size, len(sample))
    for i, item in enumerate(sample):
        expected = expected_second_sample[i]
        assert item == expected, 'Draw sample failed: got {}, expected {}'.format(item, expected)

        
def test_draw_macro_sample(macro_sampler):
    # Test getting a sample
    sample = macro_sampler.draw_sample({}, 10)

    for i, item in enumerate(sample):
        expected = expected_macro_sample[i]
        assert item == expected, 'Draw sample failed: got {}, expected {}'.format(item, expected)

def test_draw_more_macro_samples(macro_sampler):
    # Test getting a sample
    samp_size = 5
    sample = macro_sampler.draw_sample({}, 5)
    assert samp_size == len(sample), 'Received sample of size {}, expected {}'.format(samp_size, len(sample))

    for i, item in enumerate(sample):
        expected = expected_first_macro_sample[i]
        assert item == expected, 'Draw sample failed: got {}, expected {}'.format(item, expected)

    samp_size = 5
    sample = macro_sampler.draw_sample({}, 5, 5)
    assert samp_size == len(sample), 'Received sample of size {}, expected {}'.format(samp_size, len(sample))
    for i, item in enumerate(sample):
        expected = expected_second_macro_sample[i]
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

expected_macro_sample = [
    'pct 13',
    'pct 16',
    'pct 18',
    'pct 18',
    'pct 2',
    'pct 2',
    'pct 2',
    'pct 3',
    'pct 4',
    'pct 6'
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

expected_first_macro_sample = [
    'pct 16',
    'pct 2',
    'pct 2',
    'pct 2',
    'pct 3',
]


expected_second_macro_sample = [
    'pct 13',
    'pct 18',
    'pct 18',
    'pct 4',
    'pct 6',
]

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
    ('0.006731400', ('pct 2', 21), 1), 
    ('0.026790460', ('pct 2', 15), 1), 
    ('0.045368037', ('pct 4', 14), 1), 
    ('0.047744532', ('pct 1', 19), 1),
    ('0.050480775', ('pct 1', 22), 1),
    ('0.054905982', ('pct 4', 7), 1),
    ('0.057913497', ('pct 2', 6), 1),
    ('0.071305688', ('pct 1', 4), 1),
    ('0.081167466', ('pct 2', 2), 1), 
    ('0.089358944', ('pct 4', 11), 1),
    ('0.107558931', ('pct 4', 19), 1),
    ('0.120520583', ('pct 2', 23), 1),
    ('0.128325763', ('pct 2', 5), 1),
    ('0.134780861', ('pct 2', 6), 2),
    ('0.145768338', ('pct 4', 21), 1), 
    ('0.145821244', ('pct 1', 24), 1),
    ('0.153203668', ('pct 4', 18), 1),
    ('0.158020947', ('pct 1', 21), 1),
    ('0.168479164', ('pct 4', 23), 1),
    ('0.170505934', ('pct 1', 12), 1)
]

expected_first_sample = [
    ('0.006731400', ('pct 2', 21), 1), 
    ('0.026790460', ('pct 2', 15), 1), 
    ('0.045368037', ('pct 4', 14), 1), 
    ('0.047744532', ('pct 1', 19), 1),
    ('0.050480775', ('pct 1', 22), 1),
    ('0.054905982', ('pct 4', 7), 1),
    ('0.057913497', ('pct 2', 6), 1),
    ('0.071305688', ('pct 1', 4), 1),
    ('0.081167466', ('pct 2', 2), 1), 
    ('0.089358944', ('pct 4', 11), 1),
]

expected_second_sample = [
    ('0.107558931', ('pct 4', 19), 1),
    ('0.120520583', ('pct 2', 23), 1),
    ('0.128325763', ('pct 2', 5), 1),
    ('0.134780861', ('pct 2', 6), 2),
    ('0.145768338', ('pct 4', 21), 1), 
    ('0.145821244', ('pct 1', 24), 1),
    ('0.153203668', ('pct 4', 18), 1),
    ('0.158020947', ('pct 1', 21), 1),
    ('0.168479164', ('pct 4', 23), 1),
    ('0.170505934', ('pct 1', 12), 1)
]

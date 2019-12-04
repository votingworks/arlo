import pytest
import math
import numpy as np

from sampler import Sampler

@pytest.fixture
def sampler():
    seed = '12345678901234567890abcdefghijklmnopqrstuvwxyz😊'

    risk_limit = .1
    contests = {
        'Contest A': {
            'winner': 60000,
            'loser': 54000,
            'ballots': 120000,
            'winners': 1,
        },
        'Contest B': {
            'winner': 30000,
            'loser': 24000,
            'ballots': 60000,
            'winners': 1,
        },
        'Contest C': {
            'winner': 18000,
            'loser': 12600,
            'ballots': 36000,
            'winners': 1,
        },
    }

    batches = {}
    for i in range(200):
        batches['Batch {}'.format(i)] = {
            'Contest A': {
                'winner': 200,
                'loser': 180,
                'ballots': 400,
                'winners': 1
            },
        }

        batches['Batch {} AV'.format(i)] = {
            'Contest A': {
                'winner': 100,
                'loser': 90,
                'ballots': 200,
                'winners': 1
            },
        }

    for i in range(100):
        batches['Batch {}'.format(i)]['Contest B'] = {
            'winner': 200,
            'loser': 160,
            'ballots': 400,
            'winners': 1
        }
        batches['Batch {} AV'.format(i)]['Contest B'] =  {
            'winner': 100,
            'loser': 80,
            'ballots': 200,
            'winners': 1
        }

    for i in range(60):
        batches['Batch {}'.format(i)]['Contest C'] = {
            'winner': 200,
            'loser': 140,
            'ballots': 400,
            'winners': 1
        }
        batches['Batch {} AV'.format(i)]['Contest C'] = {
            'winner': 100,
            'loser': 70,
            'ballots': 200,
            'winners': 1
        }


    yield Sampler('MACRO', seed, risk_limit, contests, batches)


def test_macro_error():
    """
    make sure sampler throws an error if we don't give it batches for MACRO
    """

    assert False, 'Not implemented'

def test_max_error(sampler):

    expected_up = 0.0852 # Per the MACRO paper 

    for batch in sampler.batch_results:
        computed_up = sampler.audit.compute_max_error(sampler.contests, sampler.margins, sampler.batch_results[batch])

        delta = computed_up - expected_up
        assert delta < 0.001, \
                'Got an incorrect maximum possible overstatement: {} should be {}'.format(computed_up, expected_up)

def test_get_sample_sizes(sampler):
    expected = 36
    computed = sampler.get_sample_sizes({})
    assert computed == expected, 'Failed to compute sample sized: got {}, expected {}'.format(computed, expected)





import pytest
import numpy as np

from sampler import Sampler

@pytest.fixture
def sampler():
    seed = 12345678901234567890
    risk_limit = .1
    contests = {
        'test1': {
            'cand1': 600,
            'cand2': 400,
            'ballots': 1000
        },
        'test2': {
            'cand1': 600,
            'cand2': 200,
            'cand3': 100,
            'ballots': 900
        },
        'test3': {
            'cand1': 100,
            'ballots': 100
        }

    }

    yield Sampler(seed, risk_limit, contests)

def test_compute_margins(sampler):
    # Test margins
    true_margins = {
        'test1': { 
            'p_w': .6,
            'p_r': .4,
            's_w': .6
        },
        'test2' : {
            'p_w' : .75,
            'p_r' : .25,
            's_w': 2/3,
        },
        'test3': {
            'p_w' : 1,
            'p_r' : 0,
            's_w' : 1
        }
    }

    margins = sampler.compute_margins()
    for contest in margins:
        expected =  true_margins[contest]['p_w']
        computed = margins[contest]['p_w']
        assert expected == computed, 'p_w failed: got {}, expected {}'.format(computed, expected)
        expected =  true_margins[contest]['p_r']
        computed = margins[contest]['p_r']
        assert expected == computed, 'p_r failed: got {}, expected {}'.format(computed, expected)
        expected =  true_margins[contest]['s_w']
        computed = margins[contest]['s_w']
        assert expected == computed, 's_w failed: got {}, expected {}'.format(computed, expected)

def test_asn(sampler):
    # Test ASN computation

    true_asns = {
        'test1': 119,
        'test2': 22,
        'test3': 0,
    }

    computed_asns = sampler.get_asns()
    for contest in true_asns:
        expected = true_asns[contest]
        computed = computed_asns[contest]

        assert expected == computed, 'asn failed: got {}, expected {}'.format(computed, expected)

def test_simulate_bravo(sampler):
    # Test bravo sample simulator

    expected_mean1 = 118
    computed_mean1 = np.mean(sampler.simulate_bravo(10000, .6))
    delta = expected_mean1 - computed_mean1
    assert delta > -5, 'bravo_simulator failed: got {}, expected {}'.format(computed_mean1, expected_mean1)
    assert delta < 5, 'bravo_simulator failed: got {}, expected {}'.format(computed_mean1, expected_mean1)

def test_get_sample_sizes(sampler):
    # Test retrieving menu of sample sizes

    true_sample_sizes = {
        'test1': {
            'asn': 119,
            '70%': 130,
            '80%': 170,
            '90%': 243,
        }, 
        'test2': {
            'asn': 22,
            '70%': 19,
            '80%': 24,
            '90%': 38,
        },
        'test3': {
            'asn': 0,
            '70%': 0,
            '80%': 0,
            '90%': 0,
        },
    }

    computed_samples = sampler.get_sample_sizes()
    for contest in computed_samples:
        for key in true_sample_sizes[contest]:
            expected =  true_sample_sizes[contest][key]
            computed = computed_samples[contest][key]
            diff = expected - computed
            assert abs(diff) < 10 , '{} sample size for {} failed: got {}, expected {}'.format(key, contest, computed, expected)



def test_draw_sample(sampler):
    # Test getting a sample

    assert False, 'not implemented'
def test_compute_risk(sampler):
    # Test computing sample
    assert False, 'not implemented'

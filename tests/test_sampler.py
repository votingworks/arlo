import pytest
import math
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
            'ballots': 1000,
            'winners': 1
        },
        'test2': {
            'cand1': 600,
            'cand2': 200,
            'cand3': 100,
            'ballots': 900,
            'winners': 1
        },
        'test3': {
            'cand1': 100,
            'ballots': 100,
            'winners': 1
        },
        'test4': {
            'cand1': 100,
            'ballots': 100,
            'winners': 1
        },
        'test5': {
            'cand1' : 500,
            'cand2': 500,
            'ballots': 1000,
            'winners': 1
        },
        'test6': {
            'cand1': 300,
            'cand2': 200,
            'cand3': 200,
            'ballots': 1000,
            'winners': 1
        }
    }



    yield Sampler(seed, risk_limit, contests)

def test_compute_margins(sampler):
    # Test margins
    true_margins = {
        'test1': { 
            'winners': {
                'cand1': {
                    'p_w': .6,
                    's_w': .6,
                    'swl': {'cand2': .6}
                }
            },
            'losers': {
                'cand2': {
                    'p_l': .4,
                    's_l': .4
                }
            }
        },
        'test2' : {
            'winners': {
                'cand1': {
                    'p_w': 2/3,
                    's_w': 2/3,
                    'swl': {
                        'cand2': 6/8,
                        'cand3': 6/7

                    }
                }
            },
            'losers': {
                'cand2': {
                    'p_l': 2/9,
                    's_l': 2/9
                },
                'cand3': {
                    'p_l': 1/9,
                    's_l': 1/9
                }
                
            }
        },
        'test3': {
            'winners': {
                'cand1': {
                    'p_w': 1,
                    's_w': 1,
                    'swl': {}
                }
            },
            'losers': {}
        },
        'test4': {
            'winners': {
                'cand1': {
                    'p_w': 1,
                    's_w': 1,
                    'swl': {}
                }
            },
            'losers': {}
        },
        'test5': {
            'winners': {
                'cand1': {
                    'p_w': .5,
                    's_w': .5,
                    'swl': {
                        'cand2': .5
                    }
                }
            },
            'losers': {
                'cand2': {
                    'p_l': .5,
                    's_l': .5
                }
            }
        },
        'test6': {
            'winners': {
                'cand1': {
                    'p_w': .3,
                    's_w': 300/700,
                    'swl': {
                        'cand2': 300/(300+200),
                        'cand3': 300/(300+200)
                    }
                }
            },
            'losers': {
                'cand2': {
                    'p_l': .2,
                    's_l': 200/700
                },
                'cand3': {
                    'p_l': .2,
                    's_l': 200/700
                }

            }
        }
    }

    margins = sampler.compute_margins()
    for contest in margins:
        true_margins_for_contest = true_margins[contest]
        computed_margins_for_contest = margins[contest]

        for winner in true_margins_for_contest['winners']:
            expected = round(true_margins_for_contest['winners'][winner]['p_w'], 5)
            computed = round(computed_margins_for_contest['winners'][winner]['p_w'], 5)
            assert expected == computed, 'p_w failed: got {}, expected {}'.format(computed, expected)

            expected = round(true_margins_for_contest['winners'][winner]['s_w'], 5)
            computed = round(computed_margins_for_contest['winners'][winner]['s_w'], 5)
            assert expected == computed, 's_w failed: got {}, expected {}'.format(computed, expected)

            for cand in true_margins_for_contest['winners'][winner]['swl']:
                expected = round(true_margins_for_contest['winners'][winner]['swl'][cand], 5)
                computed = round(computed_margins_for_contest['winners'][winner]['swl'][cand], 5)
                assert expected == computed, 'swl failed: got {}, expected {}'.format(computed, expected)


        for loser in true_margins_for_contest['losers']:
            expected = round(true_margins_for_contest['losers'][loser]['p_l'], 5)
            computed = round(computed_margins_for_contest['losers'][loser]['p_l'], 5)
            assert expected == computed, 'p_l failed: got {}, expected {}'.format(computed, expected)

            expected = round(true_margins_for_contest['losers'][loser]['s_l'], 5)
            computed = round(computed_margins_for_contest['losers'][loser]['s_l'], 5)
            assert expected == computed, 's_l failed: got {}, expected {}'.format(computed, expected)
         


def test_asn(sampler):
    # Test ASN computation

    true_asns = {
        'test1': 119,
        'test2': 22,
        'test3': 0,
        'test4': 0,
        'test5': 1000,
        'test6': 238
    }

    computed_asns = sampler.get_asns()
    for contest in true_asns:
        expected = true_asns[contest]
        computed = computed_asns[contest]

        assert expected == computed, 'asn failed: got {}, expected {}'.format(computed, expected)

def test_bravo_sample_size(sampler):
    # Test bravo sample simulator
    # Test without sample
    expected_size1 = 1599
    r0_sample_win = 0    
    r0_sample_rup = 0

    computed_size1 = math.ceil(sampler.bravo_sample_size(
                                    p_w=.4, 
                                    p_r=.32,
                                    sample_w=r0_sample_win, 
                                    sample_r=r0_sample_rup,
                                    p_completion=.9))
    delta = expected_size1 - computed_size1

    assert not delta, 'bravo_sample_size failed: got {}, expected {}'.format(computed_size1, expected_size1)
    
    expected_size1 = 6067

    computed_size1 = math.ceil(sampler.bravo_sample_size(
                                    p_w=.36, 
                                    p_r=.32,
                                    sample_w=r0_sample_win, 
                                    sample_r=r0_sample_rup,
                                    p_completion=.9))
    delta = expected_size1 - computed_size1

    assert not delta, 'bravo_sample_size failed: got {}, expected {}'.format(computed_size1, expected_size1)

    expected_size1 = 2475

    computed_size1 = math.ceil(sampler.bravo_sample_size(
                                    p_w=.36, 
                                    p_r=.32,
                                    sample_w=r0_sample_win, 
                                    sample_r=r0_sample_rup,
                                    p_completion=.6))
    delta = expected_size1 - computed_size1

    assert not delta, 'bravo_sample_size failed: got {}, expected {}'.format(computed_size1, expected_size1)

    expected_size1 = 5657

    computed_size1 = math.ceil(sampler.bravo_sample_size(
                                    p_w=.52, 
                                    p_r=.47,
                                    sample_w=r0_sample_win, 
                                    sample_r=r0_sample_rup,
                                    p_completion=.9))
    delta = expected_size1 - computed_size1

    assert not delta, 'bravo_sample_size failed: got {}, expected {}'.format(computed_size1, expected_size1)

def test_bravo_sample_size_round1_finish(sampler):
    # Guarantee that the audit should have finished
    r0_sample_win = 10000
    r0_sample_rup = 0
    expected_size1 = 0

    computed_size1 = math.ceil(sampler.bravo_sample_size(
                                    p_w=.52, 
                                    p_r=.47,
                                    sample_w=r0_sample_win, 
                                    sample_r=r0_sample_rup,
                                    p_completion=.9))
    delta = expected_size1 - computed_size1

    assert not delta, 'bravo_sample_size failed: got {}, expected {}'.format(computed_size1, expected_size1)

def test_bravo_sample_size_round1_incomplete(sampler):
    expected_size1 = 2636
    r0_sample_win = 2923
    r0_sample_rup = 2735

    computed_size1 = math.ceil(sampler.bravo_sample_size(
                                    p_w=.52, 
                                    p_r=.47,
                                    sample_w=r0_sample_win, 
                                    sample_r=r0_sample_rup,
                                    p_completion=.9))
    delta = expected_size1 - computed_size1

    assert not delta, 'bravo_sample_size failed: got {}, expected {}'.format(computed_size1, expected_size1)
def test_bravo_asn_prob(sampler):
    # Test bravo sample simulator
    # Test without sample
    expected_prob1 = .52
    r0_sample_win = round0_sample_results['test1']['cand1']
    r0_sample_rup = round0_sample_results['test1']['cand2']

    computed_prob1 = round(sampler.bravo_asn_prob(
                                    p_w=.6, 
                                    p_r=.4,
                                    sample_w=r0_sample_win, 
                                    sample_r=r0_sample_rup,
                                    asn = 119), 2)
    delta = expected_prob1 - computed_prob1

    assert not delta, 'bravo_simulator failed: got {}, expected {}'.format(computed_prob1, expected_prob1)


def test_get_sample_sizes(sampler):
    # Test retrieving menu of sample sizes
    computed_samples = sampler.get_sample_sizes(round0_sample_results)
    print(computed_samples)
    for contest in computed_samples:
        for key in true_sample_sizes[contest]:
            if key == 'asn': 
                # Check probs:
                expected_prob = true_sample_sizes[contest][key]['prob']
                computed_prob = round(computed_samples[contest][key]['prob'], 2)

                assert expected_prob == computed_prob, '{} ASN probabability check for {} failed: got {}, expected {}'.format(key, contest, computed_prob, expected_prob)

                expected = true_sample_sizes[contest][key]['size']
                computed = computed_samples[contest][key]['size']
            else:
                expected =  true_sample_sizes[contest][key]
                computed = computed_samples[contest][key]
            diff = expected - computed
            # TODO are these tolerances acceptable?
            assert not diff , '{} sample size for {} failed: got {}, expected {}'.format(key, contest, computed, expected)



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

def test_compute_risk(sampler):
    # Test computing sample
    expected_Ts = {
        'test1': .07,
        'test2': 10.38,
        'test3': 1,
        'test4': 0,
        'test5': 1,
        'test6': 0.08,
    }

    expected_decisions = {
        'test1': True,
        'test2': False,
        'test3': False,
        'test4': True,
        'test5': False,
        'test6': True,
    }

    for contest, sample in round1_sample_results.items():
        T, decision = sampler.compute_risk(contest, sample)
        expected_T = expected_Ts[contest]
        diff = T - expected_T 
        assert abs(diff) < .01, 'Risk compute for {} failed! Expected {}, got {}'.format(contest, expected_Ts[contest], T)
        
        expected_decision = expected_decisions[contest]
        assert decision == expected_decision, 'Risk decision for {} failed! Expected {}, got{}'.format(contest, expected_decision, decision)
        
        

# Useful test data
round0_sample_results = {
    'test1': {
        'cand1': 0,
        'cand2': 0,
    },
    'test2': {
        'cand1': 0,
        'cand2': 0,
        'cand3': 0,
    },
    'test3': {
        'cand1': 0,
    },
    'test4': {
        'cand1': 0,
    },
    'test5': {
        'cand1': 0,
        'cand2': 0,
    },
    'test6': {
        'cand1': 0,
        'cand2': 0,
        'cand3': 0
    }
}


round1_sample_results = {
    'test1': {
        'cand1': 72,
        'cand2': 47
    },
    'test2': {
        'cand1': 25,
        'cand2': 18,
        'cand3': 5,
    },
    'test3': {
        'cand1': 0
    },
    'test4': {
        'cand1': 100
    },
    'test5': {
        'cand1': 500,
        'cand2': 500,
    },
    'test6': {
        'cand1': 72,
        'cand2': 48,
        'cand3': 48
    }
}


expected_sample = [
    ('pct 1', 4),
    ('pct 1', 12),
    ('pct 1', 19),
    ('pct 1', 21),
    ('pct 1', 22),
    ('pct 1', 24),
    ('pct 2', 2),
    ('pct 2', 5),
    ('pct 2', 6),
    ('pct 2', 6),
    ('pct 2', 15),
    ('pct 2', 21),
    ('pct 2', 23),
    ('pct 4', 7),
    ('pct 4', 11),
    ('pct 4', 14),
    ('pct 4', 18),
    ('pct 4', 19),
    ('pct 4', 21),
    ('pct 4', 23),
]

expected_first_sample = [
    ('pct 1', 4),
    ('pct 1', 19),
    ('pct 1', 22),
    ('pct 2', 2),
    ('pct 2', 6),
    ('pct 2', 15),
    ('pct 2', 21),
    ('pct 4', 7),
    ('pct 4', 11),
    ('pct 4', 14),
]

expected_second_sample = [
    ('pct 1', 12),
    ('pct 1', 21),
    ('pct 1', 24),
    ('pct 2', 5),
    ('pct 2', 6),
    ('pct 2', 23),
    ('pct 4', 18),
    ('pct 4', 19),
    ('pct 4', 21),
    ('pct 4', 23),
]
true_sample_sizes = {
    'test1': {
        'asn': {
            'size': 119,
            'prob': .52
        },
        .7: 184,
        .8: 244,
        .9: 351,
    }, 
    'test2': {
        'asn': {
            'size':22,
            'prob': .60
        },
        .7: 32,
        .8: 41,
        .9: 57,
    },
    'test3': {
        'asn': {
            'size': 0,
            'prob': 0
        },
        .7: 0,
        .8: 0,
        .9: 0,
    },
    'test4': {
        'asn': {
            'size': 0,
            'prob': 0
        },
        .7: 0,
        .8: 0,
        .9: 0,
    },
    'test5': {
        'asn': {
            'size': 1000,
            'prob': 1
        },
        .7: 1000,
        .8: 1000,
        .9: 1000
    },
    'test6': {
        'asn': {
            'size': 238,
            'prob': .79 # Note that this is an artifact of two-way math, and 
                        # should change once we go to n-winner math
        },
        .7: 368,
        .8: 488,
        .9: 702
        
    }
}

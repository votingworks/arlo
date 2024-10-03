# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_clearballot_cvr_upload 1'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-1',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-2',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-3',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-2-1',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-2-2',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-2-3',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-1-1',
        'interpretations': '1,0,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-1-2',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-1-3',
        'interpretations': '1,0,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-1',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-2',
        'interpretations': '1,1,1,1,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-4',
        'interpretations': ',,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-5',
        'interpretations': ',,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-6',
        'interpretations': ',,1,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_clearballot_cvr_upload 2'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 13
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 6
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 7
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 2
    }
}

snapshots['test_cvrs_counting_group 1'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-1',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-2',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-3',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-1',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-2',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-3',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '2-1-1',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '2-1-2',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '2-1-3',
        'interpretations': '1,0,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-1',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-2',
        'interpretations': '1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-3',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-4',
        'interpretations': ',,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-5',
        'interpretations': ',,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 6,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-6',
        'interpretations': ',,1,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_cvrs_counting_group 2'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 4
            }
        },
        'total_ballots_cast': 12,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 15
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 7
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 8
            }
        },
        'total_ballots_cast': 15,
        'votes_allowed': 2
    }
}

snapshots['test_cvrs_newlines 1'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-1',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-2',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-3',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-1',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-2',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-3',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '2-1-1',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '2-1-2',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '2-1-3',
        'interpretations': '1,0,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-1',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-2',
        'interpretations': '1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-3',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-4',
        'interpretations': ',,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-5',
        'interpretations': ',,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 6,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-6',
        'interpretations': ',,1,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_cvrs_newlines 2'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 4
            }
        },
        'total_ballots_cast': 12,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 15
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 7
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 8
            }
        },
        'total_ballots_cast': 15,
        'votes_allowed': 2
    }
}

snapshots['test_dominion_cvr_unique_voting_identifier 1'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-1',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-2',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-3',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-1',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-2',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-3',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '2-1-1',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '56_083-212',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '56_083-213',
        'interpretations': '1,0,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '56_083-221',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '56_083-222',
        'interpretations': '1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '56_083-223',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '56_083-224',
        'interpretations': ',,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '56_083-225',
        'interpretations': ',,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 6,
        'batch_name': 'BATCH2',
        'imprinted_id': '56_083-226',
        'interpretations': ',,1,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_dominion_cvr_unique_voting_identifier 2'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 4
            }
        },
        'total_ballots_cast': 12,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 15
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 7
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 8
            }
        },
        'total_ballots_cast': 15,
        'votes_allowed': 2
    }
}

snapshots['test_dominion_cvr_upload 1'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-1',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-2',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-3',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-1',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-2',
        'interpretations': '0,1,1,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-3',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '2-1-1',
        'interpretations': '1,0,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '2-1-2',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '2-1-3',
        'interpretations': '1,0,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-1',
        'interpretations': '1,0,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-2',
        'interpretations': '1,1,1,1,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-4',
        'interpretations': ',,1,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-5',
        'interpretations': ',,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '2-2-6',
        'interpretations': ',,1,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_dominion_cvr_upload 2'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 12
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 5
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 7
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 2
    }
}

snapshots['test_ess_cvr_upload 1'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '0001000415',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '0001000416',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '0001000417',
        'interpretations': '0,1,0,1,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '0001013415',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '0001013416',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '0001013417',
        'interpretations': 'u,u,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000171',
        'interpretations': '1,0,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000172',
        'interpretations': '0,1,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000173',
        'interpretations': '1,0,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000174',
        'interpretations': '0,1,0,0,1',
        'tabulator': '0002'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000175',
        'interpretations': '1,0,0,0,1',
        'tabulator': '0002'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003171',
        'interpretations': 'o,o,1,0,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003172',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003173',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0002'
    }
]

snapshots['test_ess_cvr_upload 2'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 6
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 6
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 8
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 4
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 2
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_ess_cvr_upload 3'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '0001000415',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '0001000416',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '0001000417',
        'interpretations': '0,1,0,1,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '0001013415',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '0001013416',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '0001013417',
        'interpretations': 'u,u,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000171',
        'interpretations': '1,0,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000172',
        'interpretations': '0,1,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000173',
        'interpretations': '1,0,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000174',
        'interpretations': '0,1,0,0,1',
        'tabulator': '0002'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000175',
        'interpretations': '1,0,0,0,1',
        'tabulator': '0002'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003171',
        'interpretations': 'o,o,1,0,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003172',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003173',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0002'
    }
]

snapshots['test_ess_cvr_upload 4'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 6
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 6
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 8
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 4
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 2
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_ess_cvr_upload 5'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000171',
        'interpretations': '1,0,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000172',
        'interpretations': '0,1,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000173',
        'interpretations': '1,0,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000174',
        'interpretations': '0,1,0,0,1',
        'tabulator': '0002'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000175',
        'interpretations': '1,0,0,0,1',
        'tabulator': '0002'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003172',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003173',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '02bc1dc7bc1e7774',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '039b31b93d9a8099',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '06348ce7b6d146d2',
        'interpretations': 'u,u,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH1',
        'imprinted_id': '09809965339bad95',
        'interpretations': 'o,o,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '19882855d197f6c2',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '1dd6b0ff8462558c',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '1f781b866b83de9b',
        'interpretations': '0,1,0,1,0',
        'tabulator': '0001'
    }
]

snapshots['test_ess_cvr_upload 6'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 6
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 6
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 8
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 4
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 2
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_ess_cvr_upload 7'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000171',
        'interpretations': '1,0,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000172',
        'interpretations': '0,1,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000173',
        'interpretations': '1,0,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000174',
        'interpretations': '0,1,0,0,1',
        'tabulator': '0002'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000175',
        'interpretations': '1,0,0,0,1',
        'tabulator': '0002'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003172',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003173',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '02bc1dc7bc1e7774',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '039b31b93d9a8099',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '06348ce7b6d146d2',
        'interpretations': 'u,u,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH1',
        'imprinted_id': '09809965339bad95',
        'interpretations': 'o,o,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '19882855d197f6c2',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '1dd6b0ff8462558c',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '1f781b866b83de9b',
        'interpretations': '0,1,0,1,0',
        'tabulator': '0001'
    }
]

snapshots['test_ess_cvr_upload 8'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 6
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 6
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 8
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 4
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 2
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_ess_cvr_upload_cvr_file_with_tabulator_cvr_column 1'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '0001000415',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '0001000416',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '0001000417',
        'interpretations': '0,1,0,1,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '0001013415',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '0001013416',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '0001013417',
        'interpretations': 'u,u,1,0,0',
        'tabulator': '0001'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000171',
        'interpretations': '1,0,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000172',
        'interpretations': '0,1,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000173',
        'interpretations': '1,0,0,1,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000174',
        'interpretations': '0,1,0,0,1',
        'tabulator': '0002'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '0002000175',
        'interpretations': '1,0,0,0,1',
        'tabulator': '0002'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003171',
        'interpretations': 'o,o,1,0,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003172',
        'interpretations': '0,1,1,0,0',
        'tabulator': '0002'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '0002003173',
        'interpretations': '1,0,1,0,0',
        'tabulator': '0002'
    }
]

snapshots['test_ess_cvr_upload_cvr_file_with_tabulator_cvr_column 2'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 6
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 6
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 8
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 4
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 2
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_hart_cvr_upload 1'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-1',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-2',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-3',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-1',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-2',
        'interpretations': '0,1,0,1,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-3',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH3',
        'imprinted_id': '1-3-1',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH3',
        'imprinted_id': '1-3-2',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH3',
        'imprinted_id': '1-3-3',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH4',
        'imprinted_id': '1-4-1',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH4',
        'imprinted_id': '1-4-2',
        'interpretations': '1,1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH4',
        'imprinted_id': '1-4-4',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH4',
        'imprinted_id': '1-4-5',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH4',
        'imprinted_id': '1-4-6',
        'interpretations': ',,0,0,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_hart_cvr_upload 2'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 6
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 3
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 3
            },
            'Write-In': {
                'column': 5,
                'num_votes': 1
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_hart_cvr_upload_with_duplicate_batch_names 1'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-01',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-02',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-03',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-04',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-05',
        'interpretations': '0,1,0,1,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-06',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-07',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-08',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-09',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-10',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-11',
        'interpretations': '1,1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-12',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-13',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-14',
        'interpretations': ',,0,0,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_hart_cvr_upload_with_duplicate_batch_names 2'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 6
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 3
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 3
            },
            'Write-In': {
                'column': 5,
                'num_votes': 1
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_hart_cvr_upload_with_duplicate_batch_names 3'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-01',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-02',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-03',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-04',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-05',
        'interpretations': '0,1,0,1,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-06',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-07',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-08',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-09',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-10',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-11',
        'interpretations': '1,1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-12',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-13',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-14',
        'interpretations': ',,0,0,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_hart_cvr_upload_with_duplicate_batch_names 4'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 6
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 3
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 3
            },
            'Write-In': {
                'column': 5,
                'num_votes': 1
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_hart_cvr_upload_with_duplicate_batch_names 5'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-1',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-2',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-1-3',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-1',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-2',
        'interpretations': '0,1,0,1,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-2-3',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-3-1',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-3-2',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': '1-3-3',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-4-1',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-4-2',
        'interpretations': '1,1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-4-4',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-4-5',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH2',
        'imprinted_id': '1-4-6',
        'interpretations': ',,0,0,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_hart_cvr_upload_with_duplicate_batch_names 6'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 6
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 3
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 3
            },
            'Write-In': {
                'column': 5,
                'num_votes': 1
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_hart_cvr_upload_with_scanned_ballot_information 1'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-01',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-02',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-03',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-04',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-05',
        'interpretations': '0,1,0,1,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-06',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-07',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-08',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-09',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-10',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-11',
        'interpretations': '1,1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-12',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-13',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-14',
        'interpretations': ',,0,0,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_hart_cvr_upload_with_scanned_ballot_information 10'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 6
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 3
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 3
            },
            'Write-In': {
                'column': 5,
                'num_votes': 1
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_hart_cvr_upload_with_scanned_ballot_information 2'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 6
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 3
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 3
            },
            'Write-In': {
                'column': 5,
                'num_votes': 1
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_hart_cvr_upload_with_scanned_ballot_information 3'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-01',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-02',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-03',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-04',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-05',
        'interpretations': '0,1,0,1,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-06',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-07',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-08',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-09',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-10',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-11',
        'interpretations': '1,1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-12',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-13',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-14',
        'interpretations': ',,0,0,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_hart_cvr_upload_with_scanned_ballot_information 4'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 6
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 3
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 3
            },
            'Write-In': {
                'column': 5,
                'num_votes': 1
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_hart_cvr_upload_with_scanned_ballot_information 5'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH3',
        'imprinted_id': '1-3-1',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH3',
        'imprinted_id': '1-3-2',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH3',
        'imprinted_id': '1-3-3',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH4',
        'imprinted_id': '1-4-1',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH4',
        'imprinted_id': '1-4-2',
        'interpretations': '1,1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH4',
        'imprinted_id': '1-4-4',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH4',
        'imprinted_id': '1-4-5',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH4',
        'imprinted_id': '1-4-6',
        'interpretations': ',,0,0,0,1',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-01',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-02',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-03',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-04',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-05',
        'interpretations': '0,1,0,1,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-06',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR1'
    }
]

snapshots['test_hart_cvr_upload_with_scanned_ballot_information 6'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 6
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 3
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 3
            },
            'Write-In': {
                'column': 5,
                'num_votes': 1
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_hart_cvr_upload_with_scanned_ballot_information 7'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-01',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-02',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-03',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-04',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-05',
        'interpretations': '0,1,0,1,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-06',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-07',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-08',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-09',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-10',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-11',
        'interpretations': '1,1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-12',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-13',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-14',
        'interpretations': ',,0,0,0,1',
        'tabulator': 'TABULATOR2'
    }
]

snapshots['test_hart_cvr_upload_with_scanned_ballot_information 8'] = {
    'Contest 1': {
        'choices': {
            'Choice 1-1': {
                'column': 0,
                'num_votes': 7
            },
            'Choice 1-2': {
                'column': 1,
                'num_votes': 3
            }
        },
        'total_ballots_cast': 11,
        'votes_allowed': 1
    },
    'Contest 2': {
        'choices': {
            'Choice 2-1': {
                'column': 2,
                'num_votes': 6
            },
            'Choice 2-2': {
                'column': 3,
                'num_votes': 3
            },
            'Choice 2-3': {
                'column': 4,
                'num_votes': 3
            },
            'Write-In': {
                'column': 5,
                'num_votes': 1
            }
        },
        'total_ballots_cast': 14,
        'votes_allowed': 1
    }
}

snapshots['test_hart_cvr_upload_with_scanned_ballot_information 9'] = [
    {
        'ballot_position': 1,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-01',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-02',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH1',
        'imprinted_id': 'unique-identifier-03',
        'interpretations': '0,1,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-04',
        'interpretations': '1,0,1,0,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-05',
        'interpretations': '0,1,0,1,0,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH2',
        'imprinted_id': 'unique-identifier-06',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR1'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-07',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-08',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH3',
        'imprinted_id': 'unique-identifier-09',
        'interpretations': '1,0,0,1,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 1,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-10',
        'interpretations': '1,0,0,0,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 2,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-11',
        'interpretations': '1,1,1,1,1,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 3,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-12',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 4,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-13',
        'interpretations': ',,1,0,0,0',
        'tabulator': 'TABULATOR2'
    },
    {
        'ballot_position': 5,
        'batch_name': 'BATCH4',
        'imprinted_id': 'unique-identifier-14',
        'interpretations': ',,0,0,0,1',
        'tabulator': 'TABULATOR2'
    }
]

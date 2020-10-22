# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_ballot_comparison_two_rounds 1'] = {
    'key': 'supersimple',
    'prob': None,
    'size': 22
}

snapshots['test_ballot_comparison_two_rounds 2'] = {
    'numSamples': 10,
    'numSamplesAudited': 0,
    'numUnique': 8,
    'numUniqueAudited': 0,
    'status': 'NOT_STARTED'
}

snapshots['test_ballot_comparison_two_rounds 3'] = {
    'numSamples': 12,
    'numSamplesAudited': 0,
    'numUnique': 10,
    'numUniqueAudited': 0,
    'status': 'NOT_STARTED'
}

snapshots['test_set_contest_metadata_from_cvrs 1'] = {
    'choices': [
        {
            'name': 'Choice 2-1',
            'num_votes': 30
        },
        {
            'name': 'Choice 2-2',
            'num_votes': 14
        },
        {
            'name': 'Choice 2-3',
            'num_votes': 16
        }
    ],
    'num_winners': 1,
    'total_ballots_cast': 30,
    'votes_allowed': 2
}

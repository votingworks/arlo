# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_cvr_upload 1"] = [
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-1",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-2",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-3",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-1",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-2",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-3",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "2-1-1",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "2-1-2",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "2-1-3",
        "interpretations": "1,0,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-1",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-2",
        "interpretations": "1,1,1,1,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-4",
        "interpretations": ",,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 4,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-5",
        "interpretations": ",,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 5,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-6",
        "interpretations": ",,1,0,1",
        "tabulator": "TABULATOR2",
    },
]

snapshots["test_cvr_upload 2"] = {
    "Contest 1": {
        "choices": {
            "Choice 1-1": {"column": 0, "num_votes": 6},
            "Choice 1-2": {"column": 1, "num_votes": 4},
        },
        "total_ballots_cast": 11,
        "votes_allowed": 1,
    },
    "Contest 2": {
        "choices": {
            "Choice 2-1": {"column": 2, "num_votes": 13},
            "Choice 2-2": {"column": 3, "num_votes": 6},
            "Choice 2-3": {"column": 4, "num_votes": 7},
        },
        "total_ballots_cast": 14,
        "votes_allowed": 2,
    },
}

snapshots["test_cvrs_counting_group 1"] = [
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-1",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-2",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-3",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-1",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-2",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-3",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "2-1-1",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "2-1-2",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "2-1-3",
        "interpretations": "1,0,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-1",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-2",
        "interpretations": "1,1,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-3",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 4,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-4",
        "interpretations": ",,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 5,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-5",
        "interpretations": ",,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 6,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-6",
        "interpretations": ",,1,0,1",
        "tabulator": "TABULATOR2",
    },
]

snapshots["test_cvrs_counting_group 2"] = {
    "Contest 1": {
        "choices": {
            "Choice 1-1": {"column": 0, "num_votes": 7},
            "Choice 1-2": {"column": 1, "num_votes": 4},
        },
        "total_ballots_cast": 12,
        "votes_allowed": 1,
    },
    "Contest 2": {
        "choices": {
            "Choice 2-1": {"column": 2, "num_votes": 15},
            "Choice 2-2": {"column": 3, "num_votes": 7},
            "Choice 2-3": {"column": 4, "num_votes": 8},
        },
        "total_ballots_cast": 15,
        "votes_allowed": 2,
    },
}

snapshots["test_cvrs_newlines 1"] = [
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-1",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-2",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-3",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-1",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-2",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-3",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "2-1-1",
        "interpretations": "0,1,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "2-1-2",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "2-1-3",
        "interpretations": "1,0,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-1",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-2",
        "interpretations": "1,1,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-3",
        "interpretations": "1,0,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 4,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-4",
        "interpretations": ",,1,0,1",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 5,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-5",
        "interpretations": ",,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 6,
        "batch_name": "BATCH2",
        "imprinted_id": "2-2-6",
        "interpretations": ",,1,0,1",
        "tabulator": "TABULATOR2",
    },
]

snapshots["test_cvrs_newlines 2"] = {
    "Contest 1": {
        "choices": {
            "Choice 1-1": {"column": 0, "num_votes": 7},
            "Choice 1-2": {"column": 1, "num_votes": 4},
        },
        "total_ballots_cast": 12,
        "votes_allowed": 1,
    },
    "Contest 2": {
        "choices": {
            "Choice 2-1": {"column": 2, "num_votes": 15},
            "Choice 2-2": {"column": 3, "num_votes": 7},
            "Choice 2-3": {"column": 4, "num_votes": 8},
        },
        "total_ballots_cast": 15,
        "votes_allowed": 2,
    },
}

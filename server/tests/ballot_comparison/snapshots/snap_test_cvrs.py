# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_hart_cvr_upload_with_duplicate_batch_names 1"] = [
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-01",
        "interpretations": "0,1,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-02",
        "interpretations": "1,0,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-03",
        "interpretations": "0,1,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-04",
        "interpretations": "1,0,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-05",
        "interpretations": "0,1,0,1,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-06",
        "interpretations": "1,0,0,0,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-07",
        "interpretations": "1,0,0,1,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-08",
        "interpretations": "1,0,0,0,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-09",
        "interpretations": "1,0,0,1,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-10",
        "interpretations": "1,0,0,0,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-11",
        "interpretations": "1,1,1,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-12",
        "interpretations": ",,1,0,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 4,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-13",
        "interpretations": ",,1,0,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 5,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-14",
        "interpretations": ",,0,0,0,1",
        "tabulator": "TABULATOR2",
    },
]

snapshots["test_hart_cvr_upload_with_duplicate_batch_names 2"] = {
    "Contest 1": {
        "choices": {
            "Choice 1-1": {"column": 0, "num_votes": 7},
            "Choice 1-2": {"column": 1, "num_votes": 3},
        },
        "total_ballots_cast": 11,
        "votes_allowed": 1,
    },
    "Contest 2": {
        "choices": {
            "Choice 2-1": {"column": 2, "num_votes": 6},
            "Choice 2-2": {"column": 3, "num_votes": 3},
            "Choice 2-3": {"column": 4, "num_votes": 3},
            "Write-In": {"column": 5, "num_votes": 1},
        },
        "total_ballots_cast": 14,
        "votes_allowed": 1,
    },
}

snapshots["test_hart_cvr_upload_with_duplicate_batch_names 3"] = [
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-01",
        "interpretations": "0,1,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-02",
        "interpretations": "1,0,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-03",
        "interpretations": "0,1,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-04",
        "interpretations": "1,0,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-05",
        "interpretations": "0,1,0,1,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-06",
        "interpretations": "1,0,0,0,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-07",
        "interpretations": "1,0,0,1,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-08",
        "interpretations": "1,0,0,0,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "unique-identifier-09",
        "interpretations": "1,0,0,1,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-10",
        "interpretations": "1,0,0,0,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-11",
        "interpretations": "1,1,1,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-12",
        "interpretations": ",,1,0,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 4,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-13",
        "interpretations": ",,1,0,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 5,
        "batch_name": "BATCH2",
        "imprinted_id": "unique-identifier-14",
        "interpretations": ",,0,0,0,1",
        "tabulator": "TABULATOR2",
    },
]

snapshots["test_hart_cvr_upload_with_duplicate_batch_names 4"] = {
    "Contest 1": {
        "choices": {
            "Choice 1-1": {"column": 0, "num_votes": 7},
            "Choice 1-2": {"column": 1, "num_votes": 3},
        },
        "total_ballots_cast": 11,
        "votes_allowed": 1,
    },
    "Contest 2": {
        "choices": {
            "Choice 2-1": {"column": 2, "num_votes": 6},
            "Choice 2-2": {"column": 3, "num_votes": 3},
            "Choice 2-3": {"column": 4, "num_votes": 3},
            "Write-In": {"column": 5, "num_votes": 1},
        },
        "total_ballots_cast": 14,
        "votes_allowed": 1,
    },
}

snapshots["test_hart_cvr_upload_with_duplicate_batch_names 5"] = [
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-1",
        "interpretations": "0,1,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-2",
        "interpretations": "1,0,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "1-1-3",
        "interpretations": "0,1,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-1",
        "interpretations": "1,0,1,0,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-2",
        "interpretations": "0,1,0,1,0,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "1-2-3",
        "interpretations": "1,0,0,0,1,0",
        "tabulator": "TABULATOR1",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH1",
        "imprinted_id": "1-3-1",
        "interpretations": "1,0,0,1,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH1",
        "imprinted_id": "1-3-2",
        "interpretations": "1,0,0,0,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH1",
        "imprinted_id": "1-3-3",
        "interpretations": "1,0,0,1,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 1,
        "batch_name": "BATCH2",
        "imprinted_id": "1-4-1",
        "interpretations": "1,0,0,0,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 2,
        "batch_name": "BATCH2",
        "imprinted_id": "1-4-2",
        "interpretations": "1,1,1,1,1,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 3,
        "batch_name": "BATCH2",
        "imprinted_id": "1-4-4",
        "interpretations": ",,1,0,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 4,
        "batch_name": "BATCH2",
        "imprinted_id": "1-4-5",
        "interpretations": ",,1,0,0,0",
        "tabulator": "TABULATOR2",
    },
    {
        "ballot_position": 5,
        "batch_name": "BATCH2",
        "imprinted_id": "1-4-6",
        "interpretations": ",,0,0,0,1",
        "tabulator": "TABULATOR2",
    },
]

snapshots["test_hart_cvr_upload_with_duplicate_batch_names 6"] = {
    "Contest 1": {
        "choices": {
            "Choice 1-1": {"column": 0, "num_votes": 7},
            "Choice 1-2": {"column": 1, "num_votes": 3},
        },
        "total_ballots_cast": 11,
        "votes_allowed": 1,
    },
    "Contest 2": {
        "choices": {
            "Choice 2-1": {"column": 2, "num_votes": 6},
            "Choice 2-2": {"column": 3, "num_votes": 3},
            "Choice 2-3": {"column": 4, "num_votes": 3},
            "Write-In": {"column": 5, "num_votes": 1},
        },
        "total_ballots_cast": 14,
        "votes_allowed": 1,
    },
}

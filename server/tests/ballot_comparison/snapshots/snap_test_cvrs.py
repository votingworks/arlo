# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_cvr_upload 1"] = [
    {
        "ballot_position": 1,
        "batch_name": "1 - 1",
        "imprinted_id": "1-1-1",
        "interpretations": "0,1,1,1,0",
    },
    {
        "ballot_position": 3,
        "batch_name": "1 - 1",
        "imprinted_id": "1-1-3",
        "interpretations": "1,0,1,0,1",
    },
    {
        "ballot_position": 5,
        "batch_name": "1 - 1",
        "imprinted_id": "1-1-5",
        "interpretations": "0,1,1,1,0",
    },
    {
        "ballot_position": 2,
        "batch_name": "1 - 2",
        "imprinted_id": "1-2-2",
        "interpretations": "1,0,1,0,1",
    },
    {
        "ballot_position": 4,
        "batch_name": "1 - 2",
        "imprinted_id": "1-2-4",
        "interpretations": "0,1,1,1,0",
    },
    {
        "ballot_position": 6,
        "batch_name": "1 - 2",
        "imprinted_id": "1-2-6",
        "interpretations": "1,0,1,0,1",
    },
    {
        "ballot_position": 1,
        "batch_name": "2 - 1",
        "imprinted_id": "2-1-1",
        "interpretations": "0,1,1,1,0",
    },
    {
        "ballot_position": 3,
        "batch_name": "2 - 1",
        "imprinted_id": "2-1-3",
        "interpretations": "1,0,1,0,1",
    },
    {
        "ballot_position": 5,
        "batch_name": "2 - 1",
        "imprinted_id": "2-1-5",
        "interpretations": "0,1,1,1,0",
    },
    {
        "ballot_position": 2,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-2",
        "interpretations": "1,0,1,0,1",
    },
    {
        "ballot_position": 4,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-4",
        "interpretations": "0,1,1,1,0",
    },
    {
        "ballot_position": 6,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-6",
        "interpretations": "1,0,1,0,1",
    },
    {
        "ballot_position": 8,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-8",
        "interpretations": ",,1,0,1",
    },
    {
        "ballot_position": 10,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-10",
        "interpretations": ",,1,1,0",
    },
    {
        "ballot_position": 12,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-12",
        "interpretations": ",,1,0,1",
    },
]

snapshots["test_cvr_upload 2"] = {
    "Contest 1": {
        "choices": {
            "Choice 1-1": {"affiliation": "REP", "column": 0, "num_votes": 6},
            "Choice 1-2": {"affiliation": "DEM", "column": 1, "num_votes": 6},
        },
        "total_ballots_cast": 12,
        "votes_allowed": "1",
    },
    "Contest 2": {
        "choices": {
            "Choice 2-1": {"affiliation": "LBR", "column": 2, "num_votes": 15},
            "Choice 2-2": {"affiliation": "IND", "column": 3, "num_votes": 7},
            "Choice 2-3": {"affiliation": "", "column": 4, "num_votes": 8},
        },
        "total_ballots_cast": 15,
        "votes_allowed": "2",
    },
}

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
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
        ],
    },
    {
        "ballot_position": 3,
        "batch_name": "1 - 1",
        "imprinted_id": "1-1-3",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
        ],
    },
    {
        "ballot_position": 5,
        "batch_name": "1 - 1",
        "imprinted_id": "1-1-5",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
        ],
    },
    {
        "ballot_position": 2,
        "batch_name": "1 - 2",
        "imprinted_id": "1-2-2",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
        ],
    },
    {
        "ballot_position": 4,
        "batch_name": "1 - 2",
        "imprinted_id": "1-2-4",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
        ],
    },
    {
        "ballot_position": 6,
        "batch_name": "1 - 2",
        "imprinted_id": "1-2-6",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
        ],
    },
    {
        "ballot_position": 1,
        "batch_name": "2 - 1",
        "imprinted_id": "2-1-1",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
        ],
    },
    {
        "ballot_position": 3,
        "batch_name": "2 - 1",
        "imprinted_id": "2-1-3",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
        ],
    },
    {
        "ballot_position": 5,
        "batch_name": "2 - 1",
        "imprinted_id": "2-1-5",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
        ],
    },
    {
        "ballot_position": 2,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-2",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
        ],
    },
    {
        "ballot_position": 4,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-4",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
        ],
    },
    {
        "ballot_position": 6,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-6",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
        ],
    },
    {
        "ballot_position": 8,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-8",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": None,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": None,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
        ],
    },
    {
        "ballot_position": 10,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-10",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": None,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": None,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
        ],
    },
    {
        "ballot_position": 12,
        "batch_name": "2 - 2",
        "imprinted_id": "2-2-12",
        "interpretations": [
            {
                "contest_choice_name": "Choice 1-1",
                "contest_name": "Contest 1",
                "is_voted_for": None,
            },
            {
                "contest_choice_name": "Choice 1-2",
                "contest_name": "Contest 1",
                "is_voted_for": None,
            },
            {
                "contest_choice_name": "Choice 2-1",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
            {
                "contest_choice_name": "Choice 2-2",
                "contest_name": "Contest 2",
                "is_voted_for": False,
            },
            {
                "contest_choice_name": "Choice 2-3",
                "contest_name": "Contest 2",
                "is_voted_for": True,
            },
        ],
    },
]

snapshots["test_cvr_upload 2"] = {
    "Contest 1": {
        "choices": [["Choice 1-1", "REP"], ["Choice 1-2", "DEM"]],
        "votes_allowed": 1,
    },
    "Contest 2": {
        "choices": [["Choice 2-1", "LBR"], ["Choice 2-2", "IND"], ["Choice 2-3", ""]],
        "votes_allowed": 2,
    },
}

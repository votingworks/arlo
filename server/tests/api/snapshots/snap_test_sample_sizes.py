# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_sample_sizes_round_1 1"] = {
    "Contest 1": [
        {"key": "asn", "prob": 0.52, "size": 119},
        {"key": "0.7", "prob": 0.7, "size": 184},
        {"key": "0.8", "prob": 0.8, "size": 244},
        {"key": "0.9", "prob": 0.9, "size": 351},
    ]
}

snapshots["test_sample_sizes_round_2 1"] = {
    "Contest 1": [
        {"key": "asn", "prob": 0.52, "size": 119},
        {"key": "0.7", "prob": 0.7, "size": 184},
        {"key": "0.8", "prob": 0.8, "size": 244},
        {"key": "0.9", "prob": 0.9, "size": 351},
    ]
}

snapshots["test_sample_sizes_round_2 2"] = {
    "Contest 1": {"key": "asn", "prob": 0.52, "size": 119},
    "Contest 2": None,
}

snapshots["test_sample_sizes_round_2 3"] = {
    "Contest 1": [{"key": "0.9", "prob": 0.9, "size": 539}]
}

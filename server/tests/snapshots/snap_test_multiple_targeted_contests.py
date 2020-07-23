# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_sample_size_round_1 1"] = {
    "Contest 1": [
        {"key": "asn", "prob": 0.71, "size": 191},
        {"key": "0.7", "prob": 0.7, "size": 295},
        {"key": "0.8", "prob": 0.8, "size": 391},
        {"key": "0.9", "prob": 0.9, "size": 562},
    ],
    "Contest 2": [
        {"key": "asn", "prob": 0.55, "size": 485},
        {"key": "0.7", "prob": 0.7, "size": 770},
        {"key": "0.8", "prob": 0.8, "size": 1018},
        {"key": "0.9", "prob": 0.9, "size": 1468},
    ],
}

snapshots["test_two_rounds 1"] = {
    "Contest 1 - candidate 1": 132,
    "Contest 1 - candidate 2": 59,
    "Contest 2 - No": 0,
    "Contest 2 - Yes": 0,
    "Contest 3 - candidate 1": 0,
    "Contest 3 - candidate 2": 0,
    "Contest 3 - candidate 3": 0,
}

snapshots["test_two_rounds 2"] = 1468

snapshots["test_two_rounds 3"] = {
    "Contest 2 - No": 440,
    "Contest 2 - Yes": 1028,
    "Contest 3 - candidate 1": 0,
    "Contest 3 - candidate 2": 0,
    "Contest 3 - candidate 3": 0,
}

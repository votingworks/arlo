# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_providence_compute_risk 1"] = [
    {"key": "0.7", "prob": 0.7, "size": 106},
    {"key": "0.8", "prob": 0.8, "size": 136},
    {"key": "0.9", "prob": 0.9, "size": 173},
]

snapshots["test_providence_sample_size 1"] = [
    {"key": "0.7", "prob": 0.7, "size": 106},
    {"key": "0.8", "prob": 0.8, "size": 136},
    {"key": "0.9", "prob": 0.9, "size": 173},
]

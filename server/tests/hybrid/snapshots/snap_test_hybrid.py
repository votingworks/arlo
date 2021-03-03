# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_sample_size 1"] = [
    {"key": "asn", "prob": 0.5, "size": 3, "sizeCvr": 1, "sizeNonCvr": 2},
    {"key": "0.7", "prob": 0.7, "size": 7, "sizeCvr": 3, "sizeNonCvr": 4},
    {"key": "0.8", "prob": 0.8, "size": 11, "sizeCvr": 5, "sizeNonCvr": 6},
    {"key": "0.9", "prob": 0.9, "size": 15, "sizeCvr": 7, "sizeNonCvr": 8},
]

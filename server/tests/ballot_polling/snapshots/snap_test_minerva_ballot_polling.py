# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_minerva_sample_size 1"] = [
    {"key": "0.7", "prob": 0.7, "size": 111},
    {"key": "0.8", "prob": 0.8, "size": 138},
    {"key": "0.9", "prob": 0.9, "size": 179},
]

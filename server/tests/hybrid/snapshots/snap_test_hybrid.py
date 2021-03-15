# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_sample_size 1"] = [
    {"key": "suite", "prob": None, "size": 22, "sizeCvr": 8, "sizeNonCvr": 14}
]

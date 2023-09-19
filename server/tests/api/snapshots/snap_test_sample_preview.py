# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_sample_preview 1"] = [
    {"name": "J1", "numSamples": 80, "numUnique": 76},
    {"name": "J2", "numSamples": 39, "numUnique": 36},
    {"name": "J3", "numSamples": 0, "numUnique": 0},
]

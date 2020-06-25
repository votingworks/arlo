# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_two_rounds 1"] = {
    "Contest 1 - candidate 1": 340,
    "Contest 1 - candidate 2": 145,
    "Contest 2 - No": 0,
    "Contest 2 - Yes": 0,
    "Contest 3 - candidate 1": 0,
    "Contest 3 - candidate 2": 0,
    "Contest 3 - candidate 3": 0,
}

snapshots["test_two_rounds 2"] = {
    "Contest 2 - No": 440,
    "Contest 2 - Yes": 1028,
    "Contest 3 - candidate 1": 0,
    "Contest 3 - candidate 2": 0,
    "Contest 3 - candidate 3": 0,
}

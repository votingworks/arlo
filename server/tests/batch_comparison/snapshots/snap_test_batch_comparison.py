# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_batch_comparison_sample_size 1"] = [
    {"key": "macro", "prob": None, "size": 6}
]

snapshots[
    "test_batch_comparison_sample_batches_round_2 1"
] = """Batch Name,Storage Location,Tabulator,Audit Board
Batch 2,,,Audit Board #1
Batch 4,,,Audit Board #1
"""

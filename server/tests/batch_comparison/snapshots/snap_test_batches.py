# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_batch_retrieval_list_round_1 1"
] = """Batch Name,Storage Location,Tabulator,Already Audited,Audit Board
Batch 1,,,,Audit Board #1
Batch 3,,,,Audit Board #1
Batch 2,,,,Audit Board #2
"""

# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_batch_retrieval_list_round_1 1"
] = """Batch Name,Storage Location,Tabulator,Already Audited,Audit Board
Batch 1,,,No,Audit Board #1
Batch 3,,,No,Audit Board #1
Batch 2,,,No,Audit Board #2
"""

snapshots["test_record_batch_results 1"] = {
    "Contest 1 - candidate 1": 589,
    "Contest 1 - candidate 2": 318,
    "Contest 1 - candidate 3": 466,
}

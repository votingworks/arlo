# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_batch_retrieval_list_round_1 1"
] = """Batch Name,Container,Tabulator,Audit Board
Batch 1,,,Audit Board #1
Batch 3,,,Audit Board #2
"""

snapshots[
    "test_batches_human_sort_order 1"
] = """Batch Name,Container,Tabulator,Audit Board
Batch 1 - 1,,,Audit Board #1
Batch 1 - 2,,,Audit Board #1
Batch 2,,,Audit Board #1
Batch 10,,,Audit Board #1
"""

snapshots[
    "test_batches_human_sort_order 2"
] = """######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Result\r
J1,Batch 1 - 1,"Round 1: 0.138081191, 0.302663147, 0.399800529",No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J1,Batch 1 - 2,Round 1: 0.538402036,No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J1,Batch 2,"Round 1: 0.296058777, 0.344970072",No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J1,Batch 10,"Round 1: 0.033065832, 0.377567954, 0.443556767",No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
"""

snapshots["test_record_batch_results 1"] = {
    "Contest 1 - candidate 1": 2400,
    "Contest 1 - candidate 2": 300,
    "Contest 1 - candidate 3": 240,
}

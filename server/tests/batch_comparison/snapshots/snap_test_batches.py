# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_batch_retrieval_list_round_1 1"
] = """Batch Name,Container,Tabulator
Batch 1,,
Batch 6,,
Batch 8,,
"""

snapshots[
    "test_batches_human_sort_order 1"
] = """Batch Name,Container,Tabulator
Batch 1 - 1,,
Batch 1 - 10,,
Batch 2,,
Batch 10,,
"""

snapshots[
    "test_batches_human_sort_order 2"
] = """######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Results,Reported Results,Discrepancy,Last Edited By\r
J1,Batch 1 - 1,"Round 1: 0.9610467367288398089, 0.9743784458526487453",No,,candidate 1: 10; candidate 2: 5; candidate 3: 5,,\r
J1,Batch 1 - 10,Round 1: 0.109576900310237874,No,,candidate 1: 10; candidate 2: 5; candidate 3: 5,,\r
J1,Batch 2,"Round 1: 0.474971525750860236, 0.555845039101209884",No,,candidate 1: 10; candidate 2: 5; candidate 3: 5,,\r
J1,Batch 10,"Round 1: 0.772049767819343419, 0.875085546411266410",No,,candidate 1: 10; candidate 2: 5; candidate 3: 5,,\r
"""

snapshots["test_record_batch_results 1"] = {
    "Contest 1 - candidate 1": 910,
    "Contest 1 - candidate 2": 200,
    "Contest 1 - candidate 3": 160,
}

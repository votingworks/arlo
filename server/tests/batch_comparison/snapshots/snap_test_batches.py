# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_batch_retrieval_list_round_1 1"
] = """Batch Name,Container,Tabulator
Batch 1,,
Batch 3,,
Batch 6,,
Batch 8,,
"""

snapshots[
    "test_batches_human_sort_order 1"
] = """Batch Name,Container,Tabulator
Batch 1,,
Batch 1 - 1,,
Batch 1 - 2,,
Batch 1 - 10,,
Batch 2,,
Batch 10,,
"""

snapshots[
    "test_batches_human_sort_order 2"
] = """######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Last Edited By\r
J1,Batch 1,20,Round 1: 0.720194360819624066,No,,,,,\r
J1,Batch 1 - 1,20,Round 1: 0.9610467367288398089,No,,,,,\r
J1,Batch 1 - 2,20,Round 1: 0.693314966899513707,No,,,,,\r
J1,Batch 1 - 10,20,Round 1: 0.109576900310237874,No,,,,,\r
J1,Batch 2,20,Round 1: 0.474971525750860236,No,,,,,\r
J1,Batch 10,20,Round 1: 0.772049767819343419,No,,,,,\r
Totals,,120,,,candidate 1: 0; candidate 2: 0; candidate 3: 0,candidate 1: 0; candidate 2: 0; candidate 3: 0,,\r
"""

snapshots["test_record_batch_results 1"] = {
    "Contest 1 - candidate 1": 1210,
    "Contest 1 - candidate 2": 250,
    "Contest 1 - candidate 3": 180,
}

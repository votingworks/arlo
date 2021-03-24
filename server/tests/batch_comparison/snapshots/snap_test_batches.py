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
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_batches_human_sort_order,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,240,candidate 1: 120; candidate 2: 60; candidate 3: 60\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_batches_human_sort_order,BATCH_COMPARISON,MACRO,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,11,No,,DATETIME,,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Result\r
J1,Batch 1 - 1,"Round 1: 0.138081191, 0.302663147, 0.399800529",No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J1,Batch 1 - 2,Round 1: 0.538402036,No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J1,Batch 2,"Round 1: 0.296058777, 0.344970072",No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J1,Batch 10,"Round 1: 0.033065832, 0.377567954, 0.443556767",No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J2,Batch 10,"Round 1: 0.284268304, 0.442250825",No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
"""

snapshots["test_record_batch_results 1"] = {
    "Contest 1 - candidate 1": 2400,
    "Contest 1 - candidate 2": 300,
    "Contest 1 - candidate 3": 240,
}

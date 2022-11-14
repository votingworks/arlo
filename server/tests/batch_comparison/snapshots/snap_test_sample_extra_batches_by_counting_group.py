# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_sample_extra_batches_by_counting_group 1"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org Sample Extra Batches,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,2,5000,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_sample_extra_batches_by_counting_group,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,6,No,0.1857414858,DATETIME,DATETIME,candidate 1: 700; candidate 2: 250; candidate 3: 160\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Results,Reported Results,Discrepancy,Last Edited By\r
J1,Batch 1,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,-100,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,Round 1: 0.899217854763070950,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40,candidate 1: 100; candidate 2: 50; candidate 3: 50,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 8,Round 1: 0.9723790677174592551,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40,candidate 1: 100; candidate 2: 50; candidate 3: 50,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 9,Round 1: EXTRA,Yes,candidate 1: 0; candidate 2: 0; candidate 3: 0,candidate 1: 100; candidate 2: 50; candidate 3: 50,50,jurisdiction.admin-UUID@example.com\r
J2,Batch 3,"Round 1: 0.368061935896261076, 0.733615858338543383",Yes,candidate 1: 100; candidate 2: 100; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,250,jurisdiction.admin-UUID@example.com\r
J2,Batch 6,Round 1: EXTRA,Yes,candidate 1: 1; candidate 2: 200; candidate 3: 200,candidate 1: 100; candidate 2: 50; candidate 3: 50,249,jurisdiction.admin-UUID@example.com\r
"""

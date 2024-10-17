# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_sample_extra_batches_by_counting_group[TEST-ORG/sample-extra-batches-by-counting-group/automatically-end-audit-after-one-round] 1"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
TEST-ORG/sample-extra-batches-by-counting-group/automatically-end-audit-after-one-round,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,2,5000,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_sample_extra_batches_by_counting_group[TEST-ORG/sample-extra-batches-by-counting-group/automatically-end-audit-after-one-round],BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,7,No,0.1225641097,DATETIME,DATETIME,candidate 1: 1100; candidate 2: 300; candidate 3: 200,5,1700,candidate 1: 1700; candidate 2: 850; candidate 3: 850\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Last Edited By\r
J1,Batch 1,500,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: +100; candidate 2: +200; candidate 3: +210,-100,jurisdiction.admin-UUID@example.com\r
J1,Batch 3,500,Round 1: 0.753710009967479876,Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: +100; candidate 2: +200; candidate 3: +210,-100,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,100,Round 1: 0.899217854763070950,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 3: +10,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 8,100,Round 1: 0.9723790677174592551,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 3: +10,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 9,100,Round 1: EXTRA,Yes,candidate 1: 0; candidate 2: 0; candidate 3: 0,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: +100; candidate 2: +50; candidate 3: +50,50,jurisdiction.admin-UUID@example.com\r
J2,Batch 3,500,"Round 1: 0.368061935896261076, 0.733615858338543383",Yes,candidate 1: 100; candidate 2: 100; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: +400; candidate 2: +150; candidate 3: +210,250,jurisdiction.admin-UUID@example.com\r
J2,Batch 6,250,Round 1: EXTRA,Yes,candidate 1: 1; candidate 2: 200; candidate 3: 200,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: +99; candidate 2: -150; candidate 3: -150,249,jurisdiction.admin-UUID@example.com\r
Totals,,2050,,,candidate 1: 1101; candidate 2: 500; candidate 3: 400,candidate 1: 1900; candidate 2: 950; candidate 3: 950,,\r
"""

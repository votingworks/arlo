# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_required_batches[TEST-ORG/required-batches] 1"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
TEST-ORG/required-batches,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Vote Totals,Vote Totals from Batches,Pending Ballots\r
Contest 1,Targeted,1,2,4600,candidate 1: 4600; candidate 2: 2300; candidate 3: 2300,candidate 1: 4600; candidate 2: 2300; candidate 3: 2300,0\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_required_batches[TEST-ORG/required-batches],BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,7,Yes,0.0585276635,DATETIME,DATETIME,candidate 1: 2100; candidate 2: 1050; candidate 3: 1050,5,2100,candidate 1: 2100; candidate 2: 1050; candidate 3: 1050\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Audited?,Reported Results: Contest 1,Audit Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Last Edited By,Precinct Audit Batch\r
J1,Batch 01,500,"Round 1: 0.302716308664955135, 0.336361592874418453",Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,support@example.org,Yes\r
J1,Batch 03,500,Round 1: 0.460991031946439599,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,support@example.org,\r
J1,Batch 04,500,Round 1: 0.9841272498736112234,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,support@example.org,\r
J1,Batch 05,100,Round 1: EXTRA,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,support@example.org,Yes\r
J1,Batch 07,100,Round 1: 0.644005359033749581,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,support@example.org,\r
J1,Batch 11,500,"Round 1: 0.9831918631389931679, 0.9890301455414025321",Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,support@example.org,\r
J2,Batch 02,100,Round 1: EXTRA,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,support@example.org,Yes\r
J3,Batch 02,100,Round 1: EXTRA,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,support@example.org,\r
Totals,,2400,,,candidate 1: 2400; candidate 2: 1200; candidate 3: 1200,candidate 1: 2400; candidate 2: 1200; candidate 3: 1200,,\r
"""

# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_sample_extra_batches_with_combined_batches[TEST-ORG/sample-extra-batches-by-counting-group] 1"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
TEST-ORG/sample-extra-batches-by-counting-group,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Vote Totals,Vote Totals from Batches,Pending Ballots\r
Contest 1,Targeted,1,2,5000,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500,0\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_sample_extra_batches_with_combined_batches[TEST-ORG/sample-extra-batches-by-counting-group],BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,1,No,0.6666666667,DATETIME,DATETIME,candidate 1: 1200; candidate 2: 650; candidate 3: 650,1,1250,candidate 1: 1200; candidate 2: 650; candidate 3: 650\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Audited?,Reported Results: Contest 1,Audit Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Last Edited By,Combined Batch\r
J1,Batch 7,100,Round 1: EXTRA,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,,support@example.org,"Combined Batch - Extra, Unsampled"\r
J1,Batch 9,100,Round 1: EXTRA,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,support@example.org,\r
J2,Batch 3,500,Round 1: 0.368061935896261076,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,,support@example.org,"Combined Batch - Sampled, Extra, Unsampled"\r
J2,Batch 6,250,Round 1: EXTRA,Yes,candidate 1: 200; candidate 2: 150; candidate 3: 150,,,,support@example.org,"Combined Batch - Sampled, Extra, Unsampled"\r
J1,"Combined Batch - Extra, Unsampled",600,,Yes,candidate 1: 600; candidate 2: 300; candidate 3: 300,candidate 1: 600; candidate 2: 300; candidate 3: 300,,,support@example.org,"Combines Batch 1, Batch 7"\r
J2,"Combined Batch - Sampled, Extra, Unsampled",1250,,Yes,candidate 1: 1200; candidate 2: 650; candidate 3: 650,candidate 1: 1200; candidate 2: 650; candidate 3: 650,,,support@example.org,"Combines Batch 1, Batch 3, Batch 6"\r
Totals,,950,,,candidate 1: 1900; candidate 2: 1000; candidate 3: 1000,candidate 1: 1900; candidate 2: 1000; candidate 3: 1000,,\r
"""

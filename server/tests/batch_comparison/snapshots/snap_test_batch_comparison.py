# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_batch_comparison_batches_sampled_multiple_times 1"] = {
    "numSamples": 5,
    "numSamplesAudited": 5,
    "numUnique": 3,
    "numUniqueAudited": 3,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_batches_sampled_multiple_times 2"] = {
    "numSamples": 2,
    "numSamplesAudited": 2,
    "numUnique": 2,
    "numUniqueAudited": 2,
    "status": "COMPLETE",
}

snapshots[
    "test_batch_comparison_batches_sampled_multiple_times 3"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_batch_comparison_batches_sampled_multiple_times,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Vote Totals,Vote Totals from Batches,Pending Ballots\r
Contest 1,Targeted,1,2,5000,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500,0\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_batch_comparison_batches_sampled_multiple_times,BATCH_COMPARISON,MACRO,10%,0123,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,7,Yes,0.0585276635,DATETIME,DATETIME,candidate 1: 2300; candidate 2: 1100; candidate 3: 1100,5,2250,candidate 1: 2300; candidate 2: 1100; candidate 3: 1100\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Last Edited By\r
J1,Batch 1,500,"Round 1: 0.412447190344990933, 0.9216749971146661458, 0.99056429261666903579",Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 3,500,Round 1: 0.225863102795344453,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 4,500,Round 1: 0.429402372732554625,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,jurisdiction.admin-UUID@example.com\r
J2,Batch 1,500,Round 1: 0.455651040681599115,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,jurisdiction.admin-UUID@example.com\r
J2,Batch 5,250,Round 1: 0.491722096005704980,Yes,candidate 1: 300; candidate 2: 100; candidate 3: 100,candidate 1: 300; candidate 2: 100; candidate 3: 100,,,jurisdiction.admin-UUID@example.com\r
Totals,,2250,,,candidate 1: 2300; candidate 2: 1100; candidate 3: 1100,candidate 1: 2300; candidate 2: 1100; candidate 3: 1100,,\r
"""

snapshots[
    "test_batch_comparison_combined_batches 1"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_batch_comparison_combined_batches,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Vote Totals,Vote Totals from Batches,Pending Ballots\r
Contest 1,Targeted,1,2,5000,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500,0\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_batch_comparison_combined_batches,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,7,Yes,0.0593159059,DATETIME,DATETIME,candidate 1: 2700; candidate 2: 1345; candidate 3: 1355,5,2700,candidate 1: 2700; candidate 2: 1350; candidate 3: 1350\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Last Edited By,Combined Batch\r
J1,Batch 1,500,Round 1: 0.720194360819624066,Yes,,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,support@example.org,Combined Batch\r
J1,Batch 2,500,Round 1: 0.474971525750860236,Yes,,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,support@example.org,Combined Batch\r
J1,Batch 4,500,Round 1: 0.9553762217707628661,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,support@example.org,\r
J1,Batch 6,100,Round 1: 0.899217854763070950,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,support@example.org,\r
J1,Batch 8,100,Round 1: 0.9723790677174592551,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,support@example.org,\r
J2,Batch 3,500,"Round 1: 0.368061935896261076, 0.733615858338543383",Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,support@example.org,\r
J1,Combined Batch,1500,,Yes,candidate 1: 1500; candidate 2: 745; candidate 3: 755,candidate 1: 1500; candidate 2: 750; candidate 3: 750,candidate 2: +5; candidate 3: -5,5,support@example.org,"Combines Batch 1, Batch 2, Batch 3"\r
Totals,,2200,,,candidate 1: 2700; candidate 2: 1345; candidate 3: 1355,candidate 1: 2700; candidate 2: 1350; candidate 3: 1350,,\r
"""

snapshots["test_batch_comparison_pending_ballots 1"] = [
    {"key": "macro", "prob": None, "size": 8}
]

snapshots[
    "test_batch_comparison_pending_ballots 2"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_batch_comparison_pending_ballots,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Vote Totals,Vote Totals from Batches,Pending Ballots\r
Contest 1,Targeted,1,2,5000,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500,250\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_batch_comparison_pending_ballots,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,8,Yes,0.05764801,DATETIME,DATETIME,candidate 1: 2700; candidate 2: 1350; candidate 3: 1350,7,2700,candidate 1: 2700; candidate 2: 1350; candidate 3: 1350\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Last Edited By\r
J1,Batch 1,500,Round 1: 0.720194360819624066,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 2,500,Round 1: 0.474971525750860236,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 4,500,Round 1: 0.9553762217707628661,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,100,Round 1: 0.899217854763070950,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 8,100,Round 1: 0.9723790677174592551,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,jurisdiction.admin-UUID@example.com\r
J2,Batch 3,500,"Round 1: 0.368061935896261076, 0.733615858338543383",Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,jurisdiction.admin-UUID@example.com\r
J2,Batch 4,500,Round 1: 0.608147659546583410,Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,jurisdiction.admin-UUID@example.com\r
Totals,,2700,,,candidate 1: 2700; candidate 2: 1350; candidate 3: 1350,candidate 1: 2700; candidate 2: 1350; candidate 3: 1350,,\r
"""

snapshots["test_batch_comparison_round_1 1"] = {
    "numSamples": 9,
    "numSamplesAudited": 0,
    "numUnique": 6,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_1 2"] = {
    "numSamples": 5,
    "numSamplesAudited": 0,
    "numUnique": 2,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_2 1"] = {
    "numSamples": 5,
    "numSamplesAudited": 1,
    "numUnique": 5,
    "numUniqueAudited": 1,
    "status": "IN_PROGRESS",
}

snapshots["test_batch_comparison_round_2 10"] = {
    "numSamples": 1,
    "numSamplesAudited": 1,
    "numUnique": 1,
    "numUniqueAudited": 1,
    "status": "IN_PROGRESS",
}

snapshots["test_batch_comparison_round_2 11"] = {
    "numSamples": 1,
    "numSamplesAudited": 0,
    "numUnique": 1,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_2 12"] = """Batch Name,Container,Tabulator
"""

snapshots["test_batch_comparison_round_2 13"] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_batch_comparison_round_2,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Vote Totals,Vote Totals from Batches,Pending Ballots\r
Contest 1,Targeted,1,2,5000,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500,0\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_batch_comparison_round_2,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,7,No,0.1316872428,DATETIME,DATETIME,candidate 1: 1600; candidate 2: 550; candidate 3: 450,6,2200,candidate 1: 2200; candidate 2: 1100; candidate 3: 1100\r
2,Contest 1,Targeted,2,No,,DATETIME,,candidate 1: 0; candidate 2: 0; candidate 3: 0,2,1000,candidate 1: 1000; candidate 2: 500; candidate 3: 500\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Last Edited By\r
J1,Batch 1,500,Round 1: 0.720194360819624066,Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: +100; candidate 2: +200; candidate 3: +210,-100,jurisdiction.admin-UUID@example.com\r
J1,Batch 2,500,Round 1: 0.474971525750860236,Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: +100; candidate 2: +200; candidate 3: +210,-100,jurisdiction.admin-UUID@example.com\r
J1,Batch 4,500,"Round 1: 0.9553762217707628661, Round 2: 0.9782132493451071914",Yes,candidate 1: 500; candidate 2: 250; candidate 3: 240,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 3: +10,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,100,Round 1: 0.899217854763070950,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 3: +10,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 8,100,Round 1: 0.9723790677174592551,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,jurisdiction.admin-UUID@example.com\r
J2,Batch 3,500,"Round 1: 0.368061935896261076, 0.733615858338543383",Yes,candidate 1: 100; candidate 2: 100; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: +400; candidate 2: +150; candidate 3: +210,250,jurisdiction.admin-UUID@example.com\r
J2,Batch 4,500,Round 2: 0.608147659546583410,No,,candidate 1: 500; candidate 2: 250; candidate 3: 250,,,\r
Totals,,2700,,,candidate 1: 1600; candidate 2: 550; candidate 3: 450,candidate 1: 2700; candidate 2: 1350; candidate 3: 1350,,\r
"""

snapshots["test_batch_comparison_round_2 14"] = """######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Last Edited By\r
J1,Batch 1,500,Round 1: 0.720194360819624066,Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: +100; candidate 2: +200; candidate 3: +210,-100,jurisdiction.admin-UUID@example.com\r
J1,Batch 2,500,Round 1: 0.474971525750860236,Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: +100; candidate 2: +200; candidate 3: +210,-100,jurisdiction.admin-UUID@example.com\r
J1,Batch 4,500,"Round 1: 0.9553762217707628661, Round 2: 0.9782132493451071914",Yes,candidate 1: 500; candidate 2: 250; candidate 3: 240,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 3: +10,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,100,Round 1: 0.899217854763070950,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 3: +10,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 8,100,Round 1: 0.9723790677174592551,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,,jurisdiction.admin-UUID@example.com\r
Totals,,1700,,,candidate 1: 1500; candidate 2: 450; candidate 3: 410,candidate 1: 1700; candidate 2: 850; candidate 3: 850,,\r
"""

snapshots["test_batch_comparison_round_2 2"] = {
    "numSamples": 5,
    "numSamplesAudited": 2,
    "numUnique": 5,
    "numUniqueAudited": 2,
    "status": "IN_PROGRESS",
}

snapshots["test_batch_comparison_round_2 3"] = {
    "numSamples": 5,
    "numSamplesAudited": 3,
    "numUnique": 5,
    "numUniqueAudited": 3,
    "status": "IN_PROGRESS",
}

snapshots["test_batch_comparison_round_2 4"] = {
    "numSamples": 5,
    "numSamplesAudited": 4,
    "numUnique": 5,
    "numUniqueAudited": 4,
    "status": "IN_PROGRESS",
}

snapshots["test_batch_comparison_round_2 5"] = {
    "numSamples": 5,
    "numSamplesAudited": 5,
    "numUnique": 5,
    "numUniqueAudited": 5,
    "status": "IN_PROGRESS",
}

snapshots["test_batch_comparison_round_2 6"] = {
    "numSamples": 5,
    "numSamplesAudited": 5,
    "numUnique": 5,
    "numUniqueAudited": 5,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 7"] = {
    "numSamples": 2,
    "numSamplesAudited": 0,
    "numUnique": 1,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_2 8"] = {
    "numSamples": 5,
    "numSamplesAudited": 5,
    "numUnique": 5,
    "numUniqueAudited": 5,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 9"] = {
    "numSamples": 2,
    "numSamplesAudited": 2,
    "numUnique": 1,
    "numUniqueAudited": 1,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_sample_preview 1"] = [
    {"name": "J1", "numSamples": 5, "numUnique": 5},
    {"name": "J2", "numSamples": 2, "numUnique": 1},
    {"name": "J3", "numSamples": 0, "numUnique": 0},
]

snapshots["test_batch_comparison_sample_size 1"] = [
    {"key": "macro", "prob": None, "size": 7}
]

# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_batch_comparison_batches_sampled_multiple_times 1"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_batch_comparison_batches_sampled_multiple_times,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,2,5000,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_batch_comparison_batches_sampled_multiple_times,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,6,Yes,0.0825517715,DATETIME,DATETIME,candidate 1: 1200; candidate 2: 600; candidate 3: 600\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Results,Reported Results,Discrepancy,Last Edited By\r
J1,Batch 1,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,Round 1: 0.899217854763070950,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,jurisdiction.admin-UUID@example.com\r
J1,Batch 8,Round 1: 0.9723790677174592551,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 50,candidate 1: 100; candidate 2: 50; candidate 3: 50,,jurisdiction.admin-UUID@example.com\r
J2,Batch 3,"Round 1: 0.368061935896261076, 0.733615858338543383",Yes,candidate 1: 500; candidate 2: 250; candidate 3: 250,candidate 1: 500; candidate 2: 250; candidate 3: 250,,jurisdiction.admin-UUID@example.com\r
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
    "numSamples": 4,
    "numSamplesAudited": 2,
    "numUnique": 3,
    "numUniqueAudited": 1,
    "status": "IN_PROGRESS",
}

snapshots[
    "test_batch_comparison_round_2 10"
] = """Batch Name,Container,Tabulator
Batch 3,,
Batch 4,,
"""

snapshots[
    "test_batch_comparison_round_2 11"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_batch_comparison_round_2,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,2,5000,candidate 1: 5000; candidate 2: 2500; candidate 3: 2500\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_batch_comparison_round_2,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,6,No,0.1857414858,DATETIME,DATETIME,candidate 1: 700; candidate 2: 250; candidate 3: 160\r
2,Contest 1,Targeted,5,No,,DATETIME,,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Results,Reported Results,Discrepancy,Last Edited By\r
J1,Batch 1,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,-100,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,Round 1: 0.899217854763070950,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40,candidate 1: 100; candidate 2: 50; candidate 3: 50,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 8,Round 1: 0.9723790677174592551,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40,candidate 1: 100; candidate 2: 50; candidate 3: 50,-10,jurisdiction.admin-UUID@example.com\r
J2,Batch 3,"Round 1: 0.368061935896261076, 0.733615858338543383",Yes,candidate 1: 100; candidate 2: 100; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,250,jurisdiction.admin-UUID@example.com\r
J1,Batch 3,Round 2: 0.753710009967479876,No,,candidate 1: 500; candidate 2: 250; candidate 3: 250,,\r
J1,Batch 4,"Round 2: 0.9553762217707628661, 0.9782132493451071914",No,,candidate 1: 500; candidate 2: 250; candidate 3: 250,,\r
J2,Batch 4,"Round 2: 0.608147659546583410, 0.868820918994249069",No,,candidate 1: 500; candidate 2: 250; candidate 3: 250,,\r
"""

snapshots[
    "test_batch_comparison_round_2 12"
] = """######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Results,Reported Results,Discrepancy,Last Edited By\r
J1,Batch 1,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40,candidate 1: 500; candidate 2: 250; candidate 3: 250,-100,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,Round 1: 0.899217854763070950,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40,candidate 1: 100; candidate 2: 50; candidate 3: 50,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 8,Round 1: 0.9723790677174592551,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40,candidate 1: 100; candidate 2: 50; candidate 3: 50,-10,jurisdiction.admin-UUID@example.com\r
J1,Batch 3,Round 2: 0.753710009967479876,No,,candidate 1: 500; candidate 2: 250; candidate 3: 250,,\r
J1,Batch 4,"Round 2: 0.9553762217707628661, 0.9782132493451071914",No,,candidate 1: 500; candidate 2: 250; candidate 3: 250,,\r
"""

snapshots["test_batch_comparison_round_2 2"] = {
    "numSamples": 4,
    "numSamplesAudited": 3,
    "numUnique": 3,
    "numUniqueAudited": 2,
    "status": "IN_PROGRESS",
}

snapshots["test_batch_comparison_round_2 3"] = {
    "numSamples": 4,
    "numSamplesAudited": 4,
    "numUnique": 3,
    "numUniqueAudited": 3,
    "status": "IN_PROGRESS",
}

snapshots["test_batch_comparison_round_2 4"] = {
    "numSamples": 4,
    "numSamplesAudited": 4,
    "numUnique": 3,
    "numUniqueAudited": 3,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 5"] = {
    "numSamples": 2,
    "numSamplesAudited": 0,
    "numUnique": 1,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_2 6"] = {
    "numSamples": 4,
    "numSamplesAudited": 4,
    "numUnique": 3,
    "numUniqueAudited": 3,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 7"] = {
    "numSamples": 2,
    "numSamplesAudited": 2,
    "numUnique": 1,
    "numUniqueAudited": 1,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 8"] = {
    "numSamples": 3,
    "numSamplesAudited": 0,
    "numUnique": 2,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_2 9"] = {
    "numSamples": 2,
    "numSamplesAudited": 0,
    "numUnique": 1,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_sample_size 1"] = [
    {"key": "macro", "prob": None, "size": 6}
]

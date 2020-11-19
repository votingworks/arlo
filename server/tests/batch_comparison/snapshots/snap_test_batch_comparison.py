# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_batch_comparison_round_1 1"] = {
    "numSamples": 14,
    "numSamplesAudited": 0,
    "numUnique": 5,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_1 2"] = {
    "numSamples": 6,
    "numSamplesAudited": 0,
    "numUnique": 3,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_2 1"] = {
    "numSamples": 4,
    "numSamplesAudited": 4,
    "numUnique": 2,
    "numUniqueAudited": 2,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 2"] = {
    "numSamples": 2,
    "numSamplesAudited": 0,
    "numUnique": 2,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_2 3"] = {
    "numSamples": 4,
    "numSamplesAudited": 4,
    "numUnique": 2,
    "numUniqueAudited": 2,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 4"] = {
    "numSamples": 2,
    "numSamplesAudited": 2,
    "numUnique": 2,
    "numUniqueAudited": 2,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 5"] = {
    "numSamples": 2,
    "numSamplesAudited": 0,
    "numUnique": 2,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_2 6"] = {
    "numSamples": 2,
    "numSamplesAudited": 1,
    "numUnique": 2,
    "numUniqueAudited": 1,
    "status": "NOT_STARTED",
}

snapshots[
    "test_batch_comparison_round_2 7"
] = """Batch Name,Container,Tabulator,Audit Board
Batch 2,,,Audit Board #1
Batch 4,,,Audit Board #2
"""

snapshots[
    "test_batch_comparison_round_2 8"
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
Test Audit test_batch_comparison_round_2,BATCH_COMPARISON,MACRO,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
J1,Audit Board #1,,,,\r
J1,Audit Board #2,,,,\r
J1,Audit Board #2,,,,\r
J2,Audit Board #1,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,6,No,0.189590948,DATETIME,DATETIME,candidate 1: 2400; candidate 2: 300; candidate 3: 240\r
2,Contest 1,Targeted,4,No,,DATETIME,,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Result\r
J1,Batch 1,Round 1: 0.025053745,Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40\r
J1,Batch 3,"Round 1: 0.023650366, 0.122600189, 0.150810694",Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40\r
J2,Batch 1,Round 1: 0.128219632,Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40\r
J2,Batch 5,"Round 1: 0.121751602, Round 2: 0.172408497",Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40\r
J1,Batch 2,Round 2: 0.203857756,No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J1,Batch 4,Round 2: 0.169018243,No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J2,Batch 3,Round 2: 0.176814880,No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
"""

snapshots[
    "test_batch_comparison_round_2 9"
] = """######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Result\r
J1,Batch 1,Round 1: 0.025053745,Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40\r
J1,Batch 3,"Round 1: 0.023650366, 0.122600189, 0.150810694",Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40\r
J1,Batch 2,Round 2: 0.203857756,No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J1,Batch 4,Round 2: 0.169018243,No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
"""

snapshots["test_batch_comparison_sample_size 1"] = [
    {"key": "macro", "prob": None, "size": 6}
]

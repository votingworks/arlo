# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_batch_comparison_round_1 1"] = {
    "numSamples": 10,
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
    "numSamplesAudited": 4,
    "numUnique": 3,
    "numUniqueAudited": 3,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 2"] = {
    "numSamples": 2,
    "numSamplesAudited": 0,
    "numUnique": 1,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_2 3"] = {
    "numSamples": 4,
    "numSamplesAudited": 4,
    "numUnique": 3,
    "numUniqueAudited": 3,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 4"] = {
    "numSamples": 2,
    "numSamplesAudited": 2,
    "numUnique": 1,
    "numUniqueAudited": 1,
    "status": "COMPLETE",
}

snapshots["test_batch_comparison_round_2 5"] = {
    "numSamples": 3,
    "numSamplesAudited": 0,
    "numUnique": 2,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_batch_comparison_round_2 6"] = {
    "numSamples": 1,
    "numSamplesAudited": 0,
    "numUnique": 1,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots[
    "test_batch_comparison_round_2 7"
] = """Batch Name,Container,Tabulator,Audit Board
Batch 3,,,Audit Board #1
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
1,Contest 1,Targeted,6,No,0.189590948,DATETIME,DATETIME,candidate 1: 1800; candidate 2: 300; candidate 3: 240\r
2,Contest 1,Targeted,4,No,,DATETIME,,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Result\r
J1,Batch 1,"Round 1: 0.7201943608196240, 0.7820405891326865",Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40\r
J1,Batch 6,Round 1: 0.8992178547630709,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40\r
J1,Batch 8,Round 1: 0.9723790677174592,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40\r
J2,Batch 3,"Round 1: 0.3680619358962610, 0.5623260922590551",Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40\r
J1,Batch 3,Round 2: 0.7537100099674798,No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J1,Batch 4,"Round 2: 0.9553762217707628, 0.9793207276968563",No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J2,Batch 4,Round 2: 0.6081476595465834,No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
"""

snapshots[
    "test_batch_comparison_round_2 9"
] = """######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ticket Numbers,Audited?,Audit Result\r
J1,Batch 1,"Round 1: 0.7201943608196240, 0.7820405891326865",Yes,candidate 1: 400; candidate 2: 50; candidate 3: 40\r
J1,Batch 6,Round 1: 0.8992178547630709,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40\r
J1,Batch 8,Round 1: 0.9723790677174592,Yes,candidate 1: 100; candidate 2: 50; candidate 3: 40\r
J1,Batch 3,Round 2: 0.7537100099674798,No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
J1,Batch 4,"Round 2: 0.9553762217707628, 0.9793207276968563",No,candidate 1: 0; candidate 2: 0; candidate 3: 0\r
"""

snapshots["test_batch_comparison_sample_size 1"] = [
    {"key": "macro", "prob": None, "size": 6}
]

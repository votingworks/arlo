# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_nested_sampling_end_to_end 1"] = {"Contest 1": 8, "Contest 2": 6}

snapshots["test_nested_sampling_end_to_end 2"] = {
    "Contest 1": [
        ("J1", "Batch 05", "0.9709625076938577465"),
        ("J1", "Batch 05", "0.9833518491151625693"),
        ("J1", "Batch 15", "0.880123697445425636"),
        ("J1", "Batch 21", "0.501363046258331055"),
        ("J1", "Batch 23", "0.455584192063654027"),
        ("J1", "Batch 35", "0.546585191596479016"),
        ("J1", "Batch 36", "0.865901423826860735"),
        ("J2", "Batch 3", "0.368061935896261076"),
    ],
    "Contest 2": [
        ("J1", "Batch 05", "0.9709625076938577465"),
        ("J1", "Batch 05", "0.9833518491151625693"),
        ("J1", "Batch 21", "0.501363046258331055"),
        ("J1", "Batch 23", "0.455584192063654027"),
        ("J1", "Batch 35", "0.546585191596479016"),
        ("J1", "Batch 36", "0.865901423826860735"),
    ],
}

snapshots["test_nested_sampling_end_to_end 3"] = {
    "Contest 2": [
        ("J1", "Batch 03", "0.460991031946439599"),
        ("J1", "Batch 11", "0.9831918631389931679"),
        ("J1", "Batch 15", "0.880123697445425636"),
        ("J1", "Batch 18", "0.140322073008067452"),
        ("J1", "Batch 19", "0.776430995092033462"),
        ("J1", "Batch 30", "0.264473907597457953"),
    ]
}

snapshots["test_nested_sampling_end_to_end 4"] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_nested_sampling_end_to_end,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Vote Totals,Vote Totals from Batches,Pending Ballots,Sample Nested Under\r
Contest 1,Targeted,1,1,2400,Candidate 1: 1680; Candidate 2: 720,Candidate 1: 1680; Candidate 2: 720,0,\r
Contest 2,Targeted,1,1,2000,Candidate 3: 1600; Candidate 4: 400,Candidate 3: 1600; Candidate 4: 400,0,Contest 1\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_nested_sampling_end_to_end,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,8,Yes,0.0677603615,DATETIME,DATETIME,Candidate 1: 245; Candidate 2: 105,7,350,Candidate 1: 245; Candidate 2: 105\r
1,Contest 2,Targeted,6,No,0.9536743164,DATETIME,DATETIME,Candidate 3: 210; Candidate 4: 90,7,350,Candidate 3: 240; Candidate 4: 60\r
2,Contest 2,Targeted,6,No,,DATETIME,,Candidate 3: 0; Candidate 4: 0,6,300,Candidate 3: 240; Candidate 4: 60\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Ticket Numbers: Contest 2,Audited?,Reported Results: Contest 1,Audit Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Reported Results: Contest 2,Audit Results: Contest 2,Change in Results: Contest 2,Change in Margin: Contest 2,Last Edited By\r
J1,Batch 05,50,"Round 1: 0.9709625076938577465, 0.9833518491151625693","Round 1: 0.9709625076938577465, 0.9833518491151625693",Yes,Candidate 1: 40; Candidate 2: 10,Candidate 1: 40; Candidate 2: 10,,,Candidate 3: 40; Candidate 4: 10,Candidate 3: 10; Candidate 4: 40,Candidate 3: +30; Candidate 4: -30,60,jurisdiction.admin-UUID@example.com\r
J1,Batch 15,50,Round 1: 0.880123697445425636,Round 2: 0.880123697445425636,Yes,Candidate 1: 30; Candidate 2: 20,Candidate 1: 30; Candidate 2: 20,,,Candidate 3: 40; Candidate 4: 10,Candidate 3: 40; Candidate 4: 10,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 21,50,Round 1: 0.501363046258331055,Round 1: 0.501363046258331055,Yes,Candidate 1: 30; Candidate 2: 20,Candidate 1: 30; Candidate 2: 20,,,Candidate 3: 40; Candidate 4: 10,Candidate 3: 40; Candidate 4: 10,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 23,50,Round 1: 0.455584192063654027,Round 1: 0.455584192063654027,Yes,Candidate 1: 40; Candidate 2: 10,Candidate 1: 40; Candidate 2: 10,,,Candidate 3: 40; Candidate 4: 10,Candidate 3: 40; Candidate 4: 10,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 35,50,Round 1: 0.546585191596479016,Round 1: 0.546585191596479016,Yes,Candidate 1: 40; Candidate 2: 10,Candidate 1: 40; Candidate 2: 10,,,Candidate 3: 40; Candidate 4: 10,Candidate 3: 40; Candidate 4: 10,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 36,50,Round 1: 0.865901423826860735,Round 1: 0.865901423826860735,Yes,Candidate 1: 30; Candidate 2: 20,Candidate 1: 30; Candidate 2: 20,,,Candidate 3: 40; Candidate 4: 10,Candidate 3: 40; Candidate 4: 10,,,jurisdiction.admin-UUID@example.com\r
J2,Batch 3,50,Round 1: 0.368061935896261076,,Yes,Candidate 1: 35; Candidate 2: 15,Candidate 1: 35; Candidate 2: 15,,,,,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 03,50,,Round 2: 0.460991031946439599,No,Candidate 1: 30; Candidate 2: 20,,,,Candidate 3: 40; Candidate 4: 10,,,,\r
J1,Batch 11,50,,Round 2: 0.9831918631389931679,No,Candidate 1: 40; Candidate 2: 10,,,,Candidate 3: 40; Candidate 4: 10,,,,\r
J1,Batch 18,50,,Round 2: 0.140322073008067452,No,Candidate 1: 30; Candidate 2: 20,,,,Candidate 3: 40; Candidate 4: 10,,,,\r
J1,Batch 19,50,,Round 2: 0.776430995092033462,No,Candidate 1: 35; Candidate 2: 15,,,,Candidate 3: 40; Candidate 4: 10,,,,\r
J1,Batch 30,50,,Round 2: 0.264473907597457953,No,Candidate 1: 30; Candidate 2: 20,,,,Candidate 3: 40; Candidate 4: 10,,,,\r
Totals,,600,,,,Candidate 1: 410; Candidate 2: 190,Candidate 1: 245; Candidate 2: 105,,,Candidate 3: 440; Candidate 4: 110,Candidate 3: 210; Candidate 4: 90,,\r
"""

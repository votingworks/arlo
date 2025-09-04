# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_all_ballots_audit 1"] = {
    "Contest 1 - candidate 1": 1000000,
    "Contest 1 - candidate 2": 999000,
    "Contest 1 - candidate 3": 1000,
}

snapshots[
    "test_all_ballots_audit 2"
] = """######## FULL HAND TALLY BATCH RESULTS ########\r
Jurisdiction Name,Batch Name,Batch Type,candidate 1,candidate 2,candidate 3\r
J1,Batch One,Provisional,125000,124875,125\r
J1,Batch Three,Election Day,125000,124875,125\r
J1,Batch Two,Other,250000,249750,250\r
"""

snapshots["test_all_ballots_audit 3"] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_all_ballots_audit,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Vote Totals\r
Contest 1,Targeted,1,1,2000000,candidate 1: 1000000; candidate 2: 999000; candidate 3: 1000\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_all_ballots_audit,BALLOT_POLLING,BRAVO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,2000000,Yes,0,DATETIME,DATETIME,candidate 1: 1000000; candidate 2: 999000; candidate 3: 1000\r
\r
######## FULL HAND TALLY BATCH RESULTS ########\r
Jurisdiction Name,Batch Name,Batch Type,candidate 1,candidate 2,candidate 3\r
J1,Batch One,Provisional,125000,124875,125\r
J1,Batch Three,Election Day,125000,124875,125\r
J1,Batch Two,Other,250000,249750,250\r
J2,Batch One,Absentee By Mail,250000,249750,250\r
J2,Batch Two,Advance,250000,249750,250\r
"""

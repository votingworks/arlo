# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_standardize_contest_names 1"] = [
    {"key": "supersimple", "prob": None, "size": 20}
]

snapshots[
    "test_standardize_contest_names 2"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_standardize_contest_names,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Standardized Contest 1,Targeted,1,1,30,Choice 1-1: 14; Choice 1-2: 6\r
Standardized Contest 2,Opportunistic,1,2,15,Choice 2-1: 13; Choice 2-2: 6; Choice 2-3: 7\r
\r
######## CONTEST NAME STANDARDIZATIONS ########\r
Jurisdiction,Contest Name,CVR Contest Name\r
J1,Standardized Contest 1,Contest 1\r
J1,Standardized Contest 2,Contest 2\r
J2,Standardized Contest 1,Contest 1\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_standardize_contest_names,BALLOT_COMPARISON,SUPERSIMPLE,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Standardized Contest 1,Audited?,Audit Result: Standardized Contest 1,CVR Result: Standardized Contest 1,Discrepancy: Standardized Contest 1,Audit Result: Standardized Contest 2,CVR Result: Standardized Contest 2,Discrepancy: Standardized Contest 2\r
"""

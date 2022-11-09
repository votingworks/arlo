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
Standardized Contest 2,Opportunistic,1,2,15,Choice 2-1: 12; Choice 2-2: 5; Choice 2-3: 7\r
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
1,Standardized Contest 1,Targeted,20,No,,DATETIME,,Choice 1-1: 0; Choice 1-2: 0\r
1,Standardized Contest 2,Opportunistic,,No,,DATETIME,,Choice 2-1: 0; Choice 2-2: 0; Choice 2-3: 0\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Standardized Contest 1,Audited?,Audit Result: Standardized Contest 1,CVR Result: Standardized Contest 1,Discrepancy: Standardized Contest 1,Audit Result: Standardized Contest 2,CVR Result: Standardized Contest 2,Discrepancy: Standardized Contest 2\r
J1,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.243550726331576894,NOT_AUDITED,,Choice 1-2,,,"Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,2,1-2-2,Round 1: 0.125871889047705889,NOT_AUDITED,,Choice 1-2,,,"Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,3,1-2-3,Round 1: 0.126622033568908859,NOT_AUDITED,,Choice 1-1,,,"Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH2,2,2-2-2,Round 1: 0.053992217600758631,NOT_AUDITED,,"Choice 1-1, Choice 1-2",,,"Choice 2-1, Choice 2-2, Choice 2-3",\r
J1,TABULATOR2,BATCH2,3,2-2-4,Round 1: 0.255119157791673311,NOT_AUDITED,,Blank,,,"Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH2,4,2-2-5,"Round 1: 0.064984443990590400, 0.069414660569975443",NOT_AUDITED,,Blank,,,Blank,\r
J1,TABULATOR2,BATCH2,5,2-2-6,Round 1: 0.442956417641278897,NOT_AUDITED,,Blank,,,"Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH2,6,,Round 1: 0.300053574780458718,NOT_AUDITED,,,,,,\r
J2,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.476019554092109137,NOT_AUDITED,,Choice 1-2,,,,\r
J2,TABULATOR1,BATCH1,3,1-1-3,Round 1: 0.242392535590495322,NOT_AUDITED,,Choice 1-2,,,,\r
J2,TABULATOR1,BATCH2,1,1-2-1,Round 1: 0.200269401620671924,NOT_AUDITED,,Choice 1-1,,,,\r
J2,TABULATOR2,BATCH1,1,2-1-1,Round 1: 0.174827909206366766,NOT_AUDITED,,Choice 1-1,,,,\r
J2,TABULATOR2,BATCH2,1,2-2-1,Round 1: 0.185417954749015145,NOT_AUDITED,,Choice 1-1,,,,\r
J2,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.252054739518646128, 0.297145021317217438",NOT_AUDITED,,"Choice 1-1, Choice 1-2",,,,\r
J2,TABULATOR2,BATCH2,3,2-2-4,"Round 1: 0.179114059650472941, 0.443867094961314498",NOT_AUDITED,,Blank,,,,\r
J2,TABULATOR2,BATCH2,5,2-2-6,Round 1: 0.462119987445142117,NOT_AUDITED,,Blank,,,,\r
J2,TABULATOR2,BATCH2,6,,Round 1: 0.414184312862040881,NOT_AUDITED,,,,,,\r
"""

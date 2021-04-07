# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_hybrid_two_rounds 1"
] = """Tabulator,Batch Name,Ballot Number,Imprinted ID,Ticket Numbers,Already Audited,Audit Board
TABULATOR1,BATCH1,1,1-1-1,0.243550726331576894,N,Audit Board #1
TABULATOR1,BATCH2,2,1-2-2,0.125871889047705889,N,Audit Board #1
TABULATOR1,BATCH2,3,1-2-3,0.126622033568908859,N,Audit Board #1
TABULATOR2,BATCH2,2,2-2-2,0.053992217600758631,N,Audit Board #1
TABULATOR2,BATCH2,3,2-2-4,0.255119157791673311,N,Audit Board #1
TABULATOR2,BATCH2,4,2-2-5,"0.064984443990590400,0.069414660569975443",N,Audit Board #1
TABULATOR3,BATCH1,1,,0.029052899542529576,N,Audit Board #1
TABULATOR3,BATCH1,2,,0.078395302081543460,N,Audit Board #1
TABULATOR3,BATCH1,3,,0.041030221525069793,N,Audit Board #1
TABULATOR3,BATCH1,5,,0.072664791498577026,N,Audit Board #1
TABULATOR3,BATCH1,10,,0.199742518299743122,N,Audit Board #1
"""

snapshots[
    "test_hybrid_two_rounds 2"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_hybrid_two_rounds,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes,Total Ballots Cast: CVR,Total Ballots Cast: Non-CVR,Tabulated Votes: CVR,Tabulated Votes: Non-CVR\r
Contest 1,Targeted,1,1,50,Choice 1-1: 30; Choice 1-2: 10,30,20,Choice 1-1: 12; Choice 1-2: 8,Choice 1-1: 18; Choice 1-2: 2\r
Contest 2,Opportunistic,2,2,25,Choice 2-1: 20; Choice 2-2: 8; Choice 2-3: 10,15,10,Choice 2-1: 13; Choice 2-2: 6; Choice 2-3: 7,Choice 2-1: 7; Choice 2-2: 2; Choice 2-3: 3\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_hybrid_two_rounds,HYBRID,SUITE,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
J2,Audit Board #1,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,22,No,0.7747175905,DATETIME,DATETIME,Choice 1-1: 7; Choice 1-2: 1\r
1,Contest 2,Opportunistic,,No,1.0,DATETIME,DATETIME,Choice 2-1: 4; Choice 2-2: 1; Choice 2-3: 0\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Discrepancy: Contest 1,Audit Result: Contest 2,CVR Result: Contest 2,Discrepancy: Contest 2\r
J1,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.243550726331576894,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,2,1-2-2,Round 1: 0.125871889047705889,AUDITED,"Choice 1-1, Choice 1-2",Choice 1-2,-1,Choice 2-2,"Choice 2-1, Choice 2-2",1\r
J1,TABULATOR1,BATCH2,3,1-2-3,Round 1: 0.126622033568908859,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH2,2,2-2-2,Round 1: 0.053992217600758631,AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,"Choice 2-1, Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-2, Choice 2-3",\r
J1,TABULATOR2,BATCH2,3,2-2-4,Round 1: 0.255119157791673311,AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH2,4,2-2-5,"Round 1: 0.064984443990590400, 0.069414660569975443",AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR3,BATCH1,1,,Round 1: 0.029052899542529576,AUDITED,Choice 1-1,,,Choice 2-1,,\r
J1,TABULATOR3,BATCH1,2,,Round 1: 0.078395302081543460,AUDITED,Choice 1-1,,,Choice 2-1,,\r
J1,TABULATOR3,BATCH1,3,,Round 1: 0.041030221525069793,AUDITED,Choice 1-1,,,Choice 2-1,,\r
J1,TABULATOR3,BATCH1,5,,Round 1: 0.072664791498577026,AUDITED,Choice 1-1,,,Choice 2-1,,\r
J1,TABULATOR3,BATCH1,10,,Round 1: 0.199742518299743122,AUDITED,Choice 1-1,,,Choice 2-2,,\r
J2,TABULATOR1,BATCH1,3,1-1-3,Round 1: 0.242392535590495322,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2",,\r
J2,TABULATOR1,BATCH2,1,1-2-1,Round 1: 0.200269401620671924,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3",,\r
J2,TABULATOR2,BATCH1,1,2-1-1,Round 1: 0.174827909206366766,NOT_FOUND,,Choice 1-2,2,,,\r
J2,TABULATOR2,BATCH2,1,2-2-1,Round 1: 0.185417954749015145,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3",,\r
J2,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.252054739518646128, 0.297145021317217438",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,"Choice 2-1, Choice 2-2, Choice 2-3",,\r
J2,TABULATOR2,BATCH2,3,2-2-4,Round 1: 0.179114059650472941,AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-3",,\r
J2,TABULATOR3,BATCH1,1,,Round 1: 0.052129356711674929,AUDITED,Choice 1-1,,,CONTEST_NOT_ON_BALLOT,,\r
J2,TABULATOR3,BATCH1,5,,Round 1: 0.037027823153316024,AUDITED,Choice 1-1,,,CONTEST_NOT_ON_BALLOT,,\r
J2,TABULATOR3,BATCH1,10,,Round 1: 0.087764767095634400,AUDITED,Choice 1-2,,,CONTEST_NOT_ON_BALLOT,,\r
"""

snapshots["test_sample_size 1"] = [
    {"key": "suite", "prob": None, "size": 22, "sizeCvr": 14, "sizeNonCvr": 8}
]

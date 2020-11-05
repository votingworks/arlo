# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_ballot_comparison_container_manifest 1"
] = """Container,Tabulator,Batch Name,Ballot Number,Imprinted ID,Ticket Numbers,Already Audited,Audit Board
CONTAINER2,TABULATOR1,BATCH3,2,1-3-2,0.009464169703578658,N,Audit Board #1
CONTAINER2,TABULATOR1,BATCH3,8,1-3-8,0.014246627323528638,N,Audit Board #1
CONTAINER2,TABULATOR1,BATCH3,13,1-3-13,0.008481195646651660,N,Audit Board #1
CONTAINER2,TABULATOR1,BATCH4,3,1-4-3,0.018064599389368317,N,Audit Board #1
CONTAINER2,TABULATOR1,BATCH4,6,1-4-6,0.024273506122438730,N,Audit Board #1
CONTAINER1,TABULATOR1,BATCH1,19,1-1-19,0.025724786095896671,N,Audit Board #2
CONTAINER1,TABULATOR2,BATCH1,15,2-1-15,0.006700879199748225,N,Audit Board #2
CONTAINER1,TABULATOR2,BATCH2,15,2-2-15,0.017856797084428910,N,Audit Board #2
"""

snapshots[
    "test_ballot_comparison_container_manifest 2"
] = """######## ELECTION INFO ########\r
Election Name,State\r
Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,360,Choice 1-1: 160; Choice 1-2: 0\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_ballot_comparison_container_manifest,BALLOT_COMPARISON,SUPERSIMPLE,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
J1,Audit Board #2,,,,\r
J1,Audit Board #3,,,,\r
J2,Audit Board #1,,,,\r
J2,Audit Board #2,,,,\r
J2,Audit Board #3,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,12,No,,DATETIME,,Choice 1-1: 0; Choice 1-2: 0\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Container,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Discrepancy: Contest 1\r
J1,CONTAINER1,TABULATOR1,BATCH1,19,1-1-19,Round 1: 0.025724786095896671,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER1,TABULATOR2,BATCH1,15,2-1-15,Round 1: 0.006700879199748225,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER1,TABULATOR2,BATCH2,15,2-2-15,Round 1: 0.017856797084428910,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER2,TABULATOR1,BATCH3,2,1-3-2,Round 1: 0.009464169703578658,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER2,TABULATOR1,BATCH3,8,1-3-8,Round 1: 0.014246627323528638,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER2,TABULATOR1,BATCH3,13,1-3-13,Round 1: 0.008481195646651660,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER2,TABULATOR1,BATCH4,3,1-4-3,Round 1: 0.018064599389368317,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER2,TABULATOR1,BATCH4,6,1-4-6,Round 1: 0.024273506122438730,NOT_AUDITED,,Choice 1-1,\r
J2,,TABULATOR1,BATCH1,49,1-1-49,Round 1: 0.002880564051612223,NOT_AUDITED,,,\r
J2,,TABULATOR2,BATCH1,28,2-1-28,Round 1: 0.000308070760244463,NOT_AUDITED,,,\r
J2,,TABULATOR2,BATCH1,36,2-1-36,Round 1: 0.002470081598074708,NOT_AUDITED,,,\r
J2,,TABULATOR2,BATCH2,34,2-2-34,Round 1: 0.025432662687164598,NOT_AUDITED,,,\r
"""

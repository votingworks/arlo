# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_ballot_comparison_container_manifest 1"
] = """Container,Tabulator,Batch Name,Ballot Number,Imprinted ID,Ticket Numbers,Already Audited,Audit Board
CONTAINER2,TABULATOR1,BATCH3,2,1-3-2,0.009464169703578658,N,Audit Board #1
CONTAINER2,TABULATOR1,BATCH3,13,1-3-13,0.008481195646651660,N,Audit Board #1
CONTAINER2,TABULATOR2,BATCH3,27,2-3-27,0.010200999825644035,N,Audit Board #1
CONTAINER2,TABULATOR2,BATCH3,49,2-3-49,0.001536470617324124,N,Audit Board #1
CONTAINER2,TABULATOR2,BATCH4,21,2-4-21,0.002353099293607490,N,Audit Board #1
CONTAINER0,TABULATOR2,BATCH8,47,2-8-47,0.006763450800570999,N,Audit Board #2
CONTAINER1,TABULATOR2,BATCH1,15,2-1-15,0.006700879199748225,N,Audit Board #2
CONTAINER1,TABULATOR2,BATCH2,44,2-2-44,0.000676487665235813,N,Audit Board #2
CONTAINER3,TABULATOR1,BATCH5,6,1-5-6,0.008743453399529091,N,Audit Board #3
CONTAINER3,TABULATOR1,BATCH5,25,1-5-25,0.004991423116656603,N,Audit Board #3
CONTAINER6,TABULATOR2,BATCH6,30,2-6-30,0.009230841414615846,N,Audit Board #3
"""

snapshots[
    "test_ballot_comparison_container_manifest 2"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_ballot_comparison_container_manifest,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,1000,Choice 1-1: 400; Choice 1-2: 0\r
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
1,Contest 1,Targeted,14,No,,DATETIME,,Choice 1-1: 0; Choice 1-2: 0\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Container,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Discrepancy: Contest 1\r
J1,CONTAINER0,TABULATOR2,BATCH8,47,2-8-47,Round 1: 0.006763450800570999,NOT_AUDITED,,,\r
J1,CONTAINER1,TABULATOR2,BATCH1,15,2-1-15,Round 1: 0.006700879199748225,NOT_AUDITED,,,\r
J1,CONTAINER1,TABULATOR2,BATCH2,44,2-2-44,Round 1: 0.000676487665235813,NOT_AUDITED,,,\r
J1,CONTAINER2,TABULATOR1,BATCH3,2,1-3-2,Round 1: 0.009464169703578658,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER2,TABULATOR1,BATCH3,13,1-3-13,Round 1: 0.008481195646651660,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER2,TABULATOR2,BATCH3,27,2-3-27,Round 1: 0.010200999825644035,NOT_AUDITED,,,\r
J1,CONTAINER2,TABULATOR2,BATCH3,49,2-3-49,Round 1: 0.001536470617324124,NOT_AUDITED,,,\r
J1,CONTAINER2,TABULATOR2,BATCH4,21,2-4-21,Round 1: 0.002353099293607490,NOT_AUDITED,,,\r
J1,CONTAINER3,TABULATOR1,BATCH5,6,1-5-6,Round 1: 0.008743453399529091,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER3,TABULATOR1,BATCH5,25,1-5-25,Round 1: 0.004991423116656603,NOT_AUDITED,,Choice 1-1,\r
J1,CONTAINER6,TABULATOR2,BATCH6,30,2-6-30,Round 1: 0.009230841414615846,NOT_AUDITED,,,\r
J2,,TABULATOR1,BATCH1,49,1-1-49,Round 1: 0.002880564051612223,NOT_AUDITED,,,\r
J2,,TABULATOR2,BATCH1,28,2-1-28,Round 1: 0.000308070760244463,NOT_AUDITED,,,\r
J2,,TABULATOR2,BATCH1,36,2-1-36,Round 1: 0.002470081598074708,NOT_AUDITED,,,\r
"""

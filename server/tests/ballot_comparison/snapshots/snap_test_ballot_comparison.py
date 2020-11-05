# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_ballot_comparison_cvr_metadata 1"
] = """Tabulator,Batch Name,Ballot Number,Imprinted ID,Ticket Numbers,Already Audited,Audit Board
TABULATOR1,BATCH1,1,1-1-1,0.243550726331576894,N,Audit Board #1
TABULATOR1,BATCH2,2,1-2-2,0.125871889047705889,N,Audit Board #1
TABULATOR1,BATCH2,3,1-2-3,0.126622033568908859,N,Audit Board #1
TABULATOR2,BATCH2,2,2-2-2,0.053992217600758631,N,Audit Board #1
TABULATOR2,BATCH2,3,2-2-3,0.255119157791673311,N,Audit Board #1
TABULATOR2,BATCH2,4,2-2-4,"0.064984443990590400,0.069414660569975443",N,Audit Board #1
TABULATOR2,BATCH2,5,2-2-5,"0.442956417641278897,0.492638838970333256",N,Audit Board #1
TABULATOR2,BATCH2,6,2-2-6,0.300053574780458718,N,Audit Board #1
"""

snapshots["test_ballot_comparison_two_rounds 1"] = {
    "key": "supersimple",
    "prob": None,
    "size": 22,
}

snapshots["test_ballot_comparison_two_rounds 2"] = {
    "numSamples": 10,
    "numSamplesAudited": 0,
    "numUnique": 8,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_ballot_comparison_two_rounds 3"] = {
    "numSamples": 12,
    "numSamplesAudited": 0,
    "numUnique": 10,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots[
    "test_ballot_comparison_two_rounds 4"
] = """######## ELECTION INFO ########\r
Election Name,State\r
Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,24,Choice 1-1: 14; Choice 1-2: 8\r
Contest 2,Opportunistic,1,2,30,Choice 2-1: 28; Choice 2-2: 12; Choice 2-3: 16\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_ballot_comparison_two_rounds,BALLOT_COMPARISON,SUPERSIMPLE,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
J2,Audit Board #1,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,22,No,3.9787903602,DATETIME,DATETIME,Choice 1-1: 10; Choice 1-2: 8\r
1,Contest 2,Opportunistic,,No,3.1903597519,DATETIME,DATETIME,Choice 2-1: 14; Choice 2-2: 8; Choice 2-3: 8\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Discrepancy: Contest 1,Audit Result: Contest 2,CVR Result: Contest 2,Discrepancy: Contest 2\r
J1,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.243550726331576894,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,2,1-2-2,Round 1: 0.125871889047705889,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,3,1-2-3,Round 1: 0.126622033568908859,AUDITED,"Choice 1-1, Choice 1-2",Choice 1-1,1,"Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-3",2\r
J1,TABULATOR2,BATCH2,2,2-2-2,Round 1: 0.053992217600758631,AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2, Choice 2-3",0\r
J1,TABULATOR2,BATCH2,3,2-2-3,Round 1: 0.255119157791673311,AUDITED,BLANK,Choice 1-1,1,BLANK,"Choice 2-1, Choice 2-3",1\r
J1,TABULATOR2,BATCH2,4,2-2-4,"Round 1: 0.064984443990590400, 0.069414660569975443",AUDITED,,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH2,5,2-2-5,"Round 1: 0.442956417641278897, 0.492638838970333256",AUDITED,,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR2,BATCH2,6,2-2-6,Round 1: 0.300053574780458718,AUDITED,,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.476019554092109137,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J2,TABULATOR1,BATCH1,2,1-1-2,Round 1: 0.511105635717372621,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR1,BATCH1,3,1-1-3,Round 1: 0.242392535590495322,NOT_FOUND,,Choice 1-2,2,,"Choice 2-1, Choice 2-2",2\r
J2,TABULATOR1,BATCH2,1,1-2-1,Round 1: 0.200269401620671924,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH1,1,2-1-1,Round 1: 0.174827909206366766,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J2,TABULATOR2,BATCH2,1,2-2-1,Round 1: 0.185417954749015145,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.252054739518646128, 0.297145021317217438",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2, Choice 2-3",0\r
J2,TABULATOR2,BATCH2,3,2-2-3,"Round 1: 0.179114059650472941, 0.443867094961314498",AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,5,2-2-5,Round 1: 0.462119987445142117,AUDITED,Choice 1-1,,0,,"Choice 2-1, Choice 2-2",1\r
J2,TABULATOR2,BATCH2,6,2-2-6,Round 1: 0.414184312862040881,AUDITED,,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
"""

snapshots[
    "test_ballot_comparison_two_rounds 5"
] = """######## ELECTION INFO ########\r
Election Name,State\r
Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,24,Choice 1-1: 14; Choice 1-2: 8\r
Contest 2,Opportunistic,1,2,30,Choice 2-1: 28; Choice 2-2: 12; Choice 2-3: 16\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_ballot_comparison_two_rounds,BALLOT_COMPARISON,SUPERSIMPLE,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
J2,Audit Board #1,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,22,No,3.9787903602,DATETIME,DATETIME,Choice 1-1: 10; Choice 1-2: 8\r
1,Contest 2,Opportunistic,,No,3.1903597519,DATETIME,DATETIME,Choice 2-1: 14; Choice 2-2: 8; Choice 2-3: 8\r
2,Contest 1,Targeted,24,Yes,<0.0000000001,DATETIME,DATETIME,Choice 1-1: 12; Choice 1-2: 7\r
2,Contest 2,Opportunistic,,No,0.8846022263,DATETIME,DATETIME,Choice 2-1: 15; Choice 2-2: 5; Choice 2-3: 12\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Discrepancy: Contest 1,Audit Result: Contest 2,CVR Result: Contest 2,Discrepancy: Contest 2\r
J1,TABULATOR1,BATCH1,1,1-1-1,"Round 1: 0.243550726331576894, Round 2: 0.686337915847173217",AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,2,1-2-2,"Round 1: 0.125871889047705889, Round 2: 0.752068917437552786",AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,3,1-2-3,"Round 1: 0.126622033568908859, Round 2: 0.570682515619614792",AUDITED,"Choice 1-1, Choice 1-2",Choice 1-1,1,"Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-3",2\r
J1,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.053992217600758631, Round 2: 0.528652598036440834",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2, Choice 2-3",0\r
J1,TABULATOR2,BATCH2,3,2-2-3,Round 1: 0.255119157791673311,AUDITED,BLANK,Choice 1-1,1,BLANK,"Choice 2-1, Choice 2-3",1\r
J1,TABULATOR2,BATCH2,4,2-2-4,"Round 1: 0.064984443990590400, 0.069414660569975443, Round 2: 0.662654312843285447, 0.739178008942093721",AUDITED,,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH2,5,2-2-5,"Round 1: 0.442956417641278897, 0.492638838970333256",AUDITED,,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR2,BATCH2,6,2-2-6,"Round 1: 0.300053574780458718, Round 2: 0.539920212714138536, 0.614239889448737812",AUDITED,,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.476019554092109137,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J2,TABULATOR1,BATCH1,2,1-1-2,"Round 1: 0.511105635717372621, Round 2: 0.583472201399663519",AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR1,BATCH1,3,1-1-3,"Round 1: 0.242392535590495322, Round 2: 0.705264140168043487",NOT_FOUND,,Choice 1-2,2,,"Choice 2-1, Choice 2-2",2\r
J2,TABULATOR1,BATCH2,1,1-2-1,"Round 1: 0.200269401620671924, Round 2: 0.588219390083415326",AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH1,1,2-1-1,"Round 1: 0.174827909206366766, Round 2: 0.638759896009674755, 0.666161104573622944, 0.688295361956370024",AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J2,TABULATOR2,BATCH2,1,2-2-1,Round 1: 0.185417954749015145,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.252054739518646128, 0.297145021317217438",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2, Choice 2-3",0\r
J2,TABULATOR2,BATCH2,3,2-2-3,"Round 1: 0.179114059650472941, 0.443867094961314498, Round 2: 0.553767880261132538",AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,5,2-2-5,"Round 1: 0.462119987445142117, Round 2: 0.593645562906652185, 0.727818415897312844",AUDITED,Choice 1-1,,0,,"Choice 2-1, Choice 2-2",1\r
J2,TABULATOR2,BATCH2,6,2-2-6,Round 1: 0.414184312862040881,AUDITED,,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J1,TABULATOR1,BATCH1,2,1-1-2,Round 2: 0.658361514845611561,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH1,2,2-1-2,Round 2: 0.651118570553261125,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH2,1,2-2-1,Round 2: 0.607927957276839128,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR1,BATCH2,3,1-2-3,Round 2: 0.556310137163677574,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH1,2,2-1-2,Round 2: 0.677864268646804078,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,4,2-2-4,"Round 2: 0.583133559190710795, 0.685610948371080498",AUDITED,,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
"""

snapshots["test_set_contest_metadata_from_cvrs 1"] = {
    "choices": [
        {"name": "Choice 2-1", "num_votes": 28},
        {"name": "Choice 2-2", "num_votes": 12},
        {"name": "Choice 2-3", "num_votes": 16},
    ],
    "num_winners": 1,
    "total_ballots_cast": 30,
    "votes_allowed": 2,
}

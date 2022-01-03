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
TABULATOR2,BATCH2,3,2-2-4,0.255119157791673311,N,Audit Board #1
TABULATOR2,BATCH2,4,2-2-5,"0.064984443990590400,0.069414660569975443",N,Audit Board #1
TABULATOR2,BATCH2,5,2-2-6,0.442956417641278897,N,Audit Board #1
TABULATOR2,BATCH2,6,,0.300053574780458718,N,Audit Board #1
"""

snapshots["test_ballot_comparison_multiple_targeted_contests_sample_size 1"] = [
    ({"key": "supersimple", "prob": None, "size": 10},)
]

snapshots["test_ballot_comparison_two_rounds 1"] = {
    "key": "supersimple",
    "prob": None,
    "size": 20,
}

snapshots["test_ballot_comparison_two_rounds 2"] = {
    "numSamples": 9,
    "numSamplesAudited": 0,
    "numUnique": 8,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_ballot_comparison_two_rounds 3"] = {
    "numSamples": 11,
    "numSamplesAudited": 0,
    "numUnique": 9,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots[
    "test_ballot_comparison_two_rounds 4"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_ballot_comparison_two_rounds,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,30,Choice 1-1: 14; Choice 1-2: 6\r
Contest 2,Opportunistic,1,2,30,Choice 2-1: 26; Choice 2-2: 12; Choice 2-3: 14\r
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
1,Contest 1,Targeted,20,No,1.0,DATETIME,DATETIME,Choice 1-1: 9; Choice 1-2: 7\r
1,Contest 2,Opportunistic,,No,1.0,DATETIME,DATETIME,Choice 2-1: 14; Choice 2-2: 8; Choice 2-3: 9\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Discrepancy: Contest 1,Audit Result: Contest 2,CVR Result: Contest 2,Discrepancy: Contest 2\r
J1,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.243550726331576894,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,2,1-2-2,Round 1: 0.125871889047705889,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,3,1-2-3,Round 1: 0.126622033568908859,AUDITED,"Choice 1-1, Choice 1-2",Choice 1-1,1,"Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-3",2\r
J1,TABULATOR2,BATCH2,2,2-2-2,Round 1: 0.053992217600758631,AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,"Choice 2-1, Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-2, Choice 2-3",\r
J1,TABULATOR2,BATCH2,3,2-2-4,Round 1: 0.255119157791673311,AUDITED,BLANK,,,BLANK,"Choice 2-1, Choice 2-3",1\r
J1,TABULATOR2,BATCH2,4,2-2-5,"Round 1: 0.064984443990590400, 0.069414660569975443",AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR2,BATCH2,5,2-2-6,Round 1: 0.442956417641278897,AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH2,6,,Round 1: 0.300053574780458718,NOT_FOUND,,,2,,,2\r
J2,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.476019554092109137,AUDITED,Choice 1-1,Choice 1-2,-2,Choice 2-1,"Choice 2-1, Choice 2-2",-1\r
J2,TABULATOR1,BATCH1,3,1-1-3,Round 1: 0.242392535590495322,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J2,TABULATOR1,BATCH2,1,1-2-1,Round 1: 0.200269401620671924,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH1,1,2-1-1,Round 1: 0.174827909206366766,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J2,TABULATOR2,BATCH2,1,2-2-1,Round 1: 0.185417954749015145,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.252054739518646128, 0.297145021317217438",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,"Choice 2-1, Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-2, Choice 2-3",\r
J2,TABULATOR2,BATCH2,3,2-2-4,"Round 1: 0.179114059650472941, 0.443867094961314498",AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,5,2-2-6,Round 1: 0.462119987445142117,AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,6,,Round 1: 0.414184312862040881,AUDITED,Choice 1-1,,2,"Choice 2-1, Choice 2-3",,2\r
"""

snapshots[
    "test_ballot_comparison_two_rounds 5"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_ballot_comparison_two_rounds,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,30,Choice 1-1: 14; Choice 1-2: 6\r
Contest 2,Opportunistic,1,2,30,Choice 2-1: 26; Choice 2-2: 12; Choice 2-3: 14\r
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
1,Contest 1,Targeted,20,No,1.0,DATETIME,DATETIME,Choice 1-1: 9; Choice 1-2: 7\r
1,Contest 2,Opportunistic,,No,1.0,DATETIME,DATETIME,Choice 2-1: 14; Choice 2-2: 8; Choice 2-3: 9\r
2,Contest 1,Targeted,10,Yes,0,DATETIME,DATETIME,Choice 1-1: 6; Choice 1-2: 2\r
2,Contest 2,Opportunistic,,No,1.0,DATETIME,DATETIME,Choice 2-1: 7; Choice 2-2: 3; Choice 2-3: 7\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Discrepancy: Contest 1,Audit Result: Contest 2,CVR Result: Contest 2,Discrepancy: Contest 2\r
J1,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.243550726331576894,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,2,1-2-2,Round 1: 0.125871889047705889,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR1,BATCH2,3,1-2-3,"Round 1: 0.126622033568908859, Round 2: 0.570682515619614792",AUDITED,"Choice 1-1, Choice 1-2",Choice 1-1,1,"Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-3",2\r
J1,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.053992217600758631, Round 2: 0.528652598036440834",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,"Choice 2-1, Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-2, Choice 2-3",\r
J1,TABULATOR2,BATCH2,3,2-2-4,Round 1: 0.255119157791673311,AUDITED,BLANK,,,BLANK,"Choice 2-1, Choice 2-3",1\r
J1,TABULATOR2,BATCH2,4,2-2-5,"Round 1: 0.064984443990590400, 0.069414660569975443",AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J1,TABULATOR2,BATCH2,5,2-2-6,"Round 1: 0.442956417641278897, Round 2: 0.492638838970333256",AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J1,TABULATOR2,BATCH2,6,,"Round 1: 0.300053574780458718, Round 2: 0.539920212714138536",NOT_FOUND,,,2,,,2\r
J2,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.476019554092109137,AUDITED,Choice 1-1,Choice 1-2,-2,Choice 2-1,"Choice 2-1, Choice 2-2",-1\r
J2,TABULATOR1,BATCH1,3,1-1-3,Round 1: 0.242392535590495322,AUDITED,Choice 1-2,Choice 1-2,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J2,TABULATOR1,BATCH2,1,1-2-1,"Round 1: 0.200269401620671924, Round 2: 0.588219390083415326",AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH1,1,2-1-1,Round 1: 0.174827909206366766,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
J2,TABULATOR2,BATCH2,1,2-2-1,Round 1: 0.185417954749015145,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.252054739518646128, 0.297145021317217438",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,"Choice 2-1, Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-2, Choice 2-3",\r
J2,TABULATOR2,BATCH2,3,2-2-4,"Round 1: 0.179114059650472941, 0.443867094961314498, Round 2: 0.553767880261132538",AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,5,2-2-6,Round 1: 0.462119987445142117,AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,6,,Round 1: 0.414184312862040881,AUDITED,Choice 1-1,,2,"Choice 2-1, Choice 2-3",,2\r
J2,TABULATOR1,BATCH1,2,1-1-2,"Round 2: 0.511105635717372621, 0.583472201399663519",AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR1,BATCH2,3,1-2-3,Round 2: 0.556310137163677574,AUDITED,Choice 1-1,Choice 1-1,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",\r
J2,TABULATOR2,BATCH2,4,2-2-5,Round 2: 0.583133559190710795,AUDITED,CONTEST_NOT_ON_BALLOT,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",\r
"""

snapshots[
    "test_ballot_comparison_union_choice_names 1"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_ballot_comparison_union_choice_names,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,30,Choice 1-1: 20; Choice 1-2: 6; overvote: 1; undervote: 1\r
Contest 2,Opportunistic,1,1,30,Choice 2-1: 16; Choice 2-2: 6; overvote: 0; undervote: 0; Choice 2-3: 6\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_ballot_comparison_union_choice_names,BALLOT_COMPARISON,SUPERSIMPLE,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
J2,Audit Board #1,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,12,Yes,0.047266213,DATETIME,DATETIME,Choice 1-1: 9; Choice 1-2: 3; overvote: 0; undervote: 0\r
1,Contest 2,Opportunistic,,No,0.1740640692,DATETIME,DATETIME,Choice 2-1: 4; Choice 2-2: 2; overvote: 0; undervote: 0; Choice 2-3: 4\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Discrepancy: Contest 1,Audit Result: Contest 2,CVR Result: Contest 2,Discrepancy: Contest 2\r
J1,0001,BATCH1,1,0001013415,Round 1: 0.163888857982405419,AUDITED,Choice 1-2,Choice 1-2,,Choice 2-1,Choice 2-1,\r
J1,0001,BATCH2,3,0001000417,"Round 1: 0.032225032864873362, 0.160129023760942294",AUDITED,Choice 1-2,Choice 1-2,,Choice 2-2,Choice 2-2,\r
J1,0002,BATCH1,3,0002003173,Round 1: 0.184936923730251080,AUDITED,Choice 1-1,Choice 1-1,,Choice 2-1,Choice 2-1,\r
J1,0002,BATCH2,5,0002000175,"Round 1: 0.128937575131137250, 0.240487859312182291",AUDITED,Choice 1-1,Choice 1-1,,Choice 2-2,Choice 2-2,\r
J2,0001,BATCH1,1,0001013415,Round 1: 0.228946820159681463,AUDITED,Choice 1-1,Choice 1-1,,Choice 2-1,Choice 2-1,\r
J2,0001,BATCH2,3,0001000417,Round 1: 0.269793733438455805,AUDITED,Choice 1-1,Choice 1-1,,Choice 2-3,Choice 2-3,\r
J2,0002,BATCH1,3,0002003173,Round 1: 0.328294241227374952,AUDITED,Choice 1-1,Choice 1-1,,Choice 2-1,Choice 2-1,\r
J2,0002,BATCH2,1,0002000171,Round 1: 0.390715133294243377,AUDITED,Choice 1-1,Choice 1-1,,Choice 2-3,Choice 2-3,\r
J2,0002,BATCH2,2,0002000172,Round 1: 0.064290634474137509,AUDITED,Choice 1-1,Choice 1-1,,Choice 2-3,Choice 2-3,\r
J2,0002,BATCH2,5,0002000175,Round 1: 0.212277542626930704,AUDITED,Choice 1-1,Choice 1-1,,Choice 2-3,Choice 2-3,\r
"""

snapshots["test_set_contest_metadata_on_contest_creation 1"] = {
    "choices": [
        {"name": "Choice 2-1", "num_votes": 26},
        {"name": "Choice 2-2", "num_votes": 12},
        {"name": "Choice 2-3", "num_votes": 14},
    ],
    "total_ballots_cast": 30,
    "votes_allowed": 2,
}

snapshots["test_set_contest_metadata_on_manifest_and_cvr_upload 1"] = {
    "choices": [
        {"name": "Choice 2-1", "num_votes": 26},
        {"name": "Choice 2-2", "num_votes": 12},
        {"name": "Choice 2-3", "num_votes": 14},
    ],
    "total_ballots_cast": 30,
    "votes_allowed": 2,
}

snapshots["test_set_contest_metadata_on_manifest_and_cvr_upload 2"] = {
    "choices": [
        {"name": "Choice 2-1", "num_votes": 19},
        {"name": "Choice 2-2", "num_votes": 9},
        {"name": "Choice 2-3", "num_votes": 10},
    ],
    "total_ballots_cast": 24,
    "votes_allowed": 2,
}

# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_ballot_comparison_cardstyledata_two_rounds[election_id0] 1"] = {
    "key": "default",
    "prob": None,
    "size": 15,
}

snapshots["test_ballot_comparison_cardstyledata_two_rounds[election_id0] 10"] = {
    "numSamples": 4,
    "numSamplesAudited": 4,
    "numUnique": 3,
    "numUniqueAudited": 3,
    "status": "COMPLETE",
}

snapshots[
    "test_ballot_comparison_cardstyledata_two_rounds[election_id0] 11"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_ballot_comparison_cardstyledata_two_rounds[election_id0],Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Vote Totals\r
Contest 1,Targeted,1,1,22,Choice 1-1: 14; Choice 1-2: 6\r
Contest 2,Opportunistic,1,2,28,Choice 2-1: 24; Choice 2-2: 10; Choice 2-3: 14\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_ballot_comparison_cardstyledata_two_rounds[election_id0],BALLOT_COMPARISON,CARD_STYLE_DATA,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
J1,Audit Board #1,,,,\r
J2,Audit Board #1,,,,\r
J2,Audit Board #1,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,15,No,0.3998984553,DATETIME,DATETIME,Choice 1-1: 11; Choice 1-2: 9\r
1,Contest 2,Opportunistic,,No,0.5072508038,DATETIME,DATETIME,Choice 2-1: 10; Choice 2-2: 7; Choice 2-3: 6\r
2,Contest 1,Targeted,7,Yes,0,DATETIME,DATETIME,Choice 1-1: 6; Choice 1-2: 0\r
2,Contest 2,Opportunistic,,No,0.2880935813,DATETIME,DATETIME,Choice 2-1: 5; Choice 2-2: 1; Choice 2-3: 4\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Audit Result: Contest 2,CVR Result: Contest 2,Change in Results: Contest 2,Change in Margin: Contest 2\r
J1,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.243550726331576894,AUDITED,"Choice 1-2, INVALID_WRITE_IN",Choice 1-2,,,"Choice 2-1, Choice 2-2, INVALID_WRITE_IN","Choice 2-1, Choice 2-2",,\r
J1,TABULATOR1,BATCH2,2,1-2-2,Round 1: 0.125871889047705889,AUDITED,Choice 1-2,Choice 1-2,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",,\r
J1,TABULATOR1,BATCH2,3,1-2-3,"Round 1: 0.126622033568908859, 0.570682515619614792",AUDITED,"Choice 1-1, Choice 1-2",Choice 1-1,Choice 1-2: -1,1,"Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-3",Choice 2-1: +1; Choice 2-2: -1,2\r
J1,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.053992217600758631, 0.528652598036440834",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,,"Choice 2-1, Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-2, Choice 2-3",,\r
J2,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.476019554092109137,AUDITED,"Choice 1-1, INVALID_WRITE_IN",Choice 1-2,Choice 1-1: -1; Choice 1-2: +1,-2,"Choice 2-1, INVALID_WRITE_IN","Choice 2-1, Choice 2-2",Choice 2-2: +1,-1\r
J2,TABULATOR1,BATCH1,2,1-1-2,"Round 1: 0.511105635717372621, Round 2: 0.583472201399663519",AUDITED,BLANK,Choice 1-1,Choice 1-1: +1,1,BLANK,"Choice 2-1, Choice 2-3",Choice 2-1: +1; Choice 2-3: +1,1\r
J2,TABULATOR1,BATCH1,3,1-1-3,Round 1: 0.242392535590495322,AUDITED,Choice 1-2,Choice 1-2,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",,\r
J2,TABULATOR1,BATCH2,1,1-2-1,"Round 1: 0.200269401620671924, Round 2: 0.588219390083415326",AUDITED,Choice 1-1,Choice 1-1,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",,\r
J2,TABULATOR1,BATCH2,3,1-2-3,Round 1: 0.556310137163677574,AUDITED,Choice 1-1,Choice 1-1,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",,\r
J2,TABULATOR2,BATCH1,1,2-1-1,"Round 1: 0.174827909206366766, Round 2: 0.638759896009674755, 0.666161104573622944",AUDITED,Choice 1-1,Choice 1-1,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",,\r
J2,TABULATOR2,BATCH2,1,2-2-1,Round 1: 0.185417954749015145,AUDITED,Choice 1-1,Choice 1-1,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",,\r
J2,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.252054739518646128, 0.297145021317217438",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,,"Choice 2-1, Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-2, Choice 2-3",,\r
J1,TABULATOR1,BATCH1,2,1-1-2,Round 2: 0.658361514845611561,AUDITED,"Choice 1-1, INVALID_WRITE_IN",Choice 1-1,,,"Choice 2-1, Choice 2-3, INVALID_WRITE_IN","Choice 2-1, Choice 2-3",,\r
J1,TABULATOR2,BATCH1,2,2-1-2,Round 2: 0.651118570553261125,AUDITED,Choice 1-1,Choice 1-1,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",,\r
J1,TABULATOR2,BATCH2,1,2-2-1,Round 2: 0.607927957276839128,AUDITED,Choice 1-1,Choice 1-1,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",,\r
"""

snapshots["test_ballot_comparison_cardstyledata_two_rounds[election_id0] 2"] = {
    "numSamples": 6,
    "numSamplesAudited": 0,
    "numUnique": 4,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_ballot_comparison_cardstyledata_two_rounds[election_id0] 3"] = {
    "numSamples": 9,
    "numSamplesAudited": 0,
    "numUnique": 8,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_ballot_comparison_cardstyledata_two_rounds[election_id0] 4"] = {
    "numSamples": 6,
    "numSamplesAudited": 6,
    "numUnique": 4,
    "numUniqueAudited": 4,
    "status": "COMPLETE",
}

snapshots["test_ballot_comparison_cardstyledata_two_rounds[election_id0] 5"] = {
    "numSamples": 9,
    "numSamplesAudited": 9,
    "numUnique": 8,
    "numUniqueAudited": 8,
    "status": "IN_PROGRESS",
}

snapshots["test_ballot_comparison_cardstyledata_two_rounds[election_id0] 6"] = {
    "numSamples": 6,
    "numSamplesAudited": 6,
    "numUnique": 4,
    "numUniqueAudited": 4,
    "status": "COMPLETE",
}

snapshots["test_ballot_comparison_cardstyledata_two_rounds[election_id0] 7"] = {
    "numSamples": 9,
    "numSamplesAudited": 9,
    "numUnique": 8,
    "numUniqueAudited": 8,
    "status": "COMPLETE",
}

snapshots[
    "test_ballot_comparison_cardstyledata_two_rounds[election_id0] 8"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_ballot_comparison_cardstyledata_two_rounds[election_id0],Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Vote Totals\r
Contest 1,Targeted,1,1,22,Choice 1-1: 14; Choice 1-2: 6\r
Contest 2,Opportunistic,1,2,28,Choice 2-1: 24; Choice 2-2: 10; Choice 2-3: 14\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_ballot_comparison_cardstyledata_two_rounds[election_id0],BALLOT_COMPARISON,CARD_STYLE_DATA,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
J2,Audit Board #1,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,15,No,0.3998984553,DATETIME,DATETIME,Choice 1-1: 11; Choice 1-2: 9\r
1,Contest 2,Opportunistic,,No,0.5072508038,DATETIME,DATETIME,Choice 2-1: 10; Choice 2-2: 7; Choice 2-3: 6\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Audit Result: Contest 2,CVR Result: Contest 2,Change in Results: Contest 2,Change in Margin: Contest 2\r
J1,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.243550726331576894,AUDITED,"Choice 1-2, INVALID_WRITE_IN",Choice 1-2,,,"Choice 2-1, Choice 2-2, INVALID_WRITE_IN","Choice 2-1, Choice 2-2",,\r
J1,TABULATOR1,BATCH2,2,1-2-2,Round 1: 0.125871889047705889,AUDITED,Choice 1-2,Choice 1-2,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",,\r
J1,TABULATOR1,BATCH2,3,1-2-3,"Round 1: 0.126622033568908859, 0.570682515619614792",AUDITED,"Choice 1-1, Choice 1-2",Choice 1-1,Choice 1-2: -1,1,"Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-3",Choice 2-1: +1; Choice 2-2: -1,2\r
J1,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.053992217600758631, 0.528652598036440834",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,,"Choice 2-1, Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-2, Choice 2-3",,\r
J2,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.476019554092109137,AUDITED,"Choice 1-1, INVALID_WRITE_IN",Choice 1-2,Choice 1-1: -1; Choice 1-2: +1,-2,"Choice 2-1, INVALID_WRITE_IN","Choice 2-1, Choice 2-2",Choice 2-2: +1,-1\r
J2,TABULATOR1,BATCH1,2,1-1-2,Round 1: 0.511105635717372621,AUDITED,BLANK,Choice 1-1,Choice 1-1: +1,1,BLANK,"Choice 2-1, Choice 2-3",Choice 2-1: +1; Choice 2-3: +1,1\r
J2,TABULATOR1,BATCH1,3,1-1-3,Round 1: 0.242392535590495322,AUDITED,Choice 1-2,Choice 1-2,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",,\r
J2,TABULATOR1,BATCH2,1,1-2-1,Round 1: 0.200269401620671924,AUDITED,Choice 1-1,Choice 1-1,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",,\r
J2,TABULATOR1,BATCH2,3,1-2-3,Round 1: 0.556310137163677574,AUDITED,Choice 1-1,Choice 1-1,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",,\r
J2,TABULATOR2,BATCH1,1,2-1-1,Round 1: 0.174827909206366766,AUDITED,Choice 1-1,Choice 1-1,,,"Choice 2-1, Choice 2-2","Choice 2-1, Choice 2-2",,\r
J2,TABULATOR2,BATCH2,1,2-2-1,Round 1: 0.185417954749015145,AUDITED,Choice 1-1,Choice 1-1,,,"Choice 2-1, Choice 2-3","Choice 2-1, Choice 2-3",,\r
J2,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.252054739518646128, 0.297145021317217438",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",,,"Choice 2-1, Choice 2-2, Choice 2-3","Choice 2-1, Choice 2-2, Choice 2-3",,\r
"""

snapshots["test_ballot_comparison_cardstyledata_two_rounds[election_id0] 9"] = {
    "numSamples": 3,
    "numSamplesAudited": 3,
    "numUnique": 3,
    "numUniqueAudited": 3,
    "status": "COMPLETE",
}

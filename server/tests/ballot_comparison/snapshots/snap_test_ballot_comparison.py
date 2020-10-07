# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_ballot_comparison_round_1 1"] = {
    "key": "supersimple",
    "prob": None,
    "size": 11,
}

snapshots["test_set_contest_metadata_from_cvrs 1"] = {
    "choices": [
        {"name": "Choice 2-1", "num_votes": 30},
        {"name": "Choice 2-2", "num_votes": 14},
        {"name": "Choice 2-3", "num_votes": 16},
    ],
    "num_winners": 1,
    "total_ballots_cast": 30,
    "votes_allowed": 2,
}

snapshots[
    "test_ballot_comparison_round_1 2"
] = """######## ELECTION INFO ########\r
Election Name,State\r
Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,24,Choice 1-1: 24; Choice 1-2: 12\r
Contest 2,Opportunistic,1,2,30,Choice 2-1: 30; Choice 2-2: 14; Choice 2-3: 16\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_ballot_comparison_round_1,BALLOT_COMPARISON,10%,1234567890,Yes\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,11,No,0.7413124393,DATETIME,DATETIME,Choice 1-1: 4; Choice 1-2: 5\r
1,Contest 2,Opportunistic,,No,0.3142300101,DATETIME,DATETIME,Choice 2-1: 4; Choice 2-2: 4; Choice 2-3: 0\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Batch Name,Ballot Position,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,Audit Result: Contest 2\r
J1,1 - 2,1,Round 1: 0.372324681332676827,AUDITED,Choice 1-1,Choice 2-1\r
J1,1 - 2,3,"Round 1: 0.159718557209511424, 0.357700029068711883",AUDITED,Choice 1-2,Choice 2-2\r
J1,2 - 1,2,Round 1: 0.221314572958397938,AUDITED,Choice 1-2,Choice 2-2\r
J1,2 - 2,2,Round 1: 0.373070595354246113,AUDITED,Choice 1-2,Choice 2-2\r
J1,2 - 2,4,Round 1: 0.236178593368060699,NOT_AUDITED,,\r
J2,1 - 1,1,Round 1: 0.387534455946293789,AUDITED,Choice 1-1,Choice 2-1\r
J2,1 - 1,3,Round 1: 0.145351404354762545,AUDITED,Choice 1-1,Choice 2-1\r
J2,1 - 2,1,Round 1: 0.261383583608008902,AUDITED,Choice 1-1,Choice 2-1\r
J2,2 - 2,3,Round 1: 0.394565893682896974,AUDITED,Choice 1-2,Choice 2-2\r
J2,2 - 2,4,Round 1: 0.267753678346758280,NOT_AUDITED,,\r
"""

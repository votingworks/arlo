# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_set_contest_metadata_from_cvrs 1'] = {
    'choices': [
        {
            'name': 'Choice 2-1',
            'num_votes': 30
        },
        {
            'name': 'Choice 2-2',
            'num_votes': 14
        },
        {
            'name': 'Choice 2-3',
            'num_votes': 16
        }
    ],
    'num_winners': 1,
    'total_ballots_cast': 30,
    'votes_allowed': 2
}

snapshots['test_ballot_comparison_two_rounds 1'] = {
    'key': 'supersimple',
    'prob': None,
    'size': 22
}

snapshots['test_ballot_comparison_two_rounds 2'] = '''######## ELECTION INFO ########\r
Election Name,State\r
Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,24,Choice 1-1: 16; Choice 1-2: 10\r
Contest 2,Opportunistic,1,2,30,Choice 2-1: 30; Choice 2-2: 14; Choice 2-3: 16\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_ballot_comparison_two_rounds,BALLOT_COMPARISON,10%,1234567890,Yes\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,22,No,0.1286281729,DATETIME,DATETIME,Choice 1-1: 10; Choice 1-2: 5\r
1,Contest 2,Opportunistic,,No,0.3262537939,DATETIME,DATETIME,Choice 2-1: 8; Choice 2-2: 4; Choice 2-3: 0\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Batch Name,Ballot Position,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,Audit Result: Contest 2\r
J1,1,1,Round 1: 0.253310599579579128,AUDITED,Choice 1-2,\r
J1,1,1,Round 1: 0.204858337714175386,AUDITED,,\r
J1,1,2,Round 1: 0.108800063013793873,AUDITED,Choice 1-1,Choice 2-1\r
J1,1,3,Round 1: 0.039137057734807602,AUDITED,Choice 1-2,Choice 2-2\r
J1,2,1,Round 1: 0.400356648159839639,AUDITED,Choice 1-1,Choice 2-1\r
J1,2,1,"Round 1: 0.294293713236858165, 0.396729958620615556",AUDITED,Choice 1-1,Choice 2-1\r
J1,2,3,Round 1: 0.407924628114473428,AUDITED,Choice 1-1,Choice 2-1\r
J1,2,6,Round 1: 0.467059548587695994,AUDITED,,\r
J2,1,1,"Round 1: 0.093047161560174517, 0.373730886719570665, 0.441070345112650098",AUDITED,,Choice 2-2\r
J2,1,1,"Round 1: 0.249699890162201282, 0.377116835351342164",AUDITED,Choice 1-2,Choice 2-2\r
J2,1,2,"Round 1: 0.102247232087275935, 0.391113953393971944",AUDITED,Choice 1-1,Choice 2-1\r
J2,1,2,Round 1: 0.089733987461263823,AUDITED,Choice 1-1,Choice 2-1\r
J2,1,3,Round 1: 0.273102683954282677,AUDITED,Choice 1-2,Choice 2-2\r
J2,2,1,Round 1: 0.140167565493923455,AUDITED,Choice 1-1,Choice 2-1\r
J2,2,2,Round 1: 0.425418515815626443,AUDITED,"OVERVOTE; Choice 1-1, Choice 1-2","OVERVOTE; Choice 2-1, Choice 2-2"\r
J2,2,3,Round 1: 0.359826480324232628,AUDITED,Choice 1-1,Choice 2-1\r
J2,2,6,Round 1: 0.293871936182799706,AUDITED,,\r
'''

snapshots['test_ballot_comparison_two_rounds 3'] = '''######## ELECTION INFO ########\r
Election Name,State\r
Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,24,Choice 1-1: 16; Choice 1-2: 10\r
Contest 2,Opportunistic,1,2,30,Choice 2-1: 30; Choice 2-2: 14; Choice 2-3: 16\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_ballot_comparison_two_rounds,BALLOT_COMPARISON,10%,1234567890,Yes\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,22,No,0.1286281729,DATETIME,DATETIME,Choice 1-1: 10; Choice 1-2: 5\r
1,Contest 2,Opportunistic,,No,0.3262537939,DATETIME,DATETIME,Choice 2-1: 8; Choice 2-2: 4; Choice 2-3: 0\r
2,Contest 1,Targeted,20,Yes,0.0165452069,DATETIME,DATETIME,Choice 1-1: 5; Choice 1-2: 10\r
2,Contest 2,Opportunistic,,No,0.4277811156,DATETIME,DATETIME,Choice 2-1: 3; Choice 2-2: 5; Choice 2-3: 0\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Batch Name,Ballot Position,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,Audit Result: Contest 2\r
J1,1,1,"Round 1: 0.204858337714175386, Round 2: 0.567851774911924207, 0.652680647839375772",AUDITED,Choice 1-2,Choice 2-2\r
J1,1,1,Round 1: 0.253310599579579128,AUDITED,Choice 1-2,\r
J1,1,2,Round 1: 0.108800063013793873,AUDITED,Choice 1-1,Choice 2-1\r
J1,1,3,"Round 1: 0.039137057734807602, Round 2: 0.658553689247638872",AUDITED,Choice 1-2,Choice 2-2\r
J1,2,1,"Round 1: 0.294293713236858165, 0.396729958620615556",AUDITED,Choice 1-1,Choice 2-1\r
J1,2,1,"Round 1: 0.400356648159839639, Round 2: 0.522999686877146160",AUDITED,Choice 1-1,Choice 2-1\r
J1,2,3,Round 1: 0.407924628114473428,AUDITED,Choice 1-1,Choice 2-1\r
J1,2,6,"Round 1: 0.467059548587695994, Round 2: 0.582671327671878279, 0.733166596483082713",AUDITED,,\r
J2,1,1,"Round 1: 0.249699890162201282, 0.377116835351342164, Round 2: 0.567551223878171148",AUDITED,Choice 1-2,Choice 2-2\r
J2,1,1,"Round 1: 0.093047161560174517, 0.373730886719570665, 0.441070345112650098",AUDITED,,Choice 2-2\r
J2,1,2,"Round 1: 0.102247232087275935, 0.391113953393971944",AUDITED,Choice 1-1,Choice 2-1\r
J2,1,2,Round 1: 0.089733987461263823,AUDITED,Choice 1-1,Choice 2-1\r
J2,1,3,Round 1: 0.273102683954282677,AUDITED,Choice 1-2,Choice 2-2\r
J2,2,1,Round 1: 0.140167565493923455,AUDITED,Choice 1-1,Choice 2-1\r
J2,2,2,Round 1: 0.425418515815626443,AUDITED,"OVERVOTE; Choice 1-1, Choice 1-2","OVERVOTE; Choice 2-1, Choice 2-2"\r
J2,2,3,"Round 1: 0.359826480324232628, Round 2: 0.506025545507775003, 0.520300296510202348, 0.539293040443164915",AUDITED,Choice 1-1,Choice 2-1\r
J2,2,6,Round 1: 0.293871936182799706,AUDITED,,\r
J1,1,3,Round 2: 0.706559115775721775,AUDITED,Choice 1-1,Choice 2-1\r
J1,2,2,"Round 2: 0.496746429801262910, 0.656198082383698996, 0.675041662836981163, 0.703704804809206616",AUDITED,Choice 1-2,Choice 2-2\r
J1,2,4,Round 2: 0.612659360179389854,AUDITED,,\r
J1,2,5,Round 2: 0.502647713554707613,AUDITED,,\r
J2,2,2,"Round 2: 0.607737852329141156, 0.704308803660011215",AUDITED,Choice 1-2,Choice 2-2\r
J2,2,5,Round 2: 0.478039888546290679,AUDITED,,\r
'''

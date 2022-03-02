# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_raire_ballot_comparison_two_rounds 1'] = 27

snapshots['test_raire_ballot_comparison_two_rounds 2'] = '''######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_raire_ballot_comparison_two_rounds,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,30,Choice 1-1: 16; Choice 1-2: 6\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_raire_ballot_comparison_two_rounds,BALLOT_COMPARISON,RAIRE,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
J2,Audit Board #1,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,27,No,1.0,DATETIME,DATETIME,Choice 1-1: 15; Choice 1-2: 9\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Discrepancy: Contest 1\r
J1,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.243550726331576894,AUDITED,Choice 1-2,Choice 1-2,\r
J1,TABULATOR1,BATCH2,2,1-2-2,Round 1: 0.125871889047705889,AUDITED,Choice 1-2,Choice 1-2,\r
J1,TABULATOR1,BATCH2,3,1-2-3,"Round 1: 0.126622033568908859, 0.570682515619614792",AUDITED,"Choice 1-1, Choice 1-2",Choice 1-1,1\r
J1,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.053992217600758631, 0.528652598036440834",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",\r
J1,TABULATOR2,BATCH2,3,2-2-3,Round 1: 0.255119157791673311,AUDITED,Choice 1-1,Choice 1-1,\r
J1,TABULATOR2,BATCH2,4,2-2-4,"Round 1: 0.064984443990590400, 0.069414660569975443",NOT_FOUND,,,2\r
J1,TABULATOR2,BATCH2,5,2-2-5,"Round 1: 0.442956417641278897, 0.492638838970333256",AUDITED,CONTEST_NOT_ON_BALLOT,,\r
J1,TABULATOR2,BATCH2,6,2-2-6,"Round 1: 0.300053574780458718, 0.539920212714138536",AUDITED,CONTEST_NOT_ON_BALLOT,,\r
J2,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.476019554092109137,AUDITED,BLANK,Choice 1-2,-1\r
J2,TABULATOR1,BATCH1,2,1-1-2,Round 1: 0.511105635717372621,AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR1,BATCH1,3,1-1-3,Round 1: 0.242392535590495322,AUDITED,Choice 1-2,Choice 1-2,\r
J2,TABULATOR1,BATCH2,1,1-2-1,Round 1: 0.200269401620671924,AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR1,BATCH2,3,1-2-3,Round 1: 0.556310137163677574,AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR2,BATCH1,1,2-1-1,Round 1: 0.174827909206366766,AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR2,BATCH2,1,2-2-1,Round 1: 0.185417954749015145,AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.252054739518646128, 0.297145021317217438",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",\r
J2,TABULATOR2,BATCH2,3,2-2-3,"Round 1: 0.179114059650472941, 0.443867094961314498, 0.553767880261132538",AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR2,BATCH2,5,2-2-5,Round 1: 0.462119987445142117,AUDITED,CONTEST_NOT_ON_BALLOT,,\r
J2,TABULATOR2,BATCH2,6,2-2-6,Round 1: 0.414184312862040881,AUDITED,CONTEST_NOT_ON_BALLOT,,\r
'''

snapshots['test_raire_ballot_comparison_two_rounds 3'] = '''######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_raire_ballot_comparison_two_rounds,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,30,Choice 1-1: 16; Choice 1-2: 6\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_raire_ballot_comparison_two_rounds,BALLOT_COMPARISON,RAIRE,10%,1234567890,Yes\r
\r
######## AUDIT BOARDS ########\r
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation\r
J1,Audit Board #1,,,,\r
J2,Audit Board #1,,,,\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes\r
1,Contest 1,Targeted,27,No,1.0,DATETIME,DATETIME,Choice 1-1: 15; Choice 1-2: 9\r
2,Contest 1,Targeted,16,Yes,0,DATETIME,DATETIME,Choice 1-1: 9; Choice 1-2: 2\r
\r
######## SAMPLED BALLOTS ########\r
Jurisdiction Name,Tabulator,Batch Name,Ballot Position,Imprinted ID,Ticket Numbers: Contest 1,Audited?,Audit Result: Contest 1,CVR Result: Contest 1,Discrepancy: Contest 1\r
J1,TABULATOR1,BATCH1,1,1-1-1,"Round 1: 0.243550726331576894, Round 2: 0.686337915847173217",AUDITED,Choice 1-2,Choice 1-2,\r
J1,TABULATOR1,BATCH2,2,1-2-2,Round 1: 0.125871889047705889,AUDITED,Choice 1-2,Choice 1-2,\r
J1,TABULATOR1,BATCH2,3,1-2-3,"Round 1: 0.126622033568908859, 0.570682515619614792",AUDITED,"Choice 1-1, Choice 1-2",Choice 1-1,1\r
J1,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.053992217600758631, 0.528652598036440834",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",\r
J1,TABULATOR2,BATCH2,3,2-2-3,Round 1: 0.255119157791673311,AUDITED,Choice 1-1,Choice 1-1,\r
J1,TABULATOR2,BATCH2,4,2-2-4,"Round 1: 0.064984443990590400, 0.069414660569975443, Round 2: 0.662654312843285447",NOT_FOUND,,,2\r
J1,TABULATOR2,BATCH2,5,2-2-5,"Round 1: 0.442956417641278897, 0.492638838970333256",AUDITED,CONTEST_NOT_ON_BALLOT,,\r
J1,TABULATOR2,BATCH2,6,2-2-6,"Round 1: 0.300053574780458718, 0.539920212714138536, Round 2: 0.614239889448737812",AUDITED,CONTEST_NOT_ON_BALLOT,,\r
J2,TABULATOR1,BATCH1,1,1-1-1,Round 1: 0.476019554092109137,AUDITED,BLANK,Choice 1-2,-1\r
J2,TABULATOR1,BATCH1,2,1-1-2,"Round 1: 0.511105635717372621, Round 2: 0.583472201399663519",AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR1,BATCH1,3,1-1-3,"Round 1: 0.242392535590495322, Round 2: 0.705264140168043487",AUDITED,Choice 1-2,Choice 1-2,\r
J2,TABULATOR1,BATCH2,1,1-2-1,"Round 1: 0.200269401620671924, Round 2: 0.588219390083415326",AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR1,BATCH2,3,1-2-3,Round 1: 0.556310137163677574,AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR2,BATCH1,1,2-1-1,"Round 1: 0.174827909206366766, Round 2: 0.638759896009674755, 0.666161104573622944, 0.688295361956370024",AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR2,BATCH2,1,2-2-1,Round 1: 0.185417954749015145,AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR2,BATCH2,2,2-2-2,"Round 1: 0.252054739518646128, 0.297145021317217438",AUDITED,"Choice 1-1, Choice 1-2","Choice 1-1, Choice 1-2",\r
J2,TABULATOR2,BATCH2,3,2-2-3,"Round 1: 0.179114059650472941, 0.443867094961314498, 0.553767880261132538",AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR2,BATCH2,5,2-2-5,"Round 1: 0.462119987445142117, Round 2: 0.593645562906652185",AUDITED,CONTEST_NOT_ON_BALLOT,,\r
J2,TABULATOR2,BATCH2,6,2-2-6,Round 1: 0.414184312862040881,AUDITED,CONTEST_NOT_ON_BALLOT,,\r
J1,TABULATOR1,BATCH1,2,1-1-2,Round 2: 0.658361514845611561,AUDITED,Choice 1-1,Choice 1-1,\r
J1,TABULATOR2,BATCH1,2,2-1-2,Round 2: 0.651118570553261125,AUDITED,Choice 1-1,Choice 1-1,\r
J1,TABULATOR2,BATCH2,1,2-2-1,Round 2: 0.607927957276839128,AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR2,BATCH1,2,2-1-2,Round 2: 0.677864268646804078,AUDITED,Choice 1-1,Choice 1-1,\r
J2,TABULATOR2,BATCH2,4,2-2-4,"Round 2: 0.583133559190710795, 0.685610948371080498",AUDITED,CONTEST_NOT_ON_BALLOT,,\r
'''

import re
from flask.testing import FlaskClient
from typing import List
from tests.routes_tests.test_audit_boards import set_up_audit_board

DATETIME_REGEX = re.compile("\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}")

# TODO This is just a basic snapshot test. We still need to implement more
# comprehensive testing.
def test_audit_admin_report(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    audit_board_round_1_ids: List[str],
):
    for audit_board_id in audit_board_round_1_ids:
        set_up_audit_board(
            client, election_id, jurisdiction_ids[0], contest_ids[0], audit_board_id,
        )
    rv = client.get(f"/election/{election_id}/report")
    report = rv.data.decode("utf-8")
    report = re.sub(DATETIME_REGEX, "DATETIME", report)
    assert report.splitlines() == EXPECTED_AA_REPORT.splitlines()


def test_jurisdiction_admin_report(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    audit_board_round_1_ids: List[str],
):
    for audit_board_id in audit_board_round_1_ids:
        set_up_audit_board(
            client, election_id, jurisdiction_ids[0], contest_ids[0], audit_board_id,
        )
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    report = rv.data.decode("utf-8")
    report = re.sub(DATETIME_REGEX, "DATETIME", report)
    assert report.splitlines() == EXPECTED_JA_REPORT.splitlines()


EXPECTED_AA_REPORT = """####### ELECTION INFO ########
Election Name,Test Election
State,CA

####### CONTESTS ########
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes
Contest 1,Targeted,1,1,1000,candidate 1: 600; candidate 2: 400
Contest 2,Opportunistic,2,2,600,candidate 1: 200; candidate 2: 300; candidate 3: 100

####### AUDIT SETTINGS ########
Audit Name,Test Audit
Risk Limit,10%
Random Seed,1234567890
Online Data Entry?,Yes

####### AUDIT BOARDS ########
Jurisdiction Name,Audit Board Name,Member 1 Name,Member 1 Affiliation,Member 2 Name,Member 2 Affiliation
J1,Audit Board #1,Bubbikin Republican,Democrat,Joe Schmo,Republican
J1,Audit Board #2,Bubbikin Republican,Democrat,Joe Schmo,Republican

####### ROUNDS ########
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes
1,Contest 1,Targeted,119,No,,DATETIME,,candidate 1: 0; candidate 2: 0
1,Contest 2,Opportunistic,119,No,,DATETIME,,candidate 1: 0; candidate 2: 0; candidate 3: 0

####### SAMPLED BALLOTS ########
Jurisdiction Name,Batch Name,Ballot Position,Ticket Numbers,Audited?,Audit Result: Contest 1,Audit Result: Contest 2
J1,1,12,Round 1: 0.029898626,AUDITED,candidate 1,
J1,1,21,Round 1: 0.097507658,AUDITED,candidate 1,
J1,2,5,Round 1: 0.009880204,AUDITED,candidate 1,
J1,2,15,Round 1: 0.083638485,AUDITED,candidate 1,
J1,2,25,Round 1: 0.063921946,AUDITED,candidate 1,
J1,2,26,"Round 1: 0.049415923, 0.081722795",AUDITED,candidate 1,
J1,2,32,Round 1: 0.064344935,AUDITED,candidate 1,
J1,2,46,Round 1: 0.040298630,AUDITED,candidate 1,
J1,2,56,Round 1: 0.122658553,AUDITED,candidate 1,
J1,2,70,Round 1: 0.021941471,AUDITED,candidate 2,
J1,3,2,Round 1: 0.042609199,AUDITED,candidate 2,
J1,3,29,Round 1: 0.005485737,AUDITED,candidate 2,
J1,3,34,"Round 1: 0.024245302, 0.069503402",AUDITED,candidate 2,
J1,3,53,Round 1: 0.079988573,AUDITED,candidate 2,
J1,3,58,Round 1: 0.083486109,AUDITED,candidate 2,
J1,3,64,Round 1: 0.085168554,AUDITED,candidate 2,
J1,3,67,Round 1: 0.094448606,AUDITED,candidate 2,
J1,3,76,Round 1: 0.126272907,AUDITED,candidate 2,
J1,3,77,Round 1: 0.090055481,AUDITED,candidate 2,
J1,3,85,Round 1: 0.119043017,AUDITED,candidate 2,
J1,3,90,Round 1: 0.094088629,AUDITED,candidate 2,
J1,3,97,Round 1: 0.038404368,AUDITED,candidate 2,
J1,3,99,Round 1: 0.075051405,AUDITED,candidate 2,
J1,3,107,Round 1: 0.038234097,AUDITED,BLANK,
J1,3,119,Round 1: 0.103215596,AUDITED,BLANK,
J1,4,0,Round 1: 0.100384496,AUDITED,candidate 1,
J1,4,8,Round 1: 0.036908465,AUDITED,candidate 1,
J1,4,19,Round 1: 0.039175371,AUDITED,candidate 1,
J1,4,23,Round 1: 0.054130711,AUDITED,candidate 1,
J1,4,25,Round 1: 0.084587960,AUDITED,candidate 1,
J1,4,30,Round 1: 0.080450545,AUDITED,candidate 1,
J1,4,50,Round 1: 0.009800391,AUDITED,candidate 1,
J1,4,70,Round 1: 0.103837055,AUDITED,candidate 1,
J1,4,76,Round 1: 0.097877511,AUDITED,candidate 1,
J1,4,79,Round 1: 0.011004647,AUDITED,candidate 1,
J1,4,90,Round 1: 0.019140572,AUDITED,candidate 2,
J1,4,107,Round 1: 0.057789995,AUDITED,candidate 2,
J1,4,112,Round 1: 0.103088425,AUDITED,candidate 2,
J1,4,118,Round 1: 0.011979621,AUDITED,candidate 2,
J1,4,136,Round 1: 0.086176519,AUDITED,candidate 2,
J1,4,138,Round 1: 0.024601007,AUDITED,candidate 2,
J1,4,151,Round 1: 0.099893707,AUDITED,candidate 2,
J1,4,155,Round 1: 0.003280982,AUDITED,candidate 2,
J1,4,156,Round 1: 0.093530676,AUDITED,candidate 2,
J1,4,161,Round 1: 0.002273519,AUDITED,candidate 2,
J1,4,162,Round 1: 0.005583579,AUDITED,candidate 2,
J1,4,163,Round 1: 0.053660633,AUDITED,candidate 2,
J1,4,168,Round 1: 0.117015031,AUDITED,candidate 2,
J1,4,179,Round 1: 0.069783615,AUDITED,candidate 2,
J1,4,188,Round 1: 0.125737179,AUDITED,candidate 2,
J1,4,191,Round 1: 0.054705383,AUDITED,BLANK,
J1,4,195,"Round 1: 0.011605572, 0.104478160",AUDITED,BLANK,
J1,4,197,Round 1: 0.077950055,AUDITED,BLANK,
J1,4,210,Round 1: 0.085452296,AUDITED,BLANK,
J1,4,219,"Round 1: 0.016019332, 0.116831568",AUDITED,BLANK,
J1,4,224,Round 1: 0.077039058,AUDITED,BLANK,
J1,4,225,Round 1: 0.063033739,AUDITED,BLANK,
J1,4,242,Round 1: 0.001422917,AUDITED,BLANK,
J1,4,246,Round 1: 0.086922674,AUDITED,BLANK,
J1,4,249,Round 1: 0.004795186,AUDITED,BLANK,
J1,4,250,Round 1: 0.052928705,AUDITED,BLANK,
J1,4,259,Round 1: 0.117848800,AUDITED,BLANK,
J1,4,262,Round 1: 0.029717257,AUDITED,BLANK,
J1,4,269,"Round 1: 0.023351879, 0.121366729",AUDITED,BLANK,
J1,4,295,Round 1: 0.058046981,AUDITED,BLANK,
J1,4,299,Round 1: 0.094678349,AUDITED,BLANK,
J1,4,300,Round 1: 0.100488068,AUDITED,BLANK,
J1,4,333,Round 1: 0.015306349,AUDITED,BLANK,
J1,4,341,Round 1: 0.084190854,AUDITED,BLANK,
J1,4,342,"Round 1: 0.060456051, 0.067991031",AUDITED,BLANK,
J1,4,356,Round 1: 0.010037054,AUDITED,BLANK,
J1,4,364,Round 1: 0.121400229,AUDITED,BLANK,
J1,4,376,Round 1: 0.117296621,AUDITED,BLANK,
J1,4,382,Round 1: 0.038602066,AUDITED,BLANK,
J1,4,383,Round 1: 0.035494065,AUDITED,BLANK,
J2,1,1,"Round 1: 0.108516298, 0.110818217",NOT_AUDITED,,
J2,1,18,Round 1: 0.118212369,NOT_AUDITED,,
J2,2,1,Round 1: 0.122667227,NOT_AUDITED,,
J2,2,7,Round 1: 0.070547975,NOT_AUDITED,,
J2,3,6,Round 1: 0.101617509,NOT_AUDITED,,
J2,3,23,Round 1: 0.011305342,NOT_AUDITED,,
J2,3,47,Round 1: 0.082621989,NOT_AUDITED,,
J2,3,50,Round 1: 0.088571589,NOT_AUDITED,,
J2,3,59,Round 1: 0.100598474,NOT_AUDITED,,
J2,3,61,Round 1: 0.051458420,NOT_AUDITED,,
J2,3,70,Round 1: 0.076189668,NOT_AUDITED,,
J2,3,77,Round 1: 0.054107852,NOT_AUDITED,,
J2,3,87,Round 1: 0.090430425,NOT_AUDITED,,
J2,3,90,Round 1: 0.050887047,NOT_AUDITED,,
J2,3,93,Round 1: 0.036987742,NOT_AUDITED,,
J2,3,108,"Round 1: 0.078303244, 0.089997896",NOT_AUDITED,,
J2,3,113,Round 1: 0.086575399,NOT_AUDITED,,
J2,3,123,Round 1: 0.050862375,NOT_AUDITED,,
J2,3,130,Round 1: 0.004411246,NOT_AUDITED,,
J2,3,147,Round 1: 0.121025282,NOT_AUDITED,,
J2,3,153,Round 1: 0.092320532,NOT_AUDITED,,
J2,3,175,Round 1: 0.106373103,NOT_AUDITED,,
J2,3,188,Round 1: 0.046916823,NOT_AUDITED,,
J2,3,196,Round 1: 0.021628954,NOT_AUDITED,,
J2,3,205,Round 1: 0.111684672,NOT_AUDITED,,
J2,3,206,Round 1: 0.113162179,NOT_AUDITED,,
J2,3,211,Round 1: 0.053013550,NOT_AUDITED,,
J2,3,213,Round 1: 0.014292928,NOT_AUDITED,,
J2,3,219,Round 1: 0.119142280,NOT_AUDITED,,
J2,4,14,Round 1: 0.113543982,NOT_AUDITED,,
J2,4,18,Round 1: 0.038013103,NOT_AUDITED,,
J2,4,25,Round 1: 0.077777948,NOT_AUDITED,,
J2,4,26,"Round 1: 0.000710191, 0.117496458",NOT_AUDITED,,
J2,4,29,Round 1: 0.122889862,NOT_AUDITED,,
J2,4,30,Round 1: 0.035663218,NOT_AUDITED,,
"""

EXPECTED_JA_REPORT = """####### SAMPLED BALLOTS ########
Jurisdiction Name,Batch Name,Ballot Position,Ticket Numbers,Audited?,Audit Result: Contest 1,Audit Result: Contest 2
J1,1,12,Round 1: 0.029898626,AUDITED,candidate 1,
J1,1,21,Round 1: 0.097507658,AUDITED,candidate 1,
J1,2,5,Round 1: 0.009880204,AUDITED,candidate 1,
J1,2,15,Round 1: 0.083638485,AUDITED,candidate 1,
J1,2,25,Round 1: 0.063921946,AUDITED,candidate 1,
J1,2,26,"Round 1: 0.049415923, 0.081722795",AUDITED,candidate 1,
J1,2,32,Round 1: 0.064344935,AUDITED,candidate 1,
J1,2,46,Round 1: 0.040298630,AUDITED,candidate 1,
J1,2,56,Round 1: 0.122658553,AUDITED,candidate 1,
J1,2,70,Round 1: 0.021941471,AUDITED,candidate 2,
J1,3,2,Round 1: 0.042609199,AUDITED,candidate 2,
J1,3,29,Round 1: 0.005485737,AUDITED,candidate 2,
J1,3,34,"Round 1: 0.024245302, 0.069503402",AUDITED,candidate 2,
J1,3,53,Round 1: 0.079988573,AUDITED,candidate 2,
J1,3,58,Round 1: 0.083486109,AUDITED,candidate 2,
J1,3,64,Round 1: 0.085168554,AUDITED,candidate 2,
J1,3,67,Round 1: 0.094448606,AUDITED,candidate 2,
J1,3,76,Round 1: 0.126272907,AUDITED,candidate 2,
J1,3,77,Round 1: 0.090055481,AUDITED,candidate 2,
J1,3,85,Round 1: 0.119043017,AUDITED,candidate 2,
J1,3,90,Round 1: 0.094088629,AUDITED,candidate 2,
J1,3,97,Round 1: 0.038404368,AUDITED,candidate 2,
J1,3,99,Round 1: 0.075051405,AUDITED,candidate 2,
J1,3,107,Round 1: 0.038234097,AUDITED,BLANK,
J1,3,119,Round 1: 0.103215596,AUDITED,BLANK,
J1,4,0,Round 1: 0.100384496,AUDITED,candidate 1,
J1,4,8,Round 1: 0.036908465,AUDITED,candidate 1,
J1,4,19,Round 1: 0.039175371,AUDITED,candidate 1,
J1,4,23,Round 1: 0.054130711,AUDITED,candidate 1,
J1,4,25,Round 1: 0.084587960,AUDITED,candidate 1,
J1,4,30,Round 1: 0.080450545,AUDITED,candidate 1,
J1,4,50,Round 1: 0.009800391,AUDITED,candidate 1,
J1,4,70,Round 1: 0.103837055,AUDITED,candidate 1,
J1,4,76,Round 1: 0.097877511,AUDITED,candidate 1,
J1,4,79,Round 1: 0.011004647,AUDITED,candidate 1,
J1,4,90,Round 1: 0.019140572,AUDITED,candidate 2,
J1,4,107,Round 1: 0.057789995,AUDITED,candidate 2,
J1,4,112,Round 1: 0.103088425,AUDITED,candidate 2,
J1,4,118,Round 1: 0.011979621,AUDITED,candidate 2,
J1,4,136,Round 1: 0.086176519,AUDITED,candidate 2,
J1,4,138,Round 1: 0.024601007,AUDITED,candidate 2,
J1,4,151,Round 1: 0.099893707,AUDITED,candidate 2,
J1,4,155,Round 1: 0.003280982,AUDITED,candidate 2,
J1,4,156,Round 1: 0.093530676,AUDITED,candidate 2,
J1,4,161,Round 1: 0.002273519,AUDITED,candidate 2,
J1,4,162,Round 1: 0.005583579,AUDITED,candidate 2,
J1,4,163,Round 1: 0.053660633,AUDITED,candidate 2,
J1,4,168,Round 1: 0.117015031,AUDITED,candidate 2,
J1,4,179,Round 1: 0.069783615,AUDITED,candidate 2,
J1,4,188,Round 1: 0.125737179,AUDITED,candidate 2,
J1,4,191,Round 1: 0.054705383,AUDITED,BLANK,
J1,4,195,"Round 1: 0.011605572, 0.104478160",AUDITED,BLANK,
J1,4,197,Round 1: 0.077950055,AUDITED,BLANK,
J1,4,210,Round 1: 0.085452296,AUDITED,BLANK,
J1,4,219,"Round 1: 0.016019332, 0.116831568",AUDITED,BLANK,
J1,4,224,Round 1: 0.077039058,AUDITED,BLANK,
J1,4,225,Round 1: 0.063033739,AUDITED,BLANK,
J1,4,242,Round 1: 0.001422917,AUDITED,BLANK,
J1,4,246,Round 1: 0.086922674,AUDITED,BLANK,
J1,4,249,Round 1: 0.004795186,AUDITED,BLANK,
J1,4,250,Round 1: 0.052928705,AUDITED,BLANK,
J1,4,259,Round 1: 0.117848800,AUDITED,BLANK,
J1,4,262,Round 1: 0.029717257,AUDITED,BLANK,
J1,4,269,"Round 1: 0.023351879, 0.121366729",AUDITED,BLANK,
J1,4,295,Round 1: 0.058046981,AUDITED,BLANK,
J1,4,299,Round 1: 0.094678349,AUDITED,BLANK,
J1,4,300,Round 1: 0.100488068,AUDITED,BLANK,
J1,4,333,Round 1: 0.015306349,AUDITED,BLANK,
J1,4,341,Round 1: 0.084190854,AUDITED,BLANK,
J1,4,342,"Round 1: 0.060456051, 0.067991031",AUDITED,BLANK,
J1,4,356,Round 1: 0.010037054,AUDITED,BLANK,
J1,4,364,Round 1: 0.121400229,AUDITED,BLANK,
J1,4,376,Round 1: 0.117296621,AUDITED,BLANK,
J1,4,382,Round 1: 0.038602066,AUDITED,BLANK,
J1,4,383,Round 1: 0.035494065,AUDITED,BLANK,
"""

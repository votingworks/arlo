from flask.testing import FlaskClient
from typing import List
import json

from tests.helpers import (
    set_logged_in_user,
    DEFAULT_JA_EMAIL,
    assert_is_id,
    compare_json,
    post_json,
    assert_ok,
    J1_SAMPLES_ROUND_1,
    J1_SAMPLES_ROUND_2,
)
from arlo_server.auth import UserType
from arlo_server.models import ContestChoice


def test_ja_ballot_draws_bad_round_id(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str],
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/invalid-round-id/ballot-draws"
    )
    assert rv.status_code == 404


def test_ja_ballot_draws_before_audit_boards_set_up(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballot-draws"
    )
    ballot_draws = json.loads(rv.data)["ballotDraws"]
    assert ballot_draws == []


def test_ja_ballot_draws_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballot-draws"
    )
    ballot_draws = json.loads(rv.data)["ballotDraws"]

    assert len(ballot_draws) == J1_SAMPLES_ROUND_1
    compare_json(
        ballot_draws[0],
        {
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
            "batch": {"id": assert_is_id, "name": "4", "tabulator": None},
            "position": 0,
            "status": "NOT_AUDITED",
            "ticketNumber": "0.100384496",
            "interpretations": [],
        },
    )

    ballot_with_wrong_status = next(
        (b for b in ballot_draws if b["status"] != "NOT_AUDITED"), None
    )
    assert ballot_with_wrong_status is None

    assert ballot_draws == sorted(
        ballot_draws,
        key=lambda b: (b["auditBoard"]["name"], b["batch"]["name"], b["position"],),
    )

    # Try auditing one ballot
    choice_id = ContestChoice.query.filter_by(contest_id=contest_id).first().id
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch/{ballot_draws[0]['batch']['id']}/ballot/{ballot_draws[0]['position']}",
        {
            "interpretations": [
                {
                    "contestId": contest_id,
                    "interpretation": "VOTE",
                    "choiceId": choice_id,
                    "comment": "blah blah blah",
                }
            ]
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballot-draws"
    )
    ballot_draws = json.loads(rv.data)["ballotDraws"]

    compare_json(
        ballot_draws[0],
        {
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
            "batch": {"id": assert_is_id, "name": "4", "tabulator": None},
            "position": 0,
            "status": "AUDITED",
            "ticketNumber": "0.100384496",
            "interpretations": [
                {
                    "contestId": contest_id,
                    "interpretation": "VOTE",
                    "choiceId": choice_id,
                    "comment": "blah blah blah",
                }
            ],
        },
    )


def test_ja_ballot_draws_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_2_id: str,
    audit_board_round_2_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/ballot-draws"
    )
    ballot_draws = json.loads(rv.data)["ballotDraws"]

    assert len(ballot_draws) == J1_SAMPLES_ROUND_2
    compare_json(
        ballot_draws[0],
        {
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
            "batch": {"id": assert_is_id, "name": "4", "tabulator": None},
            "position": 4,
            "status": "NOT_AUDITED",
            "ticketNumber": "0.136825434",
            "interpretations": [],
        },
    )

    previously_audited_ballots = [b for b in ballot_draws if b["status"] == "AUDITED"]
    assert len(previously_audited_ballots) == 14


def test_ja_ballot_retrieval_list_bad_round_id(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str],
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/invalid-round-id/retrieval-list"
    )
    assert rv.status_code == 404


def test_ja_ballot_retrieval_list_before_audit_boards_set_up(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/retrieval-list"
    )
    assert rv.status_code == 200
    assert "attachment; filename=" in rv.headers["Content-Disposition"]

    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    assert (
        retrieval_list
        == "Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board\n"
    )


def test_ja_ballot_retrieval_list_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/retrieval-list"
    )
    assert rv.status_code == 200
    assert "attachment; filename=" in rv.headers["Content-Disposition"]

    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    assert retrieval_list == EXPECTED_RETRIEVAL_LIST_ROUND_1


def test_ja_ballot_retrieval_list_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_2_id: str,
    audit_board_round_2_ids: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/retrieval-list"
    )
    assert rv.status_code == 200
    assert "attachment; filename=" in rv.headers["Content-Disposition"]

    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    assert retrieval_list == EXPECTED_RETRIEVAL_LIST_ROUND_2


EXPECTED_RETRIEVAL_LIST_ROUND_1 = """Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board
4,0,,,0.100384496,N,Audit Board #1
4,8,,,0.036908465,N,Audit Board #1
4,19,,,0.039175371,N,Audit Board #1
4,23,,,0.054130711,N,Audit Board #1
4,25,,,0.084587960,N,Audit Board #1
4,30,,,0.080450545,N,Audit Board #1
4,50,,,0.009800391,N,Audit Board #1
4,70,,,0.103837055,N,Audit Board #1
4,76,,,0.097877511,N,Audit Board #1
4,79,,,0.011004647,N,Audit Board #1
4,90,,,0.019140572,N,Audit Board #1
4,107,,,0.057789995,N,Audit Board #1
4,112,,,0.103088425,N,Audit Board #1
4,118,,,0.011979621,N,Audit Board #1
4,136,,,0.086176519,N,Audit Board #1
4,138,,,0.024601007,N,Audit Board #1
4,151,,,0.099893707,N,Audit Board #1
4,155,,,0.003280982,N,Audit Board #1
4,156,,,0.093530676,N,Audit Board #1
4,161,,,0.002273519,N,Audit Board #1
4,162,,,0.005583579,N,Audit Board #1
4,163,,,0.053660633,N,Audit Board #1
4,168,,,0.117015031,N,Audit Board #1
4,179,,,0.069783615,N,Audit Board #1
4,188,,,0.125737179,N,Audit Board #1
4,191,,,0.054705383,N,Audit Board #1
4,195,,,"0.011605572,0.104478160",N,Audit Board #1
4,197,,,0.077950055,N,Audit Board #1
4,210,,,0.085452296,N,Audit Board #1
4,219,,,"0.016019332,0.116831568",N,Audit Board #1
4,224,,,0.077039058,N,Audit Board #1
4,225,,,0.063033739,N,Audit Board #1
4,242,,,0.001422917,N,Audit Board #1
4,246,,,0.086922674,N,Audit Board #1
4,249,,,0.004795186,N,Audit Board #1
4,250,,,0.052928705,N,Audit Board #1
4,259,,,0.117848800,N,Audit Board #1
4,262,,,0.029717257,N,Audit Board #1
4,269,,,"0.023351879,0.121366729",N,Audit Board #1
4,295,,,0.058046981,N,Audit Board #1
4,299,,,0.094678349,N,Audit Board #1
4,300,,,0.100488068,N,Audit Board #1
4,333,,,0.015306349,N,Audit Board #1
4,341,,,0.084190854,N,Audit Board #1
4,342,,,"0.060456051,0.067991031",N,Audit Board #1
4,356,,,0.010037054,N,Audit Board #1
4,364,,,0.121400229,N,Audit Board #1
4,376,,,0.117296621,N,Audit Board #1
4,382,,,0.038602066,N,Audit Board #1
4,383,,,0.035494065,N,Audit Board #1
1,12,,,0.029898626,N,Audit Board #2
1,21,,,0.097507658,N,Audit Board #2
2,5,,,0.009880204,N,Audit Board #2
2,15,,,0.083638485,N,Audit Board #2
2,25,,,0.063921946,N,Audit Board #2
2,26,,,"0.049415923,0.081722795",N,Audit Board #2
2,32,,,0.064344935,N,Audit Board #2
2,46,,,0.040298630,N,Audit Board #2
2,56,,,0.122658553,N,Audit Board #2
2,70,,,0.021941471,N,Audit Board #2
3,2,,,0.042609199,N,Audit Board #2
3,29,,,0.005485737,N,Audit Board #2
3,34,,,"0.024245302,0.069503402",N,Audit Board #2
3,53,,,0.079988573,N,Audit Board #2
3,58,,,0.083486109,N,Audit Board #2
3,64,,,0.085168554,N,Audit Board #2
3,67,,,0.094448606,N,Audit Board #2
3,76,,,0.126272907,N,Audit Board #2
3,77,,,0.090055481,N,Audit Board #2
3,85,,,0.119043017,N,Audit Board #2
3,90,,,0.094088629,N,Audit Board #2
3,97,,,0.038404368,N,Audit Board #2
3,99,,,0.075051405,N,Audit Board #2
3,107,,,0.038234097,N,Audit Board #2
3,119,,,0.103215596,N,Audit Board #2
"""

EXPECTED_RETRIEVAL_LIST_ROUND_2 = """Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board
4,4,,,"0.136825434,0.219708710",N,Audit Board #1
4,12,,,0.180951865,N,Audit Board #1
4,20,,,"0.179108277,0.216774047",N,Audit Board #1
4,22,,,0.184254955,N,Audit Board #1
4,23,,,0.147043495,Y,Audit Board #1
4,33,,,0.163648985,N,Audit Board #1
4,34,,,0.171564305,N,Audit Board #1
4,35,,,0.238898104,N,Audit Board #1
4,37,,,0.198058240,N,Audit Board #1
4,38,,,0.139130931,N,Audit Board #1
4,41,,,0.237417609,N,Audit Board #1
4,46,,,0.208767616,N,Audit Board #1
4,61,,,0.145832703,N,Audit Board #1
4,62,,,"0.157292634,0.180026545",N,Audit Board #1
4,63,,,0.204642104,N,Audit Board #1
4,65,,,0.241732220,N,Audit Board #1
4,69,,,0.202386800,N,Audit Board #1
4,72,,,0.127406532,N,Audit Board #1
4,79,,,0.187370388,Y,Audit Board #1
4,80,,,"0.246313513,0.256750991",N,Audit Board #1
4,86,,,0.187561586,N,Audit Board #1
4,87,,,0.161506656,N,Audit Board #1
4,88,,,0.232949726,N,Audit Board #1
4,103,,,0.226044847,N,Audit Board #1
4,104,,,0.130628197,N,Audit Board #1
4,108,,,0.206776000,N,Audit Board #1
4,110,,,0.250289963,N,Audit Board #1
4,113,,,0.145054947,N,Audit Board #1
4,127,,,0.157786974,N,Audit Board #1
4,139,,,0.176563715,N,Audit Board #1
4,140,,,0.256239210,N,Audit Board #1
4,143,,,0.164190563,N,Audit Board #1
4,144,,,0.231189112,N,Audit Board #1
4,153,,,0.197267832,N,Audit Board #1
4,168,,,0.220869134,Y,Audit Board #1
4,172,,,0.160129098,N,Audit Board #1
4,174,,,0.177505094,N,Audit Board #1
4,175,,,"0.157283754,0.199598730",N,Audit Board #1
4,181,,,"0.151047195,0.235949621",N,Audit Board #1
4,184,,,0.139912878,N,Audit Board #1
4,192,,,0.221047086,N,Audit Board #1
4,202,,,0.198165510,N,Audit Board #1
4,203,,,0.160348889,N,Audit Board #1
4,206,,,0.129013616,N,Audit Board #1
4,209,,,0.232933675,N,Audit Board #1
4,210,,,0.172496772,Y,Audit Board #1
4,211,,,0.228603768,N,Audit Board #1
4,218,,,0.145502322,N,Audit Board #1
4,219,,,0.190294542,Y,Audit Board #1
4,221,,,0.234998887,N,Audit Board #1
4,226,,,0.233540775,N,Audit Board #1
4,227,,,0.191599348,N,Audit Board #1
4,230,,,0.236832173,N,Audit Board #1
4,262,,,0.190319255,Y,Audit Board #1
4,263,,,"0.213990216,0.219379809",N,Audit Board #1
4,266,,,0.226733317,N,Audit Board #1
4,274,,,0.187727181,N,Audit Board #1
4,281,,,0.227903128,N,Audit Board #1
4,283,,,0.204934764,N,Audit Board #1
4,284,,,0.188238748,N,Audit Board #1
4,314,,,0.162786098,N,Audit Board #1
4,321,,,0.203293570,N,Audit Board #1
4,326,,,0.264287107,N,Audit Board #1
4,328,,,0.217009298,N,Audit Board #1
4,331,,,0.258929618,N,Audit Board #1
4,333,,,0.236899297,Y,Audit Board #1
4,334,,,0.196594058,N,Audit Board #1
4,341,,,0.186713223,Y,Audit Board #1
4,345,,,"0.142235234,0.248346420",N,Audit Board #1
4,351,,,0.201571416,N,Audit Board #1
4,359,,,0.242059011,N,Audit Board #1
4,361,,,0.158476047,N,Audit Board #1
4,367,,,0.230697085,N,Audit Board #1
4,371,,,0.199534804,N,Audit Board #1
4,373,,,"0.141329380,0.242302075",N,Audit Board #1
4,374,,,0.257705706,N,Audit Board #1
4,380,,,0.175971415,N,Audit Board #1
4,381,,,0.246120313,N,Audit Board #1
4,383,,,0.165110514,Y,Audit Board #1
4,393,,,0.238158385,N,Audit Board #1
4,394,,,0.234881270,N,Audit Board #1
4,396,,,0.150389099,N,Audit Board #1
4,399,,,0.212018104,N,Audit Board #1
3,2,,,0.263722564,Y,Audit Board #2
3,4,,,"0.136601709,0.167735444,0.194774719",N,Audit Board #2
3,5,,,0.213932100,N,Audit Board #2
3,8,,,0.223227529,N,Audit Board #2
3,16,,,0.173243514,N,Audit Board #2
3,18,,,0.128081777,N,Audit Board #2
3,25,,,"0.257292797,0.268171402",N,Audit Board #2
3,31,,,0.230995046,N,Audit Board #2
3,33,,,0.210116781,N,Audit Board #2
3,34,,,0.147643625,Y,Audit Board #2
3,42,,,0.271018875,N,Audit Board #2
3,44,,,0.251773458,N,Audit Board #2
3,54,,,0.245478477,N,Audit Board #2
3,56,,,0.152865409,N,Audit Board #2
3,63,,,0.272241589,N,Audit Board #2
3,66,,,0.211645841,N,Audit Board #2
3,67,,,0.218831076,Y,Audit Board #2
3,72,,,0.159025454,N,Audit Board #2
3,73,,,0.220378204,N,Audit Board #2
3,74,,,0.197935246,N,Audit Board #2
3,79,,,0.139035204,N,Audit Board #2
3,82,,,0.264853527,N,Audit Board #2
3,98,,,0.225170121,N,Audit Board #2
3,108,,,0.128526780,N,Audit Board #2
3,109,,,0.152475017,N,Audit Board #2
3,113,,,0.244603560,N,Audit Board #2
1,9,,,0.132689946,N,Audit Board #3
1,11,,,0.207665625,N,Audit Board #3
1,14,,,0.240944230,N,Audit Board #3
1,16,,,0.190466245,N,Audit Board #3
1,17,,,0.273780364,N,Audit Board #3
2,0,,,0.131870811,N,Audit Board #3
2,2,,,0.167137437,N,Audit Board #3
2,7,,,0.226025316,N,Audit Board #3
2,13,,,0.192723560,N,Audit Board #3
2,14,,,0.180598277,N,Audit Board #3
2,22,,,0.200669850,N,Audit Board #3
2,23,,,0.197006552,N,Audit Board #3
2,24,,,0.259035957,N,Audit Board #3
2,25,,,0.171305534,Y,Audit Board #3
2,36,,,0.223023220,N,Audit Board #3
2,44,,,0.159172433,N,Audit Board #3
2,46,,,0.178731041,Y,Audit Board #3
2,48,,,0.192414966,N,Audit Board #3
2,49,,,0.196372471,N,Audit Board #3
2,61,,,0.212722813,N,Audit Board #3
2,65,,,0.235476826,N,Audit Board #3
2,78,,,0.258352375,N,Audit Board #3
2,86,,,0.235252480,N,Audit Board #3
2,93,,,"0.127706314,0.197977963,0.258885741",N,Audit Board #3
2,97,,,0.267717075,N,Audit Board #3
"""

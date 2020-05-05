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


def test_ja_ballot_draws_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: str,
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
    choice_id = ContestChoice.query.filter_by(contest_id=contest_ids[0]).first().id
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch/{ballot_draws[0]['batch']['id']}/ballot/{ballot_draws[0]['position']}",
        {
            "interpretations": [
                {
                    "contestId": contest_ids[0],
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
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceId": choice_id,
                    "comment": "blah blah blah",
                }
            ],
        },
    )


def test_ja_ballot_draws_before_audit_boards_set_up(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
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
            "auditBoard": None,
            "batch": {"id": assert_is_id, "name": "1", "tabulator": None},
            "position": 12,
            "status": "NOT_AUDITED",
            "ticketNumber": "0.029898626",
            "interpretations": [],
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
            "position": 3,
            "status": "NOT_AUDITED",
            "ticketNumber": "0.306411348",
            "interpretations": [],
        },
    )

    previously_audited_ballots = [b for b in ballot_draws if b["status"] == "AUDITED"]
    assert len(previously_audited_ballots) == 33


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
4,3,,,0.306411348,N,Audit Board #1
4,4,,,"0.136825434,0.219708710",N,Audit Board #1
4,6,,,0.396637328,N,Audit Board #1
4,8,,,0.326128744,Y,Audit Board #1
4,12,,,0.180951865,N,Audit Board #1
4,15,,,0.304912655,N,Audit Board #1
4,17,,,0.394012115,N,Audit Board #1
4,19,,,0.325814768,Y,Audit Board #1
4,20,,,"0.179108277,0.216774047",N,Audit Board #1
4,22,,,0.184254955,N,Audit Board #1
4,23,,,0.147043495,Y,Audit Board #1
4,29,,,0.287340369,N,Audit Board #1
4,30,,,"0.290881113,0.293975888",Y,Audit Board #1
4,33,,,0.163648985,N,Audit Board #1
4,34,,,0.171564305,N,Audit Board #1
4,35,,,0.238898104,N,Audit Board #1
4,37,,,0.198058240,N,Audit Board #1
4,38,,,"0.139130931,0.351862044",N,Audit Board #1
4,41,,,0.237417609,N,Audit Board #1
4,44,,,"0.345890437,0.381169335",N,Audit Board #1
4,46,,,0.208767616,N,Audit Board #1
4,51,,,0.341380211,N,Audit Board #1
4,61,,,"0.145832703,0.321334228",N,Audit Board #1
4,62,,,"0.157292634,0.180026545,0.276481993",N,Audit Board #1
4,63,,,0.204642104,N,Audit Board #1
4,65,,,0.241732220,N,Audit Board #1
4,69,,,0.202386800,N,Audit Board #1
4,72,,,"0.127406532,0.358831679",N,Audit Board #1
4,79,,,0.187370388,Y,Audit Board #1
4,80,,,"0.246313513,0.256750991",N,Audit Board #1
4,81,,,0.276734544,N,Audit Board #1
4,84,,,0.383081167,N,Audit Board #1
4,85,,,0.304281324,N,Audit Board #1
4,86,,,0.187561586,N,Audit Board #1
4,87,,,0.161506656,N,Audit Board #1
4,88,,,0.232949726,N,Audit Board #1
4,97,,,0.363396589,N,Audit Board #1
4,102,,,"0.289377841,0.297268450",N,Audit Board #1
4,103,,,0.226044847,N,Audit Board #1
4,104,,,0.130628197,N,Audit Board #1
4,108,,,0.206776000,N,Audit Board #1
4,110,,,"0.250289963,0.283435582,0.289362378",N,Audit Board #1
4,112,,,0.299808667,Y,Audit Board #1
4,113,,,0.145054947,N,Audit Board #1
4,120,,,0.376519313,N,Audit Board #1
4,121,,,"0.297905375,0.388792115",N,Audit Board #1
4,123,,,0.389542937,N,Audit Board #1
4,124,,,0.306875274,N,Audit Board #1
4,126,,,0.319189075,N,Audit Board #1
4,127,,,0.157786974,N,Audit Board #1
4,129,,,0.393753603,N,Audit Board #1
4,130,,,0.390587105,N,Audit Board #1
4,134,,,0.279566710,N,Audit Board #1
4,139,,,0.176563715,N,Audit Board #1
4,140,,,0.256239210,N,Audit Board #1
4,143,,,0.164190563,N,Audit Board #1
4,144,,,0.231189112,N,Audit Board #1
4,145,,,0.389442116,N,Audit Board #1
4,153,,,0.197267832,N,Audit Board #1
4,158,,,0.394263001,N,Audit Board #1
4,168,,,0.220869134,Y,Audit Board #1
4,169,,,0.300405096,N,Audit Board #1
4,172,,,0.160129098,N,Audit Board #1
4,174,,,0.177505094,N,Audit Board #1
4,175,,,"0.157283754,0.199598730",N,Audit Board #1
4,177,,,0.280104783,N,Audit Board #1
4,179,,,0.360049016,Y,Audit Board #1
4,180,,,0.373366758,N,Audit Board #1
4,181,,,"0.151047195,0.235949621",N,Audit Board #1
4,184,,,0.139912878,N,Audit Board #1
4,186,,,0.319270595,N,Audit Board #1
4,192,,,0.221047086,N,Audit Board #1
4,193,,,0.317612495,N,Audit Board #1
4,197,,,0.329850738,Y,Audit Board #1
4,200,,,0.364127508,N,Audit Board #1
4,202,,,"0.198165510,0.386181637",N,Audit Board #1
4,203,,,0.160348889,N,Audit Board #1
4,205,,,0.368835660,N,Audit Board #1
4,206,,,0.129013616,N,Audit Board #1
4,209,,,0.232933675,N,Audit Board #1
4,210,,,0.172496772,Y,Audit Board #1
4,211,,,0.228603768,N,Audit Board #1
4,217,,,0.313944473,N,Audit Board #1
4,218,,,0.145502322,N,Audit Board #1
4,219,,,0.190294542,Y,Audit Board #1
4,220,,,0.363392143,N,Audit Board #1
4,221,,,0.234998887,N,Audit Board #1
4,225,,,0.274304225,Y,Audit Board #1
4,226,,,0.233540775,N,Audit Board #1
4,227,,,0.191599348,N,Audit Board #1
4,230,,,0.236832173,N,Audit Board #1
4,232,,,0.361719520,N,Audit Board #1
4,237,,,0.383764937,N,Audit Board #1
4,238,,,0.391696770,N,Audit Board #1
4,242,,,0.399652610,Y,Audit Board #1
4,246,,,0.353538255,Y,Audit Board #1
4,247,,,0.289221463,N,Audit Board #1
4,249,,,0.274147091,Y,Audit Board #1
4,255,,,"0.338163456,0.389536273",N,Audit Board #1
4,259,,,0.279793009,Y,Audit Board #1
4,262,,,0.190319255,Y,Audit Board #1
4,263,,,"0.213990216,0.219379809",N,Audit Board #1
4,266,,,"0.226733317,0.381564547",N,Audit Board #1
4,269,,,0.314433806,Y,Audit Board #1
4,274,,,0.187727181,N,Audit Board #1
4,281,,,0.227903128,N,Audit Board #1
4,283,,,0.204934764,N,Audit Board #1
4,284,,,"0.188238748,0.314695778",N,Audit Board #1
4,286,,,0.330430985,N,Audit Board #1
4,287,,,0.325742428,N,Audit Board #1
4,294,,,"0.373652978,0.378581020",N,Audit Board #1
4,311,,,0.293268590,N,Audit Board #1
4,312,,,0.288537615,N,Audit Board #1
4,314,,,0.162786098,N,Audit Board #1
4,321,,,"0.203293570,0.362122238",N,Audit Board #1
4,323,,,0.359134485,N,Audit Board #1
4,326,,,0.264287107,N,Audit Board #1
4,328,,,0.217009298,N,Audit Board #1
4,329,,,0.303465098,N,Audit Board #1
4,331,,,0.258929618,N,Audit Board #1
4,332,,,0.390662223,N,Audit Board #1
4,333,,,0.236899297,Y,Audit Board #1
4,334,,,0.196594058,N,Audit Board #1
4,339,,,0.340796515,N,Audit Board #1
4,340,,,0.318167245,N,Audit Board #1
4,341,,,0.186713223,Y,Audit Board #1
4,344,,,0.392659841,N,Audit Board #1
4,345,,,"0.142235234,0.248346420,0.360857577",N,Audit Board #1
4,349,,,0.338067958,N,Audit Board #1
4,351,,,0.201571416,N,Audit Board #1
4,359,,,0.242059011,N,Audit Board #1
4,361,,,0.158476047,N,Audit Board #1
4,367,,,0.230697085,N,Audit Board #1
4,368,,,0.394975729,N,Audit Board #1
4,371,,,0.199534804,N,Audit Board #1
4,373,,,"0.141329380,0.242302075",N,Audit Board #1
4,374,,,0.257705706,N,Audit Board #1
4,377,,,0.332594594,N,Audit Board #1
4,380,,,0.175971415,N,Audit Board #1
4,381,,,0.246120313,N,Audit Board #1
4,383,,,0.165110514,Y,Audit Board #1
4,384,,,0.391242647,N,Audit Board #1
4,385,,,0.323322612,N,Audit Board #1
4,391,,,0.338131292,N,Audit Board #1
4,392,,,0.392415107,N,Audit Board #1
4,393,,,0.238158385,N,Audit Board #1
4,394,,,0.234881270,N,Audit Board #1
4,395,,,0.388505712,N,Audit Board #1
4,396,,,0.150389099,N,Audit Board #1
4,399,,,0.212018104,N,Audit Board #1
1,1,,,0.402094775,N,Audit Board #2
1,4,,,0.324042377,N,Audit Board #2
1,9,,,0.132689946,N,Audit Board #2
1,11,,,"0.207665625,0.399137345",N,Audit Board #2
1,12,,,"0.297461947,0.325109398",Y,Audit Board #2
1,14,,,0.240944230,N,Audit Board #2
1,16,,,"0.190466245,0.306202075",N,Audit Board #2
1,17,,,"0.273780364,0.329960353",N,Audit Board #2
2,0,,,"0.131870811,0.357557989",N,Audit Board #2
2,2,,,0.167137437,N,Audit Board #2
2,4,,,0.306919456,N,Audit Board #2
2,7,,,0.226025316,N,Audit Board #2
2,8,,,0.362663944,N,Audit Board #2
2,13,,,0.192723560,N,Audit Board #2
2,14,,,0.180598277,N,Audit Board #2
2,20,,,0.345599518,N,Audit Board #2
2,22,,,"0.200669850,0.283886729",N,Audit Board #2
2,23,,,"0.197006552,0.396775025",N,Audit Board #2
2,24,,,0.259035957,N,Audit Board #2
2,25,,,0.171305534,Y,Audit Board #2
2,26,,,0.343163592,Y,Audit Board #2
2,27,,,0.318973879,N,Audit Board #2
2,29,,,0.352816770,N,Audit Board #2
2,32,,,0.287205383,Y,Audit Board #2
2,36,,,0.223023220,N,Audit Board #2
2,37,,,0.309522790,N,Audit Board #2
2,38,,,0.336775177,N,Audit Board #2
2,44,,,0.159172433,N,Audit Board #2
2,46,,,0.178731041,Y,Audit Board #2
2,48,,,0.192414966,N,Audit Board #2
2,49,,,0.196372471,N,Audit Board #2
2,57,,,0.354356172,N,Audit Board #2
2,61,,,0.212722813,N,Audit Board #2
2,65,,,0.235476826,N,Audit Board #2
2,69,,,0.310179158,N,Audit Board #2
2,72,,,0.390854262,N,Audit Board #2
2,78,,,0.258352375,N,Audit Board #2
2,81,,,0.337196608,N,Audit Board #2
2,86,,,0.235252480,N,Audit Board #2
2,87,,,0.350639499,N,Audit Board #2
2,89,,,0.301024248,N,Audit Board #2
2,92,,,0.322053795,N,Audit Board #2
2,93,,,"0.127706314,0.197977963,0.258885741,0.273845938,0.401104595",N,Audit Board #2
2,97,,,0.267717075,N,Audit Board #2
2,98,,,0.375013588,N,Audit Board #2
3,1,,,0.274337091,N,Audit Board #3
3,2,,,0.263722564,Y,Audit Board #3
3,4,,,"0.136601709,0.167735444,0.194774719",N,Audit Board #3
3,5,,,"0.213932100,0.290313761",N,Audit Board #3
3,7,,,0.334280253,N,Audit Board #3
3,8,,,0.223227529,N,Audit Board #3
3,16,,,0.173243514,N,Audit Board #3
3,18,,,0.128081777,N,Audit Board #3
3,21,,,0.316761530,N,Audit Board #3
3,25,,,"0.257292797,0.268171402",N,Audit Board #3
3,28,,,0.402169931,N,Audit Board #3
3,30,,,0.380450047,N,Audit Board #3
3,31,,,0.230995046,N,Audit Board #3
3,32,,,0.306176707,N,Audit Board #3
3,33,,,"0.210116781,0.316099773",N,Audit Board #3
3,34,,,"0.147643625,0.314993647",Y,Audit Board #3
3,42,,,0.271018875,N,Audit Board #3
3,44,,,"0.251773458,0.357068207",N,Audit Board #3
3,54,,,0.245478477,N,Audit Board #3
3,56,,,0.152865409,N,Audit Board #3
3,61,,,0.383435671,N,Audit Board #3
3,62,,,0.328651285,N,Audit Board #3
3,63,,,0.272241589,N,Audit Board #3
3,66,,,0.211645841,N,Audit Board #3
3,67,,,"0.218831076,0.338535049",Y,Audit Board #3
3,72,,,0.159025454,N,Audit Board #3
3,73,,,"0.220378204,0.361511999",N,Audit Board #3
3,74,,,0.197935246,N,Audit Board #3
3,79,,,0.139035204,N,Audit Board #3
3,82,,,0.264853527,N,Audit Board #3
3,95,,,0.388828930,N,Audit Board #3
3,98,,,"0.225170121,0.378558432,0.380349262",N,Audit Board #3
3,108,,,0.128526780,N,Audit Board #3
3,109,,,0.152475017,N,Audit Board #3
3,113,,,0.244603560,N,Audit Board #3
3,114,,,0.352673196,N,Audit Board #3
3,118,,,0.388189334,N,Audit Board #3
"""

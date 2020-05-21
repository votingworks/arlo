import json, uuid
from typing import List
import pytest
from flask.testing import FlaskClient

from tests.helpers import (
    assert_ok,
    post_json,
    put_json,
    SAMPLE_SIZE_ROUND_1,
    set_logged_in_user,
)
from arlo_server.models import RoundContest
from arlo_server.contests import JSONDict
from arlo_server.auth import UserType
from arlo_server import db


@pytest.fixture
def json_contests(jurisdiction_ids: List[str]) -> List[JSONDict]:
    return [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 48121,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 38026,},
            ],
            "totalBallotsCast": 86147,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 2",
            "isTargeted": False,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 200,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 300,},
            ],
            "totalBallotsCast": 500,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": [],
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 3",
            "isTargeted": False,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 200,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400,},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 600,},
            ],
            "totalBallotsCast": 700,
            "numWinners": 2,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]


def test_contests_list_empty(client, election_id):
    rv = client.get(f"/election/{election_id}/contest")
    contests = json.loads(rv.data)
    assert contests == {"contests": []}


def test_contests_create_get_update_one(client, election_id, json_contests):
    contest = json_contests[0]
    rv = put_json(client, f"/election/{election_id}/contest", [contest])
    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/contest")
    contests = json.loads(rv.data)
    expected_contest = {**contest, "currentRoundStatus": None}
    assert contests == {"contests": [expected_contest]}

    contest["totalBallotsCast"] = contest["totalBallotsCast"] + 21
    contest["numWinners"] = 2
    contest["choices"].append(
        {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 21,}
    )

    rv = put_json(client, f"/election/{election_id}/contest", [contest])
    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/contest")
    contests = json.loads(rv.data)
    expected_contest = {**contest, "currentRoundStatus": None}
    assert contests == {"contests": [expected_contest]}


def test_contests_create_get_update_multiple(
    client: FlaskClient,
    election_id: str,
    json_contests: List[JSONDict],
    jurisdiction_ids: List[str],
):
    rv = put_json(client, f"/election/{election_id}/contest", json_contests)
    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/contest")
    contests = json.loads(rv.data)
    expected_contests = [
        {**contest, "currentRoundStatus": None} for contest in json_contests
    ]
    assert contests == {"contests": expected_contests}

    json_contests[0]["name"] = "Changed name"
    json_contests[1]["isTargeted"] = True
    json_contests[2]["jurisdictionIds"] = jurisdiction_ids[1:]

    rv = put_json(client, f"/election/{election_id}/contest", json_contests)
    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/contest")
    contests = json.loads(rv.data)
    expected_contests = [
        {**contest, "currentRoundStatus": None} for contest in json_contests
    ]
    assert contests == {"contests": expected_contests}


def test_contests_round_status(
    client: FlaskClient,
    election_id: str,
    json_contests: List[JSONDict],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    rv = put_json(client, f"/election/{election_id}/contest", json_contests)
    assert_ok(rv)

    rv = post_json(
        client,
        f"/election/{election_id}/round",
        {"roundNum": 1, "sampleSize": SAMPLE_SIZE_ROUND_1},
    )
    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]

    assert contests[0]["currentRoundStatus"] == {
        "isRiskLimitMet": None,
        "numBallotsSampled": SAMPLE_SIZE_ROUND_1,
    }
    assert contests[1]["currentRoundStatus"] == {
        "isRiskLimitMet": None,
        "numBallotsSampled": 0,
    }
    assert contests[2]["currentRoundStatus"] == {
        "isRiskLimitMet": None,
        "numBallotsSampled": 81,
    }

    # Fake that one opportunistic contest met its risk limit, but the targeted
    # contest did not
    opportunistic_round_contest = RoundContest.query.filter_by(
        contest_id=contests[1]["id"]
    ).one()
    opportunistic_round_contest.is_complete = True
    targeted_round_contest = RoundContest.query.filter_by(
        contest_id=contests[0]["id"]
    ).one()
    targeted_round_contest.is_complete = False
    db.session.commit()

    rv = client.get(f"/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]

    assert contests[0]["currentRoundStatus"] == {
        "isRiskLimitMet": False,
        "numBallotsSampled": SAMPLE_SIZE_ROUND_1,
    }
    assert contests[1]["currentRoundStatus"] == {
        "isRiskLimitMet": True,
        "numBallotsSampled": 0,
    }
    assert contests[2]["currentRoundStatus"] == {
        "isRiskLimitMet": None,
        "numBallotsSampled": 81,
    }


def test_contests_missing_field(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    contest: JSONDict = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 48121,},
            {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 38026,},
        ],
        "totalBallotsCast": 86147,
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
    }

    for field in contest:
        invalid_contest = contest.copy()
        del invalid_contest[field]

        rv = put_json(client, f"/election/{election_id}/contest", [invalid_contest])
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "message": f"'{field}' is a required property",
                    "errorType": "Bad Request",
                }
            ]
        }

    for field in contest["choices"][0]:
        invalid_contest = contest.copy()
        invalid_contest_choice = invalid_contest["choices"][0].copy()
        del invalid_contest_choice[field]
        invalid_contest["choices"] = [invalid_contest_choice]

        rv = put_json(client, f"/election/{election_id}/contest", [invalid_contest])
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "message": f"'{field}' is a required property",
                    "errorType": "Bad Request",
                }
            ]
        }


def test_contest_too_many_votes(client: FlaskClient, election_id: str):
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 400,},
            {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 101,},
        ],
        "totalBallotsCast": 500,
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": [],
    }

    rv = put_json(client, f"/election/{election_id}/contest", [contest])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Too many votes cast in contest: Contest 1 (501 votes, 500 allowed)",
                "errorType": "Bad Request",
            }
        ]
    }

    contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 700,},
            {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 301,},
        ],
        "totalBallotsCast": 500,
        "numWinners": 1,
        "votesAllowed": 2,
        "jurisdictionIds": [],
    }

    rv = put_json(client, f"/election/{election_id}/contest", [contest])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Too many votes cast in contest: Contest 1 (1001 votes, 1000 allowed)",
                "errorType": "Bad Request",
            }
        ]
    }


def test_audit_board_contests_list_empty(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
    json_contests: List[JSONDict],
):
    rv = put_json(client, f"/election/{election_id}/contest", [json_contests[1]])
    assert_ok(rv)
    set_logged_in_user(
        client, UserType.AUDIT_BOARD, user_key=audit_board_round_1_ids[0]
    )
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/contest"
    )
    assert json.loads(rv.data) == {"contests": []}


def test_audit_board_contests_list(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
    json_contests: List[JSONDict],
):
    rv = put_json(client, f"/election/{election_id}/contest", json_contests)
    assert_ok(rv)

    set_logged_in_user(
        client, UserType.AUDIT_BOARD, user_key=audit_board_round_1_ids[0]
    )
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/contest"
    )
    contests = json.loads(rv.data)
    expected_contests = [
        {**contest, "currentRoundStatus": None}
        for contest in [json_contests[0], json_contests[2]]
    ]
    assert contests == {"contests": expected_contests}

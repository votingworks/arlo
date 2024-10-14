import json, uuid
from typing import List
import pytest
from flask.testing import FlaskClient

from ..helpers import *  # pylint: disable=wildcard-import
from ...database import db_session
from ...models import *  # pylint: disable=wildcard-import
from ...api.contests import JSONDict
from ...auth import UserType


@pytest.fixture
def json_contests(jurisdiction_ids: List[str]) -> List[JSONDict]:
    return [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 1",
                    "numVotes": 48121,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 2",
                    "numVotes": 38026,
                },
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
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 1",
                    "numVotes": 200,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 2",
                    "numVotes": 300,
                },
            ],
            "totalBallotsCast": 500,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 3",
            "isTargeted": False,
            "choices": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 1",
                    "numVotes": 200,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 2",
                    "numVotes": 400,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 3",
                    "numVotes": 600,
                },
            ],
            "totalBallotsCast": 700,
            "numWinners": 2,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]


def test_contests_list_empty(client, election_id):
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)
    assert contests == {"contests": []}


def test_contests_create_get_update_one(client, election_id, json_contests):
    contest = json_contests[0]
    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)
    assert contests == {"contests": [contest]}

    contest["totalBallotsCast"] = contest["totalBallotsCast"] + 21
    contest["numWinners"] = 2
    contest["choices"].append(
        {
            "id": str(uuid.uuid4()),
            "name": "candidate 3",
            "numVotes": 21,
        }
    )

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)
    assert contests == {"contests": [contest]}


def test_contests_create_get_update_multiple(
    client: FlaskClient,
    election_id: str,
    json_contests: List[JSONDict],
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    rv = put_json(client, f"/api/election/{election_id}/contest", json_contests)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)
    assert contests == {"contests": json_contests}

    json_contests[0]["name"] = "Changed name"
    json_contests[1]["totalBallotsCast"] = 600
    json_contests = json_contests[:2]

    rv = put_json(client, f"/api/election/{election_id}/contest", json_contests)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)
    assert contests == {"contests": json_contests}


def test_contests_order(
    client: FlaskClient,
    election_id: str,
    json_contests: List[JSONDict],
):
    json_contests[0]["name"] = "ZZZ Contest"
    json_contests[1]["name"] = "AAA Contest"
    json_contests[0]["choices"][0]["name"] = "ZZZ Choice"
    json_contests[0]["choices"][1]["name"] = "AAA Choice"

    rv = put_json(client, f"/api/election/{election_id}/contest", json_contests)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]

    assert contests[0]["name"] == json_contests[0]["name"]
    assert contests[1]["name"] == json_contests[1]["name"]
    assert contests[0]["choices"][0]["name"] == json_contests[0]["choices"][0]["name"]
    assert contests[0]["choices"][1]["name"] == json_contests[0]["choices"][1]["name"]


def test_update_contests_after_audit_starts(
    client: FlaskClient,
    election_id: str,
    round_1_id: str,  # pylint: disable=unused-argument
):
    rv = put_json(client, f"/api/election/{election_id}/contest", [])
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Cannot update contests after audit has started.",
            }
        ]
    }


def test_update_contests_no_targeted(
    client: FlaskClient, election_id: str, json_contests: List[JSONDict]
):
    rv = put_json(client, f"/api/election/{election_id}/contest", [json_contests[1]])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Must have at least one targeted contest",
            }
        ]
    }


def test_update_contests_missing_field(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    contest: JSONDict = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {
                "id": str(uuid.uuid4()),
                "name": "candidate 1",
                "numVotes": 48121,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "candidate 2",
                "numVotes": 38026,
            },
        ],
        "totalBallotsCast": 86147,
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
    }

    for field in contest:
        invalid_contest = contest.copy()
        del invalid_contest[field]

        rv = put_json(client, f"/api/election/{election_id}/contest", [invalid_contest])
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

        rv = put_json(client, f"/api/election/{election_id}/contest", [invalid_contest])
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "message": f"'{field}' is a required property",
                    "errorType": "Bad Request",
                }
            ]
        }


def test_update_contests_invalid_jurisdictions(
    client: FlaskClient, election_id: str, json_contests
):
    json_contests[0]["jurisdictionIds"] = []
    rv = put_json(client, f"/api/election/{election_id}/contest", [json_contests[0]])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "[] is too short",
                "errorType": "Bad Request",
            }
        ]
    }

    json_contests[0]["jurisdictionIds"] = ["not a real jurisdiction id"]
    rv = put_json(client, f"/api/election/{election_id}/contest", [json_contests[0]])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Invalid jurisdiction ids",
                "errorType": "Bad Request",
            }
        ]
    }


def test_contest_too_many_votes(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {
                "id": str(uuid.uuid4()),
                "name": "candidate 1",
                "numVotes": 400,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "candidate 2",
                "numVotes": 101,
            },
        ],
        "totalBallotsCast": 500,
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
    }

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
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
            {
                "id": str(uuid.uuid4()),
                "name": "candidate 1",
                "numVotes": 700,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "candidate 2",
                "numVotes": 301,
            },
        ],
        "totalBallotsCast": 500,
        "numWinners": 1,
        "votesAllowed": 2,
        "jurisdictionIds": jurisdiction_ids,
    }

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Too many votes cast in contest: Contest 1 (1001 votes, 1000 allowed)",
                "errorType": "Bad Request",
            }
        ]
    }


def test_jurisdictions_contests_list_empty(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, user_key=default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    assert json.loads(rv.data) == {"contests": []}


def test_jurisdictions_contests_list(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    json_contests,
):
    rv = put_json(client, f"/api/election/{election_id}/contest", json_contests)
    assert_ok(rv)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, user_key=default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/contest"
    )
    contests = json.loads(rv.data)
    assert contests == {"contests": json_contests[:2]}


def test_audit_board_contests_list_empty(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    contests = Contest.query.filter_by(election_id=election_id).all()
    for contest in contests:
        contest.jurisdictions = []
    db_session.commit()

    set_logged_in_user(
        client, UserType.AUDIT_BOARD, user_key=audit_board_round_1_ids[0]
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/contest"
    )
    assert json.loads(rv.data) == {"contests": []}


def test_audit_board_contests_list(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    expected_contests = json.loads(rv.data)["contests"]

    set_logged_in_user(
        client, UserType.AUDIT_BOARD, user_key=audit_board_round_1_ids[0]
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/contest"
    )
    contests = json.loads(rv.data)
    assert contests == {"contests": expected_contests}


def test_audit_board_contests_list_order(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    db_contests = (
        Contest.query.filter_by(election_id=election_id)
        .order_by(Contest.created_at)
        .all()
    )
    db_contests[0].name = "ZZZ Contest"
    db_contests[1].name = "AAA Contest"
    db_choices = sorted(db_contests[0].choices, key=lambda c: c.created_at)  # type: ignore
    db_choices[0].name = "ZZZ Choice"
    db_choices[1].name = "AAA Choice"
    db_session.commit()

    set_logged_in_user(
        client, UserType.AUDIT_BOARD, user_key=audit_board_round_1_ids[0]
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/contest"
    )
    contests = json.loads(rv.data)["contests"]

    db_contests = (
        Contest.query.filter_by(election_id=election_id)
        .order_by(Contest.created_at)
        .all()
    )
    db_choices = sorted(db_contests[0].choices, key=lambda c: c.created_at)  # type: ignore

    assert contests[0]["name"] == db_contests[0].name
    assert contests[1]["name"] == db_contests[1].name
    assert contests[0]["choices"][0]["name"] == db_choices[0].name
    assert contests[0]["choices"][1]["name"] == db_choices[1].name

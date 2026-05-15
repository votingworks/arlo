import io
import json
import uuid
import pytest
from flask.testing import FlaskClient

from ..helpers import *
from ...database import db_session
from ...models import *
from ...api.contests import JSONDict, should_reprocess_batch_tallies
from ...auth import UserType


@pytest.fixture
def json_contests(jurisdiction_ids: list[str]) -> list[JSONDict]:
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
    json_contests: list[JSONDict],
    jurisdiction_ids: list[str],
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
    json_contests: list[JSONDict],
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
    round_1_id: str,
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
    client: FlaskClient, election_id: str, json_contests: list[JSONDict]
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
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
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
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
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
    jurisdiction_ids: list[str],
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
    jurisdiction_ids: list[str],
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
    jurisdiction_ids: list[str],
    round_1_id: str,
    audit_board_round_1_ids: list[str],
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
    jurisdiction_ids: list[str],
    round_1_id: str,
    audit_board_round_1_ids: list[str],
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
    jurisdiction_ids: list[str],
    round_1_id: str,
    audit_board_round_1_ids: list[str],
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


def test_should_reprocess_batch_tallies_treats_missing_runoff_flag_as_false():
    # serialize_contest emits isSubjectToRunoff for batch-comparison contests;
    # the client conditionally omits it when false. Normalization must treat
    # "missing" and "False" as equivalent so a no-op save doesn't trigger an
    # unnecessary batch-tallies reprocess.
    choice = {"id": "c1", "name": "candidate 1", "numVotes": 60}
    base_contest = {
        "id": "contest-1",
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [choice],
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": ["j1"],
    }
    previous = {**base_contest, "isSubjectToRunoff": False}
    new_without = {**base_contest}

    assert not should_reprocess_batch_tallies([previous], [new_without])


def test_runoff_flag_rejected_for_non_batch_comparison(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: list[str],
):
    expected_error = {
        "errors": [
            {
                "message": "Runoff-subject contests are only supported for batch comparison audits",
                "errorType": "Bad Request",
            }
        ]
    }

    # Ballot polling (default election_id fixture).
    ballot_polling_contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "Alice", "numVotes": 40},
            {"id": str(uuid.uuid4()), "name": "Bob", "numVotes": 35},
            {"id": str(uuid.uuid4()), "name": "Carla", "numVotes": 25},
        ],
        "totalBallotsCast": 100,
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
        "isSubjectToRunoff": True,
    }
    rv = put_json(
        client, f"/api/election/{election_id}/contest", [ballot_polling_contest]
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == expected_error

    # Ballot comparison uses a different (minimal) schema; verify the flag
    # surfaces the same clean error rather than a generic schema rejection.
    bc_election_id = create_election(
        client,
        audit_name="Test Audit ballot_comparison_runoff_rejection",
        audit_type=AuditType.BALLOT_COMPARISON,
        audit_math_type=AuditMathType.SUPERSIMPLE,
        organization_id=org_id,
    )
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            f"Jurisdiction,Admin Email\nJ1,j1-{bc_election_id}@example.com\n".encode()
        ),
        bc_election_id,
    )
    assert_ok(rv)
    bc_jurisdiction_id = str(
        Jurisdiction.query.filter_by(election_id=bc_election_id).one().id
    )
    ballot_comparison_contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "numWinners": 1,
        "jurisdictionIds": [bc_jurisdiction_id],
        "isSubjectToRunoff": True,
    }
    rv = put_json(
        client, f"/api/election/{bc_election_id}/contest", [ballot_comparison_contest]
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == expected_error

from typing import List
import io
import json
from flask.testing import FlaskClient

from ..helpers import *  # pylint: disable=wildcard-import
from ...auth import UserType
from ...models import *  # pylint: disable=wildcard-import
from ...util.jsonschema import JSONDict

BALLOT_1_BATCH_NAME = "4"
BALLOT_1_POSITION = 3


def test_ja_ballots_bad_round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/invalid-round-id/ballots"
    )
    assert rv.status_code == 404


def test_ja_ballots_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: str,
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    snapshot.assert_match(len(ballots))
    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
            "batch": {
                "id": assert_is_id,
                "name": BALLOT_1_BATCH_NAME,
                "tabulator": None,
                "container": None,
            },
            "position": BALLOT_1_POSITION,
            "status": "NOT_AUDITED",
            "interpretations": [],
        },
    )

    ballot_with_wrong_status = next(
        (b for b in ballots if b["status"] != "NOT_AUDITED"), None
    )
    assert ballot_with_wrong_status is None

    assert ballots == sorted(
        ballots,
        key=lambda b: (b["auditBoard"]["name"], b["batch"]["name"], b["position"]),
    )

    # Try auditing one ballot
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    choice_id = ContestChoice.query.filter_by(contest_id=contest_ids[0]).first().id
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballots[0]['id']}",
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
            ],
        },
    )
    assert_ok(rv)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
            "batch": {
                "id": assert_is_id,
                "name": BALLOT_1_BATCH_NAME,
                "tabulator": None,
                "container": None,
            },
            "position": BALLOT_1_POSITION,
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
            ],
        },
    )


def test_ja_ballots_before_audit_boards_set_up(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    snapshot.assert_match(len(ballots))

    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "auditBoard": None,
            "batch": {
                "id": assert_is_id,
                "name": "1",
                "tabulator": None,
                "container": None,
            },
            "position": BALLOT_1_POSITION,
            "status": "NOT_AUDITED",
            "interpretations": [],
        },
    )


def test_ja_ballots_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_2_id: str,
    audit_board_round_2_ids: List[str],  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    snapshot.assert_match(len(ballots))
    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
            "batch": {
                "id": assert_is_id,
                "name": BALLOT_1_BATCH_NAME,
                "tabulator": None,
                "container": None,
            },
            "position": BALLOT_1_POSITION,
            "status": "AUDITED",
            "interpretations": [
                {
                    "choiceIds": [assert_is_id],
                    "comment": None,
                    "contestId": assert_is_id,
                    "interpretation": "VOTE",
                    "hasInvalidWriteIn": False,
                },
                {
                    "choiceIds": [],
                    "comment": None,
                    "contestId": assert_is_id,
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "hasInvalidWriteIn": False,
                },
            ],
        },
    )

    previously_audited_ballots = [b for b in ballots if b["status"] == "AUDITED"]
    snapshot.assert_match(len(previously_audited_ballots))


def test_ab_list_ballot_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: str,
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    snapshot.assert_match(len(ballots))

    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "batch": {
                "id": assert_is_id,
                "name": BALLOT_1_BATCH_NAME,
                "tabulator": None,
                "container": None,
            },
            "position": BALLOT_1_POSITION,
            "status": "NOT_AUDITED",
            "interpretations": [],
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
        },
    )

    assert ballots == sorted(
        ballots,
        key=lambda b: (b["batch"]["name"], b["position"]),
    )

    # Try auditing one ballot
    choice_id = ContestChoice.query.filter_by(contest_id=contest_ids[0]).first().id
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballots[0]['id']}",
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
            ],
        },
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "batch": {
                "id": assert_is_id,
                "name": BALLOT_1_BATCH_NAME,
                "tabulator": None,
                "container": None,
            },
            "position": BALLOT_1_POSITION,
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
            ],
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
        },
    )

    # Check audit board 2 as well
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[1])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[1]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    snapshot.assert_match(len(ballots))


def test_ab_list_ballots_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
    round_2_id: str,
    audit_board_round_2_ids: List[str],
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_2_ids[0])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board/{audit_board_round_2_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    snapshot.assert_match(len(ballots))

    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "batch": {
                "id": assert_is_id,
                "name": BALLOT_1_BATCH_NAME,
                "tabulator": None,
                "container": None,
            },
            "position": 9,
            "status": "NOT_AUDITED",
            "interpretations": [],
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
        },
    )

    # Audit boards can't see ballots that were audited in previous rounds
    previously_audited_ballots = [b for b in ballots if b["status"] == "AUDITED"]
    assert previously_audited_ballots == []

    # And can't re-audit any of those ballots
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    ballot = next(b for b in ballots if b["status"] == "AUDITED")

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_2_ids[0])
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board/{audit_board_round_2_ids[0]}/ballots/{ballot['id']}",
        {},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Ballot was already audited in a previous round",
            }
        ]
    }

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot['id']}",
        {},
    )
    assert rv.status_code == 404


def test_ab_audit_ballot_not_found(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/not-a-real-ballot-id",
        {},
    )
    assert rv.status_code == 404


def test_ab_audit_ballot_happy_path(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    ballot = ballots[0]

    choice_id = ContestChoice.query.filter_by(contest_id=contest_ids[0]).first().id
    contest_2_choices = ContestChoice.query.filter_by(contest_id=contest_ids[1]).all()
    audit_requests: List[JSONDict] = [
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
            ],
        },
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "BLANK",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
            ],
        },
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "CANT_AGREE",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
            ],
        },
        {
            "status": "NOT_AUDITED",
            "interpretations": [],
        },
        {
            "status": "NOT_FOUND",
            "interpretations": [],
        },
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "CANT_AGREE",
                    "choiceIds": [],
                    "comment": "weird scribble",
                    "hasInvalidWriteIn": False,
                },
            ],
        },
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "VOTE",
                    "choiceIds": [c.id for c in contest_2_choices[0:2]],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
            ],
        },
    ]

    for audit_request in audit_requests:
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot['id']}",
            audit_request,
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
        )
        ballots = json.loads(rv.data)["ballots"]

        ballots[0]["interpretations"] = sorted(
            ballots[0]["interpretations"], key=lambda i: str(i["contestId"])
        )
        audit_request["interpretations"] = sorted(
            audit_request["interpretations"], key=lambda i: str(i["contestId"])
        )

        assert ballots[0] == {**ballot, **audit_request}


def test_ab_audit_ballot_overvote(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    ballot_id = ballots[0]["id"]

    contest_id = contest_ids[1]
    contest = Contest.query.get(contest_id)
    choice_ids = [c.id for c in contest.choices]
    assert len(choice_ids) > contest.votes_allowed

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot_id}",
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_id,
                    "interpretation": "VOTE",
                    "choiceIds": choice_ids,
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
            ],
        },
    )
    assert_ok(rv)

    interpretation = BallotInterpretation.query.get((ballot_id, contest_id))
    assert interpretation.is_overvote

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot_id}",
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "CONTEST_NOT_ON_BALLOT",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
                {
                    "contestId": contest_id,
                    "interpretation": "VOTE",
                    "choiceIds": choice_ids[0:2],
                    "comment": None,
                    "hasInvalidWriteIn": False,
                },
            ],
        },
    )
    assert_ok(rv)

    interpretation = BallotInterpretation.query.get((ballot_id, contest_id))
    assert not interpretation.is_overvote


def test_ab_audit_ballot_has_invalid_write_in(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    ballot_id = ballots[0]["id"]
    choice_id = ContestChoice.query.filter_by(contest_id=contest_ids[0]).first().id

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot_id}",
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": None,
                    "hasInvalidWriteIn": True,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "BLANK",
                    "choiceIds": [],
                    "comment": None,
                    "hasInvalidWriteIn": True,
                },
            ],
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    interpretations = ballots[0]["interpretations"]
    assert interpretations[0]["hasInvalidWriteIn"]
    assert interpretations[1]["hasInvalidWriteIn"]


def test_ab_audit_ballot_wrong_audit_board(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    ballot = ballots[0]

    choice_id = ContestChoice.query.filter_by(contest_id=contest_ids[0]).first().id

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[1])
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[1]}/ballots/{ballot['id']}",
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                    "hasInvalidWriteIn": False,
                }
            ],
        },
    )
    assert rv.status_code == 404


def test_ab_audit_ballot_invalid(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    ballot = ballots[0]

    choice_id = ContestChoice.query.filter_by(contest_id=contest_ids[0]).first().id

    for missing_field in ["status", "interpretations"]:
        audit_request = {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                    "hasInvalidWriteIn": False,
                }
            ],
        }
        del audit_request[missing_field]
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot['id']}",
            audit_request,
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Bad Request",
                    "message": f"'{missing_field}' is a required property",
                }
            ]
        }

    for missing_field in ["contestId", "interpretation", "choiceIds", "comment"]:
        interpretation = {
            "contestId": contest_ids[0],
            "interpretation": "VOTE",
            "choiceIds": [choice_id],
            "comment": "blah blah blah",
            "hasInvalidWriteIn": False,
        }
        del interpretation[missing_field]
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot['id']}",
            {
                "status": "AUDITED",
                "interpretations": [interpretation],
            },
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Bad Request",
                    "message": f"'{missing_field}' is a required property",
                }
            ]
        }

    invalid_requests = [
        (
            {
                "status": "audited",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "VOTE",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    }
                ],
            },
            "'audited' is not one of ['NOT_AUDITED', 'AUDITED', 'NOT_FOUND']",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "vote",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    }
                ],
            },
            "'vote' is not one of ['BLANK', 'CANT_AGREE', 'CONTEST_NOT_ON_BALLOT', 'VOTE']",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "VOTE",
                        "choiceIds": [],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": False,
                    },
                ],
            },
            f"Must include choiceIds with interpretation VOTE for contest {contest_ids[0]}",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "VOTE",
                        "choiceIds": [""],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": False,
                    },
                ],
            },
            "Contest choices not found: ",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": "12345",
                        "interpretation": "VOTE",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": False,
                    },
                ],
            },
            "Contest not found: 12345",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "VOTE",
                        "choiceIds": ["12345"],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": False,
                    },
                ],
            },
            "Contest choices not found: 12345",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "VOTE",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                ],
            },
            f"Contest choice {choice_id} is not associated with contest {contest_ids[1]}",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "BLANK",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": False,
                    },
                ],
            },
            f"Cannot include choiceIds with interpretation BLANK for contest {contest_ids[0]}",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "CANT_AGREE",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": False,
                    },
                ],
            },
            f"Cannot include choiceIds with interpretation CANT_AGREE for contest {contest_ids[0]}",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": False,
                    },
                ],
            },
            f"Cannot include choiceIds with interpretation CONTEST_NOT_ON_BALLOT for contest {contest_ids[0]}",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "VOTE",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": True,
                    },
                ],
            },
            f"Cannot specify hasInvalidWriteIn=True with interpretation CONTEST_NOT_ON_BALLOT for contest {contest_ids[1]}",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [],
            },
            "Must include an interpretation for each contest.",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "VOTE",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    }
                ],
            },
            "Must include an interpretation for each contest.",
        ),
        (
            {
                "status": "NOT_FOUND",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "VOTE",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": False,
                    },
                ],
            },
            "Cannot include interpretations with ballot status NOT_FOUND.",
        ),
        (
            {
                "status": "NOT_AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[0],
                        "interpretation": "VOTE",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                        "hasInvalidWriteIn": False,
                    },
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "CONTEST_NOT_ON_BALLOT",
                        "choiceIds": [],
                        "comment": None,
                        "hasInvalidWriteIn": False,
                    },
                ],
            },
            "Cannot include interpretations with ballot status NOT_AUDITED.",
        ),
    ]
    for invalid_request, expected_message in invalid_requests:
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot['id']}",
            invalid_request,
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": expected_message}]
        }


def test_ja_ballot_retrieval_list_bad_round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/invalid-round-id/ballots/retrieval-list"
    )
    assert rv.status_code == 404


def test_ja_ballot_retrieval_list_before_audit_boards_set_up(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots/retrieval-list"
    )
    assert rv.status_code == 200
    assert "attachment; filename=" in rv.headers["Content-Disposition"]

    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    assert (
        retrieval_list
        == "Batch Name,Ballot Number,Ticket Numbers,Already Audited,Audit Board\n"
    )


def test_ja_ballot_retrieval_list_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots/retrieval-list"
    )
    assert rv.status_code == 200
    assert (
        scrub_datetime(rv.headers["Content-Disposition"])
        == 'attachment; filename="ballot-retrieval-J1-Test-Audit-test-ja-ballot-retrieval-list-round-1-DATETIME.csv"'
    )

    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    assert len(json.loads(rv.data)["ballots"]) == len(retrieval_list.splitlines()) - 1


def test_ja_ballot_retrieval_list_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_2_id: str,
    audit_board_round_2_ids: str,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/ballots/retrieval-list"
    )
    assert rv.status_code == 200
    assert (
        scrub_datetime(rv.headers["Content-Disposition"])
        == 'attachment; filename="ballot-retrieval-J1-Test-Audit-test-ja-ballot-retrieval-list-round-2-DATETIME.csv"'
    )

    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/ballots"
    )
    assert len(json.loads(rv.data)["ballots"]) == len(retrieval_list.splitlines()) - 1


def test_ja_ballots_count(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots?count=true"
    )
    response = json.loads(rv.data)
    snapshot.assert_match(response)


def test_ballots_human_sort_order(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    snapshot,
):
    # Upload a manifest with mixed text/number batch names
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    human_ordered_batches = [
        "Batch 1",
        "Batch 1 - 1",
        "Batch 1 - 2",
        "Batch 1 - 10",
        "Batch 2",
        "Batch 10",
    ]
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    (
                        "Batch Name,Number of Ballots\n"
                        + "\n".join(f"{batch},10" for batch in human_ordered_batches)
                    ).encode()
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    # Start round 1
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_ids[0]: sample_size_options[contest_ids[0]][0]},
        },
    )
    assert_ok(rv)
    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    rounds = json.loads(rv.data)["rounds"]
    round_1_id = rounds[0]["id"]

    # Create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    # Check that the ballots are ordered in human order
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots/retrieval-list"
    )
    assert rv.status_code == 200
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    def unique_preserve_order(values):
        return list(dict.fromkeys(values))

    assert (
        unique_preserve_order(ballot["batch"]["name"] for ballot in ballots)
        == human_ordered_batches
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board"
    )
    audit_board_id = json.loads(rv.data)["auditBoards"][0]["id"]
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    assert (
        unique_preserve_order(ballot["batch"]["name"] for ballot in ballots)
        == human_ordered_batches
    )

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    assert_match_report(rv.data, snapshot)

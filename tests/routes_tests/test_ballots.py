from typing import List
import json
from flask.testing import FlaskClient

from tests.helpers import (
    set_logged_in_user,
    DEFAULT_JA_EMAIL,
    assert_is_id,
    compare_json,
    put_json,
    assert_ok,
    J1_BALLOTS_ROUND_1,
    J1_BALLOTS_ROUND_2,
    AB1_BALLOTS_ROUND_1,
    AB2_BALLOTS_ROUND_1,
    AB1_BALLOTS_ROUND_2,
)
from arlo_server.auth import UserType
from arlo_server.models import ContestChoice, BallotInterpretation, Contest
from util.jsonschema import JSONDict


def test_ja_ballots_bad_round_id(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str],
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/invalid-round-id/ballots"
    )
    assert rv.status_code == 404


def test_ja_ballots_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: str,
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    assert len(ballots) == J1_BALLOTS_ROUND_1
    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
            "batch": {"id": assert_is_id, "name": "4", "tabulator": None},
            "position": 8,
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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballots[0]['id']}",
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                }
            ],
        },
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
            "batch": {"id": assert_is_id, "name": "4", "tabulator": None},
            "position": 8,
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                }
            ],
        },
    )


def test_ja_ballots_before_audit_boards_set_up(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    assert len(ballots) == J1_BALLOTS_ROUND_1

    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "auditBoard": None,
            "batch": {"id": assert_is_id, "name": "1", "tabulator": None},
            "position": 12,
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
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    assert len(ballots) == J1_BALLOTS_ROUND_2
    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
            "batch": {"id": assert_is_id, "name": "4", "tabulator": None},
            "position": 3,
            "status": "NOT_AUDITED",
            "interpretations": [],
        },
    )

    previously_audited_ballots = [b for b in ballots if b["status"] == "AUDITED"]
    assert len(previously_audited_ballots) == 30


def test_ab_list_ballot_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: str,
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    assert len(ballots) == AB1_BALLOTS_ROUND_1

    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "batch": {"id": assert_is_id, "name": "4", "tabulator": None},
            "position": 8,
            "status": "NOT_AUDITED",
            "interpretations": [],
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
        },
    )

    assert ballots == sorted(
        ballots, key=lambda b: (b["batch"]["name"], b["position"]),
    )

    # Try auditing one ballot
    choice_id = ContestChoice.query.filter_by(contest_id=contest_ids[0]).first().id
    rv = put_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballots[0]['id']}",
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                }
            ],
        },
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "batch": {"id": assert_is_id, "name": "4", "tabulator": None},
            "position": 8,
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": "blah blah blah",
                }
            ],
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
        },
    )

    # Check audit board 2 as well
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[1])
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[1]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    assert len(ballots) == AB2_BALLOTS_ROUND_1


def test_ab_list_ballots_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_2_id: str,
    audit_board_round_2_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_2_ids[0])
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board/{audit_board_round_2_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    assert len(ballots) == AB1_BALLOTS_ROUND_2

    compare_json(
        ballots[0],
        {
            "id": assert_is_id,
            "batch": {"id": assert_is_id, "name": "4", "tabulator": None},
            "position": 3,
            "status": "NOT_AUDITED",
            "interpretations": [],
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
        },
    )

    previously_audited_ballots = [b for b in ballots if b["status"] == "AUDITED"]
    assert len(previously_audited_ballots) == 22


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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/not-a-real-ballot-id",
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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
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
                }
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
                }
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
                }
            ],
        },
        {"status": "NOT_AUDITED", "interpretations": [],},
        {"status": "NOT_FOUND", "interpretations": [],},
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[0],
                    "interpretation": "VOTE",
                    "choiceIds": [choice_id],
                    "comment": None,
                },
                {
                    "contestId": contest_ids[1],
                    "interpretation": "CANT_AGREE",
                    "choiceIds": [],
                    "comment": "weird scribble",
                },
            ],
        },
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_ids[1],
                    "interpretation": "VOTE",
                    "choiceIds": [c.id for c in contest_2_choices[0:2]],
                    "comment": None,
                },
            ],
        },
    ]

    for audit_request in audit_requests:
        rv = put_json(
            client,
            f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot['id']}",
            audit_request,
        )
        assert_ok(rv)

        rv = client.get(
            f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
        )
        ballots = json.loads(rv.data)["ballots"]

        ballots[0]["interpretations"] = sorted(
            ballots[0]["interpretations"], key=lambda i: i["contestId"]
        )
        audit_request["interpretations"] = sorted(
            audit_request["interpretations"], key=lambda i: i["contestId"]
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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    ballot_id = ballots[0]["id"]

    contest_id = contest_ids[1]
    contest = Contest.query.get(contest_id)
    choice_ids = [c.id for c in contest.choices]
    assert len(choice_ids) > contest.votes_allowed

    rv = put_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot_id}",
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_id,
                    "interpretation": "VOTE",
                    "choiceIds": choice_ids,
                    "comment": None,
                },
            ],
        },
    )
    assert_ok(rv)

    interpretation = BallotInterpretation.query.get((ballot_id, contest_id))
    assert interpretation.is_overvote

    rv = put_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot_id}",
        {
            "status": "AUDITED",
            "interpretations": [
                {
                    "contestId": contest_id,
                    "interpretation": "VOTE",
                    "choiceIds": choice_ids[0:2],
                    "comment": None,
                },
            ],
        },
    )
    assert_ok(rv)

    interpretation = BallotInterpretation.query.get((ballot_id, contest_id))
    assert not interpretation.is_overvote


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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots"
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
                }
            ],
        }
        del audit_request[missing_field]
        rv = put_json(
            client,
            f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot['id']}",
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
        }
        del interpretation[missing_field]
        rv = put_json(
            client,
            f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot['id']}",
            {"status": "AUDITED", "interpretations": [interpretation],},
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
                    }
                ],
            },
            "'vote' is not one of ['BLANK', 'CANT_AGREE', 'VOTE']",
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
                    }
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
                    }
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
                    }
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
                    }
                ],
            },
            "Contest choices not found: 12345",
        ),
        (
            {
                "status": "AUDITED",
                "interpretations": [
                    {
                        "contestId": contest_ids[1],
                        "interpretation": "VOTE",
                        "choiceIds": [choice_id],
                        "comment": "blah blah blah",
                    }
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
                    }
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
                    }
                ],
            },
            f"Cannot include choiceIds with interpretation CANT_AGREE for contest {contest_ids[0]}",
        ),
        (
            {"status": "AUDITED", "interpretations": [],},
            "Must include interpretations with ballot status AUDITED.",
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
                    }
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
                    }
                ],
            },
            "Cannot include interpretations with ballot status NOT_AUDITED.",
        ),
    ]
    for (invalid_request, expected_message) in invalid_requests:
        rv = put_json(
            client,
            f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/ballots/{ballot['id']}",
            invalid_request,
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": expected_message}]
        }


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
    assert ".csv" in rv.headers["Content-Disposition"]

    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    assert len(retrieval_list.splitlines()) == J1_BALLOTS_ROUND_1 + 1
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
    assert len(retrieval_list.splitlines()) == J1_BALLOTS_ROUND_2 + 1
    assert retrieval_list == EXPECTED_RETRIEVAL_LIST_ROUND_2


EXPECTED_RETRIEVAL_LIST_ROUND_1 = """Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board
4,8,,,0.036908465434400494,N,Audit Board #1
4,19,,,0.039175371814673076,N,Audit Board #1
4,23,,,0.054130711915358102,N,Audit Board #1
4,25,,,0.084587960812342841,N,Audit Board #1
4,30,,,0.080450545227510568,N,Audit Board #1
4,50,,,0.009800391720019182,N,Audit Board #1
4,70,,,0.103837055385035441,N,Audit Board #1
4,72,,,0.127406532353632486,N,Audit Board #1
4,76,,,0.097877511235874384,N,Audit Board #1
4,79,,,0.011004647116851367,N,Audit Board #1
4,90,,,0.019140572102897510,N,Audit Board #1
4,107,,,0.057789995897368832,N,Audit Board #1
4,112,,,0.103088425698468254,N,Audit Board #1
4,118,,,0.011979621355982937,N,Audit Board #1
4,136,,,0.086176519636640979,N,Audit Board #1
4,138,,,0.024601007542633783,N,Audit Board #1
4,151,,,0.099893707378789717,N,Audit Board #1
4,155,,,0.003280982424388856,N,Audit Board #1
4,156,,,0.093530676101016088,N,Audit Board #1
4,161,,,0.002273519778823474,N,Audit Board #1
4,162,,,0.005583579034696292,N,Audit Board #1
4,163,,,0.053660633322621419,N,Audit Board #1
4,168,,,0.117015031001908874,N,Audit Board #1
4,179,,,0.069783615936995520,N,Audit Board #1
4,188,,,0.125737179379637414,N,Audit Board #1
4,191,,,0.054705383792225819,N,Audit Board #1
4,195,,,"0.011605572377444965,0.104478160009884111",N,Audit Board #1
4,197,,,0.077950055597443362,N,Audit Board #1
4,210,,,0.085452296381914985,N,Audit Board #1
4,219,,,"0.016019332853519997,0.116831568613469832",N,Audit Board #1
4,224,,,0.077039058066978632,N,Audit Board #1
4,225,,,0.063033739981775843,N,Audit Board #1
4,242,,,0.001422917370063674,N,Audit Board #1
4,246,,,0.086922674711608988,N,Audit Board #1
4,249,,,0.004795186182988073,N,Audit Board #1
4,250,,,0.052928705706444505,N,Audit Board #1
4,259,,,0.117848800070428562,N,Audit Board #1
4,262,,,0.029717257151387992,N,Audit Board #1
4,269,,,"0.023351879658140877,0.121366729957805862",N,Audit Board #1
4,295,,,0.058046981034044064,N,Audit Board #1
4,299,,,0.094678349981996496,N,Audit Board #1
4,300,,,0.100488068481397853,N,Audit Board #1
4,333,,,0.015306349247709058,N,Audit Board #1
4,341,,,0.084190854845044845,N,Audit Board #1
4,342,,,"0.060456051384346034,0.067991031099023478",N,Audit Board #1
4,356,,,0.010037054248830862,N,Audit Board #1
4,364,,,0.121400229258604463,N,Audit Board #1
4,376,,,0.117296621167114194,N,Audit Board #1
4,382,,,0.038602066872714526,N,Audit Board #1
4,383,,,0.035494065576269651,N,Audit Board #1
1,12,,,0.029898626374613222,N,Audit Board #2
1,21,,,0.097507658000193474,N,Audit Board #2
2,5,,,0.009880204677447527,N,Audit Board #2
2,15,,,0.083638485230135638,N,Audit Board #2
2,25,,,0.063921946082389022,N,Audit Board #2
2,26,,,"0.049415923879170303,0.081722795103841946",N,Audit Board #2
2,32,,,0.064344935183948458,N,Audit Board #2
2,46,,,0.040298630475761721,N,Audit Board #2
2,56,,,0.122658553948710406,N,Audit Board #2
2,70,,,0.021941471451169393,N,Audit Board #2
3,2,,,0.042609199829273320,N,Audit Board #2
3,29,,,0.005485737844734212,N,Audit Board #2
3,34,,,"0.024245302017344245,0.069503402643814475",N,Audit Board #2
3,53,,,0.079988573650917747,N,Audit Board #2
3,58,,,0.083486109903754340,N,Audit Board #2
3,64,,,0.085168554836160702,N,Audit Board #2
3,67,,,0.094448606798300374,N,Audit Board #2
3,76,,,0.126272907832026485,N,Audit Board #2
3,77,,,0.090055481652564515,N,Audit Board #2
3,85,,,0.119043017926633618,N,Audit Board #2
3,90,,,0.094088629620917882,N,Audit Board #2
3,97,,,0.038404368212223909,N,Audit Board #2
3,99,,,0.075051405864746082,N,Audit Board #2
3,107,,,0.038234097413710039,N,Audit Board #2
3,119,,,0.103215596639352772,N,Audit Board #2
"""

EXPECTED_RETRIEVAL_LIST_ROUND_2 = """Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board
4,3,,,0.306411348209202158,N,Audit Board #1
4,4,,,"0.136825434334782194,0.219708710181944938",N,Audit Board #1
4,6,,,0.396637328560346813,N,Audit Board #1
4,8,,,0.326128744904794450,Y,Audit Board #1
4,12,,,0.180951865482243075,N,Audit Board #1
4,15,,,0.304912655087591581,N,Audit Board #1
4,17,,,0.394012115546532896,N,Audit Board #1
4,19,,,0.325814768747107978,Y,Audit Board #1
4,20,,,"0.179108277859473269,0.216774047328779997",N,Audit Board #1
4,22,,,0.184254955101908070,N,Audit Board #1
4,23,,,0.147043495015527446,Y,Audit Board #1
4,29,,,0.287340369108375684,N,Audit Board #1
4,30,,,"0.290881113050825370,0.293975888710665554",Y,Audit Board #1
4,33,,,0.163648985456095434,N,Audit Board #1
4,34,,,0.171564305283146266,N,Audit Board #1
4,35,,,0.238898104447680398,N,Audit Board #1
4,37,,,0.198058240466754769,N,Audit Board #1
4,38,,,"0.139130931371146810,0.351862044231103252",N,Audit Board #1
4,41,,,0.237417609753466208,N,Audit Board #1
4,44,,,"0.345890437887349508,0.381169335771532815",N,Audit Board #1
4,46,,,0.208767616795355053,N,Audit Board #1
4,51,,,0.341380211478326281,N,Audit Board #1
4,61,,,"0.145832703904963030,0.321334228807149350",N,Audit Board #1
4,62,,,"0.157292634074707531,0.180026545573898155,0.276481993048282272",N,Audit Board #1
4,63,,,0.204642104702160748,N,Audit Board #1
4,65,,,0.241732220355374323,N,Audit Board #1
4,69,,,0.202386800800755779,N,Audit Board #1
4,72,,,0.358831679935357021,Y,Audit Board #1
4,79,,,0.187370388059469513,Y,Audit Board #1
4,80,,,"0.246313513303732254,0.256750991845787224",N,Audit Board #1
4,81,,,0.276734544241692461,N,Audit Board #1
4,84,,,0.383081167908097962,N,Audit Board #1
4,85,,,0.304281324433378916,N,Audit Board #1
4,86,,,0.187561586154343788,N,Audit Board #1
4,87,,,0.161506656681743797,N,Audit Board #1
4,88,,,0.232949726539157114,N,Audit Board #1
4,97,,,0.363396589511938402,N,Audit Board #1
4,102,,,"0.289377841404552610,0.297268450984334345",N,Audit Board #1
4,103,,,0.226044847397784072,N,Audit Board #1
4,104,,,0.130628197143826704,N,Audit Board #1
4,108,,,0.206776000361526081,N,Audit Board #1
4,110,,,"0.250289963869557001,0.283435582477973072,0.289362378846627832",N,Audit Board #1
4,112,,,0.299808667434731031,Y,Audit Board #1
4,113,,,0.145054947296229832,N,Audit Board #1
4,120,,,0.376519313090041203,N,Audit Board #1
4,121,,,"0.297905375955993172,0.388792115936717617",N,Audit Board #1
4,123,,,0.389542937646563576,N,Audit Board #1
4,124,,,0.306875274157205377,N,Audit Board #1
4,126,,,0.319189075915934955,N,Audit Board #1
4,127,,,0.157786974753674741,N,Audit Board #1
4,129,,,0.393753603639927789,N,Audit Board #1
4,130,,,0.390587105925625698,N,Audit Board #1
4,134,,,0.279566710485865057,N,Audit Board #1
4,139,,,0.176563715577649727,N,Audit Board #1
4,140,,,0.256239210765411415,N,Audit Board #1
4,143,,,0.164190563912514949,N,Audit Board #1
4,144,,,0.231189112868223568,N,Audit Board #1
4,145,,,0.389442116767492257,N,Audit Board #1
4,153,,,0.197267832095737894,N,Audit Board #1
4,158,,,0.394263001168233364,N,Audit Board #1
4,168,,,0.220869134243115557,Y,Audit Board #1
4,169,,,0.300405096223246956,N,Audit Board #1
4,172,,,0.160129098050367937,N,Audit Board #1
4,174,,,"0.177505094215438844,0.404139525671973333",N,Audit Board #1
4,175,,,"0.157283754574064975,0.199598730526236048",N,Audit Board #1
4,177,,,0.280104783036490531,N,Audit Board #1
4,179,,,0.360049016169898874,Y,Audit Board #1
4,180,,,0.373366758486630474,N,Audit Board #1
4,181,,,"0.151047195070305148,0.235949621767760223",N,Audit Board #1
4,184,,,0.139912878897704078,N,Audit Board #1
4,186,,,0.319270595092385375,N,Audit Board #1
4,192,,,0.221047086286865377,N,Audit Board #1
4,193,,,0.317612495429309912,N,Audit Board #1
4,197,,,0.329850738259368164,Y,Audit Board #1
4,200,,,0.364127508837242448,N,Audit Board #1
4,202,,,"0.198165510115064564,0.386181637739754556",N,Audit Board #1
4,203,,,0.160348889833587949,N,Audit Board #1
4,205,,,0.368835660331231361,N,Audit Board #1
4,206,,,0.129013616842220829,N,Audit Board #1
4,209,,,0.232933675679986384,N,Audit Board #1
4,210,,,0.172496772398399800,Y,Audit Board #1
4,211,,,0.228603768710945224,N,Audit Board #1
4,217,,,0.313944473482969867,N,Audit Board #1
4,218,,,0.145502322235368031,N,Audit Board #1
4,219,,,0.190294542880137501,Y,Audit Board #1
4,220,,,0.363392143571177554,N,Audit Board #1
4,221,,,0.234998887989471676,N,Audit Board #1
4,225,,,0.274304225494565443,Y,Audit Board #1
4,226,,,0.233540775547363494,N,Audit Board #1
4,227,,,0.191599348792659766,N,Audit Board #1
4,230,,,0.236832173206592705,N,Audit Board #1
4,232,,,0.361719520138134602,N,Audit Board #1
4,237,,,0.383764937272872348,N,Audit Board #1
4,238,,,0.391696770276694895,N,Audit Board #1
4,242,,,0.399652610287337758,Y,Audit Board #1
4,246,,,0.353538255548811222,Y,Audit Board #1
4,247,,,0.289221463070028578,N,Audit Board #1
4,249,,,0.274147091078433568,Y,Audit Board #1
4,255,,,"0.338163456944379226,0.389536273733457251",N,Audit Board #1
4,259,,,0.279793009576461204,Y,Audit Board #1
4,262,,,0.190319255642205153,Y,Audit Board #1
4,263,,,"0.213990216904441363,0.219379809326886800",N,Audit Board #1
4,266,,,"0.226733317129553227,0.381564547511897218",N,Audit Board #1
4,269,,,0.314433806147838231,Y,Audit Board #1
4,274,,,0.187727181754991019,N,Audit Board #1
4,281,,,0.227903128734838894,N,Audit Board #1
4,283,,,0.204934764936096485,N,Audit Board #1
4,284,,,"0.188238748125655992,0.314695778302630605",N,Audit Board #1
4,286,,,0.330430985226277280,N,Audit Board #1
4,287,,,0.325742428609963500,N,Audit Board #1
4,294,,,"0.373652978451645950,0.378581020801255439",N,Audit Board #1
4,311,,,0.293268590572111102,N,Audit Board #1
4,312,,,0.288537615442311645,N,Audit Board #1
4,314,,,0.162786098666720459,N,Audit Board #1
4,321,,,"0.203293570870545808,0.362122238400667195",N,Audit Board #1
4,323,,,0.359134485710782815,N,Audit Board #1
4,326,,,0.264287107606169237,N,Audit Board #1
4,328,,,0.217009298714794629,N,Audit Board #1
4,329,,,0.303465098696144479,N,Audit Board #1
4,331,,,0.258929618457103071,N,Audit Board #1
4,332,,,0.390662223662879382,N,Audit Board #1
4,333,,,0.236899297866190604,Y,Audit Board #1
4,334,,,0.196594058755135070,N,Audit Board #1
4,339,,,0.340796515421910915,N,Audit Board #1
4,340,,,0.318167245812885061,N,Audit Board #1
4,341,,,0.186713223469463535,Y,Audit Board #1
4,344,,,0.392659841362566575,N,Audit Board #1
4,345,,,"0.142235234446025184,0.248346420348805465,0.360857577339951974",N,Audit Board #1
4,349,,,0.338067958539154425,N,Audit Board #1
4,351,,,0.201571416590933224,N,Audit Board #1
4,359,,,0.242059011269286359,N,Audit Board #1
4,361,,,0.158476047882643939,N,Audit Board #1
4,367,,,0.230697085274036760,N,Audit Board #1
4,368,,,0.394975729760285103,N,Audit Board #1
4,371,,,0.199534804601216198,N,Audit Board #1
4,373,,,"0.141329380575803673,0.242302075688094032",N,Audit Board #1
4,374,,,0.257705706563582258,N,Audit Board #1
4,377,,,0.332594594909420785,N,Audit Board #1
4,380,,,0.175971415459799864,N,Audit Board #1
4,381,,,0.246120313879933804,N,Audit Board #1
4,383,,,0.165110514900533331,Y,Audit Board #1
4,384,,,0.391242647304631196,N,Audit Board #1
4,385,,,0.323322612145165077,N,Audit Board #1
4,391,,,0.338131292366407692,N,Audit Board #1
4,392,,,0.392415107209363543,N,Audit Board #1
4,393,,,0.238158385021514593,N,Audit Board #1
4,394,,,0.234881270250802125,N,Audit Board #1
4,395,,,0.388505712968604608,N,Audit Board #1
4,396,,,0.150389099170367506,N,Audit Board #1
4,399,,,0.212018104629186137,N,Audit Board #1
4,400,,,0.209064647162605946,N,Audit Board #1
3,1,,,0.274337091625085796,N,Audit Board #2
3,2,,,0.263722564263092911,Y,Audit Board #2
3,4,,,"0.136601709208394123,0.167735444853610913,0.194774719925369337",N,Audit Board #2
3,5,,,"0.213932100721321182,0.290313761959614874",N,Audit Board #2
3,7,,,0.334280253810737261,N,Audit Board #2
3,8,,,0.223227529699281574,N,Audit Board #2
3,16,,,0.173243514732274589,N,Audit Board #2
3,18,,,0.128081777119071425,N,Audit Board #2
3,21,,,0.316761530678365521,N,Audit Board #2
3,25,,,"0.257292797242253511,0.268171402232172039",N,Audit Board #2
3,28,,,0.402169931708703726,N,Audit Board #2
3,30,,,0.380450047374936018,N,Audit Board #2
3,31,,,0.230995046716874522,N,Audit Board #2
3,32,,,0.306176707363038789,N,Audit Board #2
3,33,,,"0.210116781781480885,0.316099773972591371",N,Audit Board #2
3,34,,,"0.147643625630823737,0.314993647381652264",Y,Audit Board #2
3,42,,,0.271018875375780382,N,Audit Board #2
3,44,,,"0.251773458197558949,0.357068207314194438",N,Audit Board #2
3,54,,,0.245478477936016402,N,Audit Board #2
3,56,,,0.152865409160814813,N,Audit Board #2
3,61,,,0.383435671903186085,N,Audit Board #2
3,62,,,0.328651285297138741,N,Audit Board #2
3,63,,,0.272241589624410823,N,Audit Board #2
3,66,,,0.211645841308148762,N,Audit Board #2
3,67,,,"0.218831076203344455,0.338535049980805144",Y,Audit Board #2
3,72,,,0.159025454106288321,N,Audit Board #2
3,73,,,"0.220378204001520967,0.361511999872437411",N,Audit Board #2
3,74,,,0.197935246624845083,N,Audit Board #2
3,79,,,0.139035204830238171,N,Audit Board #2
3,82,,,0.264853527186577205,N,Audit Board #2
3,95,,,0.388828930445990200,N,Audit Board #2
3,98,,,"0.225170121374186778,0.378558432159249945,0.380349262011752089",N,Audit Board #2
3,108,,,0.128526780226929741,N,Audit Board #2
3,109,,,0.152475017498047046,N,Audit Board #2
3,113,,,0.244603560871716267,N,Audit Board #2
3,114,,,0.352673196348310797,N,Audit Board #2
3,118,,,0.388189334199859480,N,Audit Board #2
3,122,,,0.309353622615295679,N,Audit Board #2
1,1,,,0.402094775253951676,N,Audit Board #3
1,4,,,0.324042377098893634,N,Audit Board #3
1,9,,,0.132689946437387284,N,Audit Board #3
1,11,,,"0.207665625706123397,0.399137345787306591",N,Audit Board #3
1,12,,,"0.297461947303584663,0.325109398758329824",Y,Audit Board #3
1,14,,,0.240944230586866400,N,Audit Board #3
1,16,,,"0.190466245667745342,0.306202075916034411",N,Audit Board #3
1,17,,,"0.273780364695661186,0.329960353982547167",N,Audit Board #3
2,2,,,0.167137437393171549,N,Audit Board #3
2,4,,,0.306919456770704777,N,Audit Board #3
2,7,,,0.226025316117575774,N,Audit Board #3
2,8,,,0.362663944804304192,N,Audit Board #3
2,13,,,0.192723560293089118,N,Audit Board #3
2,14,,,0.180598277948515100,N,Audit Board #3
2,20,,,0.345599518389345618,N,Audit Board #3
2,22,,,"0.200669850018450383,0.283886729678307297",N,Audit Board #3
2,23,,,"0.197006552171014235,0.396775025108512251",N,Audit Board #3
2,24,,,0.259035957968990462,N,Audit Board #3
2,25,,,0.171305534115507825,Y,Audit Board #3
2,26,,,0.343163592705193077,Y,Audit Board #3
2,27,,,0.318973879768862371,N,Audit Board #3
2,29,,,0.352816770028922916,N,Audit Board #3
2,32,,,0.287205383586779603,Y,Audit Board #3
2,36,,,0.223023220812230709,N,Audit Board #3
2,37,,,0.309522790171255885,N,Audit Board #3
2,38,,,0.336775177950930063,N,Audit Board #3
2,44,,,0.159172433450509894,N,Audit Board #3
2,46,,,0.178731041606223023,Y,Audit Board #3
2,48,,,0.192414966031967046,N,Audit Board #3
2,49,,,0.196372471412485630,N,Audit Board #3
2,57,,,0.354356172197626989,N,Audit Board #3
2,61,,,0.212722813992165652,N,Audit Board #3
2,65,,,0.235476826903854232,N,Audit Board #3
2,69,,,0.310179158452875371,N,Audit Board #3
2,72,,,0.390854262487571526,N,Audit Board #3
2,78,,,0.258352375161172463,N,Audit Board #3
2,81,,,0.337196608869407609,N,Audit Board #3
2,86,,,0.235252480673820769,N,Audit Board #3
2,87,,,0.350639499212726446,N,Audit Board #3
2,89,,,0.301024248295436693,N,Audit Board #3
2,92,,,0.322053795301590963,N,Audit Board #3
2,93,,,"0.127706314641282704,0.197977963694367102,0.258885741307674245,0.273845938272679551,0.401104595824653305",N,Audit Board #3
2,97,,,0.267717075668126765,N,Audit Board #3
2,98,,,0.375013588395034996,N,Audit Board #3
2,101,,,0.158181746325504760,N,Audit Board #3
"""

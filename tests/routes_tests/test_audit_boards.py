import json, random
from flask.testing import FlaskClient
from typing import List, Tuple
from datetime import datetime
from collections import defaultdict

from tests.helpers import (
    post_json,
    assert_ok,
    compare_json,
    assert_is_id,
    assert_is_date,
    create_jurisdiction_admin,
    set_logged_in_user,
)
from arlo_server.models import (
    db,
    AuditBoard,
    SampledBallot,
    Batch,
    Round,
    RoundContest,
    Contest,
)
from arlo_server.auth import UserType

J1_SAMPLES = 81


def assert_ballots_got_assigned_correctly(
    jurisdiction_id: str,
    round_id: str,
    expected_num_audit_boards: int,
    expected_num_ballots: int,
):
    # We got the right number of audit boards
    audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction_id, round_id=round_id
    ).all()
    assert len(audit_boards) == expected_num_audit_boards

    # We got the right number of sampled ballots
    ballots = (
        SampledBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_id)
        .join(SampledBallot.draws)
        .filter_by(round_id=round_id)
        .distinct(SampledBallot.batch_id, SampledBallot.ballot_position)
        .all()
    )
    assert len(ballots) == expected_num_ballots

    # All the ballots got assigned
    assert sum(len(ab.sampled_ballots) for ab in audit_boards) == expected_num_ballots

    # Every audit board got some ballots
    for audit_board in audit_boards:
        assert len(audit_board.sampled_ballots) > 0

    # All the ballots from each batch got assigned to the same audit board
    audit_boards_by_batch = defaultdict(set)
    for audit_board in audit_boards:
        for ballot in audit_board.sampled_ballots:
            audit_boards_by_batch[ballot.batch_id].add(audit_board.id)
    for batch_id, audit_board_ids in audit_boards_by_batch.items():
        assert (
            len(audit_board_ids) == 1
        ), f"Different audit boards assigned ballots from the same batch"


def test_audit_boards_list_empty(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)
    assert audit_boards == {"auditBoards": []}


def test_audit_boards_create_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)
    assert_ballots_got_assigned_correctly(
        jurisdiction_ids[0],
        round_1_id,
        expected_num_audit_boards=1,
        expected_num_ballots=75,
    )


def test_audit_boards_list_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)
    compare_json(
        audit_boards,
        {
            "auditBoards": [
                {
                    "id": assert_is_id,
                    "name": "Audit Board #1",
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": J1_SAMPLES,
                        "numAuditedBallots": 0,
                    },
                }
            ]
        },
    )

    # Fake auditing some ballots
    audit_board = AuditBoard.query.get(audit_boards["auditBoards"][0]["id"])
    num_audited_samples = 0
    for ballot in audit_board.sampled_ballots[:10]:
        ballot.vote = "YES"
        num_audited_samples += len(ballot.draws)
    db.session.commit()

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)
    compare_json(
        audit_boards,
        {
            "auditBoards": [
                {
                    "id": assert_is_id,
                    "name": "Audit Board #1",
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": J1_SAMPLES,
                        "numAuditedBallots": num_audited_samples,
                    },
                }
            ]
        },
    )

    # Finish auditing ballots and sign off
    audit_board = db.session.merge(audit_board)
    for ballot in audit_board.sampled_ballots[10:]:
        ballot.vote = "NO"
    audit_board.signed_off_at = datetime.utcnow()
    db.session.commit()

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)
    compare_json(
        audit_boards,
        {
            "auditBoards": [
                {
                    "id": assert_is_id,
                    "name": "Audit Board #1",
                    "signedOffAt": assert_is_date,
                    "currentRoundStatus": {
                        "numSampledBallots": J1_SAMPLES,
                        "numAuditedBallots": J1_SAMPLES,
                    },
                }
            ]
        },
    )


def test_audit_boards_create_two(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )
    assert_ok(rv)
    assert_ballots_got_assigned_correctly(
        jurisdiction_ids[0],
        round_1_id,
        expected_num_audit_boards=2,
        expected_num_ballots=75,
    )


def test_audit_boards_list_two(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    AB1_SAMPLES = 54

    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )
    assert_ok(rv)

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)
    compare_json(
        audit_boards,
        {
            "auditBoards": [
                {
                    "id": assert_is_id,
                    "name": "Audit Board #1",
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": AB1_SAMPLES,
                        "numAuditedBallots": 0,
                    },
                },
                {
                    "id": assert_is_id,
                    "name": "Audit Board #2",
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": J1_SAMPLES - AB1_SAMPLES,
                        "numAuditedBallots": 0,
                    },
                },
            ]
        },
    )

    # Fake auditing some ballots
    audit_board_1 = AuditBoard.query.get(audit_boards["auditBoards"][0]["id"])
    num_audited_samples_1 = 0
    for ballot in audit_board_1.sampled_ballots[:10]:
        ballot.vote = "YES"
        num_audited_samples_1 += len(ballot.draws)
    audit_board_2 = AuditBoard.query.get(audit_boards["auditBoards"][1]["id"])
    num_audited_samples_2 = 0
    for ballot in audit_board_2.sampled_ballots[:20]:
        ballot.vote = "YES"
        num_audited_samples_2 += len(ballot.draws)
    db.session.commit()

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]

    assert audit_boards[0]["currentRoundStatus"] == {
        "numSampledBallots": AB1_SAMPLES,
        "numAuditedBallots": num_audited_samples_1,
    }
    assert audit_boards[1]["currentRoundStatus"] == {
        "numSampledBallots": J1_SAMPLES - AB1_SAMPLES,
        "numAuditedBallots": num_audited_samples_2,
    }

    # Finish auditing ballots and sign off
    audit_board_1 = db.session.merge(audit_board_1)
    for ballot in audit_board_1.sampled_ballots[10:]:
        ballot.vote = "NO"
    audit_board_1.signed_off_at = datetime.utcnow()
    db.session.commit()

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]

    assert_is_date(audit_boards[0]["signedOffAt"])
    assert audit_boards[0]["currentRoundStatus"] == {
        "numSampledBallots": AB1_SAMPLES,
        "numAuditedBallots": AB1_SAMPLES,
    }
    assert audit_boards[1]["signedOffAt"] is None
    assert audit_boards[1]["currentRoundStatus"] == {
        "numSampledBallots": J1_SAMPLES - AB1_SAMPLES,
        "numAuditedBallots": num_audited_samples_2,
    }


def test_audit_boards_create_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_2_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
        [
            {"name": "Audit Board #1"},
            {"name": "Audit Board #2"},
            {"name": "Audit Board #3"},
        ],
    )
    assert_ok(rv)

    assert_ballots_got_assigned_correctly(
        jurisdiction_ids[0],
        round_2_id,
        expected_num_audit_boards=3,
        expected_num_ballots=134,
    )


def test_audit_boards_list_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    round_2_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    J1_SAMPLES_ROUND_2 = 148  # 90% prob sample size
    AB1_SAMPLES_ROUND_2 = 92
    AB2_SAMPLES_ROUND_2 = 29

    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
        [
            {"name": "Audit Board #1"},
            {"name": "Audit Board #2"},
            {"name": "Audit Board #3"},
        ],
    )
    assert_ok(rv)

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)
    compare_json(
        audit_boards,
        {
            "auditBoards": [
                {
                    "id": assert_is_id,
                    "name": "Audit Board #1",
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": AB1_SAMPLES_ROUND_2,
                        "numAuditedBallots": 0,
                    },
                },
                {
                    "id": assert_is_id,
                    "name": "Audit Board #2",
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": AB2_SAMPLES_ROUND_2,
                        "numAuditedBallots": 0,
                    },
                },
                {
                    "id": assert_is_id,
                    "name": "Audit Board #3",
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": J1_SAMPLES_ROUND_2
                        - AB1_SAMPLES_ROUND_2
                        - AB2_SAMPLES_ROUND_2,
                        "numAuditedBallots": 0,
                    },
                },
            ]
        },
    )

    # Can still access round 1 audit boards
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    assert rv.status_code == 200


def test_audit_boards_missing_field(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{}, {"name": "Audit Board #2"}],
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Bad Request", "message": "'name' is a required property",}
        ]
    }


def test_audit_boards_duplicate_name(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #1"}],
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Audit board names must be unique",}
        ]
    }


def test_audit_boards_already_created(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #2"}],
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Audit boards already created for round 1",
            }
        ]
    }


def test_audit_boards_wrong_round(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    round_2_id: str,  # pylint: disable=unused-argument
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Round 1 is not the current round",}
        ]
    }


def test_audit_boards_bad_round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,  # pylint: disable=unused-argument
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-valid-id/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert rv.status_code == 404


def set_up_audit_board(
    client: FlaskClient, election_id: str, jurisdiction_id: str, audit_board_id: str
) -> Tuple[str, str]:
    SILLY_NAMES = [
        "Joe Schmo",
        "Jane Plain",
        "Derk Clerk",
        "Bubbikin Republican",
        "Clem O'Hat Democrat",
    ]
    member_1 = random.choice(SILLY_NAMES)
    member_2 = random.choice(SILLY_NAMES)

    # Order of the names shouldn't matter for sign-off, so we shuffle
    # the names each time we set up the audit board members
    member_names = [
        {"name": member_1, "affiliation": "DEM"},
        {"name": member_2, "affiliation": "REP"},
    ]
    random.shuffle(member_names)

    # Set up the audit board
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/audit-board/{audit_board_id}",
        {"members": member_names},
    )
    assert_ok(rv)

    # Fake auditing all the ballots
    ballots = SampledBallot.query.filter_by(audit_board_id=audit_board_id).all()
    for ballot in ballots:
        ballot.vote = "YES"
    db.session.commit()

    return member_1, member_2


def test_audit_boards_sign_off_happy_path(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    def run_audit_board_flow(jurisdiction_id: str, audit_board_id: str):
        member_1, member_2 = set_up_audit_board(
            client, election_id, jurisdiction_id, audit_board_id
        )
        set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
        rv = post_json(
            client,
            f"/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
            {"memberName1": member_1, "memberName2": member_2},
        )
        assert_ok(rv)

    run_audit_board_flow(jurisdiction_ids[0], audit_board_round_1_ids[0])

    # After one audit board signs off, shouldn't end the round yet
    round = Round.query.get(round_1_id)
    assert round.ended_at is None

    run_audit_board_flow(jurisdiction_ids[0], audit_board_round_1_ids[1])

    # After second audit board signs off, shouldn't end the round yet because
    # the other jurisdictions still didn't set up audit boards
    round = Round.query.get(round_1_id)
    assert round.ended_at is None

    # Create an audit board for the other jurisdiction that had some ballots sampled
    EMAIL = "ja1@example.com"
    create_jurisdiction_admin(jurisdiction_ids[1], EMAIL)
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, EMAIL)
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board"
    )
    audit_board = json.loads(rv.data)["auditBoards"][0]

    run_audit_board_flow(jurisdiction_ids[1], audit_board["id"])

    # Now the round should be over
    round = Round.query.get(round_1_id)
    assert round.ended_at is not None

    # Check that the risk measurements got calculated
    round_contests = (
        RoundContest.query.filter_by(round_id=round_1_id)
        .join(Contest)
        .filter_by(election_id=election_id)
        .all()
    )
    for round_contest in round_contests:
        assert round_contest.end_p_value is not None
        assert round_contest.is_complete is not None


def test_audit_boards_sign_off_missing_name(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    audit_board_id = audit_board_round_1_ids[0]
    member_1, member_2 = set_up_audit_board(
        client, election_id, jurisdiction_ids[0], audit_board_id
    )
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)

    for missing_field in ["memberName1", "memberName2"]:
        sign_off_request_body = {"memberName1": member_1, "memberName2": member_2}
        del sign_off_request_body[missing_field]

        rv = post_json(
            client,
            f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
            sign_off_request_body,
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


def test_audit_boards_sign_off_wrong_name(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    audit_board_id = audit_board_round_1_ids[0]
    member_1, member_2 = set_up_audit_board(
        client, election_id, jurisdiction_ids[0], audit_board_id
    )
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)

    for wrong_field in ["memberName1", "memberName2"]:
        wrong_name = f"Wrong Name {wrong_field}"
        sign_off_request_body = {"memberName1": member_1, "memberName2": member_2}
        sign_off_request_body[wrong_field] = wrong_name

        rv = post_json(
            client,
            f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
            sign_off_request_body,
        )

        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Bad Request",
                    "message": f"Audit board member name did not match: {wrong_name}",
                }
            ]
        }


def test_audit_boards_sign_off_before_finished(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    audit_board_id = audit_board_round_1_ids[0]
    member_1, member_2 = set_up_audit_board(
        client, election_id, jurisdiction_ids[0], audit_board_id
    )
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)

    # Undo some of the ballot auditing done by set_up_audit_board
    ballots = SampledBallot.query.filter_by(audit_board_id=audit_board_id).all()
    for ballot in ballots[:10]:
        ballot.vote = None
    db.session.commit()

    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
        {"memberName1": member_1, "memberName2": member_2},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Audit board is not finished auditing all assigned ballots",
            }
        ]
    }

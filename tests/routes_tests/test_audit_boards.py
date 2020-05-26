import json, random, uuid
from typing import List, Tuple
from datetime import datetime
from collections import defaultdict
from flask.testing import FlaskClient

from tests.helpers import (
    post_json,
    put_json,
    assert_ok,
    compare_json,
    assert_is_id,
    assert_is_date,
    assert_is_passphrase,
    create_jurisdiction_admin,
    set_logged_in_user,
    audit_ballot,
    DEFAULT_JA_EMAIL,
    J1_SAMPLES_ROUND_1,
    J1_BALLOTS_ROUND_2,
    J1_BALLOTS_ROUND_1,
    J1_SAMPLES_ROUND_2,
    AB1_BALLOTS_ROUND_1,
    AB1_BALLOTS_ROUND_2,
    AB2_BALLOTS_ROUND_2,
)
from arlo_server.models import (
    db,
    AuditBoard,
    SampledBallot,
    Batch,
    Round,
    RoundContest,
    RoundContestResult,
    Contest,
    BallotStatus,
    ContestChoice,
    Interpretation,
    SampledBallotDraw,
)
from arlo_server.auth import UserType
from util.jsonschema import JSONDict


def assert_ballots_got_assigned_correctly(
    jurisdiction_id: str,
    round_id: str,
    expected_num_audit_boards: int,
    expected_num_samples: int,
):
    # We got the right number of audit boards
    audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction_id, round_id=round_id
    ).all()
    assert len(audit_boards) == expected_num_audit_boards

    # We got the right number of sampled ballots
    ballot_draws = (
        SampledBallotDraw.query.filter_by(round_id=round_id)
        .join(SampledBallot)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_id)
        .all()
    )
    assert len(ballot_draws) == expected_num_samples

    # All the ballots got assigned
    assert sum(len(ab.sampled_ballots) for ab in audit_boards) == len(
        set(bd.ballot_id for bd in ballot_draws)
    )

    # Every audit board got some ballots
    for audit_board in audit_boards:
        assert len(audit_board.sampled_ballots) > 0

    # All the ballots from each batch got assigned to the same audit board
    audit_boards_by_batch = defaultdict(set)
    for audit_board in audit_boards:
        for ballot in audit_board.sampled_ballots:
            audit_boards_by_batch[ballot.batch_id].add(audit_board.id)
    for audit_board_ids in audit_boards_by_batch.values():
        assert (
            len(audit_board_ids) == 1
        ), "Different audit boards assigned ballots from the same batch"


def test_audit_boards_list_empty(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)
    assert audit_boards == {"auditBoards": []}


def test_audit_boards_create_one(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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
        expected_num_samples=J1_SAMPLES_ROUND_1,
    )


def test_audit_boards_list_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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
                    "passphrase": assert_is_passphrase,
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": J1_BALLOTS_ROUND_1,
                        "numAuditedBallots": 0,
                    },
                }
            ]
        },
    )

    # Fake auditing some ballots
    audit_board = AuditBoard.query.get(audit_boards["auditBoards"][0]["id"])
    for ballot in audit_board.sampled_ballots[:10]:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
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
                    "passphrase": assert_is_passphrase,
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": J1_BALLOTS_ROUND_1,
                        "numAuditedBallots": 10,
                    },
                }
            ]
        },
    )

    # Finish auditing ballots and sign off
    audit_board = AuditBoard.query.get(audit_boards["auditBoards"][0]["id"])
    for ballot in audit_board.sampled_ballots[10:]:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
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
                    "passphrase": assert_is_passphrase,
                    "signedOffAt": assert_is_date,
                    "currentRoundStatus": {
                        "numSampledBallots": J1_BALLOTS_ROUND_1,
                        "numAuditedBallots": J1_BALLOTS_ROUND_1,
                    },
                }
            ]
        },
    )


def test_audit_boards_create_two(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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
        expected_num_samples=J1_SAMPLES_ROUND_1,
    )


def test_audit_boards_list_two(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)

    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )
    assert_ok(rv)

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]
    compare_json(
        audit_boards,
        [
            {
                "id": assert_is_id,
                "name": "Audit Board #1",
                "signedOffAt": None,
                "passphrase": assert_is_passphrase,
                "currentRoundStatus": {
                    "numSampledBallots": AB1_BALLOTS_ROUND_1,
                    "numAuditedBallots": 0,
                },
            },
            {
                "id": assert_is_id,
                "name": "Audit Board #2",
                "passphrase": assert_is_passphrase,
                "signedOffAt": None,
                "currentRoundStatus": {
                    "numSampledBallots": J1_BALLOTS_ROUND_1 - AB1_BALLOTS_ROUND_1,
                    "numAuditedBallots": 0,
                },
            },
        ],
    )

    # Fake auditing some ballots
    audit_board_1 = AuditBoard.query.get(audit_boards[0]["id"])
    for ballot in audit_board_1.sampled_ballots[:10]:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
    audit_board_2 = AuditBoard.query.get(audit_boards[1]["id"])
    for ballot in audit_board_2.sampled_ballots[:20]:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
    db.session.commit()

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]

    assert audit_boards[0]["currentRoundStatus"] == {
        "numSampledBallots": AB1_BALLOTS_ROUND_1,
        "numAuditedBallots": 10,
    }
    assert audit_boards[1]["currentRoundStatus"] == {
        "numSampledBallots": J1_BALLOTS_ROUND_1 - AB1_BALLOTS_ROUND_1,
        "numAuditedBallots": 20,
    }

    # Finish auditing ballots and sign off
    audit_board_1 = AuditBoard.query.get(audit_boards[0]["id"])
    for ballot in audit_board_1.sampled_ballots[10:]:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
    audit_board_1.signed_off_at = datetime.utcnow()
    db.session.commit()

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]

    assert_is_date(audit_boards[0]["signedOffAt"])
    assert audit_boards[0]["currentRoundStatus"] == {
        "numSampledBallots": AB1_BALLOTS_ROUND_1,
        "numAuditedBallots": AB1_BALLOTS_ROUND_1,
    }
    assert audit_boards[1]["signedOffAt"] is None
    assert audit_boards[1]["currentRoundStatus"] == {
        "numSampledBallots": J1_BALLOTS_ROUND_1 - AB1_BALLOTS_ROUND_1,
        "numAuditedBallots": 20,
    }


def test_audit_boards_create_round_2(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_2_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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
        expected_num_samples=J1_SAMPLES_ROUND_2,
    )


def test_audit_boards_list_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    round_2_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)

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
                    "passphrase": assert_is_passphrase,
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": AB1_BALLOTS_ROUND_2,
                        # Some ballots got audited in round 1 and sampled again in round 2
                        "numAuditedBallots": 22,
                    },
                },
                {
                    "id": assert_is_id,
                    "name": "Audit Board #2",
                    "passphrase": assert_is_passphrase,
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": AB2_BALLOTS_ROUND_2,
                        "numAuditedBallots": 3,
                    },
                },
                {
                    "id": assert_is_id,
                    "name": "Audit Board #3",
                    "passphrase": assert_is_passphrase,
                    "signedOffAt": None,
                    "currentRoundStatus": {
                        "numSampledBallots": J1_BALLOTS_ROUND_2
                        - AB1_BALLOTS_ROUND_2
                        - AB2_BALLOTS_ROUND_2,
                        "numAuditedBallots": 5,
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
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #1"}],
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Bad Request", "message": "Audit board names must be unique",}
        ]
    }


def test_audit_boards_already_created(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-valid-id/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert rv.status_code == 404


def test_audit_boards_set_members_valid(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    member_requests = [
        [{"name": "Audit Board #1", "affiliation": "DEM"}],
        [
            {"name": "Audit Board #1", "affiliation": "REP"},
            {"name": "Audit Board #2", "affiliation": None},
        ],
    ]
    for member_request in member_requests:
        rv = put_json(
            client,
            f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}",
            member_request,
        )
        assert_ok(rv)

        rv = client.get("/auth/me")
        audit_board = json.loads(rv.data)
        assert audit_board["members"] == member_request


def test_audit_boards_set_members_invalid(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    invalid_member_requests = [
        ([{"affiliation": "DEM"}], "'name' is a required property"),
        ([{"name": "Joe Schmo"}], "'affiliation' is a required property"),
        ([{"name": "", "affiliation": "DEM"}], "'name' must not be empty."),
        ([{"name": None, "affiliation": "DEM"}], "None is not of type 'string'"),
        (
            [{"name": "Jane Plain", "affiliation": ""}],
            "'' is not one of ['DEM', 'REP', 'LIB', 'IND', 'OTH']",
        ),
        (
            [{"name": "Jane Plain", "affiliation": "Democrat"}],
            "'Democrat' is not one of ['DEM', 'REP', 'LIB', 'IND', 'OTH']",
        ),
        ([], "Must have at least one member.",),
        (
            [
                {"name": "Joe Schmo", "affiliation": "DEM"},
                {"name": "Jane Plain", "affiliation": "REP"},
                {"name": "Extra Member", "affiliation": "IND"},
            ],
            "Cannot have more than two members.",
        ),
    ]
    for invalid_member_request, expected_message in invalid_member_requests:
        set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
        rv = put_json(
            client,
            f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}",
            invalid_member_request,
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": expected_message}]
        }


CHOICE_1_VOTES = 10
CHOICE_2_VOTES = 15


def set_up_audit_board(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,
    round_id: str,
    contest_id: str,
    audit_board_id: str,
    only_one_member=False,
) -> Tuple[str, str]:
    silly_names = [
        "Joe Schmo",
        "Jane Plain",
        "Derk Clerk",
        "Bubbikin Republican",
        "Clem O'Hat Democrat",
    ]
    rand = random.Random(12345)
    member_1 = rand.choice(silly_names)
    member_2 = rand.choice(silly_names)

    member_names: List[JSONDict] = [{"name": member_1, "affiliation": "DEM"}]
    if not only_one_member:
        member_names.append({"name": member_2, "affiliation": None})

    # Set up the audit board
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)
    rv = put_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/{audit_board_id}",
        member_names,
    )
    assert_ok(rv)

    # Fake auditing all the ballots
    # We iterate over the ballot draws so that we can ensure the computed
    # results are counting based on the samples, not the ballots.
    ballot_draws = (
        SampledBallotDraw.query.join(SampledBallot)
        .filter_by(audit_board_id=audit_board_id)
        .join(Batch)
        .order_by(Batch.name, SampledBallot.ballot_position)
        .all()
    )
    choices = (
        ContestChoice.query.filter_by(contest_id=contest_id)
        .order_by(ContestChoice.name)
        .all()
    )
    for draw in ballot_draws[:CHOICE_1_VOTES]:
        audit_ballot(
            draw.sampled_ballot, contest_id, Interpretation.VOTE, choices[0].id
        )
    for draw in ballot_draws[CHOICE_1_VOTES : CHOICE_1_VOTES + CHOICE_2_VOTES]:
        audit_ballot(
            draw.sampled_ballot, contest_id, Interpretation.VOTE, choices[1].id
        )
    for draw in ballot_draws[CHOICE_1_VOTES + CHOICE_2_VOTES :]:
        audit_ballot(draw.sampled_ballot, contest_id, Interpretation.BLANK)
    db.session.commit()

    return member_1, member_2


def test_audit_boards_sign_off_happy_path(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    def run_audit_board_flow(jurisdiction_id: str, audit_board_id: str):
        member_1, member_2 = set_up_audit_board(
            client,
            election_id,
            jurisdiction_id,
            round_1_id,
            contest_ids[0],
            audit_board_id,
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
    email = "ja1@example.com"
    create_jurisdiction_admin(jurisdiction_ids[1], email)
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, email)
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

    # Create another audit board that doesn't have any ballots assigned. Even
    # though this audit board doesn't sign off, it shouldn't stop the round
    # from being completed.
    audit_board_without_ballots = AuditBoard(
        id=str(uuid.uuid4()),
        jurisdiction_id=jurisdiction_ids[1],
        round_id=round_1_id,
        name="Audit Board Without Ballots",
    )
    db.session.add(audit_board_without_ballots)
    db.session.commit()

    run_audit_board_flow(jurisdiction_ids[1], audit_board["id"])

    # Now the round should be over
    round = Round.query.get(round_1_id)
    assert round.ended_at is not None
    results = (
        RoundContestResult.query.filter_by(round_id=round_1_id)
        .order_by(RoundContestResult.result)
        .all()
    )
    assert len(results) == 5

    contest_1_results = [r for r in results if r.contest_id == contest_ids[0]]
    assert len(contest_1_results) == 2
    assert contest_1_results[0].result == CHOICE_1_VOTES * 3
    assert contest_1_results[1].result == CHOICE_2_VOTES * 3

    contest_2_results = [r for r in results if r.contest_id == contest_ids[1]]
    assert len(contest_2_results) == 3
    # Note: we didn't record any audited ballots for contest 2, so we expect 0s
    # here. But contest 2 has overlapping candidate names as contest 1, so this
    # makes ensures we don't accidentally count votes for a choice for the
    # wrong contest.
    assert contest_2_results[0].result == 0
    assert contest_2_results[1].result == 0
    assert contest_2_results[2].result == 0

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
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    audit_board_id = audit_board_round_1_ids[0]
    member_1, member_2 = set_up_audit_board(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
        contest_ids[0],
        audit_board_id,
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
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    audit_board_id = audit_board_round_1_ids[0]
    member_1, member_2 = set_up_audit_board(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
        contest_ids[0],
        audit_board_id,
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
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    audit_board_id = audit_board_round_1_ids[0]
    member_1, member_2 = set_up_audit_board(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
        contest_ids[0],
        audit_board_id,
    )
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)

    # Undo some of the ballot auditing done by set_up_audit_board
    ballots = SampledBallot.query.filter_by(audit_board_id=audit_board_id).all()
    for ballot in ballots[:10]:
        ballot.status = BallotStatus.NOT_AUDITED
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


def test_audit_board_only_one_member_sign_off_happy_path(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    audit_board_id = audit_board_round_1_ids[0]
    member_1, _ = set_up_audit_board(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
        contest_ids[0],
        audit_board_id,
        only_one_member=True,
    )
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)

    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
        {"memberName1": member_1, "memberName2": ""},
    )
    assert_ok(rv)


def test_audit_board_only_one_member_sign_off_wrong_name(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    audit_board_id = audit_board_round_1_ids[0]
    set_up_audit_board(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
        contest_ids[0],
        audit_board_id,
        only_one_member=True,
    )
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_id)

    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
        {"memberName1": "Wrong Name", "memberName2": ""},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Audit board member name did not match: Wrong Name",
            }
        ]
    }

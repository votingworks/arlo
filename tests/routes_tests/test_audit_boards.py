import pytest, json
from flask.testing import FlaskClient
from typing import List, Generator
from datetime import datetime
from collections import defaultdict

from tests.helpers import (
    post_json,
    assert_ok,
    create_jurisdiction_admin,
    set_logged_in_user,
    compare_json,
    assert_is_id,
    assert_is_date,
)
from arlo_server.models import (
    db,
    AuditBoard,
    Round,
    RoundContestResult,
    Contest,
    SampledBallot,
    Batch,
)
from arlo_server.auth import UserType

JA_EMAIL = "ja@example.com"
SAMPLE_SIZE = 119  # Bravo sample size
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


@pytest.fixture
def round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_id: str,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
) -> Generator[str, None, None]:
    rv = post_json(
        client,
        f"/election/{election_id}/round",
        {"roundNum": 1, "sampleSize": SAMPLE_SIZE},
    )
    assert_ok(rv)
    rv = client.get(f"/election/{election_id}/round",)
    rounds = json.loads(rv.data)["rounds"]
    yield rounds[0]["id"]


@pytest.fixture
def round_2_id(
    client: FlaskClient, election_id: str, contest_id: str, round_id: str,
) -> Generator[str, None, None]:
    # Fake that the first round got completed by setting Round.ended_at.
    # We also need to add RoundContestResults so that the next round sample
    # size can get computed.
    round = Round.query.get(round_id)
    round.ended_at = datetime.utcnow()
    contest = Contest.query.get(contest_id)
    db.session.add(
        RoundContestResult(
            round_id=round.id,
            contest_id=contest.id,
            contest_choice_id=contest.choices[0].id,
            result=70,
        )
    )
    db.session.add(
        RoundContestResult(
            round_id=round.id,
            contest_id=contest.id,
            contest_choice_id=contest.choices[1].id,
            result=49,
        )
    )
    db.session.commit()

    set_logged_in_user(client, UserType.AUDIT_ADMIN, "aa@example.com")
    rv = post_json(client, f"/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/round",)
    rounds = json.loads(rv.data)["rounds"]
    yield rounds[1]["id"]


@pytest.fixture
def as_jurisdiction_admin(client: FlaskClient, jurisdiction_ids: List[str]):
    create_jurisdiction_admin(jurisdiction_ids[0], JA_EMAIL)
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, JA_EMAIL)


def test_audit_boards_list_empty(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)
    assert audit_boards == {"auditBoards": []}


def test_audit_boards_create_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)
    assert_ballots_got_assigned_correctly(
        jurisdiction_ids[0],
        round_id,
        expected_num_audit_boards=1,
        expected_num_ballots=75,
    )


def test_audit_boards_list_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
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
    round_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )
    assert_ok(rv)
    assert_ballots_got_assigned_correctly(
        jurisdiction_ids[0],
        round_id,
        expected_num_audit_boards=2,
        expected_num_ballots=75,
    )


def test_audit_boards_list_two(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    AB1_SAMPLES = 54

    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )
    assert_ok(rv)

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
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
    round_id: str,
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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
    )
    assert rv.status_code == 200


def test_audit_boards_missing_field(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
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
    round_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
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
    round_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
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
    round_id: str,
    round_2_id: str,  # pylint: disable=unused-argument
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
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
    round_id: str,  # pylint: disable=unused-argument
    as_jurisdiction_admin,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-valid-id/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert rv.status_code == 404

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


def test_audit_boards_round_2(
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

import json, random, uuid, itertools
from typing import List, Tuple
from datetime import datetime
from collections import defaultdict
from flask.testing import FlaskClient

from ..helpers import *  # pylint: disable=wildcard-import
from ...models import *  # pylint: disable=wildcard-import
from ...auth import UserType
from ...api.rounds import count_audited_votes
from ...util.jsonschema import JSONDict


def assert_ballots_got_assigned_correctly(
    audit_boards: List[AuditBoard],
    ballot_draws: List[SampledBallotDraw],
):
    # All the ballots got assigned
    assert sum(len(list(ab.sampled_ballots)) for ab in audit_boards) == len(
        set(bd.ballot_id for bd in ballot_draws)
    )

    # Every audit board got some ballots
    for audit_board in audit_boards:
        assert len(list(audit_board.sampled_ballots)) > 0

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
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)
    assert audit_boards == {"auditBoards": []}


def test_audit_boards_create_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction_ids[0], round_id=round_1_id
    ).all()
    assert len(audit_boards) == 1

    ballot_draws = (
        SampledBallotDraw.query.filter_by(round_id=round_1_id)
        .join(SampledBallot)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .all()
    )
    snapshot.assert_match(len(ballot_draws))

    assert_ballots_got_assigned_correctly(audit_boards, ballot_draws)


def test_audit_boards_list_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]
    snapshot.assert_match(
        [
            {
                "name": audit_board["name"],
                "currentRoundStatus": audit_board["currentRoundStatus"],
            }
            for audit_board in audit_boards
        ]
    )
    assert audit_boards[0]["signedOffAt"] is None

    # Fake auditing some ballots
    audit_board = AuditBoard.query.get(audit_boards[0]["id"])
    for ballot in audit_board.sampled_ballots[:10]:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
    db_session.commit()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]
    snapshot.assert_match(
        [
            {
                "name": audit_board["name"],
                "currentRoundStatus": audit_board["currentRoundStatus"],
            }
            for audit_board in audit_boards
        ]
    )
    assert audit_boards[0]["signedOffAt"] is None

    # Finish auditing ballots and sign off
    audit_board = AuditBoard.query.get(audit_boards[0]["id"])
    for ballot in audit_board.sampled_ballots[10:]:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
    audit_board.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]

    snapshot.assert_match(
        [
            {
                "name": audit_board["name"],
                "currentRoundStatus": audit_board["currentRoundStatus"],
            }
            for audit_board in audit_boards
        ]
    )
    assert_is_date(audit_boards[0]["signedOffAt"])


def test_audit_boards_create_two(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )
    assert_ok(rv)

    audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction_ids[0], round_id=round_1_id
    ).all()
    assert len(audit_boards) == 2

    ballot_draws = (
        SampledBallotDraw.query.filter_by(round_id=round_1_id)
        .join(SampledBallot)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .all()
    )
    snapshot.assert_match(len(ballot_draws))

    assert_ballots_got_assigned_correctly(audit_boards, ballot_draws)


def test_audit_boards_list_two(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]
    snapshot.assert_match(
        [
            {
                "name": audit_board["name"],
                "currentRoundStatus": audit_board["currentRoundStatus"],
            }
            for audit_board in audit_boards
        ]
    )
    assert audit_boards[0]["signedOffAt"] is None
    assert audit_boards[1]["signedOffAt"] is None

    # Fake auditing some ballots
    audit_board_1 = AuditBoard.query.get(audit_boards[0]["id"])
    for ballot in audit_board_1.sampled_ballots[:10]:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
    audit_board_2 = AuditBoard.query.get(audit_boards[1]["id"])
    for ballot in audit_board_2.sampled_ballots[:20]:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
    db_session.commit()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]

    snapshot.assert_match(
        [
            {
                "name": audit_board["name"],
                "currentRoundStatus": audit_board["currentRoundStatus"],
            }
            for audit_board in audit_boards
        ]
    )
    assert audit_boards[0]["signedOffAt"] is None
    assert audit_boards[1]["signedOffAt"] is None

    # Finish auditing ballots and sign off
    audit_board_1 = AuditBoard.query.get(audit_boards[0]["id"])
    for ballot in audit_board_1.sampled_ballots[10:]:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
    audit_board_1.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]

    snapshot.assert_match(
        [
            {
                "name": audit_board["name"],
                "currentRoundStatus": audit_board["currentRoundStatus"],
            }
            for audit_board in audit_boards
        ]
    )
    assert_is_date(audit_boards[0]["signedOffAt"])
    assert audit_boards[1]["signedOffAt"] is None


def test_audit_boards_create_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_2_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
        [
            {"name": "Audit Board #1"},
            {"name": "Audit Board #2"},
            {"name": "Audit Board #3"},
        ],
    )
    assert_ok(rv)

    audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction_ids[0], round_id=round_2_id
    ).all()
    assert len(audit_boards) == 3

    ballot_draws = (
        SampledBallotDraw.query.filter_by(round_id=round_2_id)
        .join(SampledBallot)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .all()
    )
    snapshot.assert_match(len(ballot_draws))

    assert_ballots_got_assigned_correctly(audit_boards, ballot_draws)


def test_audit_boards_list_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    round_2_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
        [
            {"name": "Audit Board #1"},
            {"name": "Audit Board #2"},
            {"name": "Audit Board #3"},
        ],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
    )
    audit_boards = json.loads(rv.data)["auditBoards"]
    snapshot.assert_match(
        [
            {
                "name": audit_board["name"],
                "currentRoundStatus": audit_board["currentRoundStatus"],
            }
            for audit_board in audit_boards
        ]
    )
    assert audit_boards[0]["signedOffAt"] is None
    assert audit_boards[1]["signedOffAt"] is None
    assert audit_boards[2]["signedOffAt"] is None

    # Can still access round 1 audit boards
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    assert rv.status_code == 200


def test_audit_boards_missing_field(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{}, {"name": "Audit Board #2"}],
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "'name' is a required property",
            }
        ]
    }


def test_audit_boards_duplicate_name(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #1"}],
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Audit board names must be unique",
            }
        ]
    }


def test_audit_boards_already_created(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
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
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Round 1 is not the current round",
            }
        ]
    }


def test_audit_boards_bad_round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-valid-id/audit-board",
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
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/members",
            member_request,
        )
        assert_ok(rv)

        rv = client.get("/api/me")
        audit_board = json.loads(rv.data)
        assert audit_board["user"]["members"] == member_request


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
        (
            [],
            "Must have at least one member.",
        ),
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
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/members",
            invalid_member_request,
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": expected_message}]
        }


CHOICE_1_VOTES = 10
CHOICE_2_VOTES = 15
OVERVOTES = 3


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
        " Joe Schmo",
        "Jane Plain",
        "Derk Clerk",
        "Bubbikin Republican",
        " Clem O'Hat Democrat ",
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
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board/{audit_board_id}/members",
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

    num_ballot_draws = len(ballot_draws)
    ballot_draws = iter(ballot_draws)
    for draw in itertools.islice(ballot_draws, CHOICE_1_VOTES):
        audit_ballot(draw.sampled_ballot, contest_id, Interpretation.VOTE, [choices[0]])
    for i, draw in enumerate(itertools.islice(ballot_draws, CHOICE_2_VOTES)):
        audit_ballot(
            draw.sampled_ballot,
            contest_id,
            Interpretation.VOTE,
            [choices[1]],
            # Add an invalid write-in to the last choice 2 vote
            has_invalid_write_in=(i == CHOICE_2_VOTES - 1),
        )
    for i, draw in enumerate(itertools.islice(ballot_draws, OVERVOTES)):
        audit_ballot(
            draw.sampled_ballot,
            contest_id,
            Interpretation.VOTE,
            [choices[0], choices[1]],
            is_overvote=True,
            # Add an invalid write-in to the last overvote
            has_invalid_write_in=(i == OVERVOTES - 1),
        )
    num_blanks = num_ballot_draws - CHOICE_1_VOTES - CHOICE_2_VOTES - OVERVOTES
    for i, draw in enumerate(ballot_draws):
        audit_ballot(
            draw.sampled_ballot,
            contest_id,
            Interpretation.BLANK,
            # Add an invalid write-in to the last blank vote
            has_invalid_write_in=(i == num_blanks - 1),
        )
    db_session.commit()

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
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
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
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
            {"memberName1": member_1, "memberName2": member_2},
        )
        assert_ok(rv)

    run_audit_board_flow(jurisdiction_ids[0], audit_board_round_1_ids[0])

    # After one audit board signs off, shouldn't allow ending the round yet
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert rv.status_code == 409

    run_audit_board_flow(jurisdiction_ids[0], audit_board_round_1_ids[1])

    # After second audit board signs off, shouldn't allow ending the round yet
    # because the other jurisdictions still didn't set up audit boards
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert rv.status_code == 409

    # Create an audit board for the other jurisdiction that had some ballots sampled
    email = "ja1@example.com"
    create_jurisdiction_admin(jurisdiction_ids[1], email)
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, email)
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board"
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
    db_session.add(audit_board_without_ballots)
    db_session.commit()

    run_audit_board_flow(jurisdiction_ids[1], audit_board["id"])

    # Now the round should be endable
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

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


def test_count_audited_votes(
    election_id: str,
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    election = Election.query.get(election_id)
    round = Round.query.get(round_1_id)
    targeted_contest_id = contest_ids[0]
    opportunistic_contest_id = contest_ids[1]

    # Make sure counting before auditing ballots results in all 0s
    count_audited_votes(election, round)

    for round_contest in round.round_contests:
        for result in round_contest.results:
            assert result.result == 0

    db_session.rollback()

    ballot_draws = (
        SampledBallotDraw.query.join(SampledBallot)
        .filter_by(audit_board_id=audit_board_round_1_ids[0])
        .join(Batch)
        .order_by(Batch.name, SampledBallot.ballot_position)
        .all()
    )
    targeted_choices = (
        ContestChoice.query.filter_by(contest_id=targeted_contest_id)
        .order_by(ContestChoice.name)
        .all()
    )
    opportunistic_choices = (
        ContestChoice.query.filter_by(contest_id=opportunistic_contest_id)
        .order_by(ContestChoice.name)
        .all()
    )

    targeted_choice_1_votes = 10
    targeted_choice_2_votes = 20
    overvotes = 5

    # Make sure audit at least one ballot that was sampled multiple times
    # to ensure our test is testing the difference between counting votes for
    # targeted contests (num ballot draws) and opportunistic ballots (num ballots)
    draws_to_audit = ballot_draws[
        : targeted_choice_1_votes + targeted_choice_2_votes + overvotes
    ]
    assert len({draw.sampled_ballot.id for draw in draws_to_audit}) < len(
        draws_to_audit
    )

    opportunistic_choice_1_and_2_ballots = set()
    opportunistic_choice_2_and_3_ballots = set()

    ballot_draws = iter(ballot_draws)

    for draw in itertools.islice(ballot_draws, targeted_choice_1_votes):
        audit_ballot(
            draw.sampled_ballot,
            targeted_contest_id,
            Interpretation.VOTE,
            [targeted_choices[0]],
        )
        audit_ballot(
            draw.sampled_ballot,
            opportunistic_contest_id,
            Interpretation.VOTE,
            [opportunistic_choices[0], opportunistic_choices[1]],
        )
        opportunistic_choice_1_and_2_ballots.add(draw.sampled_ballot.id)

    for draw in itertools.islice(ballot_draws, targeted_choice_2_votes):
        audit_ballot(
            draw.sampled_ballot,
            targeted_contest_id,
            Interpretation.VOTE,
            [targeted_choices[1]],
        )
        audit_ballot(
            draw.sampled_ballot,
            opportunistic_contest_id,
            Interpretation.VOTE,
            [opportunistic_choices[1], opportunistic_choices[2]],
        )
        opportunistic_choice_2_and_3_ballots.add(draw.sampled_ballot.id)

    # Overvotes shouldn't be counted in the totals
    for draw in itertools.islice(ballot_draws, overvotes):
        audit_ballot(
            draw.sampled_ballot,
            targeted_contest_id,
            Interpretation.VOTE,
            targeted_choices,
            is_overvote=True,
        )
        audit_ballot(
            draw.sampled_ballot,
            opportunistic_contest_id,
            Interpretation.VOTE,
            opportunistic_choices,
            is_overvote=True,
        )

    count_audited_votes(election, round)

    targeted_choice_1_result = RoundContestResult.query.filter_by(
        round_id=round_1_id,
        contest_id=targeted_contest_id,
        contest_choice_id=targeted_choices[0].id,
    ).first()
    targeted_choice_2_result = RoundContestResult.query.filter_by(
        round_id=round_1_id,
        contest_id=targeted_contest_id,
        contest_choice_id=targeted_choices[1].id,
    ).first()

    assert targeted_choice_1_result.result == targeted_choice_1_votes
    assert targeted_choice_2_result.result == targeted_choice_2_votes

    opportunistic_choice_1_result = RoundContestResult.query.filter_by(
        round_id=round_1_id,
        contest_id=opportunistic_contest_id,
        contest_choice_id=opportunistic_choices[0].id,
    ).first()
    opportunistic_choice_2_result = RoundContestResult.query.filter_by(
        round_id=round_1_id,
        contest_id=opportunistic_contest_id,
        contest_choice_id=opportunistic_choices[1].id,
    ).first()
    opportunistic_choice_3_result = RoundContestResult.query.filter_by(
        round_id=round_1_id,
        contest_id=opportunistic_contest_id,
        contest_choice_id=opportunistic_choices[2].id,
    ).first()

    assert opportunistic_choice_1_result.result == len(
        opportunistic_choice_1_and_2_ballots
    )
    assert opportunistic_choice_2_result.result == len(
        opportunistic_choice_1_and_2_ballots
    ) + len(opportunistic_choice_2_and_3_ballots)
    assert opportunistic_choice_3_result.result == len(
        opportunistic_choice_2_and_3_ballots
    )


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
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
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
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
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
    db_session.commit()

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
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
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
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
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_id}/sign-off",
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


def test_audit_boards_sign_off_whitespace(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    member_1, member_2 = set_up_audit_board(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
        contest_ids[0],
        audit_board_round_1_ids[0],
    )
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/sign-off",
        {"memberName1": f" {member_1}", "memberName2": f"  {member_2}  "},
    )
    assert_ok(rv)


def test_audit_board_human_order(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str
):
    # Create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": f"Audit Board #{i}"} for i in range(1, 11)],
    )
    assert_ok(rv)

    # Check that we return them in human order
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
    )
    assert [
        audit_board["name"] for audit_board in json.loads(rv.data)["auditBoards"]
    ] == [f"Audit Board #{i}" for i in range(1, 11)]


def test_reopen_audit_board(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    member_1, member_2 = set_up_audit_board(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
        contest_ids[0],
        audit_board_round_1_ids[0],
    )
    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board_round_1_ids[0])
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/sign-off",
        {
            "memberName1": member_1,
            "memberName2": member_2,
        },
    )
    assert_ok(rv)
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/sign-off"
    )
    assert_ok(rv)
    assert AuditBoard.query.get(audit_board_round_1_ids[0]).signed_off_at is None


def test_reopen_audit_board_error_cases(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_up_audit_board(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
        contest_ids[0],
        audit_board_round_1_ids[0],
    )
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/sign-off"
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Audit board has not signed off.",
            }
        ]
    }

    run_audit_round(round_1_id, contest_ids[0], contest_ids, 0.55)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/sign-off"
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Can't reopen audit board after round ends.",
            }
        ]
    }

    # Start a second round
    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 2,
            "sampleSizes": {
                contest_id: options[0]
                for contest_id, options in sample_size_options.items()
            },
        },
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    assert rv.status_code == 200

    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board_round_1_ids[0]}/sign-off"
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Audit board is not part of the current round.",
            }
        ]
    }

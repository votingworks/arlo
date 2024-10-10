from typing import List
import json
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ...auth import UserType
from ..helpers import *  # pylint: disable=wildcard-import


def test_rounds_list_empty(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)
    assert rounds == {"rounds": []}

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round"
    )
    rounds = json.loads(rv.data)
    assert rounds == {"rounds": []}


def test_rounds_create_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_size = sample_size_options[contest_ids[0]][0]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_ids[0]: sample_size},
        },
    )
    assert_ok(rv)

    expected_rounds = {
        "rounds": [
            {
                "id": assert_is_id,
                "roundNum": 1,
                "startedAt": assert_is_date,
                "endedAt": None,
                "isAuditComplete": None,
                "needsFullHandTally": False,
                "isFullHandTally": False,
                "drawSampleTask": {
                    "status": "PROCESSED",
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": None,
                },
            }
        ]
    }

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round"
    )
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    # Check that we also created RoundContest objects
    round_contests = RoundContest.query.filter_by(
        round_id=rounds["rounds"][0]["id"]
    ).all()
    assert len(round_contests) == 2
    assert sorted([rc.contest_id for rc in round_contests]) == sorted(contest_ids)

    # Check that the ballots got sampled
    ballot_draws = SampledBallotDraw.query.filter_by(
        round_id=rounds["rounds"][0]["id"]
    ).all()
    assert len(ballot_draws) == sample_size["size"]
    # Check that we're sampling ballots from the two jurisdictions that uploaded manifests
    sampled_jurisdictions = {
        draw.sampled_ballot.batch.jurisdiction_id for draw in ballot_draws
    }
    assert sorted(sampled_jurisdictions) == sorted(jurisdiction_ids[:2])


def test_rounds_create_two(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    snapshot,
):
    run_audit_round(round_1_id, contest_ids[0], contest_ids, 0.5)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

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

    expected_rounds = {
        "rounds": [
            {
                "id": assert_is_id,
                "roundNum": 1,
                "startedAt": assert_is_date,
                "endedAt": assert_is_date,
                "isAuditComplete": False,
                "needsFullHandTally": False,
                "isFullHandTally": False,
                "drawSampleTask": {
                    "status": "PROCESSED",
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": None,
                },
            },
            {
                "id": assert_is_id,
                "roundNum": 2,
                "startedAt": assert_is_date,
                "endedAt": None,
                "isAuditComplete": None,
                "needsFullHandTally": False,
                "isFullHandTally": False,
                "drawSampleTask": {
                    "status": "PROCESSED",
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": None,
                },
            },
        ]
    }
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round"
    )
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    ballot_draws = SampledBallotDraw.query.filter_by(
        round_id=rounds["rounds"][1]["id"]
    ).all()
    # Check that we automatically select the 90% prob sample size
    snapshot.assert_match(len(ballot_draws))
    # Check that we're sampling ballots from the two jurisdictions that uploaded manifests
    sampled_jurisdictions = {
        draw.sampled_ballot.batch.jurisdiction_id for draw in ballot_draws
    }
    assert sorted(sampled_jurisdictions) == sorted(jurisdiction_ids[:2])


def test_rounds_complete_audit(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],
    round_1_id: str,
):
    run_audit_round(round_1_id, contest_ids[0], contest_ids, 0.7)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    expected_rounds = {
        "rounds": [
            {
                "id": assert_is_id,
                "roundNum": 1,
                "startedAt": assert_is_date,
                "endedAt": assert_is_date,
                "isAuditComplete": True,
                "needsFullHandTally": False,
                "isFullHandTally": False,
                "drawSampleTask": {
                    "status": "PROCESSED",
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": None,
                },
            }
        ]
    }
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)


def test_rounds_round_2_required_if_all_blanks(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],
    round_1_id: str,
):
    run_audit_round_all_blanks(round_1_id, contest_ids[0], contest_ids)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert len(rounds) == 1
    assert_is_date(rounds[0]["endedAt"])
    assert not rounds[0]["isAuditComplete"]


def test_rounds_end_logic_unaffected_by_invalid_write_ins_1(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],
    round_1_id: str,
):
    run_audit_round(
        round_1_id, contest_ids[0], contest_ids, 0.7, invalid_write_in_ratio=1
    )
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert len(rounds) == 1
    assert_is_date(rounds[0]["endedAt"])
    assert rounds[0]["isAuditComplete"]


def test_rounds_end_logic_unaffected_by_invalid_write_ins_2(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],
    round_1_id: str,
):
    run_audit_round(
        round_1_id, contest_ids[0], contest_ids, 0.5, invalid_write_in_ratio=1
    )
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert len(rounds) == 1
    assert_is_date(rounds[0]["endedAt"])
    assert not rounds[0]["isAuditComplete"]


def test_rounds_end_logic_unaffected_by_invalid_write_ins_3(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],
    round_1_id: str,
):
    run_audit_round_all_blanks(
        round_1_id, contest_ids[0], contest_ids, invalid_write_in_ratio=1
    )
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert len(rounds) == 1
    assert_is_date(rounds[0]["endedAt"])
    assert not rounds[0]["isAuditComplete"]


def test_rounds_create_before_previous_round_complete(
    client: FlaskClient,
    election_id: str,
    contest_ids: str,
    round_1_id: str,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 2,
            "sampleSizes": {contest_ids[0]: {"key": "0.9", "size": 10, "prob": 0.9}},
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "The current round is not complete",
                "errorType": "Conflict",
            }
        ]
    }


def test_rounds_wrong_number_too_big(
    client: FlaskClient, election_id: str, contest_ids: List[str]
):
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 2,
            "sampleSizes": {
                contest_ids[0]: {"key": "custom", "size": 10, "prob": None}
            },
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "The next round should be round number 1",
                "errorType": "Bad Request",
            }
        ]
    }


def test_rounds_wrong_number_too_small(
    client: FlaskClient,
    election_id: str,
    contest_ids: str,
):
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contest_ids[0]: {"key": "custom", "size": 10, "prob": None}
            },
        },
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contest_ids[0]: {"key": "custom", "size": 10, "prob": None}
            },
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "The next round should be round number 2",
                "errorType": "Bad Request",
            }
        ]
    }


def test_rounds_missing_sample_sizes(client: FlaskClient, election_id: str):
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 1})
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "'sampleSizes' is a required property",
                "errorType": "Bad Request",
            }
        ]
    }


def test_rounds_missing_round_num(
    client: FlaskClient, election_id: str, contest_ids: List[str]
):
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "sampleSizes": {
                contest_ids[0]: {"key": "custom", "size": 10, "prob": None}
            },
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "'roundNum' is a required property",
                "errorType": "Bad Request",
            }
        ]
    }


def test_rounds_bad_sample_sizes(
    client: FlaskClient, election_id: str, contest_ids: List[str]
):
    bad_sample_sizes = [
        ({}, "Sample sizes provided do not match targeted contest ids"),
        (
            {"not_a_real_id": {"key": "custom", "size": 10, "prob": None}},
            "Sample sizes provided do not match targeted contest ids",
        ),
        (
            {
                contest_ids[0]: {"key": "custom", "size": 10, "prob": None},
                contest_ids[1]: {"key": "custom", "size": 10, "prob": None},
            },
            "Sample sizes provided do not match targeted contest ids",
        ),
        (
            {contest_ids[0]: {"key": "bad_key", "size": 10, "prob": None}},
            "Invalid sample size key for contest Contest 1: bad_key",
        ),
        (
            {contest_ids[0]: {"key": "custom", "size": 3000, "prob": None}},
            "Sample size for contest Contest 1 must be less than or equal to: 1000 (the total number of ballots in the contest)",
        ),
    ]
    for bad_sample_size, expected_error in bad_sample_sizes:
        rv = post_json(
            client,
            f"/api/election/{election_id}/round",
            {"roundNum": 1, "sampleSizes": bad_sample_size},
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "message": expected_error,
                    "errorType": "Bad Request",
                }
            ]
        }


def test_finish_round_after_round_already_finished(
    client: FlaskClient, election_id: str, contest_ids: List[str], round_1_id: str
):
    run_audit_round(round_1_id, contest_ids[0], contest_ids, 0.5)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Round already finished",
                "errorType": "Conflict",
            }
        ]
    }


def test_finish_round_before_launch(client: FlaskClient, election_id: str):
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Audit not started",
                "errorType": "Conflict",
            }
        ]
    }


def test_undo_start_round_before_launch(client: FlaskClient, election_id: str):
    rv = client.delete(f"/api/election/{election_id}/round/current")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Audit not started",
                "errorType": "Conflict",
            }
        ]
    }


def test_undo_start_round_1(
    client: FlaskClient,
    election_id: str,
    round_1_id: str,  # pylint: disable=unused-argument
):
    rv = client.delete(f"/api/election/{election_id}/round/current")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    assert json.loads(rv.data) == {"rounds": []}

    assert (
        SampledBallot.query.join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election_id)
        .count()
        == 0
    )
    assert (
        SampledBallotDraw.query.join(SampledBallot)
        .join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election_id)
        .count()
        == 0
    )


def test_undo_start_round_1_with_audit_boards(
    client: FlaskClient,
    election_id: str,
    round_1_id: str,  # pylint: disable=unused-argument
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.delete(f"/api/election/{election_id}/round/current")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Cannot undo starting this round because some jurisdictions have already created audit boards.",
                "errorType": "Conflict",
            }
        ]
    }


def test_undo_start_round_2(
    client: FlaskClient, election_id: str, round_1_id: str, round_2_id: str
):
    rv = client.delete(f"/api/election/{election_id}/round/current")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert len(rounds) == 1
    assert rounds[0]["id"] == round_1_id

    sampled_ballots = (
        SampledBallot.query.join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election_id)
        .all()
    )
    assert len(sampled_ballots) > 0
    for ballot in sampled_ballots:
        assert len(ballot.draws) > 0
        assert all(draw.round_id == round_1_id for draw in ballot.draws)

    assert SampledBallotDraw.query.filter_by(round_id=round_2_id).count() == 0

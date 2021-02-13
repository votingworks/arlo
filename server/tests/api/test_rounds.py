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
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_size = sample_size_options[contest_ids[0]][0]["size"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_ids[0]: sample_size},},
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
                "sampledAllBallots": False,
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
    assert len(ballot_draws) == sample_size
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

    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    expected_rounds = {
        "rounds": [
            {
                "id": assert_is_id,
                "roundNum": 1,
                "startedAt": assert_is_date,
                "endedAt": assert_is_date,
                "isAuditComplete": False,
                "sampledAllBallots": False,
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
                "sampledAllBallots": False,
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
    client: FlaskClient, election_id: str, contest_ids: List[str], round_1_id: str,
):
    run_audit_round(round_1_id, contest_ids[0], contest_ids, 0.7)

    expected_rounds = {
        "rounds": [
            {
                "id": assert_is_id,
                "roundNum": 1,
                "startedAt": assert_is_date,
                "endedAt": assert_is_date,
                "isAuditComplete": True,
                "sampledAllBallots": False,
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


def test_rounds_create_before_previous_round_complete(
    client: FlaskClient,
    election_id: str,
    contest_ids: str,
    manifests,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_ids[0]: 10}},
    )
    assert_ok(rv)

    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2},)
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"message": "The current round is not complete", "errorType": "Conflict",}
        ]
    }


def test_rounds_wrong_number_too_big(client: FlaskClient, election_id: str):
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2})
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
    client: FlaskClient, election_id: str, contest_ids: str,
):
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_ids[0]: 10}},
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_ids[0]: 10}},
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
                "message": "Sample sizes are required for round 1",
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
        {"sampleSizes": {contest_ids[0]: 10}},
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
        {},
        {"not_a_real_id": 1},
        {contest_ids[0]: 10, contest_ids[1]: 20},
    ]
    for bad_sample_size in bad_sample_sizes:
        rv = post_json(
            client,
            f"/api/election/{election_id}/round",
            {"roundNum": 1, "sampleSizes": bad_sample_size},
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "message": "Sample sizes provided do not match targeted contest ids",
                    "errorType": "Bad Request",
                }
            ]
        }


def test_custom_sample_size_validation(
    client: FlaskClient, election_id: str, contest_ids: List[str]
):
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_ids[0]: 3000}},
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Sample size must be less than or equal to: 1000 (the total number of ballots in the targeted contest)",
                "errorType": "Conflict",
            }
        ]
    }

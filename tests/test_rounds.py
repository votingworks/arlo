from typing import List
import json
from flask.testing import FlaskClient

from arlo_server.models import (
    SampledBallotDraw,
    RoundContest,
)
from arlo_server.auth import UserType
from tests.helpers import (
    assert_ok,
    post_json,
    compare_json,
    assert_is_id,
    assert_is_date,
    set_logged_in_user,
    run_audit_round,
    DEFAULT_JA_EMAIL,
)


def test_rounds_list_empty(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = client.get(f"/election/{election_id}/round")
    rounds = json.loads(rv.data)
    assert rounds == {"rounds": []}

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round")
    rounds = json.loads(rv.data)
    assert rounds == {"rounds": []}


def test_rounds_create_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: str,
    manifests,  # pylint: disable=unused-argument
):
    sample_size = 119  # BRAVO sample size
    rv = post_json(
        client,
        f"/election/{election_id}/round",
        {"roundNum": 1, "sampleSize": sample_size,},
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
            }
        ]
    }

    rv = client.get(f"/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round")
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
):
    run_audit_round(round_1_id, contest_ids[0], 0.5)

    rv = post_json(client, f"/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    expected_rounds = {
        "rounds": [
            {
                "id": assert_is_id,
                "roundNum": 1,
                "startedAt": assert_is_date,
                "endedAt": assert_is_date,
                "isAuditComplete": False,
            },
            {
                "id": assert_is_id,
                "roundNum": 2,
                "startedAt": assert_is_date,
                "endedAt": None,
                "isAuditComplete": None,
            },
        ]
    }
    rv = client.get(f"/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    ballot_draws = SampledBallotDraw.query.filter_by(
        round_id=rounds["rounds"][1]["id"]
    ).all()
    # Check that we automatically select the 90% prob sample size
    assert len(ballot_draws) == 395
    # Check that we're sampling ballots from the two jurisdictions that uploaded manifests
    sampled_jurisdictions = {
        draw.sampled_ballot.batch.jurisdiction_id for draw in ballot_draws
    }
    assert sorted(sampled_jurisdictions) == sorted(jurisdiction_ids[:2])


def test_rounds_complete_audit(
    client: FlaskClient, election_id: str, contest_ids: List[str], round_1_id: str,
):
    run_audit_round(round_1_id, contest_ids[0], 0.7)

    expected_rounds = {
        "rounds": [
            {
                "id": assert_is_id,
                "roundNum": 1,
                "startedAt": assert_is_date,
                "endedAt": assert_is_date,
                "isAuditComplete": True,
            }
        ]
    }
    rv = client.get(f"/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)


def test_rounds_create_before_previous_round_complete(
    client: FlaskClient,
    election_id: str,
    contest_ids: str,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    rv = post_json(
        client, f"/election/{election_id}/round", {"roundNum": 1, "sampleSize": 10,},
    )
    assert_ok(rv)

    rv = post_json(client, f"/election/{election_id}/round", {"roundNum": 2},)
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"message": "The current round is not complete", "errorType": "Conflict",}
        ]
    }


def test_rounds_wrong_number_too_big(client: FlaskClient, election_id: str):
    rv = post_json(
        client, f"/election/{election_id}/round", {"roundNum": 2, "sampleSize": 10}
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
    contest_ids: str,  # pylint: disable=unused-argument
):
    rv = post_json(
        client, f"/election/{election_id}/round", {"roundNum": 1, "sampleSize": 10,},
    )
    assert_ok(rv)

    rv = post_json(
        client, f"/election/{election_id}/round", {"roundNum": 1, "sampleSize": 10,},
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


def test_rounds_missing_sample_size(client: FlaskClient, election_id: str):
    rv = post_json(client, f"/election/{election_id}/round", {"roundNum": 1})
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Sample size is required for round 1",
                "errorType": "Bad Request",
            }
        ]
    }


def test_rounds_missing_round_num(client: FlaskClient, election_id: str):
    rv = post_json(client, f"/election/{election_id}/round", {"sampleSize": 10})
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "'roundNum' is a required property",
                "errorType": "Bad Request",
            }
        ]
    }

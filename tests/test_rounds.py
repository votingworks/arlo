from flask.testing import FlaskClient
from typing import List
import json, datetime, uuid

from arlo_server import db
from arlo_server.models import (
    SampledBallotDraw,
    SampledBallot,
    Round,
    RoundContest,
    RoundContestResult,
    Batch,
)
from arlo_server.auth import UserType
from tests.helpers import (
    assert_ok,
    post_json,
    put_json,
    compare_json,
    assert_is_id,
    assert_is_date,
    set_logged_in_user,
    create_jurisdiction_admin,
)

JA_EMAIL = "ja@example.com"


def test_rounds_list_empty(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = client.get(f"/election/{election_id}/round")
    rounds = json.loads(rv.data)
    assert rounds == {"rounds": []}

    create_jurisdiction_admin(jurisdiction_ids[0], user_email=JA_EMAIL)
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, JA_EMAIL)
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round")
    rounds = json.loads(rv.data)
    assert rounds == {"rounds": []}


def test_rounds_create_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
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
            }
        ]
    }

    rv = client.get(f"/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    create_jurisdiction_admin(jurisdiction_ids[0], user_email=JA_EMAIL)
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, JA_EMAIL)
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    # Check that we also created RoundContest objects
    round_contests = RoundContest.query.filter_by(
        round_id=rounds["rounds"][0]["id"]
    ).all()
    assert len(round_contests) == 1
    assert round_contests[0].contest_id == contest_id

    # Check that the ballots got sampled
    ballot_draws = SampledBallotDraw.query.filter_by(
        round_id=rounds["rounds"][0]["id"]
    ).all()
    assert len(ballot_draws) == sample_size
    # Because we sample with replacement, we might have less sampled ballots
    # than ballot draws, so we'll just check that each draw has a corresponding
    # ballot
    for draw in ballot_draws:
        assert SampledBallot.query.filter_by(
            batch_id=draw.batch_id, ballot_position=draw.ballot_position
        ).one_or_none()
    # Check that we're sampling ballots from the two jurisdictions that uploaded manifests
    sampled_jurisdictions = {draw.batch.jurisdiction_id for draw in ballot_draws}
    assert sorted(sampled_jurisdictions) == sorted(jurisdiction_ids[:2])


def test_rounds_create_two(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    rv = client.get(f"/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    del contest["currentRoundStatus"]

    contests = [
        contest,
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 2",
            "isTargeted": False,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 300,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 200,},
            ],
            "totalBallotsCast": 5000,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": [jurisdiction_ids[0], jurisdiction_ids[2]],
        },
    ]
    rv = put_json(client, f"/election/{election_id}/contest", contests)
    assert_ok(rv)

    rv = post_json(
        client, f"/election/{election_id}/round", {"roundNum": 1, "sampleSize": 119,},
    )
    assert_ok(rv)

    # Fake that the first round got completed by setting Round.ended_at.
    # We also need to add RoundContestResults so that the next round sample
    # size can get computed.
    round = Round.query.filter_by(election_id=election_id).one()
    round.ended_at = datetime.datetime.utcnow()
    db.session.add(
        RoundContestResult(
            round_id=round.id,
            contest_id=contest["id"],
            contest_choice_id=contest["choices"][0]["id"],
            result=70,
        )
    )
    db.session.add(
        RoundContestResult(
            round_id=round.id,
            contest_id=contest["id"],
            contest_choice_id=contest["choices"][1]["id"],
            result=49,
        )
    )
    db.session.commit()

    rv = client.get(f"/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(
        rounds,
        {
            "rounds": [
                {
                    "id": assert_is_id,
                    "roundNum": 1,
                    "startedAt": assert_is_date,
                    "endedAt": assert_is_date,
                }
            ]
        },
    )

    rv = post_json(client, f"/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    expected_rounds = {
        "rounds": [
            {
                "id": assert_is_id,
                "roundNum": 1,
                "startedAt": assert_is_date,
                "endedAt": assert_is_date,
            },
            {
                "id": assert_is_id,
                "roundNum": 2,
                "startedAt": assert_is_date,
                "endedAt": None,
            },
        ]
    }
    rv = client.get(f"/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    create_jurisdiction_admin(jurisdiction_ids[0], user_email=JA_EMAIL)
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, JA_EMAIL)
    rv = client.get(f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round")
    rounds = json.loads(rv.data)
    compare_json(rounds, expected_rounds)

    ballot_draws = (
        SampledBallotDraw.query.filter_by(round_id=rounds["rounds"][1]["id"])
        .join(Batch)
        .all()
    )
    # Check that we automatically select the 90% prob sample size
    assert len(ballot_draws) == 205
    # Check that we're sampling ballots from the two jurisdictions that uploaded manifests
    sampled_jurisdictions = {draw.batch.jurisdiction_id for draw in ballot_draws}
    assert sorted(sampled_jurisdictions) == sorted(jurisdiction_ids[:2])
    rv = client.get(f"/election/{election_id}/contest")


def test_rounds_create_before_previous_round_complete(
    client: FlaskClient,
    election_id: str,
    contest_id: str,  # pylint: disable=unused-argument
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
    contest_id: str,  # pylint: disable=unused-argument
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

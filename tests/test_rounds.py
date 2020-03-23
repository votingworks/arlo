import pytest
from flask.testing import FlaskClient
from typing import List
import json, io, datetime

from arlo_server import db
from arlo_server.models import (
    SampledBallotDraw,
    SampledBallot,
    Round,
    RoundContest,
    RoundContestResult,
    Batch,
)
from bgcompute import bgcompute_update_ballot_manifest_file
from helpers import post_json, compare_json, assert_is_id, assert_is_date


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n"
                    b"1,23\n"
                    b"2,101\n"
                    b"3,122\n"
                    b"4,400"
                ),
                "manifest.csv",
            )
        },
    )
    assert rv.status_code == 200
    rv = client.put(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n"
                    b"1,20\n"
                    b"2,10\n"
                    b"3,220\n"
                    b"4,40"
                ),
                "manifest.csv",
            )
        },
    )
    assert rv.status_code == 200
    bgcompute_update_ballot_manifest_file()


def test_rounds_list_empty(client: FlaskClient, election_id: str):
    rv = client.get(f"/election/{election_id}/round")
    rounds = json.loads(rv.data)
    assert rounds == {"rounds": []}


def test_rounds_create_one(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest: dict,
    manifests,
):
    sample_size = 119  # BRAVO sample size
    rv = post_json(
        client,
        f"/election/{election_id}/round",
        {"roundNum": 1, "sampleSize": sample_size,},
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"status": "ok"}

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
                    "endedAt": None,
                }
            ]
        },
    )

    # Check that we also created RoundContest objects
    round_contests = RoundContest.query.filter_by(
        round_id=rounds["rounds"][0]["id"]
    ).all()
    assert len(round_contests) == 1
    assert round_contests[0].contest_id == contest["id"]

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
    contest: dict,
    manifests,
    election_settings,
):
    rv = post_json(
        client, f"/election/{election_id}/round", {"roundNum": 1, "sampleSize": 119,},
    )
    assert rv.status_code == 200

    # Fake that the first round got completed
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
    assert rv.status_code == 200

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
                },
                {
                    "id": assert_is_id,
                    "roundNum": 2,
                    "startedAt": assert_is_date,
                    "endedAt": None,
                },
            ]
        },
    )

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


def test_rounds_create_before_previous_round_complete(
    client: FlaskClient, election_id: str, contest: dict, manifests, election_settings
):
    rv = post_json(
        client, f"/election/{election_id}/round", {"roundNum": 1, "sampleSize": 10,},
    )
    assert rv.status_code == 200

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
    client: FlaskClient, election_id: str, contest: dict
):
    rv = post_json(
        client, f"/election/{election_id}/round", {"roundNum": 1, "sampleSize": 10,},
    )
    assert rv.status_code == 200

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

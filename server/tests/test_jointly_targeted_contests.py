import uuid, json
from typing import List
import pytest
from flask.testing import FlaskClient

from .helpers import *  # pylint: disable=wildcard-import

SAMPLE_SIZE = 485


@pytest.fixture
def contest_ids(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
) -> List[str]:
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 600,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400,},
            ],
            "totalBallotsCast": 1600,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 2",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "Yes", "numVotes": 800,},
                {"id": str(uuid.uuid4()), "name": "No", "numVotes": 650,},
            ],
            "totalBallotsCast": 1600,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 3",
            "isTargeted": False,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 200,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 300,},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 100,},
            ],
            "totalBallotsCast": 600,
            "numWinners": 2,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


def test_sample_size_round_1(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_sizes = json.loads(rv.data)
    # Importantly, these are the sample sizes for Contest 2, not Contest 1
    # (which we see in test_sample_sizes.py), since it has a smaller margin of
    # victory and thus a bigger sample size.
    assert sample_sizes["sampleSizes"][0]["size"] > SAMPLE_SIZE_ROUND_1
    assert sample_sizes == {
        "sampleSizes": [
            {"prob": 0.55, "size": SAMPLE_SIZE, "type": "ASN"},
            {"prob": 0.7, "size": 770, "type": None},
            {"prob": 0.8, "size": 1018, "type": None},
            {"prob": 0.9, "size": 1468, "type": None},
        ]
    }


def test_sample_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSize": SAMPLE_SIZE},
    )
    assert_ok(rv)
    round_1 = Round.query.first()

    # Audit all the ballots for Contest 1 and meet the risk limit, but don't
    # audit any for Contest 2, which should still trigger a second round.
    run_audit_round(round_1.id, contest_ids[0], 0.7)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(
        rounds,
        {
            "rounds": [
                {
                    "id": round_1.id,
                    "roundNum": 1,
                    "startedAt": assert_is_date,
                    "endedAt": assert_is_date,
                    "isAuditComplete": False,
                }
            ]
        },
    )

    # Check that the ballots got sampled
    ballot_draws = SampledBallotDraw.query.filter_by(
        round_id=rounds["rounds"][0]["id"]
    ).all()
    assert len(ballot_draws) == SAMPLE_SIZE
    # Check that we're sampling ballots from the two jurisdictions that uploaded manifests
    sampled_jurisdictions = {
        draw.sampled_ballot.batch.jurisdiction_id for draw in ballot_draws
    }
    assert sorted(sampled_jurisdictions) == sorted(jurisdiction_ids[:2])

    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2})
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)
    compare_json(
        rounds,
        {
            "rounds": [
                {
                    "id": round_1.id,
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
        },
    )

    # Check that we used the correct sample size (90% prob for Contest 2)
    ballot_draws = SampledBallotDraw.query.filter_by(
        round_id=rounds["rounds"][1]["id"]
    ).all()
    assert len(ballot_draws) == 1468


def test_jointly_targeted_contest_universes_must_match(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "isTargeted": True,
                "choices": [
                    {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 600,},
                    {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400,},
                ],
                "totalBallotsCast": 1000,
                "numWinners": 1,
                "votesAllowed": 1,
                "jurisdictionIds": jurisdiction_ids,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 2",
                "isTargeted": True,
                "choices": [
                    {"id": str(uuid.uuid4()), "name": "Yes", "numVotes": 800,},
                    {"id": str(uuid.uuid4()), "name": "No", "numVotes": 650,},
                ],
                "totalBallotsCast": 1600,
                "numWinners": 1,
                "votesAllowed": 1,
                "jurisdictionIds": jurisdiction_ids[1:],
            },
        ],
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "All targeted contests must have the same jurisdictions.",
            }
        ]
    }


def test_jointly_targeted_contest_total_ballots_must_match(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "isTargeted": True,
                "choices": [
                    {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 600,},
                    {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400,},
                ],
                "totalBallotsCast": 1000,
                "numWinners": 1,
                "votesAllowed": 1,
                "jurisdictionIds": jurisdiction_ids,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 2",
                "isTargeted": True,
                "choices": [
                    {"id": str(uuid.uuid4()), "name": "Yes", "numVotes": 800,},
                    {"id": str(uuid.uuid4()), "name": "No", "numVotes": 650,},
                ],
                "totalBallotsCast": 1600,
                "numWinners": 1,
                "votesAllowed": 1,
                "jurisdictionIds": jurisdiction_ids,
            },
        ],
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "All targeted contests must have the same total ballots cast.",
            }
        ]
    }

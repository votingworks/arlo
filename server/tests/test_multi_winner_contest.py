import uuid, json
from typing import List
import pytest
from flask.testing import FlaskClient

from .helpers import *  # pylint: disable=wildcard-import
from ..models import *  # pylint: disable=wildcard-import


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
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 1",
                    "numVotes": 600,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 2",
                    "numVotes": 300,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 3",
                    "numVotes": 100,
                },
            ],
            "totalBallotsCast": 1000,
            "numWinners": 2,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


def test_multi_winner_sample_size(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    options = sample_size_options[contest_ids[0]]
    # We only expect the asn sample size option for multi-winner contests
    assert len(options) == 1
    assert options[0]["key"] == "asn"
    snapshot.assert_match(options)


def run_multi_winner_audit_round(
    round_id: str,
    target_contest_id: str,
    vote1_ratio: float,
    vote2_ratio: float,
):
    contest = Contest.query.get(target_contest_id)
    ballot_draws = (
        SampledBallotDraw.query.filter_by(round_id=round_id)
        .join(SampledBallot)
        .join(Batch)
        .order_by(Batch.name, SampledBallot.ballot_position)
        .all()
    )
    winner1_votes = int(vote1_ratio * len(ballot_draws))
    winner2_votes = int(vote2_ratio * len(ballot_draws))
    for ballot_draw in ballot_draws[:winner1_votes]:
        audit_ballot(
            ballot_draw.sampled_ballot,
            contest.id,
            Interpretation.VOTE,
            [contest.choices[0]],
        )
    for ballot_draw in ballot_draws[winner1_votes : (winner2_votes + winner1_votes)]:
        audit_ballot(
            ballot_draw.sampled_ballot,
            contest.id,
            Interpretation.VOTE,
            [contest.choices[1]],
        )
    for ballot_draw in ballot_draws[(winner1_votes + winner2_votes) :]:
        audit_ballot(
            ballot_draw.sampled_ballot,
            contest.id,
            Interpretation.VOTE,
            [contest.choices[2]],
        )
    db_session.commit()


def test_multi_winner_two_rounds(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    contest_id = contest_ids[0]

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_sizes = json.loads(rv.data)["sampleSizes"]
    selected_sample_sizes = {contest_id: sample_sizes[contest_id][0]}

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": selected_sample_sizes},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    run_multi_winner_audit_round(round_1_id, contest_id, 0.5, 0.3)

    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    assert json.loads(rv.data)["rounds"][0]["isAuditComplete"] is False

    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    sample_size_options = json.loads(rv.data)["sampleSizes"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 2,
            "sampleSizes": {contest_id: sample_size_options[contest_id][0]},
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    run_multi_winner_audit_round(round_2_id, contest_id, 0.7, 0.3)

    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    assert json.loads(rv.data)["rounds"][1]["isAuditComplete"] is True

    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

import csv
import io
import itertools
from datetime import timezone
import pytest
from flask.testing import FlaskClient

from ..helpers import *
from ...audit_math import sampler


@pytest.fixture
def election_id(client: FlaskClient, org_id: str, request):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    return create_election(
        client,
        audit_name=f"Test Audit {request.node.name}",
        audit_type=AuditType.BALLOT_POLLING,
        audit_math_type=AuditMathType.PROVIDENCE,
        organization_id=org_id,
    )


@pytest.fixture
def election_settings(client: FlaskClient, election_id: str):
    settings = {
        "electionName": "Test Election",
        "online": False,
        "randomSeed": "1234567890",
        "riskLimit": 10,
        "state": USState.California,
    }
    rv = put_json(client, f"/api/election/{election_id}/settings", settings)
    assert_ok(rv)


def test_providence_sample_size(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    election_settings,
    manifests,
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200

    sample_size_options = json.loads(rv.data)["sampleSizes"][contest_ids[0]]
    assert len(sample_size_options) == 3
    snapshot.assert_match(sample_size_options)


def test_providence_round_random_seeds(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    election_settings,
    manifests,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    round_1_body = {
        "roundNum": 1,
        "sampleSizes": {contest_ids[0]: sample_size_options[contest_ids[0]][0]},
    }

    # Round 1 uses the election's random seed, so a new one can't be provided
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {**round_1_body, "randomSeed": "1111111111"},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "A random seed can only be provided for rounds after round 1 of a Providence audit",
            }
        ]
    }

    rv = post_json(client, f"/api/election/{election_id}/round", round_1_body)
    assert_ok(rv)
    round_1 = Round.query.filter_by(election_id=election_id, round_num=1).one()
    assert round_1.random_seed == "1234567890"

    # Skip auditing round 1, since we only care about how round 2 is sampled
    round_1.ended_at = datetime.now(timezone.utc)
    for round_contest in round_1.round_contests:
        round_contest.is_complete = False
    db_session.commit()

    round_2_sample_size = {"key": "custom", "size": 10, "prob": None}
    round_2_body = {
        "roundNum": 2,
        "sampleSizes": {contest_ids[0]: round_2_sample_size},
    }
    rv = post_json(client, f"/api/election/{election_id}/round", round_2_body)
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "A new random seed is required for each round",
            }
        ]
    }

    # Reusing an earlier round's seed would draw the same ballots again
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {**round_2_body, "randomSeed": "1234567890"},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Cannot reuse a previous random seed",
            }
        ]
    }

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {**round_2_body, "randomSeed": "0987654321"},
    )
    assert_ok(rv)
    round_2 = Round.query.filter_by(election_id=election_id, round_num=2).one()
    assert round_2.random_seed == "0987654321"

    # Round 2 should be drawn from a fresh stream of tickets using the new seed
    contest = Contest.query.get(contest_ids[0])
    manifest = {
        (jurisdiction.name, batch.tabulator, batch.name): list(
            range(1, batch.num_ballots + 1)
        )
        for jurisdiction in contest.jurisdictions
        for batch in jurisdiction.batches
    }
    expected_draws = {
        (batch_key, ballot_position, ticket_number)
        for ticket_number, (batch_key, ballot_position), _ in sampler.draw_sample(
            "0987654321", manifest, 10
        )
    }
    round_2_draws = {
        (
            (
                draw.sampled_ballot.batch.jurisdiction.name,
                draw.sampled_ballot.batch.tabulator,
                draw.sampled_ballot.batch.name,
            ),
            draw.sampled_ballot.ballot_position,
            draw.ticket_number,
        )
        for draw in SampledBallotDraw.query.filter_by(round_id=round_2.id)
    }
    assert round_2_draws == expected_draws

    # Each round's seed is included in the audit report
    rv = client.get(f"/api/election/{election_id}/report")
    report = rv.data.decode("utf-8")
    rows = list(csv.reader(io.StringIO(report)))
    rounds_start = rows.index(["######## ROUNDS ########"])
    header = rows[rounds_start + 1]
    round_rows = itertools.takewhile(lambda row: row, rows[rounds_start + 2 :])
    seed_column = header.index("Random Seed")
    assert {(row[0], row[seed_column]) for row in round_rows} == {
        ("1", "1234567890"),
        ("2", "0987654321"),
    }

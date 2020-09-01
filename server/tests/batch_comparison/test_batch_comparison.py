from typing import List
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...util.group_by import group_by


def test_batch_comparison_sample_size(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_id: str,
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
    snapshot,
):
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 200
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    snapshot.assert_match(sample_size_options[contest_id])


def test_batch_comparison_sample_batches(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
):
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 200
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_size = sample_size_options[contest_id][0]["size"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_id: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]

    # Check that we also created RoundContest objects
    round_contests = RoundContest.query.filter_by(round_id=rounds[0]["id"]).all()
    assert len(round_contests) == 1
    assert round_contests[0]

    # Check that the batches got sampled
    batch_draws = SampledBatchDraw.query.filter_by(round_id=rounds[0]["id"]).all()
    assert len(batch_draws) == sample_size

    # Check that we're sampling batches from the jurisdiction that uploaded manifests
    sampled_jurisdictions = {draw.batch.jurisdiction_id for draw in batch_draws}
    assert sampled_jurisdictions == {jurisdiction_ids[0]}

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{rounds[0]['id']}/audit-board",
        [
            {"name": "Audit Board #1"},
            {"name": "Audit Board #2"},
            {"name": "Audit Board #3"},
        ],
    )
    assert_ok(rv)

    # Check that the batches got divvied up evenly between the audit boards
    sampled_batches = (
        Batch.query.join(SampledBatchDraw).filter_by(round_id=rounds[0]["id"]).all()
    )
    audit_board_batches = [
        [batch.id for batch in batches]
        for batches in group_by(
            sampled_batches, key=lambda batch: batch.audit_board_id
        ).values()
    ]
    assert len(audit_board_batches) == 3
    assert abs(len(audit_board_batches[0]) - len(audit_board_batches[1])) <= 1
    assert abs(len(audit_board_batches[1]) - len(audit_board_batches[2])) <= 1

    # And check that each batch got assigned to one and only one audit board
    assert sorted(
        list(set(batch_id for batches in audit_board_batches for batch_id in batches))
    ) == sorted(
        list(batch_id for batches in audit_board_batches for batch_id in batches)
    )


# TODO come back and test a second round of sampling once we actually have a
# way to complete a round
def test_batch_comparison_sample_batches_round_2():
    pass

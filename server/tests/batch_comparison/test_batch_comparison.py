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
    # Use an artificially large sample size in order to have enough samples to work with
    sample_size = 20
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_id: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]

    compare_json(
        rounds,
        [
            {
                "id": assert_is_id,
                "roundNum": 1,
                "startedAt": assert_is_date,
                "endedAt": None,
                "isAuditComplete": None,
            }
        ],
    )

    # Check that we also created RoundContest objects
    round_contests = RoundContest.query.filter_by(round_id=rounds[0]["id"]).all()
    assert len(round_contests) == 1
    assert round_contests[0]

    # Check that the batches got sampled
    batch_draws = SampledBatchDraw.query.filter_by(round_id=rounds[0]["id"]).all()
    assert len(batch_draws) == sample_size

    # Check that we're sampling batches from the jurisdiction that uploaded manifests
    sampled_jurisdictions = {draw.batch.jurisdiction_id for draw in batch_draws}
    assert sampled_jurisdictions == set(jurisdiction_ids[:2])

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
        Batch.query.filter_by(jurisdiction_id=jurisdiction_ids[0])
        .join(SampledBatchDraw)
        .filter_by(round_id=rounds[0]["id"])
        .all()
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


def test_batch_comparison_sample_batches_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
    snapshot,
):
    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    choice_ids = [choice["id"] for choice in contests[0]["choices"]]
    batch_results = {
        batch["id"]: {choice_ids[0]: 400, choice_ids[1]: 50, choice_ids[2]: 40,}
        for batch in batches
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/results",
        batch_results,
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    batch_results = {
        batch["id"]: {choice_ids[0]: 400, choice_ids[1]: 50, choice_ids[2]: 40,}
        for batch in batches
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/results",
        batch_results,
    )
    assert_ok(rv)

    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2})
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    compare_json(
        rounds,
        [
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
        ],
    )

    # Check that we also created RoundContest objects
    round_contests = RoundContest.query.filter_by(round_id=rounds[1]["id"]).all()
    assert len(round_contests) == 1
    assert round_contests[0]

    # Check that we automatically select the sample size
    batch_draws = SampledBatchDraw.query.filter_by(round_id=rounds[1]["id"]).all()
    assert len(batch_draws) == 6

    # Check that we're sampling batches from the jurisdiction that uploaded manifests
    sampled_jurisdictions = {draw.batch.jurisdiction_id for draw in batch_draws}
    assert sampled_jurisdictions == set(jurisdiction_ids[:2])

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{rounds[1]['id']}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"},],
    )
    assert_ok(rv)

    # Test the retrieval list correctly marks ballots that were sampled last round
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{rounds[1]['id']}/batches/retrieval-list"
    )
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)

    # Test the audit reports
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    assert_match_report(rv.data, snapshot)

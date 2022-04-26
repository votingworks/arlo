import json
from datetime import datetime, timezone, timedelta
from typing import List
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ... import config


def test_sample_sizes_without_contests(client: FlaskClient, election_id: str):
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 200
    compare_json(
        json.loads(rv.data),
        {
            "sampleSizes": None,
            "selected": None,
            "task": {
                "status": "ERRORED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Cannot compute sample sizes until contests are set",
            },
        },
    )


def test_sample_sizes_without_risk_limit(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],  # pylint: disable=unused-argument
):
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 200
    compare_json(
        json.loads(rv.data),
        {
            "sampleSizes": None,
            "selected": None,
            "task": {
                "status": "ERRORED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Cannot compute sample sizes until risk limit is set",
            },
        },
    )


def test_sample_sizes_round_1(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    snapshot,
):
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    response = json.loads(rv.data)
    contest_id_to_name = dict(Contest.query.values(Contest.id, Contest.name))
    snapshot.assert_match(
        {contest_id_to_name[id]: sizes for id, sizes in response["sampleSizes"].items()}
    )
    assert response["selected"] is None


def test_sample_sizes_round_2(
    client: FlaskClient,
    election_id: str,
    round_1_id: str,  # pylint: disable=unused-argument
    snapshot,
):
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    response = json.loads(rv.data)
    contest_id_to_name = dict(Contest.query.values(Contest.id, Contest.name))
    # Should still return round 1 sample sizes
    snapshot.assert_match(
        {contest_id_to_name[id]: sizes for id, sizes in response["sampleSizes"].items()}
    )
    # Should show which sample size got selected
    snapshot.assert_match(
        {contest_id_to_name[id]: size for id, size in response["selected"].items()}
    )
    compare_json(
        response["task"],
        {
            "status": "PROCESSED",
            "startedAt": assert_is_date,
            "completedAt": assert_is_date,
            "error": None,
        },
    )


def test_sample_sizes_background(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    orig_run_background_tasks_immediately = config.RUN_BACKGROUND_TASKS_IMMEDIATELY
    config.RUN_BACKGROUND_TASKS_IMMEDIATELY = False

    # When we first request sample sizes, we expect a background task to get
    # created, but no sample sizes returned yet
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert json.loads(rv.data) == {
        "sampleSizes": None,
        "selected": None,
        "task": {
            "status": "READY_TO_PROCESS",
            "startedAt": None,
            "completedAt": None,
            "error": None,
        },
    }

    # Simulate starting the task
    started_at = datetime.now(timezone.utc)
    sample_sizes = SampleSizeOptions.query.filter_by(
        election_id=election_id, round_num=1
    ).one()
    sample_sizes.task.started_at = started_at
    db_session.commit()

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert json.loads(rv.data) == {
        "sampleSizes": None,
        "selected": None,
        "task": {
            "status": "PROCESSING",
            "startedAt": started_at.isoformat(),
            "completedAt": None,
            "error": None,
        },
    }

    # Simulate completing the task
    sample_sizes = SampleSizeOptions.query.filter_by(
        election_id=election_id, round_num=1
    ).one()
    sample_sizes.sample_size_options = {
        contest_ids[0]: {"asn": {"key": "asn", "size": 1, "prob": 0.5}}
    }
    completed_at = datetime.now(timezone.utc)
    sample_sizes.task.completed_at = completed_at
    db_session.commit()

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert json.loads(rv.data) == {
        "sampleSizes": {contest_ids[0]: [{"key": "asn", "size": 1, "prob": 0.5}]},
        "selected": None,
        "task": {
            "status": "PROCESSED",
            "startedAt": started_at.isoformat(),
            "completedAt": completed_at.isoformat(),
            "error": None,
        },
    }

    # Simulate the results of the task expiring after five seconds
    # A new task should be started
    sample_sizes = SampleSizeOptions.query.filter_by(
        election_id=election_id, round_num=1
    ).one()
    completed_at = datetime.now(timezone.utc) - timedelta(seconds=5)
    sample_sizes.task.completed_at = completed_at
    db_session.commit()

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert json.loads(rv.data) == {
        "sampleSizes": None,
        "selected": None,
        "task": {
            "status": "READY_TO_PROCESS",
            "startedAt": None,
            "completedAt": None,
            "error": None,
        },
    }

    config.RUN_BACKGROUND_TASKS_IMMEDIATELY = orig_run_background_tasks_immediately

import json
from flask.testing import FlaskClient

from ..helpers import *
from ... import config

dummy_sample_size = {"key": "custom", "size": 10, "prob": None}


def test_sample_preview(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    manifests,
    election_settings,
    contest_ids: list[str],
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # To start, no sample preview should exist
    rv = client.get(f"/api/election/{election_id}/sample-preview")
    assert rv.status_code == 200
    print(rv.data)
    sample_preview = json.loads(rv.data)
    assert sample_preview == {
        "jurisdictions": None,
        "task": None,
    }

    # Start computing a sample preview
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_size = sample_size_options[contest_ids[0]][0]
    rv = post_json(
        client,
        f"/api/election/{election_id}/sample-preview",
        {"sampleSizes": {contest_ids[0]: sample_size}},
    )
    assert_ok(rv)

    # Check the computed sample preview
    rv = client.get(f"/api/election/{election_id}/sample-preview")
    assert rv.status_code == 200
    sample_preview = json.loads(rv.data)
    compare_json(
        sample_preview["task"],
        {
            "status": "PROCESSED",
            "startedAt": assert_is_date,
            "completedAt": assert_is_date,
            "error": None,
        },
    )
    assert len(sample_preview["jurisdictions"]) == len(jurisdiction_ids)
    snapshot.assert_match(sample_preview["jurisdictions"])

    # Make sure it matches the sample drawn when we start a round
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_ids[0]: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    for i, jurisdiction in enumerate(jurisdictions):
        preview = sample_preview["jurisdictions"][i]
        assert preview["name"] == jurisdiction["name"]
        assert preview["numSamples"] == jurisdiction["currentRoundStatus"]["numSamples"]
        assert preview["numUnique"] == jurisdiction["currentRoundStatus"]["numUnique"]


def test_sample_preview_in_progress(
    client: FlaskClient,
    election_id: str,
    manifests,
    election_settings,
    contest_ids: list[str],
):
    orig_run_background_tasks_immediately = config.RUN_BACKGROUND_TASKS_IMMEDIATELY
    config.RUN_BACKGROUND_TASKS_IMMEDIATELY = False

    # Start computing a sample preview
    rv = post_json(
        client,
        f"/api/election/{election_id}/sample-preview",
        {"sampleSizes": {contest_ids[0]: dummy_sample_size}},
    )
    assert_ok(rv)

    # Check the sample preview task was created
    rv = client.get(f"/api/election/{election_id}/sample-preview")
    assert rv.status_code == 200
    sample_preview = json.loads(rv.data)
    compare_json(
        sample_preview["task"],
        {
            "status": "READY_TO_PROCESS",
            "startedAt": None,
            "completedAt": None,
            "error": None,
        },
    )

    # Try to start another sample preview
    rv = post_json(
        client,
        f"/api/election/{election_id}/sample-preview",
        {"sampleSizes": {contest_ids[0]: dummy_sample_size}},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Arlo is already computing a sample preview.",
                "errorType": "Conflict",
            }
        ]
    }

    config.RUN_BACKGROUND_TASKS_IMMEDIATELY = orig_run_background_tasks_immediately


def test_preview_after_audit_launch(
    client: FlaskClient,
    election_id: str,
    contest_ids: list[str],
    round_1_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        f"/api/election/{election_id}/sample-preview",
        {"sampleSizes": {contest_ids[0]: dummy_sample_size}},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Preview not allowed after audit launch",
                "errorType": "Bad Request",
            }
        ]
    }

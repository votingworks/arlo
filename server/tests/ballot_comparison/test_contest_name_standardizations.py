import json
import io
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from .conftest import TEST_CVRS


def test_standardize_contest_names(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Standardized Contest 1",
            "isTargeted": True,
            "numWinners": 1,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Standardized Contest 2",
            "isTargeted": False,
            "numWinners": 1,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    # Get contests needing standardization
    rv = client.get(f"/api/election/{election_id}/contest/standardizations")
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "standardizations": {
            jurisdiction_ids[0]: {
                "Standardized Contest 1": None,
                "Standardized Contest 2": None,
            },
            jurisdiction_ids[1]: {"Standardized Contest 1": None},
        },
        "cvrContestNames": {
            jurisdiction_ids[0]: ["Contest 1", "Contest 2"],
            jurisdiction_ids[1]: ["Contest 1", "Contest 2"],
        },
    }

    # Put some standardizations
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest/standardizations",
        {
            jurisdiction_ids[0]: {
                "Standardized Contest 1": None,
                "Standardized Contest 2": "Contest 2",
            },
            jurisdiction_ids[1]: {"Standardized Contest 1": "Contest 1"},
        },
    )
    assert_ok(rv)

    # Get again, should have been saved
    rv = client.get(f"/api/election/{election_id}/contest/standardizations")
    assert rv.status_code == 200
    assert json.loads(rv.data)["standardizations"] == {
        jurisdiction_ids[0]: {
            "Standardized Contest 1": None,
            "Standardized Contest 2": "Contest 2",
        },
        jurisdiction_ids[1]: {"Standardized Contest 1": "Contest 1"},
    }

    # Try to get the sample sizes - should fail because we haven't standardized
    # all targeted contest names
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
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
                "error": "Couldn't find contest Standardized Contest 1 in the CVR for jurisdiction J1",
            },
        },
    )

    # Finish standardizing
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest/standardizations",
        {
            jurisdiction_ids[0]: {
                "Standardized Contest 1": "Contest 1",
                "Standardized Contest 2": "Contest 2",
            },
            jurisdiction_ids[1]: {"Standardized Contest 1": "Contest 1"},
        },
    )
    assert_ok(rv)

    # Get again, should have been saved
    rv = client.get(f"/api/election/{election_id}/contest/standardizations")
    assert rv.status_code == 200
    assert json.loads(rv.data)["standardizations"] == {
        jurisdiction_ids[0]: {
            "Standardized Contest 1": "Contest 1",
            "Standardized Contest 2": "Contest 2",
        },
        jurisdiction_ids[1]: {"Standardized Contest 1": "Contest 1"},
    }

    # Clear out the old error so we don't have to wait for it to expire
    sample_sizes = SampleSizeOptions.query.filter_by(
        election_id=election_id, round_num=1
    ).one()
    sample_sizes.task = None
    db_session.commit()

    # Now sample sizes should work
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200
    response = json.loads(rv.data)
    assert response["task"]["status"] == "PROCESSED"
    # Should match test_ballot_comparison_two_rounds from test_ballot_comparison.py
    snapshot.assert_match(response["sampleSizes"][contests[0]["id"]])

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contests[0]["id"]: response["sampleSizes"][contests[0]["id"]][0]
            },
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/report")
    assert rv.status_code == 200
    assert_match_report(rv.data, snapshot)


def test_standardize_contest_names_before_cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Standardized Contest 1",
            "isTargeted": True,
            "numWinners": 1,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest/standardizations")
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"standardizations": {}, "cvrContestNames": {}}


def test_standardize_contest_names_before_contests(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest/standardizations")
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"standardizations": {}, "cvrContestNames": {}}


def test_standardize_contest_names_cvr_change(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Standardized Contest 1",
            "isTargeted": True,
            "numWinners": 1,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    # Get standardizations
    rv = client.get(f"/api/election/{election_id}/contest/standardizations")
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "standardizations": {
            jurisdiction_ids[0]: {"Standardized Contest 1": None},
        },
        "cvrContestNames": {jurisdiction_ids[0]: ["Contest 1", "Contest 2"]},
    }

    # Put some standardizations
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest/standardizations",
        {
            jurisdiction_ids[0]: {"Standardized Contest 1": "Contest 1"},
        },
    )
    assert_ok(rv)

    # Change the CVR contest name, so the standardization is outdated
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(TEST_CVRS.replace("Contest 1", "Contest A").encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    # Get standardizations, should not include outdated standardization
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest/standardizations")
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "standardizations": {jurisdiction_ids[0]: {"Standardized Contest 1": None}},
        "cvrContestNames": {jurisdiction_ids[0]: ["Contest A", "Contest 2"]},
    }

    # Try to get the sample sizes - should fail because we haven't standardized
    # all targeted contest names
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
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
                "error": "Couldn't find contest Standardized Contest 1 in the CVR for jurisdiction J1",
            },
        },
    )


def test_standardize_contest_names_contest_change(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    contest_id = str(uuid.uuid4())
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": contest_id,
            "name": "Standardized Contest 1",
            "isTargeted": True,
            "numWinners": 1,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    # Get standardizations
    rv = client.get(f"/api/election/{election_id}/contest/standardizations")
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "standardizations": {
            jurisdiction_ids[0]: {"Standardized Contest 1": None},
        },
        "cvrContestNames": {jurisdiction_ids[0]: ["Contest 1", "Contest 2"]},
    }

    # Put some standardizations
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest/standardizations",
        {
            jurisdiction_ids[0]: {"Standardized Contest 1": "Contest 1"},
        },
    )
    assert_ok(rv)

    # Change contest name
    contests = [
        {
            "id": contest_id,
            "name": "Standardized Contest A",
            "isTargeted": True,
            "numWinners": 1,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    # Get standardizations, should not include outdated standardization
    rv = client.get(f"/api/election/{election_id}/contest/standardizations")
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "standardizations": {jurisdiction_ids[0]: {"Standardized Contest A": None}},
        "cvrContestNames": {jurisdiction_ids[0]: ["Contest 1", "Contest 2"]},
    }

    # Try to get the sample sizes - should fail because we haven't standardized
    # all targeted contest names
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
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
                "error": "Couldn't find contest Standardized Contest A in the CVR for jurisdiction J1",
            },
        },
    )


def test_standardize_contest_names_wrong_audit_type(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    election = Election.query.get(election_id)
    election.audit_type = AuditType.BALLOT_POLLING
    db_session.commit()

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = put_json(client, f"/api/election/{election_id}/contest/standardizations", {})
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Cannot standardize contest names for this audit type",
            }
        ]
    }


def test_standardize_contest_names_after_audit_starts(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest_id = str(uuid.uuid4())
    contests = [
        {
            "id": contest_id,
            "name": "Contest 1",
            "isTargeted": True,
            "numWinners": 1,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_id: {"size": 1, "key": "custom", "prob": None}},
        },
    )
    assert_ok(rv)

    rv = put_json(client, f"/api/election/{election_id}/contest/standardizations", {})
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Cannot standardize contest names after the audit has started.",
            }
        ]
    }

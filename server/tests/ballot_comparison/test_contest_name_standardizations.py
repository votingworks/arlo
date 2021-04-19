import json
import io
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from .conftest import TEST_CVRS
from ...worker.bgcompute import bgcompute_update_cvr_file


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
        jurisdiction_ids[0]: {
            "Standardized Contest 1": None,
            "Standardized Contest 2": None,
        },
        jurisdiction_ids[1]: {"Standardized Contest 1": None,},
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
    assert json.loads(rv.data) == {
        jurisdiction_ids[0]: {
            "Standardized Contest 1": None,
            "Standardized Contest 2": "Contest 2",
        },
        jurisdiction_ids[1]: {"Standardized Contest 1": "Contest 1"},
    }

    # Try to get the sample sizes - should fail because we haven't standardized
    # all targeted contest names
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
    assert json.loads(rv.data) == {
        jurisdiction_ids[0]: {
            "Standardized Contest 1": "Contest 1",
            "Standardized Contest 2": "Contest 2",
        },
        jurisdiction_ids[1]: {"Standardized Contest 1": "Contest 1"},
    }

    # Clear out the old error so we don't have to wait for it to expire
    election = Election.query.get(election_id)
    election.sample_size_options_task = None
    db_session.commit()

    # Now sample sizes should work
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 200
    response = json.loads(rv.data)
    assert response["task"]["status"] == "PROCESSED"
    # Should match test_ballot_comparison_two_rounds from test_ballot_comparison.py
    snapshot.assert_match(response["sampleSizes"][contests[0]["id"]])


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
    assert json.loads(rv.data) == {}


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
    assert json.loads(rv.data) == {}


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
        jurisdiction_ids[0]: {"Standardized Contest 1": None},
    }

    # Put some standardizations
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest/standardizations",
        {jurisdiction_ids[0]: {"Standardized Contest 1": "Contest 1"},},
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
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_cvr_file(election_id)

    # Get standardizations, should not include outdated standardization
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest/standardizations")
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        jurisdiction_ids[0]: {"Standardized Contest 1": None},
    }

    # Try to get the sample sizes - should fail because we haven't standardized
    # all targeted contest names
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
        jurisdiction_ids[0]: {"Standardized Contest 1": None},
    }

    # Put some standardizations
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest/standardizations",
        {jurisdiction_ids[0]: {"Standardized Contest 1": "Contest 1"},},
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
        jurisdiction_ids[0]: {"Standardized Contest A": None},
    }

    # Try to get the sample sizes - should fail because we haven't standardized
    # all targeted contest names
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
                "error": "Couldn't find contest Standardized Contest A in the CVR for jurisdiction J1",
            },
        },
    )

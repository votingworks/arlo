import json
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import

# TODO test before CVRs uploaded
# TODO test every dependency that this impacts


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
    snapshot.assert_match(response["sampleSizes"][contests[0]["id"]])

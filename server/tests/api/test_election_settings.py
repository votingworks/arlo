import json
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


def test_settings_get_empty(client: FlaskClient, election_id: str):
    rv = client.get(f"/api/election/{election_id}/settings")
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "electionName": None,
        "online": False,
        "randomSeed": None,
        "riskLimit": None,
        "state": None,
        "auditType": "BALLOT_POLLING",
        "auditMathType": "BRAVO",
        "auditName": "Test Audit test_settings_get_empty",
    }


def test_jurisdiction_settings_get_empty(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/settings"
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "electionName": None,
        "online": False,
        "randomSeed": None,
        "riskLimit": None,
        "state": None,
        "auditType": "BALLOT_POLLING",
        "auditMathType": "BRAVO",
        "auditName": "Test Audit test_jurisdiction_settings_get_empty",
    }


def test_update_election(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = client.get(f"/api/election/{election_id}/settings")

    election = json.loads(rv.data)
    election["electionName"] = "An Updated Name"
    election["online"] = False
    election["randomSeed"] = "a new random seed"
    election["riskLimit"] = 15
    election["state"] = USState.Mississippi

    rv = put_json(client, f"/api/election/{election_id}/settings", election)
    assert_ok(rv)

    expected_settings = {
        "electionName": "An Updated Name",
        "online": False,
        "randomSeed": "a new random seed",
        "riskLimit": 15,
        "state": "MS",
        "auditType": "BALLOT_POLLING",
        "auditMathType": "BRAVO",
        "auditName": "Test Audit test_update_election",
    }

    rv = client.get(f"/api/election/{election_id}/settings")
    assert rv.status_code == 200
    assert json.loads(rv.data) == expected_settings

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/settings"
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == expected_settings


def test_update_election_settings_after_audit_starts(
    client: FlaskClient,
    election_id: str,
    round_1_id: str,  # pylint: disable=unused-argument
):
    rv = put_json(
        client,
        f"/api/election/{election_id}/settings",
        {
            "electionName": "An Updated Name",
            "online": True,
            "randomSeed": "a new random seed",
            "riskLimit": 15,
            "state": USState.Mississippi,
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Cannot update settings after audit has started.",
            }
        ]
    }


def test_invalid_state(client: FlaskClient, election_id: str):
    # Get the existing data.
    rv = client.get(f"/api/election/{election_id}/settings")

    # Set an invalid state.
    election = json.loads(rv.data)
    election["state"] = "XX"

    # Attempt to write invalid data.
    rv = put_json(client, f"/api/election/{election_id}/settings", election)

    assert rv.status_code == 400, f"unexpected response: {rv.data}"
    compare_json(
        json.loads(rv.data),
        {
            "errors": [
                {
                    "message": asserts_startswith("'XX' is not one of ['AL',"),
                    "errorType": "Bad Request",
                }
            ]
        },
    )


def test_invalid_risk_limit(client: FlaskClient, election_id: str):
    # Get the existing data.
    rv = client.get(f"/api/election/{election_id}/settings")

    # Set an invalid state.
    election = json.loads(rv.data)
    election["riskLimit"] = -1

    # Attempt to write invalid data.
    rv = put_json(client, f"/api/election/{election_id}/settings", election)

    assert rv.status_code == 400, f"unexpected response: {rv.data}"
    compare_json(
        json.loads(rv.data),
        {
            "errors": [
                {
                    "message": "-1 is less than the minimum of 1",
                    "errorType": "Bad Request",
                }
            ]
        },
    )


def test_invalid_additional_property(client: FlaskClient, election_id: str):
    rv = put_json(
        client,
        f"/api/election/{election_id}/settings",
        {"electionNameTypo": "An Updated Name"},
    )
    assert rv.status_code == 400, f"unexpected response: {rv.data}"
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Additional properties are not allowed ('electionNameTypo' was unexpected)",
                "errorType": "Bad Request",
            }
        ]
    }

import json
import pytest
from flask.testing import FlaskClient

from arlo_server.models import Election, USState

from tests.helpers import put_json, compare_json, asserts_startswith


def test_get_empty(client: FlaskClient, election_id: str):
    rv = client.get(f"/election/{election_id}/settings")
    assert rv.status_code == 200, f"unexpected response: {rv.data}"
    assert json.loads(rv.data) == {
        "electionName": None,
        "online": False,
        "randomSeed": None,
        "riskLimit": None,
        "state": None,
    }


def test_update_election(client: FlaskClient, election_id: str):
    # Get the existing data.
    rv = client.get(f"/election/{election_id}/settings")

    # Update the values.
    election = json.loads(rv.data)
    election["electionName"] = "An Updated Name"
    election["online"] = True
    election["randomSeed"] = "a new random seed"
    election["riskLimit"] = 15
    election["state"] = USState.Mississippi

    rv = put_json(client, f"/election/{election_id}/settings", election)
    assert rv.status_code == 200, f"unexpected response: {rv.data}"
    assert json.loads(rv.data) == {"status": "ok"}

    election_record = Election.query.filter_by(id=election_id).one()
    assert election_record.election_name == "An Updated Name"
    assert election_record.online is True
    assert election_record.random_seed == "a new random seed"
    assert election_record.risk_limit == 15
    assert election_record.state == USState.Mississippi


def test_invalid_state(client: FlaskClient, election_id: str):
    # Get the existing data.
    rv = client.get(f"/election/{election_id}/settings")

    # Set an invalid state.
    election = json.loads(rv.data)
    election["state"] = "XX"

    # Attempt to write invalid data.
    rv = put_json(client, f"/election/{election_id}/settings", election)

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
    rv = client.get(f"/election/{election_id}/settings")

    # Set an invalid state.
    election = json.loads(rv.data)
    election["riskLimit"] = -1

    # Attempt to write invalid data.
    rv = put_json(client, f"/election/{election_id}/settings", election)

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
        f"/election/{election_id}/settings",
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

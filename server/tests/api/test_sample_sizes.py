import json
from typing import List
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import


def test_sample_sizes_without_contests(client: FlaskClient, election_id: str):
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Cannot compute sample sizes until contests are set",
                "errorType": "Bad Request",
            }
        ]
    }


def test_sample_sizes_without_risk_limit(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],  # pylint: disable=unused-argument
):
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Cannot compute sample sizes until risk limit is set",
                "errorType": "Bad Request",
            }
        ]
    }


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

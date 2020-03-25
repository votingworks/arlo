from flask.testing import FlaskClient
import json


def test_sample_sizes_without_contests(client: FlaskClient, election_id: str):
    rv = client.get(f"/election/{election_id}/sample-sizes")
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
    client: FlaskClient, election_id: str, contest: str
):
    rv = client.get(f"/election/{election_id}/sample-sizes")
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
    client: FlaskClient, election_id: str, contest: str, election_settings: None
):
    rv = client.get(f"/election/{election_id}/sample-sizes")
    sample_sizes = json.loads(rv.data)
    assert sample_sizes == {
        "sampleSizes": [
            {"prob": 0.52, "size": 119, "type": "ASN"},
            {"prob": 0.7, "size": 184, "type": None},
            {"prob": 0.8, "size": 244, "type": None},
            {"prob": 0.9, "size": 351, "type": None},
        ]
    }

import json

from flask.testing import FlaskClient


def test_public_compute_sample_sizes(client: FlaskClient):
    body = json.dumps(
        dict(
            electionResults=dict(
                candidates=[
                    dict(name="Helga Hippo", votes=10),
                    dict(name="Bobby Bear", votes=5),
                ],
                numWinners=1,
                totalBallotsCast=20,
            ),
            riskLimitPercentage=5,
        )
    )
    rv = client.post(
        "/api/public/sample-sizes",
        headers={"Content-Type": "application/json"},
        data=body,
    )
    sample_sizes = json.loads(rv.data)
    assert sample_sizes == {
        "ballotComparison": 0,
        "ballotPolling": 0,
        "batchComparison": 0,
    }

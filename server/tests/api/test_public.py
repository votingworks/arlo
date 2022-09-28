import json

from flask.testing import FlaskClient


def test_public_compute_sample_sizes(client: FlaskClient, snapshot):
    body = {
        "electionResults": {
            "candidates": [
                {"name": "Helga Hippo", "votes": 5},
                {"name": "Bobby Bear", "votes": 5},
            ],
            "numWinners": 1,
            "totalBallotsCast": 10,
        },
    }
    rv = client.post(
        "/api/public/sample-sizes",
        headers={"Content-Type": "application/json"},
        data=json.dumps(body),
    )
    response = json.loads(rv.data)
    snapshot.assert_match(response)

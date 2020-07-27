import pytest
from flask.testing import FlaskClient

from .helpers import *  # pylint: disable=wildcard-import


@pytest.fixture
def election_settings(client: FlaskClient, election_id: str):
    settings = {
        "electionName": "Test Election",
        "online": False,
        "randomSeed": "1234567890",
        "riskLimit": 10,
        "state": USState.California,
    }
    rv = put_json(client, f"/api/election/{election_id}/settings", settings)
    assert_ok(rv)


def test_run_offline_audit(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contests[0]["id"]: 100}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]

    jurisdiction_1_results = {
        contests[0]["id"]: {
            contests[0]["choices"][0]["id"]: 30,
            contests[0]["choices"][1]["id"]: 20,
        },
        contests[1]["id"]: {
            contests[1]["choices"][0]["id"]: 20,
            contests[1]["choices"][1]["id"]: 30,
            contests[1]["choices"][2]["id"]: 10,
        },
    }

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{rounds[0]['id']}/results",
        jurisdiction_1_results,
    )
    assert_ok(rv)

    # Round shouldn't be over yet, since we haven't recorded results for all jurisdictions with sampled ballots
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is None

    jurisdiction_2_results = {
        contests[0]["id"]: {
            contests[0]["choices"][0]["id"]: 20,
            contests[0]["choices"][1]["id"]: 10,
        },
        contests[1]["id"]: {
            contests[1]["choices"][0]["id"]: 10,
            contests[1]["choices"][1]["id"]: 15,
            contests[1]["choices"][2]["id"]: 10,
        },
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{rounds[0]['id']}/results",
        jurisdiction_2_results,
    )
    assert_ok(rv)

    # Round should be over
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is not None

    snapshot.assert_match(
        {
            f"{result.contest.name} - {result.contest_choice.name}": result.result
            for result in RoundContestResult.query.all()
        }
    )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

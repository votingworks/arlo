import pytest
from flask.testing import FlaskClient

from ..helpers import *  # pylint: disable=wildcard-import


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


@pytest.fixture
def contest_ids(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
) -> List[str]:
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 600,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400,},
            ],
            "totalBallotsCast": 1000,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


def test_minerva_ballot_polling_one_round(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],  # pylint: disable=unused-argument
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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
    round_id = rounds[0]["id"]

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )

    jurisdiction_1_results = {
        contests[0]["id"]: {
            contests[0]["choices"][0]["id"]: 30,
            contests[0]["choices"][1]["id"]: 20,
        },
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/results",
        jurisdiction_1_results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/results",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == jurisdiction_1_results

    # Round shouldn't be over yet, since we haven't recorded results for all jurisdictions with sampled ballots
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round"
    )
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is None

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )

    jurisdiction_2_results = {
        contests[0]["id"]: {
            contests[0]["choices"][0]["id"]: 20,
            contests[0]["choices"][1]["id"]: 10,
        },
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/results",
        jurisdiction_2_results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/results",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == jurisdiction_2_results

    # Round should be over
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round"
    )
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is not None

    snapshot.assert_match(
        {
            f"{result.contest.name} - {result.contest_choice.name}": result.result
            for result in RoundContestResult.query.filter_by(round_id=round_id).all()
        }
    )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)


def test_minerva_ballot_polling_two_rounds(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],  # pylint: disable=unused-argument
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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
    round_id = rounds[0]["id"]

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )

    jurisdiction_1_results = {
        contests[0]["id"]: {
            contests[0]["choices"][0]["id"]: 20,
            contests[0]["choices"][1]["id"]: 20,
        },
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/results",
        jurisdiction_1_results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/results",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == jurisdiction_1_results

    # Round shouldn't be over yet, since we haven't recorded results for all jurisdictions with sampled ballots
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round"
    )
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is None

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )

    jurisdiction_2_results = {
        contests[0]["id"]: {
            contests[0]["choices"][0]["id"]: 10,
            contests[0]["choices"][1]["id"]: 10,
        },
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/results",
        jurisdiction_2_results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/results",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == jurisdiction_2_results

    # Round should be over
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round"
    )
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is not None

    snapshot.assert_match(
        {
            f"{result.contest.name} - {result.contest_choice.name}": result.result
            for result in RoundContestResult.query.filter_by(round_id=round_id).all()
        }
    )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

    # Start a second round
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )

    jurisdiction_1_results = {
        contests[0]["id"]: {
            contests[0]["choices"][0]["id"]: 50,
            contests[0]["choices"][1]["id"]: 0,
        },
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/results",
        jurisdiction_1_results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/results",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == jurisdiction_1_results

    # Round shouldn't be over yet, since we haven't recorded results for all jurisdictions with sampled ballots
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round"
    )
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[1]["endedAt"] is None

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_2_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )

    jurisdiction_2_results = {
        contests[0]["id"]: {
            contests[0]["choices"][0]["id"]: 30,
            contests[0]["choices"][1]["id"]: 0,
        },
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_2_id}/results",
        jurisdiction_2_results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_2_id}/results",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == jurisdiction_2_results

    # Round should be over
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round"
    )
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is not None

    snapshot.assert_match(
        {
            f"{result.contest.name} - {result.contest_choice.name}": result.result
            for result in RoundContestResult.query.filter_by(round_id=round_2_id).all()
        }
    )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

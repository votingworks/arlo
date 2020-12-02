import pytest
from flask.testing import FlaskClient

from ..helpers import *  # pylint: disable=wildcard-import


@pytest.fixture
def election_id(client: FlaskClient, org_id: str, request):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    return create_election(
        client,
        audit_name=f"Test Audit {request.node.name}",
        audit_type=AuditType.BALLOT_POLLING,
        audit_math_type=AuditMathType.MINERVA,
        organization_id=org_id,
    )


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


def test_minerva_sample_size(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 200

    sample_size_options = json.loads(rv.data)["sampleSizes"][contest_ids[0]]
    assert len(sample_size_options) == 3
    snapshot.assert_match(sample_size_options)


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

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

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
        contests[1]["id"]: {
            contests[1]["choices"][0]["id"]: 20,
            contests[1]["choices"][1]["id"]: 30,
            contests[1]["choices"][2]["id"]: 10,
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
        contests[1]["id"]: {
            contests[1]["choices"][0]["id"]: 10,
            contests[1]["choices"][1]["id"]: 15,
            contests[1]["choices"][2]["id"]: 5,
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

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

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
        contests[1]["id"]: {
            contests[1]["choices"][0]["id"]: 10,
            contests[1]["choices"][1]["id"]: 15,
            contests[1]["choices"][2]["id"]: 10,
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
        contests[1]["id"]: {
            contests[1]["choices"][0]["id"]: 10,
            contests[1]["choices"][1]["id"]: 15,
            contests[1]["choices"][2]["id"]: 10,
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

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

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
        contests[1]["id"]: {
            contests[1]["choices"][0]["id"]: 20,
            contests[1]["choices"][1]["id"]: 30,
            contests[1]["choices"][2]["id"]: 10,
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
        contests[1]["id"]: {
            contests[1]["choices"][0]["id"]: 20,
            contests[1]["choices"][1]["id"]: 30,
            contests[1]["choices"][2]["id"]: 10,
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

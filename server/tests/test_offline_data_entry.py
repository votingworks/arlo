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


def test_offline_results_empty(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    contests = Contest.query.filter(Contest.id.in_(contest_ids)).all()
    expected_return_data = {
        contest.id: {choice.id: None for choice in contest.choices}
        for contest in contests
    }

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/results",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == expected_return_data


def test_run_offline_audit(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
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
        {
            "roundNum": 1,
            "sampleSizes": {
                contests[0]["id"]: {"key": "custom", "size": 100, "prob": None}
            },
        },
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


def test_offline_results_without_audit_boards(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/results",
        {},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Must set up audit boards before recording results",
            }
        ]
    }


def test_offline_results_invalid(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    contests = Contest.query.filter(Contest.id.in_(contest_ids)).all()

    invalid_results = [
        ({}, "Invalid contest ids"),
        ({"not-a-real-id": {}}, "Invalid contest ids"),
        (
            {contest.id: {} for contest in contests},
            f"Invalid choice ids for contest {contests[0].id}",
        ),
        (
            {
                contest.id: {choice.id: 0 for choice in contest.choices[:1]}
                for contest in contests
            },
            f"Invalid choice ids for contest {contests[0].id}",
        ),
        (
            {
                contest.id: {choice.id: 0 for choice in contest.choices}
                for contest in contests[:1]
            },
            "Invalid contest ids",
        ),
        (
            {
                contest.id: {choice.id: "not a number" for choice in contest.choices}
                for contest in contests
            },
            "'not a number' is not of type 'integer'",
        ),
        (
            {
                contest.id: {choice.id: -1 for choice in contest.choices}
                for contest in contests
            },
            "-1 is less than the minimum of 0",
        ),
        (
            {
                contest.id: {choice.id: 100 for choice in contest.choices}
                for contest in contests
            },
            "Total results for contest Contest 1 should not exceed 80 - the number of sampled ballots (80) times the number of votes allowed (1).",
        ),
    ]

    for invalid_result, expected_error in invalid_results:
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/results",
            invalid_result,
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": expected_error}]
        }


def test_offline_results_bad_round(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    election_id_2 = create_election(client, "Other Election", organization_id=org_id)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/audit-board",
            [{"name": "Audit Board #1"}],
        )
        assert_ok(rv)

        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/results",
            {
                contest["id"]: {choice["id"]: 0 for choice in contest["choices"]}
                for contest in contests
            },
        )
        assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 2,
            "sampleSizes": {
                contest_id: options[0]
                for contest_id, options in sample_size_options.items()
            },
        },
    )
    assert_ok(rv)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/results",
        {},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Round 1 is not the current round"}
        ]
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-round-id/results",
        {},
    )
    assert rv.status_code == 404

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-round-id/results",
    )
    assert rv.status_code == 404

    # Hackily set the round's election id to be a different election to test
    # that we correctly check the round and election match
    round = Round.query.get(round_1_id)
    round.election_id = election_id_2
    db_session.add(round)
    db_session.commit()

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/results",
        {},
    )
    assert rv.status_code == 404


def test_offline_results_in_online_election(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    election = Election.query.get(election_id)
    election.online = True
    db_session.commit()

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/results",
        {},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Cannot record offline results for online audit.",
            }
        ]
    }


def test_offline_results_jurisdiction_with_no_ballots(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    # Try submitting results for all the contests, even though J3 isn't assigned to every contest
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, f"j3-{election_id}@example.com"
    )

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[2]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[2]}/round/{round_1_id}/results",
        {
            contest["id"]: {choice["id"]: 0 for choice in contest["choices"]}
            for contest in contests
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Bad Request", "message": "Invalid contest ids"}]
    }

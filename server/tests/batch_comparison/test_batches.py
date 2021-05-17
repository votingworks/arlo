from typing import List
import io
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...worker.bgcompute import (
    bgcompute_update_ballot_manifest_file,
    bgcompute_update_batch_tallies_file,
)

J1_BATCHES_ROUND_1 = 3
J2_BATCHES_ROUND_1 = 1


def test_list_batches_bad_round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-real-round/batches"
    )
    assert rv.status_code == 404


def test_list_batches(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) == J1_BATCHES_ROUND_1
    compare_json(
        batches[0],
        {"id": assert_is_id, "name": "Batch 1", "numBallots": 500, "auditBoard": None,},
    )

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"},],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    compare_json(
        batches[0],
        {
            "id": assert_is_id,
            "name": "Batch 1",
            "numBallots": 500,
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
        },
    )


def test_batch_retrieval_list_bad_round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-real-round/batches/retrieval-list"
    )
    assert rv.status_code == 404


# Note: round 2 retrieval list tested in test_batch_comparison.py
def test_batch_retrieval_list_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    round_1_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/retrieval-list"
    )
    assert rv.status_code == 200
    assert (
        scrub_datetime(rv.headers["Content-Disposition"])
        == 'attachment; filename="batch-retrieval-J1-Test-Audit-test-batch-retrieval-list-round-1-DATETIME.csv"'
    )

    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    assert retrieval_list == "Batch Name,Container,Tabulator,Audit Board\n"

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"},],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/retrieval-list"
    )
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    assert len(retrieval_list.splitlines()) == J1_BATCHES_ROUND_1 + 1
    snapshot.assert_match(retrieval_list)


def test_record_batch_results(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) == J1_BATCHES_ROUND_1
    round_1_batch_ids = [batch["id"] for batch in batches]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/results"
    )
    assert rv.status_code == 200
    results = json.loads(rv.data)

    assert results == {
        batch["id"]: {choice_ids[0]: None, choice_ids[1]: None, choice_ids[2]: None,}
        for batch in batches
    }

    results = {
        batches[0]["id"]: {choice_ids[0]: 400, choice_ids[1]: 50, choice_ids[2]: 40,},
        batches[1]["id"]: {choice_ids[0]: 100, choice_ids[1]: 50, choice_ids[2]: 40,},
        batches[2]["id"]: {choice_ids[0]: 10, choice_ids[1]: 50, choice_ids[2]: 40,},
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/results",
        results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/results"
    )
    assert rv.status_code == 200
    new_results = json.loads(rv.data)
    assert new_results == results

    # Round shouldn't be over yet, since we haven't recorded results for all jurisdictions with sampled batches
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round"
    )
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is None

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) == J2_BATCHES_ROUND_1

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/results"
    )
    assert rv.status_code == 200
    results = json.loads(rv.data)

    assert results == {
        batch["id"]: {choice_ids[0]: None, choice_ids[1]: None, choice_ids[2]: None,}
        for batch in batches
    }

    for batch in batches:
        results[batch["id"]][choice_ids[0]] = 400
        results[batch["id"]][choice_ids[1]] = 50
        results[batch["id"]][choice_ids[2]] = 40

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/results",
        results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/results"
    )
    assert rv.status_code == 200
    new_results = json.loads(rv.data)
    assert new_results == results

    # Round should be over
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round"
    )
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is not None

    snapshot.assert_match(
        {
            f"{result.contest.name} - {result.contest_choice.name}": result.result
            for result in RoundContestResult.query.filter_by(round_id=round_1_id).all()
        }
    )

    # Start a new round to test round 2
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2})
    assert_ok(rv)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round"
    )
    assert rv.status_code == 200
    rounds = json.loads(rv.data)["rounds"]
    round_2_id = rounds[1]["id"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) == 2
    # Batches that were sampled in round 1 should be filtered out
    for batch in batches:
        assert batch["id"] not in round_1_batch_ids

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/batches/results"
    )
    assert rv.status_code == 200
    results = json.loads(rv.data)
    assert set(results.keys()) == {batch["id"] for batch in batches}

    for batch in batches:
        results[batch["id"]][choice_ids[0]] = 400
        results[batch["id"]][choice_ids[1]] = 50
        results[batch["id"]][choice_ids[2]] = 40

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/batches/results",
        results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/batches/results"
    )
    assert rv.status_code == 200
    new_results = json.loads(rv.data)
    assert new_results == results


def test_record_batch_results_without_audit_boards(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/results",
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


def test_record_batch_results_invalid(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,  # pylint: disable=unused-argument
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    choice_ids = [choice["id"] for choice in contests[0]["choices"]]
    batch_ids = [batch["id"] for batch in batches]

    invalid_results = [
        ({}, "Invalid batch ids"),
        ({"not-a-real-id": {}}, "Invalid batch ids"),
        (
            {batch_id: {} for batch_id in batch_ids},
            f"Invalid choice ids for batch {batches[0]['name']}",
        ),
        (
            {
                batch_id: {choice_id: 0 for choice_id in choice_ids[:1]}
                for batch_id in batch_ids
            },
            f"Invalid choice ids for batch {batches[0]['name']}",
        ),
        (
            {
                batch_id: {choice_id: 0 for choice_id in choice_ids}
                for batch_id in batch_ids[:1]
            },
            "Invalid batch ids",
        ),
        (
            {
                batch_id: {choice_id: "not a number" for choice_id in choice_ids}
                for batch_id in batch_ids[:1]
            },
            "'not a number' is not of type 'integer'",
        ),
        (
            {
                batch_id: {choice_id: -1 for choice_id in choice_ids}
                for batch_id in batch_ids[:1]
            },
            "-1 is less than the minimum of 0",
        ),
        (
            {
                batch_id: {choice_id: 400 for choice_id in choice_ids}
                for batch_id in batch_ids
            },
            "Total votes for batch Batch 1 should not exceed 1000 - the number of ballots in the batch (500) times the number of votes allowed (2).",
        ),
    ]

    for invalid_result, expected_error in invalid_results:
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/results",
            invalid_result,
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": expected_error}]
        }


def test_record_batch_results_bad_round(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]

    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

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

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches"
        )
        assert rv.status_code == 200
        batches = json.loads(rv.data)["batches"]
        batch_results = {
            batch["id"]: {choice_id: 0 for choice_id in choice_ids} for batch in batches
        }
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/results",
            batch_results,
        )
        assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2})
    assert_ok(rv)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/results",
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
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-round-id/batches/results",
        {},
    )
    assert rv.status_code == 404

    # Hackily set the round's election id to be a different election to test
    # that we correctly check the round and election match
    round = Round.query.get(round_1_id)
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    election_id_2 = create_election(client, "Other Election", organization_id=org_id)
    round.election_id = election_id_2
    db_session.add(round)
    db_session.commit()

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/results",
        {},
    )
    assert rv.status_code == 404


def test_batches_human_sort_order(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    snapshot,
):
    human_ordered_batches = [
        "Batch 1",
        "Batch 1 - 1",
        "Batch 1 - 2",
        "Batch 1 - 10",
        "Batch 2",
        "Batch 10",
    ]

    # Set contests
    contest_id = str(uuid.uuid4())
    contests = [
        {
            "id": contest_id,
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 1",
                    "numVotes": len(human_ordered_batches) * 10 * 2,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 2",
                    "numVotes": len(human_ordered_batches) * 5 * 2,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 3",
                    "numVotes": len(human_ordered_batches) * 5 * 2,
                },
            ],
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    # Upload a manifest with mixed text/number batch names
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/ballot-manifest",
            data={
                "manifest": (
                    io.BytesIO(
                        (
                            "Batch Name,Number of Ballots\n"
                            + "\n".join(
                                f"{batch},20" for batch in human_ordered_batches
                            )
                        ).encode()
                    ),
                    "manifest.csv",
                )
            },
        )
        assert_ok(rv)
        bgcompute_update_ballot_manifest_file(election_id)

        # Upload batch tallies
        batch_tallies_file = (
            "Batch Name,candidate 1,candidate 2,candidate 3\n"
            + "\n".join(f"{batch},10,5,5" for batch in human_ordered_batches)
        )
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/batch-tallies",
            data={
                "batchTallies": (
                    io.BytesIO(batch_tallies_file.encode()),
                    "batchTallies.csv",
                )
            },
        )
        assert_ok(rv)
        bgcompute_update_batch_tallies_file(election_id)
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/batch-tallies",
        )

    # Start round 1
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_id: sample_size_options[contest_id][0]},
        },
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round",)
    rounds = json.loads(rv.data)["rounds"]
    round_1_id = rounds[0]["id"]

    # Create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    # Check that the batches are ordered in human order
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/retrieval-list"
    )
    assert rv.status_code == 200
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    batches = json.loads(rv.data)["batches"]

    def unique_preserve_order(values):
        return list(dict.fromkeys(values))

    unique_batches = unique_preserve_order(batch["name"] for batch in batches)
    assert unique_batches == [
        batch for batch in human_ordered_batches if batch in unique_batches
    ]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    assert_match_report(rv.data, snapshot)

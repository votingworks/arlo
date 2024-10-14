import io
import uuid, json
from typing import List, Tuple
import urllib.parse
import pytest
from flask.testing import FlaskClient

from .helpers import *  # pylint: disable=wildcard-import
from ..models import *  # pylint: disable=wildcard-import


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
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 1",
                    "numVotes": 1000000,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 2",
                    "numVotes": 999000,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 3",
                    "numVotes": 1000,
                },
            ],
            "totalBallotsCast": 2000000,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n"
                    b"1,200000\n"
                    b"2,200000\n"
                    b"3,200000\n"
                    b"4,200000\n"
                    b"5,200000"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n"
                    b"1,200000\n"
                    b"2,200000\n"
                    b"3,200000\n"
                    b"4,200000\n"
                    b"5,200000"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)


def test_all_ballots_sample_size(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    options = sample_size_options[contest_ids[0]]
    # We only expect the all-ballots sample size option when the margin is
    # small and the number of ballots is large
    assert options == [{"key": "all-ballots", "size": 2000000, "prob": None}]


def test_all_ballots_audit(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    contest_id = contest_ids[0]

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = client.get(f"/api/election/{election_id}/settings")
    assert json.loads(rv.data)["online"] is True

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_sizes = json.loads(rv.data)["sampleSizes"]
    selected_sample_sizes = {contest_id: sample_sizes[contest_id][0]}

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": selected_sample_sizes},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    round_1 = json.loads(rv.data)["rounds"][0]
    round_id = round_1["id"]

    compare_json(
        round_1,
        {
            "id": assert_is_id,
            "roundNum": 1,
            "startedAt": assert_is_date,
            "endedAt": None,
            "isAuditComplete": None,
            "needsFullHandTally": True,
            "isFullHandTally": True,
            "drawSampleTask": {
                "status": "PROCESSED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
        },
    )

    # Election should have been converted to offline automatically
    rv = client.get(f"/api/election/{election_id}/settings")
    assert json.loads(rv.data)["online"] is False

    # No ballots actually got sampled (i.e. written to the db)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/ballots"
    )
    assert json.loads(rv.data) == {"ballots": []}

    # Create audit boards and record results for one jurisdiction
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    contest = json.loads(rv.data)["contests"][0]

    # Record partial results
    jurisdiction_1_results = {
        "batchName": "Batch/Zero",  # Make sure we support slashes in the URL
        "batchType": "Election Day",
        "choiceResults": {
            choice["id"]: int(choice["numVotes"] / 4) for choice in contest["choices"]
        },
    }

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch/",
        jurisdiction_1_results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "finalizedAt": None,
        "results": [jurisdiction_1_results],
    }

    # Update the batch (from Batch/Zero to Batch One)
    jurisdiction_1_results = {
        "batchName": "Batch One",
        "batchType": "Provisional",
        "choiceResults": {
            choice["id"]: choice["numVotes"] / 8 for choice in contest["choices"]
        },
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch/{urllib.parse.quote('Batch/Zero')}",
        jurisdiction_1_results,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "finalizedAt": None,
        "results": [jurisdiction_1_results],
    }

    # Check jurisdiction progress
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    jurisdiction_sample_size = int(selected_sample_sizes[contest_id]["size"] / 2)
    assert jurisdictions[0]["currentRoundStatus"] == {
        "numSamples": jurisdiction_sample_size,
        "numSamplesAudited": int(jurisdiction_sample_size / 4),
        "numUnique": jurisdiction_sample_size,
        "numUniqueAudited": int(jurisdiction_sample_size / 4),
        "numBatchesAudited": 1,
        "status": "IN_PROGRESS",
    }

    # Add next results
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    next_jurisdiction_1_results_a = {
        "batchName": "Batch Two",
        "batchType": "Other",
        "choiceResults": {
            choice["id"]: int(choice["numVotes"] / 4) for choice in contest["choices"]
        },
    }

    next_jurisdiction_1_results_b = {
        "batchName": "Batch Three",
        "batchType": "Election Day",
        "choiceResults": {
            choice["id"]: int(choice["numVotes"] / 8) for choice in contest["choices"]
        },
    }

    next_jurisdiction_1_results_c = {
        "batchName": "Batch/Bogus",  # Make sure we support slashes in the URL
        "batchType": "Election Day",
        "choiceResults": {
            choice["id"]: int(choice["numVotes"] / 2) for choice in contest["choices"]
        },
    }

    updated_jurisdiction_1_results = [
        jurisdiction_1_results,
        next_jurisdiction_1_results_a,
        next_jurisdiction_1_results_b,
        next_jurisdiction_1_results_c,
    ]

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch/",
        next_jurisdiction_1_results_a,
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch/",
        next_jurisdiction_1_results_b,
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch/",
        next_jurisdiction_1_results_c,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "finalizedAt": None,
        "results": updated_jurisdiction_1_results,
    }

    # Delete a result
    updated_jurisdiction_1_results = updated_jurisdiction_1_results[:-1]
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch/{urllib.parse.quote('Batch/Bogus')}"
    )
    assert_ok(rv)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "finalizedAt": None,
        "results": updated_jurisdiction_1_results,
    }

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/finalize",
    )
    assert_ok(rv)

    # Finalize the results
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/full-hand-tally/batch",
    )
    assert rv.status_code == 200
    compare_json(
        json.loads(rv.data),
        {
            "finalizedAt": assert_is_date,
            "results": updated_jurisdiction_1_results,
        },
    )

    # Trying to end the round should fail, since we haven't recorded results for
    # all jurisdictions with sampled ballots
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert rv.status_code == 409

    # Check jurisdiction progress
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    jurisdiction_sample_size = int(selected_sample_sizes[contest_id]["size"] / 2)
    assert jurisdictions[0]["currentRoundStatus"] == {
        "numSamples": jurisdiction_sample_size,
        "numSamplesAudited": jurisdiction_sample_size,
        "numUnique": jurisdiction_sample_size,
        "numUniqueAudited": jurisdiction_sample_size,
        "numBatchesAudited": 3,
        "status": "COMPLETE",
    }
    assert jurisdictions[1]["currentRoundStatus"] == {
        "numSamples": jurisdiction_sample_size,
        "numSamplesAudited": 0,
        "numUnique": jurisdiction_sample_size,
        "numUniqueAudited": 0,
        "numBatchesAudited": 0,
        "status": "NOT_STARTED",
    }

    # Now do the second jurisdiction
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )

    jurisdiction_2_results = [
        {
            "batchName": "Batch One",
            "batchType": "Absentee By Mail",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
        {
            "batchName": "Batch Two",
            "batchType": "Advance",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    ]

    for result in jurisdiction_2_results:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/full-hand-tally/batch/",
            result,
        )
        assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/full-hand-tally/batch",
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "finalizedAt": None,
        "results": jurisdiction_2_results,
    }

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/full-hand-tally/finalize",
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_id}/full-hand-tally/batch",
    )
    assert rv.status_code == 200
    compare_json(
        json.loads(rv.data),
        {
            "finalizedAt": assert_is_date,
            "results": jurisdiction_2_results,
        },
    )

    # End the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    snapshot.assert_match(
        {
            f"{result.contest.name} - {result.contest_choice.name}": result.result
            for result in RoundContestResult.query.filter_by(round_id=round_id).all()
        }
    )

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    assert_match_report(rv.data, snapshot)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)


def test_full_hand_tally_results_validation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    contest = json.loads(rv.data)["contests"][0]

    # Record invalid results
    invalid_results: List[Tuple[dict, str]] = [
        (
            {
                "batchName": "",
                "batchType": "Provisional",
                "choiceResults": {
                    choice["id"]: choice["numVotes"] / 4
                    for choice in contest["choices"]
                },
            },
            "'' is too short",
        ),
        (
            {
                "batchName": "a" * 201,
                "batchType": "Provisional",
                "choiceResults": {
                    choice["id"]: choice["numVotes"] / 4
                    for choice in contest["choices"]
                },
            },
            f"'{'a' * 201}' is too long",
        ),
        (
            {
                "batchName": None,
                "batchType": "Provisional",
                "choiceResults": {
                    choice["id"]: choice["numVotes"] / 4
                    for choice in contest["choices"]
                },
            },
            "None is not of type 'string'",
        ),
        (
            {
                "batchType": "Provisional",
                "choiceResults": {
                    choice["id"]: choice["numVotes"] / 4
                    for choice in contest["choices"]
                },
            },
            "'batchName' is a required property",
        ),
        (
            {
                "batchName": "Batch 1",
                "batchType": "bad type",
                "choiceResults": {
                    choice["id"]: choice["numVotes"] / 4
                    for choice in contest["choices"]
                },
            },
            "'bad type' is not one of ['Absentee By Mail', 'Advance', 'Election Day', 'Provisional', 'Other']",
        ),
        (
            {
                "batchName": "Batch 1",
                "batchType": "Provisional",
                "choiceResults": {
                    choice["id"]: choice["numVotes"] / 4
                    for choice in contest["choices"][:1]
                },
            },
            "Invalid choice ids for batch Batch 1",
        ),
        (
            {
                "batchName": "Batch 1",
                "batchType": "Provisional",
                "choiceResults": {"not a real id": 0},
            },
            "Invalid choice ids for batch Batch 1",
        ),
        (
            {
                "batchName": "Batch 1",
                "batchType": "Provisional",
                "choiceResults": {
                    choice["id"]: 1000 * 1000 * 1000 + 1
                    for choice in contest["choices"]
                },
            },
            "1000000001 is greater than the maximum of 1000000000",
        ),
    ]

    for invalid_result, expected_message in invalid_results:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/",
            invalid_result,
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": expected_message}]
        }

        if invalid_result.get("batchName"):
            rv = put_json(
                client,
                f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/{invalid_result['batchName']}",
                invalid_result,
            )
            assert rv.status_code == 400
            assert json.loads(rv.data) == {
                "errors": [{"errorType": "Bad Request", "message": expected_message}]
            }

    # No duplicate batch names
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/",
        {
            "batchName": "Batch 1",
            "batchType": "Provisional",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/",
        {
            "batchName": "Batch 1",
            "batchType": "Election Day",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Conflict", "message": "Batch names must be unique"}]
    }

    # No renaming to another batch's name
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/",
        {
            "batchName": "Batch 2",
            "batchType": "Provisional",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert_ok(rv)

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/Batch 2",
        {
            "batchName": "Batch 1",
            "batchType": "Provisional",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Conflict", "message": "Batch names must be unique"}]
    }

    # Can't edit a batch that doesn't exist
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/not a real batch",
        {
            "batchName": "Batch 3",
            "batchType": "Election Day",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Conflict", "message": "This batch has been deleted"}]
    }

    # Special case: deleting a batch that doesn't exist is ok (maybe somebody else already deleted it)
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/not a real batch",
    )
    assert_ok(rv)

    # Can't edit a batch that's been deleted
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/Batch 1",
    )
    assert_ok(rv)

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/Batch 1",
        {
            "batchName": "Batch 1",
            "batchType": "Provisional",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Conflict", "message": "This batch has been deleted"}]
    }

    # Can't add/edit/delete results after finalizing
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/finalize",
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/",
        {
            "batchName": "Batch 1",
            "batchType": "Provisional",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Results have already been finalized"}
        ]
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/Batch 1",
        {
            "batchName": "Batch 1",
            "batchType": "Provisional",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Results have already been finalized"}
        ]
    }

    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/Batch 1",
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Results have already been finalized"}
        ]
    }


def test_full_hand_tally_results_unfinalize(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    contest = json.loads(rv.data)["contests"][0]

    # JA uploads results
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/",
        {
            "batchName": "Batch 1",
            "batchType": "Provisional",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert_ok(rv)

    # AA tries to unfinalize the results before they have been finalized
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/finalize"
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Results have not been finalized"}
        ]
    }

    # JA finalizes results
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/finalize",
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch"
    )
    assert_is_date(json.loads(rv.data)["finalizedAt"])

    # AA unfinalizes the results
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/finalize"
    )
    assert_ok(rv)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch"
    )
    assert json.loads(rv.data)["finalizedAt"] is None

    # JA updates the results
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch/",
        {
            "batchName": "Batch 2",
            "batchType": "Election Day",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert_ok(rv)

    # JA refinalizes the results
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/finalize",
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/batch"
    )
    assert_is_date(json.loads(rv.data)["finalizedAt"])

    # Other jurisdiction enters results and finalizes to end the round
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/full-hand-tally/batch/",
        {
            "batchName": "Batch 1",
            "batchType": "Election Day",
            "choiceResults": {
                choice["id"]: choice["numVotes"] / 4 for choice in contest["choices"]
            },
        },
    )
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/full-hand-tally/finalize",
    )
    assert_ok(rv)

    # End the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # AA tries to unfinalize results but can't
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/full-hand-tally/finalize"
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Results cannot be unfinalized after the audit round ends",
            }
        ]
    }

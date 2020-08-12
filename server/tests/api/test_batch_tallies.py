import io, json
from typing import List
import pytest
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...bgcompute import (
    bgcompute_update_batch_tallies_file,
    bgcompute_update_ballot_manifest_file,
)
from ...util.process_file import ProcessingStatus


@pytest.fixture
def election_id(client: FlaskClient, request):
    return create_election(
        client,
        audit_name=f"Test Audit {request.node.name}",
        audit_type=AuditType.BATCH_COMPARISON,
    )


@pytest.fixture
def contest_ids(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 600},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 500},
            ],
            "totalBallotsCast": 1500,
            "numWinners": 1,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n"
                    b"Batch 1,200\n"
                    b"Batch 2,300\n"
                    b"Batch 3,400\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_ballot_manifest_file()


def test_batch_tallies_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                    b"Batch 1,1,10,100\n"
                    b"Batch 2,2,20,200\n"
                    b"Batch 3,3,30,300\n"
                ),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "batchTallies.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.READY_TO_PROCESS,
                "startedAt": None,
                "completedAt": None,
                "error": None,
            },
        },
    )

    bgcompute_update_batch_tallies_file()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "batchTallies.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
        },
    )

    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert jurisdiction.batch_tallies == {
        "Batch 1": {
            "Contest 1": {"candidate 1": 1, "candidate 2": 10, "candidate 3": 100,}
        },
        "Batch 2": {
            "Contest 1": {"candidate 1": 2, "candidate 2": 20, "candidate 3": 200,}
        },
        "Batch 3": {
            "Contest 1": {"candidate 1": 3, "candidate 2": 30, "candidate 3": 300,}
        },
    }


def test_batch_tallies_replace(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                    b"Batch 1,1,10,100\n"
                    b"Batch 2,2,20,200\n"
                    b"Batch 3,3,30,300\n"
                ),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).batch_tallies_file_id

    bgcompute_update_batch_tallies_file()

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                    b"Batch 1,11,10,100\n"
                    b"Batch 2,2,22,200\n"
                    b"Batch 3,3,30,333\n"
                ),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)

    # The old file should have been deleted
    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert File.query.get(file_id) is None
    assert jurisdiction.batch_tallies_file_id != file_id

    bgcompute_update_batch_tallies_file()

    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert jurisdiction.batch_tallies == {
        "Batch 1": {
            "Contest 1": {"candidate 1": 11, "candidate 2": 10, "candidate 3": 100,}
        },
        "Batch 2": {
            "Contest 1": {"candidate 1": 2, "candidate 2": 22, "candidate 3": 200,}
        },
        "Batch 3": {
            "Contest 1": {"candidate 1": 3, "candidate 2": 30, "candidate 3": 333,}
        },
    }


def test_batch_tallies_clear(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                    b"Batch 1,1,10,100\n"
                    b"Batch 2,2,20,200\n"
                    b"Batch 3,3,30,300\n"
                ),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).batch_tallies_file_id

    bgcompute_update_batch_tallies_file()

    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    assert json.loads(rv.data) == {"file": None, "processing": None}

    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert jurisdiction.batch_tallies_file_id is None
    assert File.query.get(file_id) is None
    assert jurisdiction.batch_tallies is None


def test_batch_tallies_upload_missing_file(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing required file parameter 'batchTallies'",
            }
        ]
    }


def test_batch_tallies_upload_bad_csv(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={"batchTallies": (io.BytesIO(b"not a CSV file"), "random.txt")},
    )
    assert_ok(rv)

    bgcompute_update_batch_tallies_file()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "random.txt", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Please submit a valid CSV file with columns separated by commas.",
            },
        },
    )


def test_batch_tallies_upload_missing_choice(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)

    headers = ["Batch Name", "candidate 1", "candidate 2", "candidate 3"]
    for missing_field in headers:
        header_row = ",".join(h for h in headers if h != missing_field)

        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
            data={
                "batchTallies": (
                    io.BytesIO(header_row.encode() + b"\n1,2,3"),
                    "batchTallies.csv",
                )
            },
        )
        assert_ok(rv)

        bgcompute_update_batch_tallies_file()

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {"name": "batchTallies.csv", "uploadedAt": assert_is_date,},
                "processing": {
                    "status": ProcessingStatus.ERRORED,
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": f"Missing required column: {missing_field}.",
                },
            },
        )


def test_batch_tallies_wrong_batch_names(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)

    bad_files = [
        (
            (b"Batch Name,candidate 1,candidate 2,candidate 3\n" b"Batch 1,1,10,100\n"),
            (
                "Batch names must match the ballot manifest file.\n"
                "Found missing batch names: Batch 2, Batch 3"
            ),
        ),
        (
            (
                b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                b"Batch 1,1,10,100\n"
                b"Batch 2,2,20,200\n"
                b"Batch 3,3,30,300\n"
                b"Batch 4,4,40,400\n"
            ),
            (
                "Batch names must match the ballot manifest file.\n"
                "Found extra batch names: Batch 4"
            ),
        ),
        (
            (
                b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                b"Batch 1,1,10,100\n"
                b"Batch 4,4,40,400\n"
                b"Batch 2,2,20,200\n"
            ),
            (
                "Batch names must match the ballot manifest file.\n"
                "Found extra batch names: Batch 4\n"
                "Found missing batch names: Batch 3"
            ),
        ),
    ]
    for bad_file, expected_error in bad_files:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
            data={"batchTallies": (io.BytesIO(bad_file), "batchTallies.csv",)},
        )
        assert_ok(rv)

        bgcompute_update_batch_tallies_file()

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {"name": "batchTallies.csv", "uploadedAt": assert_is_date,},
                "processing": {
                    "status": ProcessingStatus.ERRORED,
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": expected_error,
                },
            },
        )


def test_batch_tallies_too_many_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                    b"Batch 1,300,10,100\n"
                    b"Batch 2,2,20,200\n"
                    b"Batch 3,3,30,300\n"
                ),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)

    bgcompute_update_batch_tallies_file()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "batchTallies.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": 'The total votes for batch "Batch 1" (410 votes) cannot exceed 400 - the number of ballots from the manifest (200 ballots) multipled by the number of votes allowed for the contest (2 votes per ballot).',
            },
        },
    )


def test_batch_tallies_ballot_polling(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    # Hackily change the audit type
    election = Election.query.get(election_id)
    election.audit_type = AuditType.BALLOT_POLLING
    db_session.add(election)
    db_session.commit()

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                    b"Batch 1,300,10,100\n"
                    b"Batch 2,2,20,200\n"
                    b"Batch 3,3,30,300\n"
                ),
                "batchTallies.csv",
            )
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Can only upload batch tallies file for batch comparison audits.",
            }
        ]
    }


def test_batch_tallies_bad_jurisdiction(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                    b"Batch 1,300,10,100\n"
                    b"Batch 2,2,20,200\n"
                    b"Batch 3,3,30,300\n"
                ),
                "batchTallies.csv",
            )
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Jurisdiction does not have any contests assigned",
            }
        ]
    }


def test_batch_tallies_before_manifests(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                    b"Batch 1,300,10,100\n"
                    b"Batch 2,2,20,200\n"
                    b"Batch 3,3,30,300\n"
                ),
                "batchTallies.csv",
            )
        },
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Must upload ballot manifest before uploading batch tallies.",
            }
        ]
    }

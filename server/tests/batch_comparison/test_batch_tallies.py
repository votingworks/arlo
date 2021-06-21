import io, json
from typing import List
from flask.testing import FlaskClient
import pytest

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...worker.bgcompute import (
    bgcompute_update_batch_tallies_file,
    bgcompute_update_ballot_manifest_file,
)
from ...util.process_file import ProcessingStatus


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
                    b"Batch 1,200\n"
                    b"Batch 2,300\n"
                    b"Batch 3,400\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_ballot_manifest_file(election_id)


def test_batch_tallies_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["batchTallies"]["numBallots"] is None

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    batch_tallies_file = (
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 3,3,30,300\n"
        b"Batch 1,1,10,100\n"
        b"Batch 2,2,20,200\n"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={"batchTallies": (io.BytesIO(batch_tallies_file), "batchTallies.csv",)},
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

    bgcompute_update_batch_tallies_file(election_id)

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
    contest = Contest.query.get(contest_id)
    assert jurisdiction.batch_tallies == {
        "Batch 1": {
            contest_id: {
                contest.choices[0].id: 1,
                contest.choices[1].id: 10,
                contest.choices[2].id: 100,
                "ballots": 200,  # based on ballot manifest
            }
        },
        "Batch 2": {
            contest_id: {
                contest.choices[0].id: 2,
                contest.choices[1].id: 20,
                contest.choices[2].id: 200,
                "ballots": 300,
            }
        },
        "Batch 3": {
            contest_id: {
                contest.choices[0].id: 3,
                contest.choices[1].id: 30,
                contest.choices[2].id: 300,
                "ballots": 400,
            }
        },
    }

    # Test that the AA jurisdictions list includes batch tallies
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    compare_json(
        jurisdictions[0]["batchTallies"],
        {
            "file": {"name": "batchTallies.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": "PROCESSED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
            "numBallots": (111 + 222 + 333) / 2,
        },
    )

    # Test that the AA can download the batch tallies file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies/csv"
    )
    assert rv.status_code == 200
    assert (
        rv.headers["Content-Disposition"] == 'attachment; filename="batchTallies.csv"'
    )
    assert rv.data == batch_tallies_file


def test_batch_tallies_replace(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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

    bgcompute_update_batch_tallies_file(election_id)

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

    bgcompute_update_batch_tallies_file(election_id)

    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    contest = Contest.query.get(contest_id)
    assert jurisdiction.batch_tallies == {
        "Batch 1": {
            contest_id: {
                contest.choices[0].id: 11,
                contest.choices[1].id: 10,
                contest.choices[2].id: 100,
                "ballots": 200,
            }
        },
        "Batch 2": {
            contest_id: {
                contest.choices[0].id: 2,
                contest.choices[1].id: 22,
                contest.choices[2].id: 200,
                "ballots": 300,
            }
        },
        "Batch 3": {
            contest_id: {
                contest.choices[0].id: 3,
                contest.choices[1].id: 30,
                contest.choices[2].id: 333,
                "ballots": 400,
            }
        },
    }


def test_batch_tallies_clear(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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

    bgcompute_update_batch_tallies_file(election_id)

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

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies/csv"
    )
    assert rv.status_code == 404


def test_batch_tallies_upload_missing_file(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={"batchTallies": (io.BytesIO(b"not a CSV file"), "random.txt")},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Please submit a valid CSV. If you are working with an Excel spreadsheet, make sure you export it as a .csv file before uploading",
            }
        ]
    }


def test_batch_tallies_upload_missing_choice(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

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

        bgcompute_update_batch_tallies_file(election_id)

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
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

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

        bgcompute_update_batch_tallies_file(election_id)

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
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                    b"Batch 3,3,30,300\n"
                    b"Batch 1,300,10,100\n"
                    b"Batch 2,2,20,200\n"
                ),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)

    bgcompute_update_batch_tallies_file(election_id)

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

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, f"j3-{election_id}@example.com"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[2]}/batch-tallies",
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
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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


def test_batch_tallies_reprocess_after_manifest_reupload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Upload tallies
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                    b"Batch 3,3,30,300\n"
                    b"Batch 1,1,10,100\n"
                    b"Batch 2,2,20,200\n"
                ),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_batch_tallies_file(election_id)

    # Reupload a manifest but remove a batch
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n" b"Batch 1,200\n" b"Batch 2,300\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_ballot_manifest_file(election_id)

    # Error should be recorded for tallies
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
                "error": "Batch names must match the ballot manifest file.\nFound extra batch names: Batch 3",
            },
        },
    )

    assert Jurisdiction.query.get(jurisdiction_ids[0]).batch_tallies is None

    # Fix the manifest
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
    bgcompute_update_ballot_manifest_file(election_id)

    # Tallies should be fixed
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

    assert Jurisdiction.query.get(jurisdiction_ids[0]).batch_tallies is not None

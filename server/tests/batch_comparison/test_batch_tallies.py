import io, json
from typing import List
from flask.testing import FlaskClient
import pytest

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(
            b"Batch Name,Number of Ballots\n"
            b"Batch 1,200\n"
            b"Batch 2,300\n"
            b"Batch 3,400\n"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)


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
    rv = upload_batch_tallies(
        client, io.BytesIO(batch_tallies_file), election_id, jurisdiction_ids[0]
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batchTallies"),
                "uploadedAt": assert_is_date,
            },
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
            "file": {
                "name": asserts_startswith("batchTallies"),
                "uploadedAt": assert_is_date,
            },
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
    assert rv.headers["Content-Disposition"].startswith(
        'attachment; filename="batchTallies'
    )
    assert rv.data == batch_tallies_file


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
    rv = upload_batch_tallies(
        client,
        io.BytesIO(
            b"Batch Name,candidate 1,candidate 2,candidate 3\n"
            b"Batch 1,1,10,100\n"
            b"Batch 2,2,20,200\n"
            b"Batch 3,3,30,300\n"
        ),
        election_id,
        jurisdiction_ids[0],
    )

    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).batch_tallies_file_id

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


def test_batch_tallies_replace_as_audit_admin(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    manifests,  # pylint: disable=unused-argument
):
    # Check that AA can also get/put/clear batch tallies
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = upload_batch_tallies(
        client,
        io.BytesIO(
            b"Batch Name,candidate 1,candidate 2,candidate 3\n"
            b"Batch 1,1,10,100\n"
            b"Batch 2,2,20,200\n"
            b"Batch 3,3,30,300\n"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).batch_tallies_file_id

    rv = upload_batch_tallies(
        client,
        io.BytesIO(
            b"Batch Name,candidate 1,candidate 2,candidate 3\n"
            b"Batch 1,11,10,100\n"
            b"Batch 2,2,22,200\n"
            b"Batch 3,3,30,333\n"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    # The old file should have been deleted
    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert File.query.get(file_id) is None
    assert jurisdiction.batch_tallies_file_id != file_id

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

    # Now clear the batch tallies and check they are deleted
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    assert json.loads(rv.data) == {"file": None, "processing": None}


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
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies/upload-complete",
        data={},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing required JSON parameter: storagePathKey",
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
    rv = client.post(
        "/api/file-upload",
        data={
            "file": (
                io.BytesIO(b"not a CSV file"),
                "random.txt",
            ),
            "key": "test_dir/random.txt",
        },
    )
    assert_ok(rv)
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies/upload-complete",
        data={
            "storagePathKey": "test_dir/random.txt",
            "fileName": "random.txt",
            "fileType": "text/plain",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Please submit a valid CSV. If you are working with an Excel spreadsheet, make sure you export it as a .csv file before uploading.",
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

        rv = upload_batch_tallies(
            client,
            io.BytesIO(header_row.encode() + b"\n1,2,3"),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "name": asserts_startswith("batchTallies"),
                    "uploadedAt": assert_is_date,
                },
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
        rv = upload_batch_tallies(
            client, io.BytesIO(bad_file), election_id, jurisdiction_ids[0]
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "name": asserts_startswith("batchTallies"),
                    "uploadedAt": assert_is_date,
                },
                "processing": {
                    "status": "ERRORED",
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
    rv = upload_batch_tallies(
        client,
        io.BytesIO(
            b"Batch Name,candidate 1,candidate 2,candidate 3\n"
            b"Batch 3,3,30,300\n"
            b"Batch 1,300,10,100\n"
            b"Batch 2,2,20,200\n"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batchTallies"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": 'The total votes for contest "Contest 1" in batch "Batch 1" (410 votes) cannot exceed 400 - the number of ballots from the manifest (200 ballots) multiplied by the number of votes allowed for the contest (2 votes per ballot).',
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
    rv = upload_batch_tallies(
        client,
        io.BytesIO(
            b"Batch Name,candidate 1,candidate 2,candidate 3\n"
            b"Batch 1,300,10,100\n"
            b"Batch 2,2,20,200\n"
            b"Batch 3,3,30,300\n"
        ),
        election_id,
        jurisdiction_ids[0],
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
    rv = upload_batch_tallies(
        client,
        io.BytesIO(
            b"Batch Name,candidate 1,candidate 2,candidate 3\n"
            b"Batch 1,300,10,100\n"
            b"Batch 2,2,20,200\n"
            b"Batch 3,3,30,300\n"
        ),
        election_id,
        jurisdiction_ids[2],
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
    rv = upload_batch_tallies(
        client,
        io.BytesIO(
            b"Batch Name,candidate 1,candidate 2,candidate 3\n"
            b"Batch 1,300,10,100\n"
            b"Batch 2,2,20,200\n"
            b"Batch 3,3,30,300\n"
        ),
        election_id,
        jurisdiction_ids[0],
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
    rv = upload_batch_tallies(
        client,
        io.BytesIO(
            b"Batch Name,candidate 1,candidate 2,candidate 3\n"
            b"Batch 3,3,30,300\n"
            b"Batch 1,1,10,100\n"
            b"Batch 2,2,20,200\n"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    # Reupload a manifest but remove a batch
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Name,Number of Ballots\n" b"Batch 1,200\n" b"Batch 2,300\n"),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    # Error should be recorded for tallies
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batchTallies"),
                "uploadedAt": assert_is_date,
            },
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
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(
            b"Batch Name,Number of Ballots\n"
            b"Batch 1,200\n"
            b"Batch 2,300\n"
            b"Batch 3,400\n"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    # Tallies should be fixed
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batchTallies"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
        },
    )

    assert Jurisdiction.query.get(jurisdiction_ids[0]).batch_tallies is not None


def test_batch_tallies_template_csv_generation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids,  # pylint: disable=unused-argument
):
    for user_type, user_email in [
        (UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL),
        (UserType.JURISDICTION_ADMIN, default_ja_email(election_id)),
    ]:
        set_logged_in_user(client, user_type, user_email)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies/template-csv"
        )
        assert rv.status_code == 200
        csv_contents = rv.data.decode("utf-8")
        assert csv_contents == (
            "Batch Name,candidate 1,candidate 2,candidate 3\r\n"
            "Batch 1,0,0,0\r\n"
            "Batch 2,0,0,0\r\n"
            "Batch 3,0,0,0\r\n"
        )


def test_batch_tallies_get_upload_url_missing_file_type(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies/upload-url"
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing expected query parameter: fileType",
            }
        ]
    }


def test_batch_tallies_get_upload_url(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    allowed_users = [
        (UserType.JURISDICTION_ADMIN, default_ja_email(election_id)),
        (UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL),
    ]
    for user, email in allowed_users:
        set_logged_in_user(client, user, email)
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies/upload-url",
            query_string={"fileType": "text/csv"},
        )
        assert rv.status_code == 200

        response_data = json.loads(rv.data)
        expected_url = "/api/file-upload"

        assert response_data["url"] == expected_url
        assert response_data["fields"]["key"].startswith(
            f"audits/{election_id}/jurisdictions/{jurisdiction_ids[0]}/batch_tallies_"
        )
        assert response_data["fields"]["key"].endswith(".csv")

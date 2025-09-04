import io
import json
from typing import List
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *


def test_ballot_manifest_upload(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Name,Number of Ballots\n1,23\n12,100\n6,0\n"),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
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
    assert jurisdiction.manifest_num_batches == 3
    assert jurisdiction.manifest_num_ballots == 123
    assert len(jurisdiction.batches) == 3
    assert jurisdiction.batches[0].name == "1"
    assert jurisdiction.batches[0].num_ballots == 23
    assert jurisdiction.batches[1].name == "12"
    assert jurisdiction.batches[1].num_ballots == 100
    assert jurisdiction.batches[2].name == "6"
    assert jurisdiction.batches[2].num_ballots == 0


def test_ballot_manifest_clear(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Name,Number of Ballots\n1,23\n"),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).manifest_file_id

    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    assert json.loads(rv.data) == {"file": None, "processing": None}

    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert jurisdiction.manifest_num_batches is None
    assert jurisdiction.manifest_num_ballots is None
    assert jurisdiction.batches == []
    assert jurisdiction.manifest_file_id is None
    assert File.query.get(file_id) is None


def test_ballot_manifest_replace_as_audit_admin(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    # Check that AA can also get/put/clear manifest
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Name,Number of Ballots\n1,23\n12,100\n6,0,,\n"),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).manifest_file_id

    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Name,Number of Ballots\n1,23\n12,6\n"),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    # The old file should have been deleted
    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert File.query.get(file_id) is None
    assert jurisdiction.manifest_file_id != file_id

    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert jurisdiction.manifest_num_batches == 2
    assert jurisdiction.manifest_num_ballots == 29
    assert len(jurisdiction.batches) == 2
    assert jurisdiction.batches[0].name == "1"
    assert jurisdiction.batches[0].num_ballots == 23
    assert jurisdiction.batches[1].name == "12"
    assert jurisdiction.batches[1].num_ballots == 6

    # Now clear the manifest and check that it's deleted
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    assert json.loads(rv.data) == {"file": None, "processing": None}


def test_ballot_manifest_upload_missing_file_path(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest/upload-complete",
        json={},
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


def test_ballot_manifest_upload_batch_inventory_worksheet(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Inventory Worksheet \r\n"),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": 'You have uploaded a Batch Inventory Worksheet. Please upload a ballot manifest file exported from Step 4: "Download Audit Files".',
            },
        },
    )


def test_ballot_manifest_upload_bad_csv(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
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
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest/upload-complete",
        json={
            "storagePathKey": "test_dir/random.txt",
            "fileName": "random.txt",
            "fileType": "text/csv",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Invalid storage path",
                "errorType": "Bad Request",
            }
        ]
    }
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest/upload-complete",
        json={
            "storagePathKey": f"{get_jurisdiction_folder_path(election_id, jurisdiction_ids[0])}/{timestamp_filename('manifest', 'csv')}",
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


def test_ballot_manifest_upload_missing_field(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    for missing_field in ["Batch Name", "Number of Ballots"]:
        headers = ["Batch Name", "Number of Ballots", "Container", "Tabulator"]
        header_row = ",".join(h for h in headers if h != missing_field)

        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = upload_ballot_manifest(
            client,
            io.BytesIO(header_row.encode() + b"\n1,2,3"),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "name": asserts_startswith("manifest"),
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


def test_ballot_manifest_upload_invalid_num_ballots(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Name,Number of Ballots\n1,not a number\n"),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Expected a number in column Number of Ballots, row 2. Got: not a number.",
            },
        },
    )


def test_ballot_manifest_upload_duplicate_batch_name(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Name,Number of Ballots\n12,23\n12,100\n6,0\n"),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Each row must be uniquely identified by Batch Name. Found duplicate: 12.",
            },
        },
    )


def test_ballot_manifest_get_upload_url_missing_file_type(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest/upload-url"
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


def test_ballot_manifest_get_upload_url(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    allowed_users = [
        (UserType.JURISDICTION_ADMIN, default_ja_email(election_id)),
        (UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL),
    ]
    for user, email in allowed_users:
        set_logged_in_user(client, user, email)
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest/upload-url",
            query_string={"fileType": "text/csv"},
        )
        assert rv.status_code == 200

        response_data = json.loads(rv.data)
        expected_url = "/api/file-upload"

        assert response_data["url"] == expected_url
        assert response_data["fields"]["key"].startswith(
            f"audits/{election_id}/jurisdictions/{jurisdiction_ids[0]}/manifest_"
        )
        assert response_data["fields"]["key"].endswith(".csv")

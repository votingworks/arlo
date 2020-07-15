import io, json
from typing import List
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import (
    set_logged_in_user,
    DEFAULT_JA_EMAIL,
    UserType,
    compare_json,
    assert_is_date,
    assert_ok,
)
from ...bgcompute import bgcompute_update_ballot_manifest_file
from ...util.process_file import ProcessingStatus


def test_ballot_manifest_upload(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots,Storage Location,Tabulator\n"
                    b"1,23,Bin 2,Tabulator 1\n"
                    b"12,100,Bin 3,Tabulator 2\n"
                    b"6,0,,\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "manifest.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.READY_TO_PROCESS,
                "startedAt": None,
                "completedAt": None,
                "error": None,
            },
        },
    )

    bgcompute_update_ballot_manifest_file()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "manifest.csv", "uploadedAt": assert_is_date,},
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
    assert jurisdiction.batches[0].storage_location == "Bin 2"
    assert jurisdiction.batches[0].tabulator == "Tabulator 1"
    assert jurisdiction.batches[1].name == "12"
    assert jurisdiction.batches[1].num_ballots == 100
    assert jurisdiction.batches[1].storage_location == "Bin 3"
    assert jurisdiction.batches[1].tabulator == "Tabulator 2"
    assert jurisdiction.batches[2].name == "6"
    assert jurisdiction.batches[2].num_ballots == 0
    assert jurisdiction.batches[2].storage_location is None
    assert jurisdiction.batches[2].tabulator is None


def test_ballot_manifest_replace(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots,Storage Location,Tabulator\n"
                    b"1,23,Bin 2,Tabulator 1\n"
                    b"12,100,Bin 3,Tabulator 2\n"
                    b"6,0,,\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).manifest_file_id
    assert file_id

    bgcompute_update_ballot_manifest_file()

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots,Storage Location,Tabulator\n"
                    b"1,23,Bin 2,Tabulator 1\n"
                    b"12,6,Bin 6,Tabulator 2\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    # The old file should have been deleted
    assert File.query.get(file_id) is None

    bgcompute_update_ballot_manifest_file()

    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert jurisdiction.manifest_num_batches == 2
    assert jurisdiction.manifest_num_ballots == 29
    assert len(jurisdiction.batches) == 2
    assert jurisdiction.batches[0].name == "1"
    assert jurisdiction.batches[0].num_ballots == 23
    assert jurisdiction.batches[0].storage_location == "Bin 2"
    assert jurisdiction.batches[0].tabulator == "Tabulator 1"
    assert jurisdiction.batches[1].name == "12"
    assert jurisdiction.batches[1].num_ballots == 6
    assert jurisdiction.batches[1].storage_location == "Bin 6"
    assert jurisdiction.batches[1].tabulator == "Tabulator 2"


def test_ballot_manifest_clear(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots,Storage Location,Tabulator\n"
                    b"1,23,Bin 2,Tabulator 1\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    num_files = File.query.count()

    bgcompute_update_ballot_manifest_file()

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
    assert File.query.count() == num_files - 1


def test_ballot_manifest_upload_missing_file(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing required file parameter 'manifest'",
            }
        ]
    }


def test_ballot_manifest_upload_bad_csv(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={"manifest": (io.BytesIO(b"not a CSV file"), "random.txt")},
    )
    assert_ok(rv)

    bgcompute_update_ballot_manifest_file()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
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


def test_ballot_manifest_upload_missing_field(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    for missing_field in ["Batch Name", "Number of Ballots"]:
        headers = ["Batch Name", "Number of Ballots", "Storage Location", "Tabulator"]
        header_row = ",".join(h for h in headers if h != missing_field)

        set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
            data={
                "manifest": (
                    io.BytesIO(header_row.encode() + b"\n1,2,3"),
                    "manifest.csv",
                )
            },
        )
        assert_ok(rv)

        bgcompute_update_ballot_manifest_file()

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {"name": "manifest.csv", "uploadedAt": assert_is_date,},
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
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots,Storage Location,Tabulator\n"
                    b"1,not a number,Bin 2,Tabulator 1\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    bgcompute_update_ballot_manifest_file()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "manifest.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Expected a number in column Number of Ballots, row 1. Got: not a number.",
            },
        },
    )


def test_ballot_manifest_upload_duplicate_batch_name(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots,Storage Location,Tabulator\n"
                    b"12,23,Bin 2,Tabulator 1\n"
                    b"12,100,Bin 3,Tabulator 2\n"
                    b"6,0,,\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    bgcompute_update_ballot_manifest_file()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "manifest.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Values in column Batch Name must be unique. Found duplicate value: 12.",
            },
        },
    )

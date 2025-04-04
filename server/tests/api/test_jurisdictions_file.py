import json, io
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


def test_missing_file(client: FlaskClient, election_id: str):
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/file/upload-complete", json={}
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Missing required JSON parameter: storagePathKey",
                "errorType": "Bad Request",
            }
        ]
    }


def test_bad_csv_file(client: FlaskClient, election_id: str):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"not a CSV file"),
        election_id,
    )
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/file/upload-complete",
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
        f"/api/election/{election_id}/jurisdiction/file/upload-complete",
        json={
            "storagePathKey": f"{get_audit_folder_path(election_id)}/{timestamp_filename('participating_jurisdictions', 'csv')}",
            "fileName": "random.txt",
            "fileType": "text/plain",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Please submit a valid CSV. If you are working with an Excel spreadsheet, make sure you export it as a .csv file before uploading.",
                "errorType": "Bad Request",
            }
        ]
    }


def test_missing_one_csv_field(client, election_id):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction\nJurisdiction #1"),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/jurisdiction/file")
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("participating_jurisdictions"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Missing required column: Admin Email.",
            },
        },
    )


def test_jurisdictions_file_metadata(client, election_id):
    rv = client.get(f"/api/election/{election_id}/jurisdiction/file")
    assert json.loads(rv.data) == {"file": None, "processing": None}

    contents = "Jurisdiction,Admin Email\nJ1,ja@example.com"
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(contents.encode()),
        election_id,
    )
    assert_ok(rv)

    election = Election.query.filter_by(id=election_id).one()
    assert election.jurisdictions_file.name.startswith("participating_jurisdictions")
    assert election.jurisdictions_file.uploaded_at

    rv = client.get(f"/api/election/{election_id}/jurisdiction/file")
    response = json.loads(rv.data)
    file = response["file"]
    processing = response["processing"]
    assert file["name"].startswith("participating_jurisdictions")
    assert file["uploadedAt"]
    assert processing["status"] == ProcessingStatus.PROCESSED
    assert processing["startedAt"]
    assert processing["completedAt"]
    assert processing["error"] is None

    rv = client.get(f"/api/election/{election_id}/jurisdiction/file/csv")
    assert rv.headers["Content-Disposition"].startswith(
        'attachment; filename="participating_jurisdictions'
    )
    assert rv.data.decode("utf-8") == contents


def test_replace_jurisdictions_file(client, election_id):
    # Create the initial file.
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            b"Jurisdiction,Admin Email\n" b"J1,ja@example.com\n" b"J2,ja2@example.com"
        ),
        election_id,
    )
    assert_ok(rv)

    election = Election.query.get(election_id)
    assert {
        j.name: [ja.user.email for ja in j.jurisdiction_administrations]
        for j in election.jurisdictions
    } == {
        "J1": ["ja@example.com"],
        "J2": ["ja2@example.com"],
    }

    file_id = election.jurisdictions_file_id

    # Replace it with another file.
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            b"Jurisdiction,Admin Email\n" b"J2,ja2@example.com\n" b"J3,ja3@example.com"
        ),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/file",
    )
    assert rv.status_code == 200
    response = json.loads(rv.data)
    assert response["file"]["name"].startswith("participating_jurisdictions")

    assert File.query.get(file_id) is None, "the old file should have been deleted"

    election = Election.query.get(election_id)
    assert {
        j.name: [ja.user.email for ja in j.jurisdiction_administrations]
        for j in election.jurisdictions
    } == {
        "J2": ["ja2@example.com"],
        "J3": ["ja3@example.com"],
    }


def test_no_jurisdiction(client, election_id):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email"),
        election_id,
    )
    assert_ok(rv)

    election = Election.query.filter_by(id=election_id).one()
    assert election.jurisdictions == []


def test_single_jurisdiction_single_admin(client, election_id):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\nJ1,a1@example.com"),
        election_id,
    )
    assert_ok(rv)

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1"]

    jurisdiction = election.jurisdictions[0]
    assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
        "a1@example.com"
    ]


def test_single_jurisdiction_multiple_admins(client, election_id):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\nJ1,a1@example.com\nJ1,a2@example.com"),
        election_id,
    )
    assert_ok(rv)

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1"]

    jurisdiction = election.jurisdictions[0]
    assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
        "a1@example.com",
        "a2@example.com",
    ]


def test_multiple_jurisdictions_single_admin(client, election_id):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\nJ1,a1@example.com\nJ2,a1@example.com"),
        election_id,
    )
    assert_ok(rv)

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1", "J2"]

    for jurisdiction in election.jurisdictions:
        assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
            "a1@example.com"
        ]


def test_download_jurisdictions_file_not_found(client, election_id):
    rv = client.get(f"/api/election/{election_id}/jurisdiction/file/csv")
    assert rv.status_code == 404


def test_convert_emails_to_lowercase(client, election_id):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            b"Jurisdiction,Admin Email\n"
            b"J1,lowecase@example.com\n"
            b"J2,UPPERCASE@EXAMPLE.COM\n"
            b"J3,MiXeDcAsE@eXaMpLe.CoM\n"
        ),
        election_id,
    )
    assert_ok(rv)

    election = Election.query.filter_by(id=election_id).one()
    for jurisdiction in election.jurisdictions:
        for admin in jurisdiction.jurisdiction_administrations:
            assert admin.user.email == admin.user.email.lower()


def test_upload_jurisdictions_file_after_audit_starts(
    client: FlaskClient,
    election_id: str,
    round_1_id: str,  # pylint: disable=unused-argument
):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\n" b"J1,j1@example.com\n"),
        election_id,
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Cannot update jurisdictions after audit has started.",
            }
        ]
    }


def test_upload_jurisdictions_file_duplicate_row(
    client: FlaskClient,
    election_id: str,
):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            b"Jurisdiction,Admin Email\n" b"J1,j1@example.com\n" b"J1,j1@example.com"
        ),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/jurisdiction/file")
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("participating_jurisdictions"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Each row must be uniquely identified by ('Admin Email', 'Jurisdiction'). Found duplicate: ('j1@example.com', 'J1').",
            },
        },
    )


def test_jurisdictions_file_dont_clobber_other_elections(
    client: FlaskClient, election_id, org_id
):
    election = Election.query.get(election_id)
    db_session.expunge(election)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, user_key=DEFAULT_AA_EMAIL)
    other_election_id = create_election(
        client, audit_name="Test Audit 2", organization_id=org_id
    )

    # Add jurisdictions.
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\n" b"J1,j1@example.com\n"),
        election_id,
    )
    assert_ok(rv)

    # Add jurisdictions for other election
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\n" b"J2,j2@example.com\n"),
        other_election_id,
    )
    assert_ok(rv)

    # Now change them
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\n" b"J3,j3@example.com\n"),
        other_election_id,
    )
    assert_ok(rv)

    # Make sure first election admins were not clobbered
    assert (
        len(
            Jurisdiction.query.filter_by(election_id=election.id)
            .first()
            .jurisdiction_administrations
        )
        == 1
    )


def test_jurisdictions_file_expected_num_ballots(client: FlaskClient, election_id: str):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            b"Jurisdiction,Admin Email,Expected Number of Ballots\n"
            # If multiple rows for the same jurisdiction, the last one wins
            b"J1,a1@example.com,10\n"
            b"J1,a2@example.com,20\n"
            # Value is optional
            b"J2,a1@example.com,\n"
            # If no value in some rows for jurisdiction, the last value wins
            b"J3,a1@example.com,10\n"
            b"J3,a2@example.com,\n"
            b"J4,a1@example.com,\n"
            b"J4,a2@example.com,500\n"
        ),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert [
        (j["name"], j["expectedBallotManifestNumBallots"]) for j in jurisdictions
    ] == [("J1", 20), ("J2", None), ("J3", 10), ("J4", 500)]


def test_jurisdiction_file_get_upload_url_missing_file_type(
    client: FlaskClient, election_id: str
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, user_key=DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction/file/upload-url")
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing expected query parameter: fileType",
            }
        ]
    }


def test_jurisdiction_file_get_upload_url(client: FlaskClient, election_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, user_key=DEFAULT_AA_EMAIL)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/file/upload-url",
        query_string={"fileType": "text/csv"},
    )
    assert rv.status_code == 200

    response_data = json.loads(rv.data)
    expected_url = "/api/file-upload"

    assert response_data["url"] == expected_url
    assert response_data["fields"]["key"].startswith(
        f"audits/{election_id}/participating_jurisdictions_"
    )
    assert response_data["fields"]["key"].endswith(".csv")

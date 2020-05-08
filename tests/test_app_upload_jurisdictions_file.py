import json, io

from flask.testing import FlaskClient

from arlo_server.models import (
    Election,
    File,
    ProcessingStatus,
)
from bgcompute import bgcompute_update_election_jurisdictions_file
from tests.helpers import assert_ok


def test_missing_file(client: FlaskClient, election_id: str):
    rv = client.put(f"/election/{election_id}/jurisdiction/file")
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": 'Expected file parameter "jurisdictions" was missing',
                "errorType": "MissingFile",
            }
        ]
    }


def test_bad_csv_file(client: FlaskClient, election_id: str):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={"jurisdictions": (io.BytesIO(b"not a CSV file"), "random.txt")},
    )
    assert rv.status_code == 200

    assert bgcompute_update_election_jurisdictions_file() == 1

    rv = client.get(f"/election/{election_id}/jurisdiction/file")
    assert (
        json.loads(rv.data)["processing"]["error"]
        == "Please submit a valid CSV file with columns separated by commas."
    )


def test_missing_one_csv_field(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction\nJurisdiction #1"),
                "jurisdictions.csv",
            )
        },
    )
    assert bgcompute_update_election_jurisdictions_file() == 1

    rv = client.get(f"/election/{election_id}/jurisdiction/file")
    assert (
        json.loads(rv.data)["processing"]["error"]
        == "Missing required column: Admin Email."
    )


def test_metadata(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email\n" b"J1,ja@example.com"),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)

    election = Election.query.filter_by(id=election_id).one()
    assert election.jurisdictions_file.contents == (
        "Jurisdiction,Admin Email\n" "J1,ja@example.com"
    )
    assert election.jurisdictions_file.name == "jurisdictions.csv"
    assert election.jurisdictions_file.uploaded_at

    # Get the file data before processing.
    rv = client.get(f"/election/{election_id}/jurisdiction/file")
    response = json.loads(rv.data)
    file = response["file"]
    processing = response["processing"]
    assert file["name"] == "jurisdictions.csv"
    assert file["uploadedAt"]
    assert processing["status"] == ProcessingStatus.READY_TO_PROCESS
    assert processing["startedAt"] is None
    assert processing["completedAt"] is None
    assert processing["error"] is None

    # Actually process the file.
    assert bgcompute_update_election_jurisdictions_file() == 1

    # Now there should be data.
    rv = client.get(f"/election/{election_id}/jurisdiction/file")
    response = json.loads(rv.data)
    file = response["file"]
    processing = response["processing"]
    assert file["name"] == "jurisdictions.csv"
    assert file["uploadedAt"]
    assert processing["status"] == ProcessingStatus.PROCESSED
    assert processing["startedAt"]
    assert processing["completedAt"]
    assert processing["error"] is None

    rv = client.get(f"/election/{election_id}/jurisdiction/file/csv")
    assert (
        rv.headers["Content-Disposition"] == 'attachment; filename="jurisdictions.csv"'
    )
    assert rv.data.decode("utf-8") == election.jurisdictions_file.contents


def test_replace_jurisdictions_file(client, election_id):
    # Create the initial file.
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email\n" b"J1,ja@example.com"),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)
    assert File.query.count() == 1, "the file should exist before a response is sent"

    # Replace it with another file.
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email\n" b"J2,ja2@example.com"),
                "jurisdictions2.csv",
            )
        },
    )
    assert_ok(rv)
    assert File.query.count() == 1, "the old file should have been deleted"


def test_no_jurisdiction(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email"),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)

    # Process the file in the background.
    assert bgcompute_update_election_jurisdictions_file() == 1

    rv = client.get(f"/election/{election_id}/jurisdiction/file")
    assert (
        json.loads(rv.data)["processing"]["error"]
        == "CSV must contain at least one row after headers."
    )


def test_single_jurisdiction_single_admin(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email\nJ1,a1@example.com"),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)

    # Process the file in the background.
    assert bgcompute_update_election_jurisdictions_file() == 1

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1"]

    jurisdiction = election.jurisdictions[0]
    assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
        "a1@example.com"
    ]


def test_single_jurisdiction_multiple_admins(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    b"Jurisdiction,Admin Email\nJ1,a1@example.com\nJ1,a2@example.com"
                ),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)

    # Process the file in the background.
    assert bgcompute_update_election_jurisdictions_file() == 1

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1"]

    jurisdiction = election.jurisdictions[0]
    assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
        "a1@example.com",
        "a2@example.com",
    ]


def test_multiple_jurisdictions_single_admin(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    b"Jurisdiction,Admin Email\nJ1,a1@example.com\nJ2,a1@example.com"
                ),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)

    # Process the file in the background.
    assert bgcompute_update_election_jurisdictions_file() == 1

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1", "J2"]

    for jurisdiction in election.jurisdictions:
        assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
            "a1@example.com"
        ]


def test_download_jurisdictions_file_not_found(client, election_id):
    rv = client.get(f"/election/{election_id}/jurisdiction/file/csv")
    assert rv.status_code == 404


def test_convert_emails_to_lowercase(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    b"Jurisdiction,Admin Email\n"
                    b"J1,lowecase@example.com\n"
                    b"J2,UPPERCASE@EXAMPLE.COM\n"
                    b"J3,MiXeDcAsE@eXaMpLe.CoM\n"
                ),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)

    # Process the file in the background.
    assert bgcompute_update_election_jurisdictions_file() == 1

    election = Election.query.filter_by(id=election_id).one()
    for jurisdiction in election.jurisdictions:
        for a in jurisdiction.jurisdiction_administrations:
            assert a.user.email == a.user.email.lower()

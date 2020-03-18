import os, math, uuid
import tempfile
import json, csv, io

from flask.testing import FlaskClient
from tests.helpers import post_json
import pytest

from arlo_server import app, db
from arlo_server.models import (
    Election,
    File,
    JurisdictionAdministration,
    ProcessingStatus,
    User,
)
from bgcompute import bgcompute_update_election_jurisdictions_file


def test_missing_file(client, election_id):
    rv = client.put(f"/election/{election_id}/jurisdictions/file")
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": 'Expected file parameter "jurisdictions" was missing',
                "errorType": "MissingFile",
            }
        ]
    }


def test_bad_csv_file(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdictions/file",
        data={"jurisdictions": (io.BytesIO(b"not a CSV file"), "random.txt")},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": 'Missing required CSV field "Jurisdiction"',
                "errorType": "MissingRequiredCsvField",
                "fieldName": "Jurisdiction",
            },
            {
                "message": 'Missing required CSV field "Admin Email"',
                "errorType": "MissingRequiredCsvField",
                "fieldName": "Admin Email",
            },
        ]
    }


def test_missing_one_csv_field(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdictions/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction\nJurisdiction #1"),
                "jurisdictions.csv",
            )
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": 'Missing required CSV field "Admin Email"',
                "errorType": "MissingRequiredCsvField",
                "fieldName": "Admin Email",
            }
        ]
    }


def test_metadata(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdictions/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email"),
                "jurisdictions.csv",
            )
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"status": "ok"}

    election = Election.query.filter_by(id=election_id).one()
    assert election.jurisdictions_file.contents == "Jurisdiction,Admin Email"
    assert election.jurisdictions_file.name == "jurisdictions.csv"
    assert election.jurisdictions_file.uploaded_at

    # Get the file data before processing.
    rv = client.get(f"/election/{election_id}/jurisdictions/file")
    response = json.loads(rv.data)
    file = response["file"]
    processing = response["processing"]
    assert file["contents"] == "Jurisdiction,Admin Email"
    assert file["name"] == "jurisdictions.csv"
    assert file["uploadedAt"]
    assert processing["status"] == ProcessingStatus.READY_TO_PROCESS
    assert processing["startedAt"] == None
    assert processing["completedAt"] == None
    assert processing["error"] == None

    # Actually process the file.
    assert bgcompute_update_election_jurisdictions_file() == 1

    # Now there should be data.
    rv = client.get(f"/election/{election_id}/jurisdictions/file")
    response = json.loads(rv.data)
    file = response["file"]
    processing = response["processing"]
    assert file["contents"] == "Jurisdiction,Admin Email"
    assert file["name"] == "jurisdictions.csv"
    assert file["uploadedAt"]
    assert processing["status"] == ProcessingStatus.PROCESSED
    assert processing["startedAt"]
    assert processing["completedAt"]
    assert processing["error"] == None


def test_replace_jurisdictions_file(client, election_id):
    # Create the initial file.
    rv = client.put(
        f"/election/{election_id}/jurisdictions/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email"),
                "jurisdictions.csv",
            )
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"status": "ok"}
    assert File.query.count() == 1, "the file should exist before a response is sent"

    # Replace it with another file.
    rv = client.put(
        f"/election/{election_id}/jurisdictions/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email"),
                "jurisdictions2.csv",
            )
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"status": "ok"}
    assert File.query.count() == 1, "the old file should have been deleted"


def test_no_jurisdiction(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdictions/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email"),
                "jurisdictions.csv",
            )
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"status": "ok"}

    # Process the file in the background.
    assert bgcompute_update_election_jurisdictions_file() == 1

    election = Election.query.filter_by(id=election_id).one()
    assert election.jurisdictions == []
    assert JurisdictionAdministration.query.count() == 0
    assert User.query.count() == 0


def test_single_jurisdiction_single_admin(client, election_id):
    rv = client.put(
        f"/election/{election_id}/jurisdictions/file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email\nJ1,a1@example.com"),
                "jurisdictions.csv",
            )
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"status": "ok"}

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
        f"/election/{election_id}/jurisdictions/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    b"Jurisdiction,Admin Email\nJ1,a1@example.com\nJ1,a2@example.com"
                ),
                "jurisdictions.csv",
            )
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"status": "ok"}

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
        f"/election/{election_id}/jurisdictions/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    b"Jurisdiction,Admin Email\nJ1,a1@example.com\nJ2,a1@example.com"
                ),
                "jurisdictions.csv",
            )
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"status": "ok"}

    # Process the file in the background.
    assert bgcompute_update_election_jurisdictions_file() == 1

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1", "J2"]

    for jurisdiction in election.jurisdictions:
        assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
            "a1@example.com"
        ]

import os, math, uuid
import tempfile
import json, csv, io

from flask.testing import FlaskClient
from tests.helpers import post_json
import pytest

from models import Election, JurisdictionAdministration, User
from arlo_server import app, db


@pytest.fixture
def client() -> FlaskClient:
    app.config["TESTING"] = True
    client = app.test_client()

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield client

    db.session.commit()


def test_missing_file(client):
    rv = post_json(client, "/election/new", {})
    election_id = json.loads(rv.data)["electionId"]

    rv = client.post(f"/election/{election_id}/jurisdictions_file")
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": 'Expected file parameter "jurisdictions" was missing',
                "errorType": "MissingFile",
            }
        ]
    }


def test_bad_csv_file(client):
    rv = post_json(client, "/election/new", {})
    election_id = json.loads(rv.data)["electionId"]

    rv = client.post(
        f"/election/{election_id}/jurisdictions_file",
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


def test_missing_one_csv_field(client):
    rv = post_json(client, "/election/new", {})
    election_id = json.loads(rv.data)["electionId"]

    rv = client.post(
        f"/election/{election_id}/jurisdictions_file",
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


def test_metadata(client):
    rv = post_json(client, "/election/new", {})
    election_id = json.loads(rv.data)["electionId"]

    rv = client.post(
        f"/election/{election_id}/jurisdictions_file",
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
    assert election.jurisdictions_file == "Jurisdiction,Admin Email"
    assert election.jurisdictions_filename == "jurisdictions.csv"
    assert election.jurisdictions_file_uploaded_at

    rv = client.get(f"/election/{election_id}/jurisdictions_file")
    jurisdictions_file = json.loads(rv.data)
    assert jurisdictions_file["content"] == "Jurisdiction,Admin Email"
    assert jurisdictions_file["filename"] == "jurisdictions.csv"
    assert jurisdictions_file["uploaded_at"]


def test_no_jurisdiction(client):
    rv = post_json(client, "/election/new", {})
    election_id = json.loads(rv.data)["electionId"]

    rv = client.post(
        f"/election/{election_id}/jurisdictions_file",
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
    assert election.jurisdictions == []
    assert JurisdictionAdministration.query.count() == 0
    assert User.query.count() == 0


def test_single_jurisdiction_single_admin(client):
    rv = post_json(client, "/election/new", {})
    election_id = json.loads(rv.data)["electionId"]

    rv = client.post(
        f"/election/{election_id}/jurisdictions_file",
        data={
            "jurisdictions": (
                io.BytesIO(b"Jurisdiction,Admin Email\nJ1,a1@example.com"),
                "jurisdictions.csv",
            )
        },
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {"status": "ok"}

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1"]

    jurisdiction = election.jurisdictions[0]
    assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
        "a1@example.com"
    ]


def test_single_jurisdiction_multiple_admins(client):
    rv = post_json(client, "/election/new", {})
    election_id = json.loads(rv.data)["electionId"]

    rv = client.post(
        f"/election/{election_id}/jurisdictions_file",
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

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1"]

    jurisdiction = election.jurisdictions[0]
    assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
        "a1@example.com",
        "a2@example.com",
    ]


def test_multiple_jurisdictions_single_admin(client):
    rv = post_json(client, "/election/new", {})
    election_id = json.loads(rv.data)["electionId"]

    rv = client.post(
        f"/election/{election_id}/jurisdictions_file",
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

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1", "J2"]

    for jurisdiction in election.jurisdictions:
        assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
            "a1@example.com"
        ]

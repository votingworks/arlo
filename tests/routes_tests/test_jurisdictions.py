import pytest
from sqlalchemy.exc import SQLAlchemyError
from flask.testing import FlaskClient

import json, io
from typing import List

from helpers import compare_json, assert_is_date, asserts_startswith
from arlo_server import db
from arlo_server.models import Jurisdiction
from bgcompute import (
    bgcompute_update_election_jurisdictions_file,
    bgcompute_update_ballot_manifest_file,
)


@pytest.fixture()
def jurisdiction_ids(client: FlaskClient, election_id: str) -> List[str]:
    # We expect the list endpoint to order the jurisdictions by name, so we
    # upload them out of order.
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    b"Jurisdiction,Admin Email\n"
                    b"J2,a2@example.com\n"
                    b"J3,a3@example.com\n"
                    b"J1,a1@example.com"
                ),
                "jurisdictions.csv",
            )
        },
    )
    assert json.loads(rv.data) == {"status": "ok"}
    bgcompute_update_election_jurisdictions_file()
    jurisdictions = (
        Jurisdiction.query.filter_by(election_id=election_id)
        .order_by(Jurisdiction.name)
        .all()
    )
    assert len(jurisdictions) == 3
    yield [j.id for j in jurisdictions]


def test_jurisdictions_list_empty(client, election_id):
    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    assert jurisdictions == []


def test_jurisdictions_list_no_manifest(client, election_id, jurisdiction_ids):
    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    assert jurisdictions == [
        {
            "id": jurisdiction_ids[0],
            "name": "J1",
            "ballotManifest": {
                "file": None,
                "processing": None,
                "numBallots": None,
                "numBatches": None,
            },
        },
        {
            "id": jurisdiction_ids[1],
            "name": "J2",
            "ballotManifest": {
                "file": None,
                "processing": None,
                "numBallots": None,
                "numBatches": None,
            },
        },
        {
            "id": jurisdiction_ids[2],
            "name": "J3",
            "ballotManifest": {
                "file": None,
                "processing": None,
                "numBallots": None,
                "numBatches": None,
            },
        },
    ]


def test_jurisdictions_list_with_manifest(client, election_id, jurisdiction_ids):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n"
                    b"1,23\n"
                    b"2,101\n"
                    b"3,122\n"
                    b"4,400"
                ),
                "manifest.csv",
            )
        },
    )
    assert json.loads(rv.data) == {"status": "ok"}
    assert bgcompute_update_ballot_manifest_file() == 1

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    expected = [
        {
            "id": jurisdiction_ids[0],
            "name": "J1",
            "ballotManifest": {
                "file": {"name": "manifest.csv", "uploadedAt": assert_is_date},
                "processing": {
                    "status": "PROCESSED",
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": None,
                },
                "numBallots": 23 + 101 + 122 + 400,
                "numBatches": 4,
            },
        },
        {
            "id": jurisdiction_ids[1],
            "name": "J2",
            "ballotManifest": {
                "file": None,
                "processing": None,
                "numBallots": None,
                "numBatches": None,
            },
        },
        {
            "id": jurisdiction_ids[2],
            "name": "J3",
            "ballotManifest": {
                "file": None,
                "processing": None,
                "numBallots": None,
                "numBatches": None,
            },
        },
    ]
    compare_json(jurisdictions, expected)


def test_duplicate_batch_name(client, election_id, jurisdiction_ids):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/manifest",
        data={
            "manifest": (
                io.BytesIO(b"Batch Name,Number of Ballots\n" b"1,23\n" b"1,101\n"),
                "manifest.csv",
            )
        },
    )
    assert json.loads(rv.data) == {"status": "ok"}

    with pytest.raises(SQLAlchemyError):
        bgcompute_update_ballot_manifest_file()

    db.session.rollback()

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    expected = [
        {
            "id": jurisdiction_ids[0],
            "name": "J1",
            "ballotManifest": {
                "file": {"name": "manifest.csv", "uploadedAt": assert_is_date},
                "processing": {
                    "status": "ERRORED",
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": asserts_startswith(
                        '(psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "batch_jurisdiction_id_name_key"'
                    ),
                },
                "numBallots": None,
                "numBatches": None,
            },
        },
        {
            "id": jurisdiction_ids[1],
            "name": "J2",
            "ballotManifest": {
                "file": None,
                "processing": None,
                "numBallots": None,
                "numBatches": None,
            },
        },
        {
            "id": jurisdiction_ids[2],
            "name": "J3",
            "ballotManifest": {
                "file": None,
                "processing": None,
                "numBallots": None,
                "numBatches": None,
            },
        },
    ]
    compare_json(jurisdictions, expected)

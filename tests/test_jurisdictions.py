import pytest
from flask.testing import FlaskClient

import json, io, uuid
from typing import List

from helpers import post_json, compare_json, assert_is_date, create_org_and_admin
from arlo_server.auth import UserType
from arlo_server.models import Jurisdiction
from bgcompute import bgcompute_update_election_jurisdictions_file


@pytest.fixture()
def jurisdiction_ids(client: FlaskClient, election_id: str) -> List[str]:
    # We expect the list endpoint to order the jurisdictions by name, so we
    # upload them out of order.
    rv = client.put(
        f"/election/{election_id}/jurisdictions/file",
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
    jurisdictions = Jurisdiction.query.filter_by(election_id=election_id).all()
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
            "id": jurisdiction_ids[2],
            "name": "J1",
            "ballotManifest": {
                "filename": None,
                "numBallots": None,
                "numBatches": None,
                "uploadedAt": None,
            },
        },
        {
            "id": jurisdiction_ids[0],
            "name": "J2",
            "ballotManifest": {
                "filename": None,
                "numBallots": None,
                "numBatches": None,
                "uploadedAt": None,
            },
        },
        {
            "id": jurisdiction_ids[1],
            "name": "J3",
            "ballotManifest": {
                "filename": None,
                "numBallots": None,
                "numBatches": None,
                "uploadedAt": None,
            },
        },
    ]


def test_jurisdictions_list_with_manifest(client, election_id, jurisdiction_ids):
    rv = client.post(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[2]}/manifest",
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

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    expected = [
        {
            "id": jurisdiction_ids[2],
            "name": "J1",
            "ballotManifest": {
                "filename": "manifest.csv",
                "numBallots": 23 + 101 + 122 + 400,
                "numBatches": 4,
                "uploadedAt": assert_is_date,
            },
        },
        {
            "id": jurisdiction_ids[0],
            "name": "J2",
            "ballotManifest": {
                "filename": None,
                "numBallots": None,
                "numBatches": None,
                "uploadedAt": None,
            },
        },
        {
            "id": jurisdiction_ids[1],
            "name": "J3",
            "ballotManifest": {
                "filename": None,
                "numBallots": None,
                "numBatches": None,
                "uploadedAt": None,
            },
        },
    ]
    compare_json(jurisdictions, expected)

import io
import json
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


def test_hybrid_manifest(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["ballotManifest"]["numBallotsCvr"] is None
    assert jurisdictions[0]["ballotManifest"]["numBallotsNonCvr"] is None

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Container,Tabulator,Batch Name,Number of Ballots,CVR\n"
                    b"CONTAINER1,TABULATOR1,BATCH1,50,Y\n"
                    b"CONTAINER1,TABULATOR1,BATCH2,50,Y\n"
                    b"CONTAINER1,TABULATOR2,BATCH1,50,Y\n"
                    b"CONTAINER1,TABULATOR2,BATCH2,50,Y\n"
                    b"CONTAINER2,TABULATOR1,BATCH3,50,Y\n"
                    b"CONTAINER2,TABULATOR1,BATCH4,50,Y\n"
                    b"CONTAINER2,TABULATOR2,BATCH3,50,Y\n"
                    b"CONTAINER2,TABULATOR2,BATCH4,50,Y\n"
                    b"CONTAINER3,TABULATOR1,BATCH5,50,N\n"
                    b"CONTAINER3,TABULATOR1,BATCH6,50,N\n"
                    b"CONTAINER3,TABULATOR2,BATCH5,50,N\n"
                    b"CONTAINER3,TABULATOR2,BATCH6,50,N\n"
                    b"CONTAINER4,TABULATOR1,BATCH7,50,N\n"
                    b"CONTAINER4,TABULATOR1,BATCH8,50,N\n"
                    b"CONTAINER4,TABULATOR2,BATCH7,50,N\n"
                    b"CONTAINER4,TABULATOR2,BATCH8,50,N\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    batches = Batch.query.join(Jurisdiction).filter_by(election_id=election_id).all()
    assert all(
        batch.has_cvrs is True
        for batch in batches
        if batch.container in ["CONTAINER1", "CONTAINER2"]
    )
    assert all(
        batch.has_cvrs is False
        for batch in batches
        if batch.container in ["CONTAINER3", "CONTAINER4"]
    )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["ballotManifest"]["numBallotsCvr"] == 8 * 50
    assert jurisdictions[0]["ballotManifest"]["numBallotsNonCvr"] == 8 * 50


def test_hybrid_manifest_missing_cvr_column(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Container,Tabulator,Batch Name,Number of Ballots\n"
                    b"CONTAINER1,TABULATOR1,BATCH1,50\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "manifest.csv",
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Missing required column: CVR.",
            },
        },
    )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["ballotManifest"]["numBallotsCvr"] is None
    assert jurisdictions[0]["ballotManifest"]["numBallotsNonCvr"] is None

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Container,Tabulator,Batch Name,Number of Ballots,CVR\n"
                    b"CONTAINER1,TABULATOR1,BATCH1,50,yy\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "manifest.csv",
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Expected Y or N in column CVR, row 2. Got: yy.",
            },
        },
    )

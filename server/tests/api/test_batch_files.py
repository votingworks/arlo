import io
import json
from flask.testing import FlaskClient
from zipfile import ZipFile
import hashlib

from ...models import *  # pylint: disable=wildcard-import, unused-wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import, unused-wildcard-import


def test_start_manifests_bundle_generation(
    client: FlaskClient,
    org_id: str,
):
    # Create a batch comparison election
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    election_id = create_election(
        client,
        audit_name="Test Manifests Bundle",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
        organization_id=org_id,
    )

    # Create a single jurisdiction
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            b"Jurisdiction,Admin Email\n" b"Test County,ja@example.com\n"
        ),
        election_id,
    )
    assert_ok(rv)

    # Get the jurisdiction
    jurisdiction = Jurisdiction.query.filter_by(election_id=election_id).one()

    # Upload a manifest
    manifest_csv = b"Batch Name,Number of Ballots\nBatch 1,100\nBatch 2,200\n"
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, "ja@example.com")
    rv = upload_ballot_manifest(
        client, io.BytesIO(manifest_csv), election_id, jurisdiction.id
    )
    assert_ok(rv)

    # Start manifests bundle generation
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/batch-files/manifests-bundle")
    assert rv.status_code == 200
    
    response_data = json.loads(rv.data)
    assert "bundleId" in response_data
    assert "status" in response_data
    bundle_id = response_data["bundleId"]
    
    # In test environment, background tasks run immediately,
    # so the status should already be PROCESSED
    assert response_data["status"]["status"] == "PROCESSED"
    
    # Fetch the download URL via GET endpoint
    rv = client.get(f"/api/election/{election_id}/batch-files/bundle/{bundle_id}")
    assert rv.status_code == 200
    
    response_data = json.loads(rv.data)
    assert response_data["status"]["status"] == "PROCESSED"
    assert "downloadUrl" in response_data
    
    # Verify the bundle was created
    bundle = BatchFileBundle.query.get(bundle_id)
    assert bundle is not None
    assert bundle.bundle_type == "manifests"
    assert bundle.file is not None
    assert bundle.file.storage_path != ""


def test_start_candidate_totals_bundle_generation(
    client: FlaskClient,
    org_id: str,
):
    # Create a batch comparison election
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    election_id = create_election(
        client,
        audit_name="Test Candidate Totals Bundle",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
        organization_id=org_id,
    )

    # Create jurisdictions with files
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            b"Jurisdiction,Admin Email\n"
            b"County A,ja1@example.com\n"
            b"County B,ja2@example.com\n"
        ),
        election_id,
    )
    assert_ok(rv)

    # Set up contests
    jurisdictions = (
        Jurisdiction.query.filter_by(election_id=election_id)
        .order_by(Jurisdiction.name)
        .all()
    )
    jurisdiction_ids = [j.id for j in jurisdictions]

    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 1000},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 500},
            ],
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    # Upload manifests and batch tallies for each jurisdiction
    for jurisdiction_id in jurisdiction_ids:
        jurisdiction = Jurisdiction.query.get(jurisdiction_id)
        admin = JurisdictionAdministration.query.filter_by(
            jurisdiction_id=jurisdiction_id
        ).first()
        set_logged_in_user(client, UserType.JURISDICTION_ADMIN, admin.user.email)

        # Upload manifest
        manifest_csv = b"Batch Name,Number of Ballots\nBatch 1,100\n"
        rv = upload_ballot_manifest(
            client, io.BytesIO(manifest_csv), election_id, jurisdiction.id
        )
        assert_ok(rv)

        # Upload batch tallies
        batch_tallies_csv = (
            b"Batch Name,candidate 1,candidate 2\n"
            b"Batch 1,60,40\n"
        )
        rv = upload_batch_tallies(
            client, io.BytesIO(batch_tallies_csv), election_id, jurisdiction.id
        )
        assert_ok(rv)

    # Start candidate totals bundle generation
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(
        f"/api/election/{election_id}/batch-files/candidate-totals-bundle"
    )
    assert rv.status_code == 200
    
    response_data = json.loads(rv.data)
    bundle_id = response_data["bundleId"]
    
    # In test environment, background tasks run immediately,
    # so the status should already be PROCESSED
    assert response_data["status"]["status"] == "PROCESSED"
    
    # Fetch the download URL via GET endpoint
    rv = client.get(f"/api/election/{election_id}/batch-files/bundle/{bundle_id}")
    assert rv.status_code == 200
    
    response_data = json.loads(rv.data)
    assert response_data["status"]["status"] == "PROCESSED"
    assert "downloadUrl" in response_data
    
    # Verify the bundle
    bundle = BatchFileBundle.query.get(bundle_id)
    assert bundle is not None
    assert bundle.bundle_type == "candidate-totals"


def test_batch_files_endpoints_require_audit_admin(
    client: FlaskClient,
    election_id: str,
):
    # Test that jurisdiction admins cannot start bundle generation
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.post(
        f"/api/election/{election_id}/batch-files/candidate-totals-bundle"
    )
    assert rv.status_code == 403

    rv = client.post(f"/api/election/{election_id}/batch-files/manifests-bundle")
    assert rv.status_code == 403


def test_empty_bundle_when_no_files_uploaded(
    client: FlaskClient,
    org_id: str,
):
    # Create a batch comparison election with no files uploaded
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    election_id = create_election(
        client,
        audit_name="Test Empty Bundle",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
        organization_id=org_id,
    )

    # Create jurisdictions but don't upload files
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            b"Jurisdiction,Admin Email\n" b"County A,ja1@example.com\n"
        ),
        election_id,
    )
    assert_ok(rv)

    # Start manifests bundle generation (should work even with no files)
    rv = client.post(f"/api/election/{election_id}/batch-files/manifests-bundle")
    assert rv.status_code == 200
    
    response_data = json.loads(rv.data)
    bundle_id = response_data["bundleId"]
    
    # In test environment, background tasks run immediately,
    # so the status should already be PROCESSED
    assert response_data["status"]["status"] == "PROCESSED"

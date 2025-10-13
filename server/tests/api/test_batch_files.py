import io
from flask.testing import FlaskClient
from zipfile import ZipFile
import hashlib

from ...models import *  # pylint: disable=wildcard-import, unused-wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import, unused-wildcard-import


def test_download_manifests_bundle(
    client: FlaskClient[Any],
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

    # Download the manifests bundle
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/batch-files/manifests-bundle")
    assert rv.status_code == 200
    assert rv.content_type == "application/zip"

    # Verify the outer ZIP structure
    outer_zip = ZipFile(io.BytesIO(rv.data))
    outer_files = outer_zip.namelist()
    assert len(outer_files) == 2, f"Expected 2 files in outer ZIP, got {len(outer_files)}"

    # Find the inner ZIP and hash file
    inner_zip_files = [f for f in outer_files if f.endswith(".zip")]
    hash_files = [f for f in outer_files if f.endswith(".sha256sum")]

    assert len(inner_zip_files) == 1, "Expected exactly one .zip file"
    assert len(hash_files) == 1, "Expected exactly one .sha256sum file"

    inner_zip_name = inner_zip_files[0]
    hash_file_name = hash_files[0]

    # Verify the hash file name matches the, List zip file name
    assert hash_file_name == f"{inner_zip_name}.sha256sum"

    # Extract and verify the inner ZIP
    inner_zip_bytes = outer_zip.read(inner_zip_name)
    inner_zip = ZipFile(io.BytesIO(inner_zip_bytes))
    inner_files = inner_zip.namelist()

    # Should contain one CSV file (one jurisdiction)
    assert len(inner_files) == 1, f"Expected 1 file in inner ZIP, got {len(inner_files)}"
    # Verify it's a CSV file (using original database filename)
    assert inner_files[0].endswith(".csv"), f"Expected CSV file, got {inner_files[0]}"

    # Verify the CSV content
    csv_content = inner_zip.read(inner_files[0]).decode("utf-8")
    assert "Batch Name,Number of Ballots" in csv_content
    assert "Batch 1,100" in csv_content
    assert "Batch 2,200" in csv_content

    # Verify the hash is correct
    computed_hash = hashlib.sha256(inner_zip_bytes).hexdigest()
    hash_content = outer_zip.read(hash_file_name).decode("utf-8")
    stored_hash = hash_content.split()[0]

    assert computed_hash == stored_hash, "Hash mismatch!"
    assert inner_zip_name in hash_content, "ZIP filename not in hash file"


def test_download_candidate_totals_bundle_with_multiple_jurisdictions(
    client: FlaskClient[Any],
    org_id: str,
):
    # Create a batch comparison election
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    election_id = create_election(
        client,
        audit_name="Test Tallies Bundle",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
        organization_id=org_id,
    )

    # Create multiple jurisdictions
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            b"Jurisdiction,Admin Email\n"
            b"County A,ja1@example.com\n"
            b"County B & District,ja2@example.com\n"
            b"County #3 (Test),ja3@example.com\n"
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
        # Re-query to avoid detached instance issues
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

        # Upload batch tallies (no Contest 1 column in header, since we only upload candidate counts)
        batch_tallies_csv = (
            b"Batch Name,candidate 1,candidate 2\n"
            b"Batch 1,60,40\n"
        )
        rv = upload_batch_tallies(
            client, io.BytesIO(batch_tallies_csv), election_id, jurisdiction.id
        )
        assert_ok(rv)

    # Download the candidate totals bundle
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(
        f"/api/election/{election_id}/batch-files/candidate-totals-bundle"
    )
    assert rv.status_code == 200
    assert rv.content_type == "application/zip"

    # Verify the outer ZIP structure
    outer_zip = ZipFile(io.BytesIO(rv.data))
    outer_files = outer_zip.namelist()
    assert len(outer_files) == 2

    # Find the inner ZIP and hash file
    inner_zip_name = [f for f in outer_files if f.endswith(".zip")][0]
    hash_file_name = [f for f in outer_files if f.endswith(".sha256sum")][0]

    # Extract and verify the inner ZIP
    inner_zip_bytes = outer_zip.read(inner_zip_name)
    inner_zip = ZipFile(io.BytesIO(inner_zip_bytes))
    inner_files = inner_zip.namelist()

    # Should contain three CSV files (three jurisdictions)
    assert len(inner_files) == 3, f"Expected 3 files, got {len(inner_files)}"

    # Verify all files are CSVs (using original database filenames)
    for filename in inner_files:
        assert filename.endswith(".csv"), f"Expected CSV file, got {filename}"

    # Verify one of the CSV contents (just pick the first one)
    csv_content = inner_zip.read(inner_files[0]).decode("utf-8")
    assert "Batch Name" in csv_content
    assert "candidate 1" in csv_content
    assert "candidate 2" in csv_content
    assert "Batch 1" in csv_content
    assert "60,40" in csv_content

    # Verify the hash
    computed_hash = hashlib.sha256(inner_zip_bytes).hexdigest()
    hash_content = outer_zip.read(hash_file_name).decode("utf-8")
    stored_hash = hash_content.split()[0]
    assert computed_hash == stored_hash


def test_batch_files_endpoints_require_audit_admin(
    client: FlaskClient[Any],
    election_id: str,
):
    # Test that jurisdiction admins cannot download bundles
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/batch-files/candidate-totals-bundle"
    )
    assert rv.status_code == 403

    rv = client.get(f"/api/election/{election_id}/batch-files/manifests-bundle")
    assert rv.status_code == 403


def test_empty_bundle_when_no_files_uploaded(
    client: FlaskClient[Any],
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

    # Create jurisdictions but don't upload any files
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\nTest County,ja@example.com\n"),
        election_id,
    )
    assert_ok(rv)

    # Try to download manifests bundle (should work but inner ZIP will be empty)
    rv = client.get(f"/api/election/{election_id}/batch-files/manifests-bundle")
    assert rv.status_code == 200

    # Verify the bundle structure (should still have outer ZIP with empty inner ZIP + hash)
    outer_zip = ZipFile(io.BytesIO(rv.data))
    outer_files = outer_zip.namelist()
    assert len(outer_files) == 2

    inner_zip_name = [f for f in outer_files if f.endswith(".zip")][0]
    inner_zip_bytes = outer_zip.read(inner_zip_name)
    inner_zip = ZipFile(io.BytesIO(inner_zip_bytes))

    # Inner ZIP should be empty
    assert len(inner_zip.namelist()) == 0

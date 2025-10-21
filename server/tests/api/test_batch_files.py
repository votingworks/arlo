import io
import json
from flask.testing import FlaskClient
from zipfile import ZipFile
from unittest.mock import patch, MagicMock

from ...models import *  # pylint: disable=wildcard-import, unused-wildcard-import
from ...util.file import retrieve_file
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
        io.BytesIO(b"Jurisdiction,Admin Email\nTest County,ja@example.com\n"),
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

    # Verify the inner ZIP has the correct directory structure
    # Download and inspect the generated ZIP file
    with retrieve_file(bundle.file) as outer_zip_io:
        with ZipFile(outer_zip_io, "r") as outer_zip:
            # Get the inner ZIP file (not the hash file)
            inner_zip_name = [
                name for name in outer_zip.namelist() if name.endswith(".zip")
            ][0]

            # Extract and open the inner ZIP
            inner_zip_data = outer_zip.read(inner_zip_name)
            inner_zip_io = io.BytesIO(inner_zip_data)

            with ZipFile(inner_zip_io, "r") as inner_zip:
                # Verify files are in jurisdiction directories
                file_list = inner_zip.namelist()
                assert len(file_list) == 1  # One manifest file

                # Should be in format: {cleaned-jurisdiction-name}/{original-filename}
                assert file_list[0].startswith("Test-County/")
                assert file_list[0].endswith(".csv")


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
        batch_tallies_csv = b"Batch Name,candidate 1,candidate 2\nBatch 1,60,40\n"
        rv = upload_batch_tallies(
            client, io.BytesIO(batch_tallies_csv), election_id, jurisdiction.id
        )
        assert_ok(rv)

    # Start candidate totals bundle generation
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/batch-files/candidate-totals-bundle")
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

    # Verify the inner ZIP has the correct directory structure
    with retrieve_file(bundle.file) as outer_zip_io:
        with ZipFile(outer_zip_io, "r") as outer_zip:
            # Get the inner ZIP file
            inner_zip_name = [
                name for name in outer_zip.namelist() if name.endswith(".zip")
            ][0]

            # Extract and open the inner ZIP
            inner_zip_data = outer_zip.read(inner_zip_name)
            inner_zip_io = io.BytesIO(inner_zip_data)

            with ZipFile(inner_zip_io, "r") as inner_zip:
                # Verify files are in jurisdiction directories
                file_list = inner_zip.namelist()
                assert len(file_list) == 2  # Two jurisdictions with batch tallies

                # Files should be in format: {cleaned-jurisdiction-name}/{original-filename}
                # Jurisdictions are "County A" and "County B" -> "County-A", "County-B"
                county_a_files = [f for f in file_list if f.startswith("County-A/")]
                county_b_files = [f for f in file_list if f.startswith("County-B/")]

                assert len(county_a_files) == 1
                assert len(county_b_files) == 1
                assert county_a_files[0].endswith(".csv")
                assert county_b_files[0].endswith(".csv")


def test_batch_files_endpoints_require_audit_admin(
    client: FlaskClient,
    election_id: str,
):
    # Test that jurisdiction admins cannot start bundle generation
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.post(f"/api/election/{election_id}/batch-files/candidate-totals-bundle")
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
        io.BytesIO(b"Jurisdiction,Admin Email\nCounty A,ja1@example.com\n"),
        election_id,
    )
    assert_ok(rv)

    # Start manifests bundle generation (should work even with no files)
    rv = client.post(f"/api/election/{election_id}/batch-files/manifests-bundle")
    assert rv.status_code == 200

    response_data = json.loads(rv.data)
    bundle_id = response_data["bundleId"]
    assert bundle_id is not None

    # In test environment, background tasks run immediately,
    # so the status should already be PROCESSED
    assert response_data["status"]["status"] == "PROCESSED"


def test_bundle_status_with_error(
    client: FlaskClient,
    org_id: str,
):
    # Create a batch comparison election
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    election_id = create_election(
        client,
        audit_name="Test Bundle Error",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
        organization_id=org_id,
    )

    # Create a jurisdiction and upload manifest
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\nTest County,ja@example.com\n"),
        election_id,
    )
    assert_ok(rv)

    jurisdiction = Jurisdiction.query.filter_by(election_id=election_id).one()
    manifest_csv = b"Batch Name,Number of Ballots\nBatch 1,100\n"
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
    bundle_id = response_data["bundleId"]

    # Manually set an error on the task to test error path
    bundle = BatchFileBundle.query.get(bundle_id)
    bundle.file.task.error = "Test error message"
    db_session.commit()

    # Fetch the bundle status
    rv = client.get(f"/api/election/{election_id}/batch-files/bundle/{bundle_id}")
    assert rv.status_code == 200

    response_data = json.loads(rv.data)
    assert response_data["error"] == "Test error message"


def test_direct_download_endpoint(
    client: FlaskClient,
    org_id: str,
):
    # Create a batch comparison election
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    election_id = create_election(
        client,
        audit_name="Test Direct Download",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
        organization_id=org_id,
    )

    # Create a jurisdiction and upload manifest
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\nTest County,ja@example.com\n"),
        election_id,
    )
    assert_ok(rv)

    jurisdiction = Jurisdiction.query.filter_by(election_id=election_id).one()
    manifest_csv = b"Batch Name,Number of Ballots\nBatch 1,100\n"
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
    bundle_id = response_data["bundleId"]

    # Test direct download endpoint
    rv = client.get(
        f"/api/election/{election_id}/batch-files/bundle/{bundle_id}/download"
    )
    assert rv.status_code == 200
    # For local storage, should serve the file directly
    assert rv.mimetype == "application/zip"


def test_download_endpoint_bundle_not_found(
    client: FlaskClient,
    election_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    fake_bundle_id = str(uuid.uuid4())

    rv = client.get(
        f"/api/election/{election_id}/batch-files/bundle/{fake_bundle_id}/download"
    )
    assert rv.status_code == 404
    assert json.loads(rv.data)["error"] == "Bundle not found"


def test_s3_presigned_url_generation(
    client: FlaskClient,
    org_id: str,
):
    """Test S3 presigned URL generation for existing bundles"""
    # Create a batch comparison election (using local storage first)
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    election_id = create_election(
        client,
        audit_name="Test S3 URLs",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
        organization_id=org_id,
    )

    # Create a jurisdiction and upload manifest
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\nTest County,ja@example.com\n"),
        election_id,
    )
    assert_ok(rv)

    jurisdiction = Jurisdiction.query.filter_by(election_id=election_id).one()
    manifest_csv = b"Batch Name,Number of Ballots\nBatch 1,100\n"
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, "ja@example.com")
    rv = upload_ballot_manifest(
        client, io.BytesIO(manifest_csv), election_id, jurisdiction.id
    )
    assert_ok(rv)

    # Start manifests bundle generation (will use local storage)
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/batch-files/manifests-bundle")
    assert rv.status_code == 200

    response_data = json.loads(rv.data)
    bundle_id = response_data["bundleId"]

    # Now manually update the bundle's storage path to simulate S3 storage
    # This allows us to test the presigned URL generation without actually using S3
    bundle = BatchFileBundle.query.get(bundle_id)
    bundle.file.storage_path = "s3://test-bucket/audits/test/manifests_bundle.zip"
    from ...database import db_session

    db_session.commit()

    # Mock S3 client for presigned URL generation
    with (
        patch(
            "server.api.batch_files.config.FILE_UPLOAD_STORAGE_PATH", "s3://test-bucket"
        ),
        patch("server.api.batch_files.s3") as mock_s3,
    ):
        mock_s3_instance = MagicMock()
        mock_s3.return_value = mock_s3_instance
        mock_s3_instance.generate_presigned_url.return_value = (
            "https://s3.example.com/presigned-url"
        )

        # Fetch the bundle status - should generate presigned URL
        rv = client.get(f"/api/election/{election_id}/batch-files/bundle/{bundle_id}")
        assert rv.status_code == 200

        response_data = json.loads(rv.data)
        assert "downloadUrl" in response_data
        assert response_data["downloadUrl"] == "https://s3.example.com/presigned-url"

        # Verify generate_presigned_url was called with correct params
        mock_s3_instance.generate_presigned_url.assert_called_once()
        presigned_call_args = mock_s3_instance.generate_presigned_url.call_args
        assert presigned_call_args[0][0] == "get_object"
        assert presigned_call_args[1]["Params"]["Bucket"] == "test-bucket"
        assert (
            presigned_call_args[1]["Params"]["Key"]
            == "audits/test/manifests_bundle.zip"
        )
        assert presigned_call_args[1]["ExpiresIn"] == 3600

        # Test download endpoint with S3 - should return presigned URL
        mock_s3_instance.generate_presigned_url.reset_mock()
        mock_s3_instance.generate_presigned_url.return_value = (
            "https://s3.example.com/presigned-url-2"
        )

        rv = client.get(
            f"/api/election/{election_id}/batch-files/bundle/{bundle_id}/download"
        )
        assert rv.status_code == 200
        response_data = json.loads(rv.data)
        assert response_data["downloadUrl"] == "https://s3.example.com/presigned-url-2"


def test_s3_upload_function():
    """Test the S3 upload path in _upload_bundle_file"""
    import tempfile
    import os
    from ...api.batch_files import _upload_bundle_file

    # Create a temporary file to upload
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".zip") as f:
        f.write(b"test bundle content")
        temp_file_path = f.name

    try:
        with (
            patch(
                "server.api.batch_files.config.FILE_UPLOAD_STORAGE_PATH",
                "s3://test-bucket",
            ),
            patch("server.api.batch_files.s3") as mock_s3,
            patch("server.api.batch_files.get_full_storage_path") as mock_get_full,
        ):
            mock_s3_instance = MagicMock()
            mock_s3.return_value = mock_s3_instance
            mock_get_full.return_value = (
                "s3://test-bucket/audits/test-election/batch-files/test.zip"
            )

            # Call the function
            result_path = _upload_bundle_file(
                temp_file_path, "test-bundle.zip", "test-election-id"
            )

            # Verify S3 put_object was called
            mock_s3_instance.put_object.assert_called_once()
            call_args = mock_s3_instance.put_object.call_args

            assert call_args[1]["Bucket"] == "test-bucket"
            assert call_args[1]["ContentType"] == "application/zip"
            assert "Expires" in call_args[1]
            assert "Body" in call_args[1]

            # Verify the key structure
            key = call_args[1]["Key"]
            assert "batch-files" in key
            assert "test-bundle.zip" in key

            # Verify return value
            assert (
                result_path
                == "s3://test-bucket/audits/test-election/batch-files/test.zip"
            )
    finally:
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

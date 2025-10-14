import tempfile
import shutil
import hashlib
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, IO
from urllib.parse import urlparse
from flask import jsonify

from . import api
from ..auth import restrict_access, UserType
from ..models import Election, Jurisdiction, File, BatchFileBundle
from ..database import db_session
from ..util.file import (
    retrieve_file_to_buffer,
    zip_files,
    s3,
    get_full_storage_path,
    get_audit_folder_path,
    serialize_file_processing,
)
from ..util.csv_download import election_timestamp_name
from ..util.isoformat import isoformat
from ..worker.tasks import background_task, create_background_task, UserError
from .. import config


@api.route(
    "/election/<election_id>/batch-files/candidate-totals-bundle",
    methods=["POST"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def start_candidate_totals_bundle_generation(election: Election):
    """
    Starts background task to generate candidate totals bundle.
    Returns the bundle ID for status checking.
    """
    bundle = BatchFileBundle(
        id=str(uuid.uuid4()),
        election_id=election.id,
        bundle_type="candidate-totals",
    )
    db_session.add(bundle)

    # Create a File record that will be populated by the background task
    bundle.file = File(
        id=str(uuid.uuid4()),
        name=f"candidate_totals_{isoformat(datetime.now(timezone.utc))}.zip",
        storage_path="",  # Will be set by background task
        uploaded_at=datetime.now(timezone.utc),
    )

    bundle.file.task = create_background_task(
        generate_batch_files_bundle,
        dict(
            election_id=election.id,
            bundle_id=bundle.id,
            bundle_type="candidate-totals",
        ),
    )

    db_session.commit()

    return jsonify(
        {
            "bundleId": bundle.id,
            "status": serialize_file_processing(bundle.file),
        }
    )


@api.route(
    "/election/<election_id>/batch-files/manifests-bundle",
    methods=["POST"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def start_manifests_bundle_generation(election: Election):
    """
    Starts background task to generate manifests bundle.
    Returns the bundle ID for status checking.
    """
    bundle = BatchFileBundle(
        id=str(uuid.uuid4()),
        election_id=election.id,
        bundle_type="manifests",
    )
    db_session.add(bundle)

    # Create a File record that will be populated by the background task
    bundle.file = File(
        id=str(uuid.uuid4()),
        name=f"manifests_{isoformat(datetime.now(timezone.utc))}.zip",
        storage_path="",  # Will be set by background task
        uploaded_at=datetime.now(timezone.utc),
    )

    bundle.file.task = create_background_task(
        generate_batch_files_bundle,
        dict(
            election_id=election.id,
            bundle_id=bundle.id,
            bundle_type="manifests",
        ),
    )

    db_session.commit()

    return jsonify(
        {
            "bundleId": bundle.id,
            "status": serialize_file_processing(bundle.file),
        }
    )


@api.route(
    "/election/<election_id>/batch-files/bundle/<bundle_id>",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def get_batch_files_bundle_status(election: Election, bundle_id: str):
    """
    Gets the status of a batch files bundle generation task.
    Returns download URL when ready.
    """
    bundle = BatchFileBundle.query.filter_by(
        id=bundle_id, election_id=election.id
    ).first()

    if not bundle:
        return jsonify({"error": "Bundle not found"}), 404

    status = serialize_file_processing(bundle.file)

    response = {
        "bundleId": bundle.id,
        "bundleType": bundle.bundle_type,
        "status": status,
    }

    # If completed successfully, include download URL
    if bundle.file and bundle.file.task and bundle.file.task.completed_at:
        if bundle.file.task.error:
            response["error"] = bundle.file.task.error
        else:
            # Generate presigned URL for download
            response["downloadUrl"] = _get_bundle_download_url(bundle)

    return jsonify(response)


def _get_bundle_download_url(bundle: BatchFileBundle) -> str:
    """Generate a presigned URL for downloading the bundle from S3."""
    if not bundle.file or not bundle.file.storage_path:
        raise UserError("Bundle file not available")

    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        parsed_path = urlparse(bundle.file.storage_path)
        bucket_name = parsed_path.netloc
        key = parsed_path.path[1:]

        # Generate presigned URL valid for 1 hour
        url = s3().generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=3600,  # 1 hour
        )
        return url
    else:
        # For local storage, return API endpoint
        return f"/api/election/{bundle.election_id}/batch-files/bundle/{bundle.id}/download"


@api.route(
    "/election/<election_id>/batch-files/bundle/<bundle_id>/download",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def download_batch_files_bundle(election: Election, bundle_id: str):
    """
    Direct download endpoint for local file storage.
    For S3 storage, presigned URLs are used instead.
    """
    bundle = BatchFileBundle.query.filter_by(
        id=bundle_id, election_id=election.id
    ).first()

    if not bundle or not bundle.file:
        return jsonify({"error": "Bundle not found"}), 404

    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        # For S3, redirect to presigned URL
        return jsonify({"downloadUrl": _get_bundle_download_url(bundle)})
    else:
        # For local storage, serve the file directly
        from flask import send_file

        return send_file(
            bundle.file.storage_path,
            as_attachment=True,
            download_name=bundle.file.name,
            mimetype="application/zip",
        )


@background_task
def generate_batch_files_bundle(
    election_id: str, bundle_id: str, bundle_type: str
):
    """
    Background task to generate a batch files bundle (manifests or candidate totals).
    Creates a nested ZIP structure with hash file and uploads to S3 with expiration.
    """
    election = Election.query.get(election_id)
    bundle = BatchFileBundle.query.get(bundle_id)

    if not election or not bundle:
        raise UserError("Election or bundle not found")

    # Create temporary directory for all our work
    temp_dir = tempfile.mkdtemp()

    try:
        # Map bundle type to file attribute name
        if bundle_type == "candidate-totals":
            file_attr = "batch_tallies_file"
            filter_condition = Jurisdiction.batch_tallies_file_id.isnot(None)
        else:  # manifests
            file_attr = "manifest_file"
            filter_condition = Jurisdiction.manifest_file_id.isnot(None)

        # Get jurisdictions with the appropriate files
        jurisdictions = (
            Jurisdiction.query.filter_by(election_id=election.id)
            .filter(filter_condition)
            .order_by(Jurisdiction.name)
            .all()
        )

        # Step 1: Retrieve all jurisdiction files
        jurisdiction_files: Dict[str, IO[bytes]] = {}
        temp_file_handles = []

        for jurisdiction in jurisdictions:
            source_file = getattr(jurisdiction, file_attr)
            if source_file is None:
                continue

            # Retrieve the file content
            file_handle = retrieve_file_to_buffer(source_file, temp_dir)

            # Use the original filename from the database
            filename = source_file.name
            jurisdiction_files[filename] = file_handle
            temp_file_handles.append(file_handle)

        # Step 2: Create inner ZIP
        inner_zip_io = zip_files(jurisdiction_files)

        # Close individual file handles
        for handle in temp_file_handles:
            handle.close()

        # Step 3: Write inner ZIP to temp file and compute hash
        base_name = election_timestamp_name(election)
        inner_zip_filename = f"{base_name}-{bundle_type}.zip"
        inner_zip_path = os.path.join(temp_dir, inner_zip_filename)

        with open(inner_zip_path, "wb") as f:
            inner_zip_io.seek(0)
            shutil.copyfileobj(inner_zip_io, f)

        inner_zip_io.close()

        # Step 4: Compute SHA256 hash
        hash_obj = hashlib.sha256()
        with open(inner_zip_path, "rb") as f:
            while True:
                chunk = f.read(65536)  # 64KB chunks
                if not chunk:
                    break
                hash_obj.update(chunk)

        hash_value = hash_obj.hexdigest()

        # Step 5: Create hash file
        hash_filename = f"{inner_zip_filename}.sha256sum"
        hash_path = os.path.join(temp_dir, hash_filename)

        with open(hash_path, "w") as f:
            f.write(f"{hash_value}  {inner_zip_filename}\n")

        # Step 6: Create outer ZIP containing inner ZIP and hash file
        outer_filename = f"{base_name}-{bundle_type}_bundle.zip"
        outer_zip_path = os.path.join(temp_dir, outer_filename)

        with open(inner_zip_path, "rb") as inner_f, open(
            hash_path, "rb"
        ) as hash_f:
            outer_zip_io = zip_files(
                {
                    inner_zip_filename: inner_f,
                    hash_filename: hash_f,
                }
            )

        with open(outer_zip_path, "wb") as f:
            outer_zip_io.seek(0)
            shutil.copyfileobj(outer_zip_io, f)

        outer_zip_io.close()

        # Step 7: Upload to S3 or local storage
        storage_path = _upload_bundle_file(
            outer_zip_path, outer_filename, election_id
        )

        # Step 8: Update the File record with the storage path
        bundle.file.storage_path = storage_path
        db_session.commit()

    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass  # Best effort cleanup


def _upload_bundle_file(
    file_path: str, filename: str, election_id: str
) -> str:
    """
    Uploads the bundle file to S3 with expiration or local storage.
    Returns the storage path.
    """
    storage_prefix = f"{get_audit_folder_path(election_id)}/batch-files"
    storage_path_relative = f"{storage_prefix}/{filename}"

    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        # Upload to S3 with expiration
        bucket_name = urlparse(config.FILE_UPLOAD_STORAGE_PATH).netloc
        key = storage_path_relative

        # Set expiration to 24 hours from now
        expiration_time = datetime.now(timezone.utc) + timedelta(hours=24)

        with open(file_path, "rb") as f:
            s3().put_object(
                Bucket=bucket_name,
                Key=key,
                Body=f,
                ContentType="application/zip",
                Expires=expiration_time,
            )

        return get_full_storage_path(storage_path_relative)
    else:
        # Local storage
        full_path = get_full_storage_path(storage_path_relative)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        shutil.copy2(file_path, full_path)
        return full_path

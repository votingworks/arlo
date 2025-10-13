import tempfile
import shutil
import hashlib
import os
from typing import IO
from flask import Response, send_file

from . import api
from ..auth import restrict_access, UserType
from ..models import Election, Jurisdiction
from ..util.file import retrieve_file_to_buffer, zip_files
from ..util.csv_download import election_timestamp_name


@api.route(
    "/election/<election_id>/batch-files/candidate-totals-bundle",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def download_candidate_totals_bundle(election: Election):
    """
    Downloads a ZIP bundle containing:
    - candidate_totals_[timestamp].zip (inner ZIP with all jurisdiction files)
    - candidate_totals_[timestamp].zip.sha256sum (hash of inner ZIP)
    """
    return _download_batch_files_bundle(election, "candidate-totals")


@api.route(
    "/election/<election_id>/batch-files/manifests-bundle",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def download_manifests_bundle(election: Election):
    """
    Downloads a ZIP bundle containing:
    - manifests_[timestamp].zip (inner ZIP with all jurisdiction files)
    - manifests_[timestamp].zip.sha256sum (hash of inner ZIP)
    """
    return _download_batch_files_bundle(election, "manifests")


def _download_batch_files_bundle(election: Election, file_type: str) -> Response:
    """
    Creates a bundle ZIP containing:
    1. An inner ZIP with all jurisdiction files
    2. A .sha256sum file with the hash of the inner ZIP

    Uses temporary files for processing and ensures cleanup.
    """
    # Create temporary directory for all our work
    temp_dir = tempfile.mkdtemp()

    try:
        # Get jurisdictions with the appropriate files
        query = Jurisdiction.query.filter_by(election_id=election.id)

        if file_type == "candidate-totals":
            query = query.filter(Jurisdiction.batch_tallies_file_id.isnot(None))
        else:  # manifests
            query = query.filter(Jurisdiction.manifest_file_id.isnot(None))

        jurisdictions = query.order_by(Jurisdiction.name).all()

        # Step 1: Retrieve all jurisdiction files to temp directory
        # and prepare them for the inner ZIP
        jurisdiction_files: dict[str, IO[bytes]] = {}
        temp_file_handles: list[IO[bytes]] = []  # Keep track for cleanup

        for jurisdiction in jurisdictions:
            # Get the file from the jurisdiction
            # Map the file_type parameter to the actual model attribute
            file_attr = "batch_tallies_file" if file_type == "candidate-totals" else "manifest_file"
            source_file = getattr(jurisdiction, file_attr)
            if source_file is None:
                continue

            # Retrieve the file content
            file_handle = retrieve_file_to_buffer(source_file, temp_dir)
            
            # Use the original filename from the database
            filename = source_file.name
            jurisdiction_files[filename] = file_handle
            temp_file_handles.append(file_handle)

        # Step 2: Create inner ZIP using existing zip_files helper
        inner_zip_io = zip_files(jurisdiction_files)

        # Close individual file handles (they've been copied into the ZIP)
        for handle in temp_file_handles:
            handle.close()

        # Step 3: Write inner ZIP to temp file so we can compute hash
        timestamp = election_timestamp_name(election)
        inner_zip_filename = f"{file_type}_{timestamp}.zip"

        inner_zip_path = os.path.join(temp_dir, inner_zip_filename)
        with open(inner_zip_path, "wb") as f:
            shutil.copyfileobj(inner_zip_io, f)
        inner_zip_io.close()

        # Step 4: Compute SHA256 hash of inner ZIP
        hasher = hashlib.sha256()
        with open(inner_zip_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                hasher.update(chunk)
        hash_hex = hasher.hexdigest()

        # Step 5: Create hash file
        hash_filename = f"{inner_zip_filename}.sha256sum"
        hash_path = os.path.join(temp_dir, hash_filename)
        with open(hash_path, "w") as f:
            _ = f.write(f"{hash_hex}  {inner_zip_filename}\n")

        # Step 6: Create outer ZIP with both files
        outer_zip_files: dict[str, IO[bytes]] = {
            inner_zip_filename: open(inner_zip_path, "rb"),
            hash_filename: open(hash_path, "rb"),
        }

        outer_zip_io = zip_files(outer_zip_files)

        # Close the file handles we opened for outer ZIP
        for handle in outer_zip_files.values():
            handle.close()

        # Step 7: Write outer ZIP to final temp file for sending
        outer_filename = f"{file_type}_bundle_{timestamp}.zip"
        outer_zip_path = os.path.join(temp_dir, outer_filename)
        with open(outer_zip_path, "wb") as f:
            shutil.copyfileobj(outer_zip_io, f)
        outer_zip_io.close()

        # Step 8: Send the file
        # Register cleanup callback to remove temp directory after response is sent
        response: Response = send_file(
            outer_zip_path,
            as_attachment=True,
            download_name=outer_filename,
            mimetype="application/zip",
        )

        @response.call_on_close
        def cleanup():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass  # Best effort cleanup

        return response

    except Exception:
        # Clean up on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

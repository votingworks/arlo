from datetime import datetime
import shutil
import io
import os
import re
import tempfile
from typing import BinaryIO, IO, List, Mapping, Optional, Dict, Any, Tuple
from urllib.parse import urlparse
from zipfile import ZipFile
from werkzeug.exceptions import BadRequest
import boto3
from flask import Request

from .. import config
from ..models import *  # pylint: disable=wildcard-import
from ..worker.tasks import serialize_background_task
from ..util.isoformat import isoformat
from ..util.jsonschema import JSONDict
from ..util.csv_parse import is_filetype_csv_mimetype


class FileType(str, enum.Enum):
    CSV = "csv"
    ZIP = "zip"
    XML = "xml"


def serialize_file(file: Optional[File]) -> Optional[JSONDict]:
    if file is None:
        return None

    return {
        "name": file.name,
        "uploadedAt": isoformat(file.uploaded_at),
    }


def serialize_file_processing(file: Optional[File]) -> Optional[JSONDict]:
    if file is None:
        return None

    return serialize_background_task(file.task)


def timestamp_filename(prefix: str, extension: str) -> str:
    return f"{prefix}_{isoformat(datetime.now(timezone.utc))}.{extension}"


def s3():  # pylint: disable=invalid-name
    return boto3.client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        region_name=config.AWS_DEFAULT_REGION,
    )


def store_file(file: IO[bytes], storage_path: str) -> str:
    assert not os.path.isabs(storage_path)
    full_path = get_full_storage_path(storage_path)
    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        raise Exception("This method should only be used for local file storage.")
    else:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as system_file:
            shutil.copyfileobj(file, system_file)
    return full_path


def retrieve_file(storage_path: str) -> BinaryIO:
    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        assert storage_path.startswith(config.FILE_UPLOAD_STORAGE_PATH)
        parsed_path = urlparse(storage_path)
        bucket_name = parsed_path.netloc
        key = parsed_path.path[1:]
        file = io.BytesIO()
        s3().download_fileobj(bucket_name, key, file)
        file.seek(0)
        return file
    else:
        return open(storage_path, "rb")


# Similar functionality to retrieve_file expect when retrieving s3 files they are streamed
# to a temporary file on disk to avoid loading the file in memory. Should be used for large file retrieval
# The caller of this function is repsonsible for making sure that the working_directory is cleaned up and removed.
def retrieve_file_to_buffer(storage_path: str, working_directory: str) -> BinaryIO:
    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        assert storage_path.startswith(config.FILE_UPLOAD_STORAGE_PATH)
        parsed_path = urlparse(storage_path)
        bucket_name = parsed_path.netloc
        key = parsed_path.path[1:]
        with tempfile.NamedTemporaryFile(
            dir=working_directory, delete=False
        ) as temp_file:
            s3().download_fileobj(bucket_name, key, temp_file)
            temp_file_path = temp_file.name
        # reopen the file to have a read only pointer
        return open(temp_file_path, "rb")
    else:
        return open(storage_path, "rb")


def delete_file(storage_path: str):
    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        assert storage_path.startswith("s3://")
        parsed_path = urlparse(storage_path)
        bucket_name = parsed_path.netloc
        key = parsed_path.path[1:]
        s3().delete_object(Bucket=bucket_name, Key=key)
    else:
        os.remove(storage_path)


def zip_files(files: Mapping[str, IO[bytes]]) -> IO[bytes]:
    zip_file = tempfile.TemporaryFile()
    with ZipFile(zip_file, "w") as zip_archive:
        for file_name, contents_stream in files.items():
            with zip_archive.open(file_name, "w") as archive_file:
                shutil.copyfileobj(contents_stream, archive_file)
    zip_file.seek(0)
    return zip_file


def read_zip_filenames(zip_file: BinaryIO) -> List[str]:
    with ZipFile(zip_file, "r") as zip_archive:
        return [
            entry_name
            for entry_name in zip_archive.namelist()
            # ZIP files created on Macs include a hidden __MACOSX folder
            if not entry_name.startswith("__") and not entry_name.startswith(".")
        ]


# Extracts the contents of the provided zip file to the specified directory and returns the list of
# extracted file names
def unzip_files(zip_file: BinaryIO, directory_to_extract_to: str) -> List[str]:
    with ZipFile(zip_file, "r") as zip_archive:
        zip_archive.extractall(directory_to_extract_to)
        return [
            entry_name
            for entry_name in zip_archive.namelist()
            # ZIP files created on Macs include a hidden __MACOSX folder
            if not entry_name.startswith("__") and not entry_name.startswith(".")
        ]


def get_full_storage_path(file_path: str) -> str:
    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        bucket_name = urlparse(config.FILE_UPLOAD_STORAGE_PATH).netloc
        return f"s3://{bucket_name}/{file_path}"
    else:
        full_path = os.path.normpath(
            os.path.join(config.FILE_UPLOAD_STORAGE_PATH, file_path)
        )
        storage_root = os.path.realpath(config.FILE_UPLOAD_STORAGE_PATH)
        full_path = os.path.realpath(
            os.path.normpath(os.path.join(storage_root, file_path))
        )
        if os.path.commonpath([full_path, storage_root]) != storage_root:
            raise BadRequest("Invalid storage path")
        return full_path


def get_file_upload_url(
    storage_prefix: str, file_name: str, file_type: str
) -> Optional[Dict[str, Any]]:
    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        bucket_name = urlparse(config.FILE_UPLOAD_STORAGE_PATH).netloc
        response: Dict[str, Any] = s3().generate_presigned_post(
            bucket_name,
            f"{storage_prefix}/{file_name}",
            # More documentation on different options to specify here:
            # https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-HTTPPOSTConstructPolicy.html
            Conditions=[
                {"bucket": bucket_name},
                {"Content-Type": file_type},
                {"key": f"{storage_prefix}/{file_name}"},
            ],
            ExpiresIn=60 * 10,  # 10 minutes
        )
        return response
    else:
        return {
            "url": "/api/file-upload",
            "fields": {
                "key": f"{storage_prefix}/{file_name}",
            },
        }


def get_audit_folder_path(election_id: str) -> str:
    return f"audits/{election_id}"


def get_jurisdiction_folder_path(
    election_id: str,
    jurisdiction_id: str,
) -> str:
    return f"{get_audit_folder_path(election_id)}/jurisdictions/{jurisdiction_id}"


def validate_and_get_standard_file_upload_request_params(
    request: Request,
    expected_file_directory_path: str,
    expected_file_name_prefix: str,
    expected_file_types: List[FileType],
) -> Tuple[str, str, str]:
    data = request.get_json()
    if data is None:
        raise BadRequest("Missing JSON request body")
    storage_path = data.get("storagePathKey")
    filename = data.get("fileName")
    file_type = data.get("fileType")
    if not storage_path:
        raise BadRequest("Missing required JSON parameter: storagePathKey")
    if not filename:
        raise BadRequest("Missing required JSON parameter: fileName")
    if not file_type:
        raise BadRequest("Missing required JSON parameter: fileType")

    validate_mimetype(file_type, expected_file_types)

    expected_extensions = "|".join(
        [re.escape(file_type.value) for file_type in expected_file_types]
    )
    pattern = re.compile(
        rf"^{re.escape(expected_file_directory_path)}/{expected_file_name_prefix}_\d{{4}}-\d{{2}}-\d{{2}}T\d{{2}}:\d{{2}}:\d{{2}}\.\d{{6}}\+\d{{2}}:\d{{2}}\.(?:{expected_extensions})$"
    )
    if not pattern.match(storage_path):
        raise BadRequest("Invalid storage path")

    return (get_full_storage_path(storage_path), filename, file_type)


def is_filetype_zip_mimetype(mime_type: str) -> bool:
    return mime_type in ["application/zip", "application/x-zip-compressed"]


def is_filetype_xml_mimetype(mime_type: str) -> bool:
    return mime_type in ["text/xml"]


def validate_mimetype(mime_type: str, expected_file_types: List[FileType]) -> None:
    for type in expected_file_types:
        if type == FileType.CSV:
            if is_filetype_csv_mimetype(mime_type):
                return None
        elif type == FileType.XML:
            if is_filetype_xml_mimetype(mime_type):
                return None
        elif type == FileType.ZIP:
            if is_filetype_zip_mimetype(mime_type):
                return None

    if expected_file_types == [FileType.CSV]:
        raise BadRequest(
            "Please submit a valid CSV. If you are working with an Excel spreadsheet, make sure you export it as a .csv file before uploading."
        )

    expected_types_str = " or ".join([type.value for type in expected_file_types])
    # If we are expecting a CSV file have a clearer error message for that case
    raise BadRequest(f"Please submit a valid file. Expected: {expected_types_str}")


def any_jurisdiction_file_is_processing(jurisdiction: Jurisdiction) -> bool:
    return bool(
        (jurisdiction.manifest_file and jurisdiction.manifest_file.is_processing())
        or (jurisdiction.cvr_file and jurisdiction.cvr_file.is_processing())
        or (
            jurisdiction.batch_tallies_file
            and jurisdiction.batch_tallies_file.is_processing()
        )
    )

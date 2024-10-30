from datetime import datetime
import shutil
import io
import os
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


# Extracts the contents of the provided zip file to the specified directory and returns the list of
# extracted file names
def unzip_files(zip_file: BinaryIO, directory_to_extract_to: str) -> List[str]:
    with ZipFile(zip_file, "r") as zip_archive:
        zip_archive.extractall(directory_to_extract_to)
        return zip_archive.namelist()


def get_full_storage_path(file_path: str) -> str:
    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        bucket_name = urlparse(config.FILE_UPLOAD_STORAGE_PATH).netloc
        return f"s3://{bucket_name}/{file_path}"
    else:
        return os.path.join(config.FILE_UPLOAD_STORAGE_PATH, file_path)


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


def get_standard_file_upload_request_params(request: Request) -> Tuple[str, str, str]:
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
    return (get_full_storage_path(storage_path), filename, file_type)


def is_filetype_zip_mimetype(file_type: str) -> bool:
    return file_type in ["application/zip", "application/x-zip-compressed"]


def is_filetype_xml_mimetype(file_type: str) -> bool:
    return file_type in ["text/xml"]


def validate_csv_or_zip_mimetype(file_type: str) -> None:
    if not is_filetype_zip_mimetype(file_type) and not is_filetype_csv_mimetype(
        file_type
    ):
        raise BadRequest("Please submit a valid CSV or ZIP file.")


def validate_zip_mimetype(file_type: str) -> None:
    if not is_filetype_zip_mimetype(file_type):
        raise BadRequest("Please submit a valid ZIP file.")


def validate_xml_mimetype(file_type: str) -> None:
    if not is_filetype_xml_mimetype(file_type):
        raise BadRequest("Please submit a valid XML file.")

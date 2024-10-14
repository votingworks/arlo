from datetime import datetime
import shutil
import io
import os
import tempfile
from typing import BinaryIO, IO, List, Mapping, Optional
from urllib.parse import urlparse
from zipfile import ZipFile
import boto3

from .. import config
from ..models import *  # pylint: disable=wildcard-import
from ..worker.tasks import serialize_background_task
from ..util.isoformat import isoformat
from ..util.jsonschema import JSONDict


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
    )


def store_file(file: IO[bytes], storage_path: str) -> str:
    assert not os.path.isabs(storage_path)
    full_path = os.path.join(config.FILE_UPLOAD_STORAGE_PATH, storage_path)
    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        bucket_name = urlparse(config.FILE_UPLOAD_STORAGE_PATH).netloc
        s3().upload_fileobj(file, bucket_name, storage_path)
    else:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as system_file:
            shutil.copyfileobj(file, system_file)
    return full_path


def retrieve_file(storage_path: str) -> BinaryIO:
    if config.FILE_UPLOAD_STORAGE_PATH.startswith("s3://"):
        assert storage_path.startswith("s3://")
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

from datetime import datetime
import shutil
import io
import os
import tempfile
from typing import IO, BinaryIO, Dict, Iterable, Optional
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


def zip_files(files: Dict[str, BinaryIO]) -> IO[bytes]:
    zip_file = tempfile.TemporaryFile()
    with ZipFile(zip_file, "w") as zip_archive:
        for file_name, contents_stream in files.items():
            with zip_archive.open(file_name, "w") as archive_file:
                shutil.copyfileobj(contents_stream, archive_file)
    zip_file.seek(0)
    return zip_file


def unzip_files(zip_file: BinaryIO) -> Dict[str, BinaryIO]:
    extract_dir = tempfile.TemporaryDirectory()
    with ZipFile(zip_file, "r") as zip_archive:
        zip_archive.extractall(extract_dir.name)
        return {
            file_name: open(os.path.join(extract_dir.name, file_name), "rb")
            for file_name in zip_archive.namelist()
        }


def chunked_upload_dir_path(chunked_upload_id: str):
    tempdir_path = tempfile.gettempdir()
    return os.path.join(tempdir_path, chunked_upload_id)


# Store each chunk in a separate file
# /tmp/<chunked_upload_id>/<file_name>/<chunk_number>
def store_uploaded_file_chunk(
    chunked_upload_id: str, file_name: str, chunk_number: str, chunk_contents: BinaryIO
):
    file_dir_path = os.path.join(chunked_upload_dir_path(chunked_upload_id), file_name)
    os.makedirs(file_dir_path, exist_ok=True)
    chunk_path = os.path.join(file_dir_path, chunk_number)
    print("Uploading", chunk_path)
    with open(chunk_path, "wb") as chunk_file:
        chunk_file.write(chunk_contents.read())


# Concatenate a list of files into a single file on disk
def concatenate_files(file_names: Iterable[str], output_path: str):
    with open(output_path, "wb") as output_file:
        for file_name in file_names:
            with open(file_name, "rb") as input_file:
                output_file.write(input_file.read())


# Open the files from a chunked upload as a dict of file_name -> file_stream
# This matches the format of how we load files from Flask's request.files
def open_chunked_upload_files(chunked_upload_id: str) -> Dict[str, BinaryIO]:
    upload_dir_path = chunked_upload_dir_path(chunked_upload_id)
    files = {}
    for file_dir in os.scandir(upload_dir_path):
        # Sort the chunks by name *as numbers*
        chunk_file_names = sorted(os.listdir(file_dir.path), key=int)
        chunk_file_paths = [
            os.path.join(file_dir.path, chunk_file_name)
            for chunk_file_name in chunk_file_names
        ]
        concatenated_file_path = os.path.join(file_dir.path, "concatenated")
        concatenate_files(chunk_file_paths, concatenated_file_path)
        files[file_dir.name] = open(concatenated_file_path, "rb")
    return files


def clean_up_chunked_upload(chunked_upload_id: str):
    shutil.rmtree(chunked_upload_dir_path(chunked_upload_id))

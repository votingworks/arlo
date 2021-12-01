from datetime import datetime
import io
import contextlib
from os import path
import os
from typing import BinaryIO, Generator, Optional
from urllib.parse import urlparse
from sqlalchemy.sql.sqltypes import Binary
from werkzeug.datastructures import FileStorage

import boto3


from ..config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, FILE_UPLOAD_STORAGE_PATH
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
    return f"{prefix}-{isoformat(datetime.now(timezone.utc))}.{extension}"


s3 = (
    boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    if FILE_UPLOAD_STORAGE_PATH.startswith("s3://")
    else None
)


print(FILE_UPLOAD_STORAGE_PATH)
print(s3)


def store_file(file: FileStorage, storage_path: str) -> str:
    assert not path.isabs(storage_path)
    full_path = path.join(FILE_UPLOAD_STORAGE_PATH, storage_path)
    print(full_path)
    if s3:
        bucket_name = urlparse(FILE_UPLOAD_STORAGE_PATH).netloc
        s3.upload_fileobj(file, bucket_name, storage_path)
    else:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        file.save(full_path)
    return full_path


@contextlib.contextmanager
def retrieve_file(storage_path: str):
    print(storage_path)
    file: Optional[BinaryIO] = None
    try:
        if s3:
            assert storage_path.startswith("s3://")
            parsed_path = urlparse(storage_path)
            bucket_name = parsed_path.netloc
            key = parsed_path.path[1:]
            file = io.BytesIO()
            s3.download_fileobj(bucket_name, key, file)
            file.seek(0)
        else:
            file = open(storage_path, "rb")
        yield file
    finally:
        if file:
            file.close()


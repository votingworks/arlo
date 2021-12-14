from datetime import datetime, timezone
import tempfile
import io
from unittest.mock import patch
from werkzeug.datastructures import FileStorage

from ...util.file import retrieve_file, store_file
from ... import config


@patch("boto3.client", autospec=True)
def test_file_storage_s3(mock_boto_client):
    config.AWS_ACCESS_KEY_ID = "test access key id"
    config.AWS_SECRET_ACCESS_KEY = "test secret access key"
    original_file_upload_storage_path = config.FILE_UPLOAD_STORAGE_PATH
    config.FILE_UPLOAD_STORAGE_PATH = "s3://test_bucket"

    file = FileStorage(io.BytesIO(b"test file contents"))
    store_file(file, "test_dir/test_file.csv")
    mock_boto_client.assert_called_once_with(
        "s3",
        aws_access_key_id="test access key id",
        aws_secret_access_key="test secret access key",
    )
    mock_boto_client.return_value.upload_fileobj.assert_called_once_with(
        file, "test_bucket", "test_dir/test_file.csv"
    )

    mock_boto_client.return_value.download_fileobj.side_effect = lambda bucket, key, stream: stream.write(
        file.read()
    )
    retrieved_file = retrieve_file("s3://test_bucket/test_dir/test_file.csv")
    mock_boto_client.return_value.download_fileobj.assert_called_once()
    assert (
        mock_boto_client.return_value.download_fileobj.call_args[0][0] == "test_bucket"
    )
    assert (
        mock_boto_client.return_value.download_fileobj.call_args[0][1]
        == "test_dir/test_file.csv"
    )
    assert retrieved_file.read() == b"test file contents"

    config.FILE_UPLOAD_STORAGE_PATH = original_file_upload_storage_path


def test_file_storage_local_file():
    original_file_upload_storage_path = config.FILE_UPLOAD_STORAGE_PATH
    config.FILE_UPLOAD_STORAGE_PATH = tempfile.TemporaryDirectory().name

    file = FileStorage(io.BytesIO(b"test file contents"))
    path = f"test_dir/{datetime.now(timezone.utc).timestamp()}/test_file.csv"
    storage_path = store_file(file, path)

    with open(f"{config.FILE_UPLOAD_STORAGE_PATH}/{path}", "rb") as stored_file:
        assert stored_file.read() == b"test file contents"

    retrieved_file = retrieve_file(storage_path)
    assert retrieved_file.read() == b"test file contents"

    config.FILE_UPLOAD_STORAGE_PATH = original_file_upload_storage_path

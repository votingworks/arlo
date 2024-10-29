from datetime import datetime, timezone
import os.path
import tempfile
import io
from unittest.mock import patch
from werkzeug.exceptions import BadRequest
import pytest

from ...util.file import (
    delete_file,
    retrieve_file,
    store_file,
    get_file_upload_url,
    get_standard_file_upload_request_params,
    validate_zip_mimetype,
    validate_csv_or_zip_mimetype,
    validate_xml_mimetype,
    get_full_storage_path,
)
from ... import config


@patch("boto3.client", autospec=True)
def test_store_file_raises_with_s3_config(mock_boto_client):
    config.AWS_ACCESS_KEY_ID = "test access key id"
    config.AWS_SECRET_ACCESS_KEY = "test secret access key"
    config.AWS_DEFAULT_REGION = "test region"
    original_file_upload_storage_path = config.FILE_UPLOAD_STORAGE_PATH
    config.FILE_UPLOAD_STORAGE_PATH = "s3://test_bucket"

    file = io.BytesIO(b"test file contents")

    # store file should raise an exception as we do not allow passthrough uploads to s3
    with pytest.raises(
        Exception, match=r"This method should only be used for local file storage."
    ):
        store_file(file, "test_dir/test_file.csv")

    path = "/fake/path/to/file"
    filename = "test_file.csv"
    full_path = f"{path}/{filename}"
    # test create presigned url
    get_file_upload_url(path, filename, "text/csv")

    mock_boto_client.assert_called_once_with(
        "s3",
        aws_access_key_id="test access key id",
        aws_secret_access_key="test secret access key",
        region_name="test region",
    )
    mock_boto_client.return_value.generate_presigned_post.assert_called_once_with(
        "test_bucket",
        full_path,
        Conditions=[
            {"bucket": "test_bucket"},
            {"Content-Type": "text/csv"},
            {"key": full_path},
        ],
        ExpiresIn=600,
    )

    mock_boto_client.return_value.download_fileobj.side_effect = (
        lambda bucket, key, stream: stream.write(file.read())
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

    with pytest.raises(AssertionError):
        retrieve_file("invalid/path/to/file")

    delete_file("s3://test_bucket/test_dir/test_file.csv")
    mock_boto_client.return_value.delete_object.assert_called_once()
    assert (
        mock_boto_client.return_value.delete_object.call_args.kwargs["Bucket"]
        == "test_bucket"
    )
    assert (
        mock_boto_client.return_value.delete_object.call_args.kwargs["Key"]
        == "test_dir/test_file.csv"
    )

    config.FILE_UPLOAD_STORAGE_PATH = original_file_upload_storage_path


def test_file_storage_local_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_file_upload_storage_path = config.FILE_UPLOAD_STORAGE_PATH
        config.FILE_UPLOAD_STORAGE_PATH = temp_dir

        file = io.BytesIO(b"test file contents")
        path = f"test_dir/{datetime.now(timezone.utc).timestamp()}"
        filename = "test_file.csv"
        full_path = f"{path}/{filename}"

        upload_url = get_file_upload_url(path, filename, "text/csv")
        assert upload_url == {"url": "/api/file-upload", "fields": {"key": full_path}}

        storage_path = store_file(file, full_path)

        with open(
            f"{config.FILE_UPLOAD_STORAGE_PATH}/{full_path}", "rb"
        ) as stored_file:
            assert stored_file.read() == b"test file contents"

        retrieved_file = retrieve_file(storage_path)
        assert retrieved_file.read() == b"test file contents"

        delete_file(storage_path)
        assert not os.path.exists(f"{config.FILE_UPLOAD_STORAGE_PATH}/{full_path}")

        config.FILE_UPLOAD_STORAGE_PATH = original_file_upload_storage_path


## Tests for general file type utils


@patch("flask.Request", autospec=True)
def test_get_standard_file_upload_request_params(mock_request):
    mock_request.form = {
        "storagePathKey": "test_dir/test_file.csv",
        "fileName": "test_file.csv",
        "fileType": "text/csv",
    }
    (storage_path, filename, file_type) = get_standard_file_upload_request_params(
        mock_request
    )
    assert storage_path == f"{config.FILE_UPLOAD_STORAGE_PATH}/test_dir/test_file.csv"
    assert filename == "test_file.csv"
    assert file_type == "text/csv"

    with pytest.raises(
        BadRequest, match="Missing required JSON parameter: storagePathKey"
    ):
        mock_request.form = {
            "fileName": "test_file.csv",
            "fileType": "text/csv",
        }
        get_standard_file_upload_request_params(mock_request)

    with pytest.raises(BadRequest, match="Missing required JSON parameter: fileName"):
        mock_request.form = {
            "storagePathKey": "test_dir/test_file.csv",
            "fileType": "text/csv",
        }
        get_standard_file_upload_request_params(mock_request)

    with pytest.raises(BadRequest, match="Missing required JSON parameter: fileType"):
        mock_request.form = {
            "storagePathKey": "test_dir/test_file.csv",
            "fileName": "test_file.csv",
        }
        get_standard_file_upload_request_params(mock_request)


def test_validate_zip_mimetype():
    validate_zip_mimetype("application/zip")
    validate_zip_mimetype("application/x-zip-compressed")

    for invalid_mimetype in [
        "text/csv",
        "application/pdf",
        "text/plain",
    ]:
        with pytest.raises(
            BadRequest, match="400 Bad Request: Please submit a valid ZIP file."
        ):
            validate_zip_mimetype(invalid_mimetype)


def test_validate_xml_mimetype():
    validate_xml_mimetype("text/xml")

    for invalid_mimetype in [
        "text/csv",
        "application/pdf",
        "text/plain",
        "application/zip",
    ]:
        with pytest.raises(
            BadRequest, match="400 Bad Request: Please submit a valid XML file."
        ):
            validate_xml_mimetype(invalid_mimetype)


def test_validate_csv_or_zip_mimetype():
    validate_csv_or_zip_mimetype("text/csv")
    validate_csv_or_zip_mimetype("application/vnd.ms-excel")
    validate_csv_or_zip_mimetype("application/zip")
    validate_csv_or_zip_mimetype("application/x-zip-compressed")

    for invalid_mimetype in [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/pdf",
        "text/plain",
        "text/xml",
    ]:
        with pytest.raises(
            BadRequest, match="400 Bad Request: Please submit a valid CSV or ZIP file."
        ):
            validate_csv_or_zip_mimetype(invalid_mimetype)


def test_get_full_storage_path():
    config.FILE_UPLOAD_STORAGE_PATH = "/test/storage/path"
    assert (
        get_full_storage_path("test_dir/test_file.csv")
        == "/test/storage/path/test_dir/test_file.csv"
    )

    config.FILE_UPLOAD_STORAGE_PATH = "s3://test_bucket"
    assert (
        get_full_storage_path("test_dir/test_file.csv")
        == "s3://test_bucket/test_dir/test_file.csv"
    )

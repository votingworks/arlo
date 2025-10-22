from datetime import datetime, timezone
import os.path
import shutil
import tempfile
import io
from typing import List, Tuple
from unittest.mock import patch
from werkzeug.exceptions import BadRequest
import pytest

from server.models import File

from ...util.file import (
    FileType,
    delete_file,
    get_full_storage_path,
    read_zip_filenames,
    retrieve_file,
    retrieve_file_to_buffer,
    store_file,
    get_file_upload_url,
    validate_and_get_standard_file_upload_request_params,
    timestamp_filename,
    zip_files,
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
    file_record = File(storage_path="s3://test_bucket/test_dir/test_file.csv")
    retrieved_file = retrieve_file(file_record)
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
        retrieve_file(File(storage_path="invalid/path/to/file"))

    delete_file(file_record)
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


@patch("boto3.client", autospec=True)
def test_retrieve_file_streaming(mock_boto_client):
    config.AWS_ACCESS_KEY_ID = "test access key id"
    config.AWS_SECRET_ACCESS_KEY = "test secret access key"
    config.AWS_DEFAULT_REGION = "test region"
    original_file_upload_storage_path = config.FILE_UPLOAD_STORAGE_PATH
    config.FILE_UPLOAD_STORAGE_PATH = "s3://test_bucket"

    file = io.BytesIO(b"test data")
    mock_boto_client.return_value.download_fileobj.side_effect = (
        lambda bucket, key, stream: stream.write(file.read())
    )

    with tempfile.TemporaryDirectory() as working_dir:
        file = retrieve_file_to_buffer(
            File(storage_path="s3://test_bucket/test_file.csv"), working_dir
        )
        assert file.read() == b"test data"
        temp_file_path = os.path.join(working_dir, file.name)

        with open(temp_file_path, "rb") as temp_file:
            assert temp_file.read() == b"test data"
        shutil.rmtree(working_dir)

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
        file_record = File(storage_path=storage_path)

        with open(
            f"{config.FILE_UPLOAD_STORAGE_PATH}/{full_path}", "rb"
        ) as stored_file:
            assert stored_file.read() == b"test file contents"

        retrieved_file = retrieve_file(file_record)
        assert retrieved_file.read() == b"test file contents"

        delete_file(file_record)
        assert not os.path.exists(f"{config.FILE_UPLOAD_STORAGE_PATH}/{full_path}")

        config.FILE_UPLOAD_STORAGE_PATH = original_file_upload_storage_path


## Tests for general file type utils
@patch("flask.Request", autospec=True)
def test_validate_and_get_standard_file_upload_request_params(mock_request):
    happy_path_tests: Tuple[FileType, str, List[FileType]] = [
        # test file type, test file mimetype, [allowed types]
        [FileType.CSV, "text/csv", [FileType.CSV]],
        [FileType.ZIP, "application/zip", [FileType.ZIP]],
        [FileType.XML, "text/xml", [FileType.XML]],
        [FileType.XML, "text/xml", [FileType.CSV, FileType.XML]],
        [FileType.ZIP, "application/x-zip-compressed", [FileType.ZIP, FileType.XML]],
        [FileType.CSV, "application/vnd.ms-excel", [FileType.ZIP, FileType.CSV]],
        [FileType.CSV, "text/csv", [FileType.ZIP, FileType.CSV, FileType.XML]],
        [FileType.XML, "text/xml", [FileType.ZIP, FileType.CSV, FileType.XML]],
    ]
    for test_file_type, test_mime_type, allowed_types in happy_path_tests:
        expected_filename = timestamp_filename("test_file", test_file_type.value)
        mock_request.get_json.return_value = {
            "storagePathKey": f"test_dir/{expected_filename}",
            "fileName": expected_filename,
            "fileType": test_mime_type,
        }
        (storage_path, filename, file_type) = (
            validate_and_get_standard_file_upload_request_params(
                mock_request, "test_dir", "test_file", allowed_types
            )
        )
        assert (
            storage_path
            == f"{config.FILE_UPLOAD_STORAGE_PATH}/test_dir/{expected_filename}"
        )
        assert filename == expected_filename
        assert file_type == test_mime_type


@patch("flask.Request", autospec=True)
def test_validate_and_get_standard_file_upload_request_params_errors(mock_request):
    expected_filename = timestamp_filename("test_file", "csv")
    with pytest.raises(
        BadRequest, match="Missing required JSON parameter: storagePathKey"
    ):
        mock_request.get_json.return_value = {
            "fileName": expected_filename,
            "fileType": "text/csv",
        }
        validate_and_get_standard_file_upload_request_params(
            mock_request, "test_dir", "test_file", [FileType.CSV]
        )

    with pytest.raises(BadRequest, match="Missing required JSON parameter: fileName"):
        mock_request.get_json.return_value = {
            "storagePathKey": f"test_dir/{expected_filename}",
            "fileType": "text/csv",
        }
        validate_and_get_standard_file_upload_request_params(
            mock_request, "test_dir", "test_file", [FileType.CSV]
        )

    with pytest.raises(BadRequest, match="Missing required JSON parameter: fileType"):
        mock_request.get_json.return_value = {
            "storagePathKey": f"test_dir/{expected_filename}",
            "fileName": expected_filename,
        }
        validate_and_get_standard_file_upload_request_params(
            mock_request, "test_dir", "test_file", [FileType.CSV]
        )

    with pytest.raises(BadRequest, match="Missing JSON request body"):
        mock_request.get_json.return_value = None
        validate_and_get_standard_file_upload_request_params(
            mock_request, "test_dir", "test_file", [FileType.CSV]
        )

    file_type_error_tests: Tuple[FileType, str, List[FileType], str] = [
        # test file type, test file mimetype, [allowed types], expected error message
        [
            FileType.CSV,
            "text/csv",
            [FileType.ZIP],
            "Please submit a valid file. Expected: zip",
        ],
        [
            FileType.ZIP,
            "application/zip",
            [FileType.XML],
            "Please submit a valid file. Expected: xml",
        ],
        [
            FileType.XML,
            "text/xml",
            [FileType.CSV],
            "Please submit a valid CSV. If you are working with an Excel spreadsheet, make sure you export it as a .csv file before uploading.",
        ],
        [
            FileType.XML,
            "text/xml",
            [FileType.CSV, FileType.ZIP],
            "Please submit a valid file. Expected: csv or zip",
        ],
        [
            FileType.ZIP,
            "application/x-zip-compressed",
            [FileType.CSV, FileType.XML],
            "Please submit a valid file. Expected: csv or xml",
        ],
        [
            FileType.CSV,
            "application/vnd.ms-excel",
            [FileType.ZIP, FileType.XML],
            "Please submit a valid file. Expected: zip or xml",
        ],
        [
            FileType.CSV,
            "invalid",
            [FileType.ZIP, FileType.CSV, FileType.XML],
            "Please submit a valid file. Expected: zip or csv or xml",
        ],
        [
            FileType.XML,
            "text/xaml",
            [FileType.ZIP, FileType.CSV, FileType.XML],
            "Please submit a valid file. Expected: zip or csv or xml",
        ],
    ]
    for (
        test_file_type,
        test_mime_type,
        allowed_types,
        expected_err,
    ) in file_type_error_tests:
        expected_filename = timestamp_filename("test_file", test_file_type)
        mock_request.get_json.return_value = {
            "storagePathKey": f"test_dir/{expected_filename}",
            "fileName": expected_filename,
            "fileType": test_mime_type,
        }
        with pytest.raises(BadRequest, match=expected_err):
            validate_and_get_standard_file_upload_request_params(
                mock_request, "test_dir", "test_file", allowed_types
            )

    storage_path_tests = [
        f"test_dir/{timestamp_filename('test_file', 'zip')}",
        f"test_dir/{timestamp_filename('test_file', 'xml')}",
        f"test_dir/{timestamp_filename('something_else', 'csv')}",
        f"something_else/{timestamp_filename('test_file', 'csv')}",
        "something_else/test_file_2024-05-05.csv",
    ]

    for storage_path_test in storage_path_tests:
        with pytest.raises(BadRequest, match="Invalid storage path"):
            mock_request.get_json.return_value = {
                "storagePathKey": storage_path_test,
                "fileName": expected_filename,
                "fileType": "text/csv",
            }
            validate_and_get_standard_file_upload_request_params(
                mock_request, "test_dir", "test_file", [FileType.CSV]
            )


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


def test_read_zip_filenames():
    zip = zip_files({"a": io.BytesIO(b"hello"), "b": io.BytesIO(b"world")})
    assert read_zip_filenames(io.BytesIO(zip.read())) == ["a", "b"]

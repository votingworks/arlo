import json
import io
import tempfile
from typing import Any, TypedDict

from flask.testing import FlaskClient
from ..helpers import *
from ... import config


def copy_dict_and_remove_key(input: dict, key: str):
    return {k: input[k] for k in input if k != key}


def test_public_compute_sample_sizes_input_validation(client: FlaskClient):
    class TestCase(TypedDict):
        body: Any
        expected_status_code: int
        expected_error_message: str

    valid_input = {
        "electionResults": {
            "candidates": [
                {"name": "Helga Hippo", "votes": 1000},
                {"name": "Bobby Bear", "votes": 900},
            ],
            "numWinners": 1,
            "totalBallotsCast": 2000,
        },
    }
    test_cases: list[TestCase] = [
        {
            "body": copy_dict_and_remove_key(valid_input, "electionResults"),
            "expected_status_code": 400,
            "expected_error_message": "'electionResults' is a required property",
        },
        {
            "body": {
                **valid_input,
                "electionResults": copy_dict_and_remove_key(
                    valid_input["electionResults"], "candidates"
                ),
            },
            "expected_status_code": 400,
            "expected_error_message": "'candidates' is a required property",
        },
        {
            "body": {
                **valid_input,
                "electionResults": copy_dict_and_remove_key(
                    valid_input["electionResults"], "numWinners"
                ),
            },
            "expected_status_code": 400,
            "expected_error_message": "'numWinners' is a required property",
        },
        {
            "body": {
                **valid_input,
                "electionResults": copy_dict_and_remove_key(
                    valid_input["electionResults"], "totalBallotsCast"
                ),
            },
            "expected_status_code": 400,
            "expected_error_message": "'totalBallotsCast' is a required property",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "candidates": [{"name": "Helga Hippo", "votes": 1000}],
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "[{'name': 'Helga Hippo', 'votes': 1000}] is too short",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "candidates": [
                        {"votes": 1000},
                        {"name": "Bobby Bear", "votes": 900},
                    ],
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "'name' is a required property",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "candidates": [
                        {"name": "Helga Hippo"},
                        {"name": "Bobby Bear", "votes": 900},
                    ],
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "'votes' is a required property",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "candidates": [
                        {"name": "Helga Hippo", "votes": -1},
                        {"name": "Bobby Bear", "votes": 900},
                    ],
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "-1 is less than the minimum of 0",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1e16},
                        {"name": "Bobby Bear", "votes": 900},
                    ],
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "1e+16 is greater than the maximum of 1000000000000000.0",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1.2},
                        {"name": "Bobby Bear", "votes": 900},
                    ],
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "1.2 is not of type 'integer'",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {**valid_input["electionResults"], "numWinners": 0},
            },
            "expected_status_code": 400,
            "expected_error_message": "0 is less than the minimum of 1",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "numWinners": 1e16,
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "1e+16 is greater than the maximum of 1000000000000000.0",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "numWinners": 1.2,
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "1.2 is not of type 'integer'",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "totalBallotsCast": 0,
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "0 is less than the minimum of 1",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "totalBallotsCast": 1e16,
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "1e+16 is greater than the maximum of 1000000000000000.0",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "totalBallotsCast": 1.2,
                },
            },
            "expected_status_code": 400,
            "expected_error_message": "1.2 is not of type 'integer'",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Helga Hippo", "votes": 900},
                    ],
                },
            },
            "expected_status_code": 409,
            "expected_error_message": "Candidates must have unique names",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {
                    **valid_input["electionResults"],
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 0},
                        {"name": "Bobby Bear", "votes": 0},
                    ],
                },
            },
            "expected_status_code": 409,
            "expected_error_message": "At least 1 candidate must have greater than 0 votes",
        },
        {
            "body": {
                **valid_input,
                "electionResults": {**valid_input["electionResults"], "numWinners": 2},
            },
            "expected_status_code": 409,
            "expected_error_message": "Number of winners must be less than number of candidates",
        },
    ]
    for test_case in test_cases:
        rv = client.post(
            "/api/public/sample-sizes",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_case["body"]),
        )
        assert rv.status_code == test_case["expected_status_code"]
        response = json.loads(rv.data)
        assert "errors" in response
        assert len(response["errors"]) == 1
        assert "message" in response["errors"][0]
        assert response["errors"][0]["message"] == test_case["expected_error_message"]


def test_public_compute_sample_sizes(client: FlaskClient, snapshot):
    class TestCase(TypedDict):
        description: str
        body: Any

    test_cases: list[TestCase] = [
        {
            "description": "500-vote margin",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 500},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 1500,
                },
            },
        },
        {
            "description": "500-vote margin with additional ballots cast",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 500},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 2000,
                },
            },
        },
        {
            "description": "100-vote margin",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 900},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 1900,
                },
            },
        },
        {
            "description": "100-vote margin with additional ballots cast",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 900},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 2000,
                },
            },
        },
        {
            "description": "10-vote margin",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 990},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 1990,
                },
            },
        },
        {
            "description": "10-vote margin with additional ballots cast",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 990},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 2000,
                },
            },
        },
        {
            "description": "1-vote margin",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 999},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 1999,
                },
            },
        },
        {
            "description": "1-vote margin with additional ballots cast",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 999},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 2000,
                },
            },
        },
        {
            "description": "Tie",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 1000},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 2000,
                },
            },
        },
        {
            "description": "Tie with additional ballots cast",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 1000},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 2001,
                },
            },
        },
        {
            "description": "Landslide",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 0},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 1000,
                },
            },
        },
        {
            "description": "Landslide with additional ballots cast",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 0},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 1001,
                },
            },
        },
        {
            "description": "Many candidates",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 900},
                        {"name": "Sally Sloth", "votes": 800},
                        {"name": "Lenny Lion", "votes": 700},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 3400,
                },
            },
        },
        {
            "description": "Many candidates with multiple winners",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 900},
                        {"name": "Sally Sloth", "votes": 800},
                        {"name": "Lenny Lion", "votes": 700},
                    ],
                    "numWinners": 2,
                    "totalBallotsCast": 3400,
                },
            },
        },
        {
            "description": "Small number of votes",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 2},
                        {"name": "Bobby Bear", "votes": 1},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 3,
                },
            },
        },
        {
            "description": "Small number of votes with additional ballots cast",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 2},
                        {"name": "Bobby Bear", "votes": 1},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 10,
                },
            },
        },
        {
            "description": "Large number of votes",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1_000_000_000},
                        {"name": "Bobby Bear", "votes": 900_000_000},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 1_900_000_000,
                },
            },
        },
        {
            "description": "Large number of votes with additional ballots cast",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1_000_000_000},
                        {"name": "Bobby Bear", "votes": 900_000_000},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 2_000_000_000,
                },
            },
        },
        {
            "description": "Large number of votes with small margin",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1_000_000},
                        {"name": "Bobby Bear", "votes": 999_999},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 1_999_999,
                },
            },
        },
        {
            "description": "Super large number of votes with small margin",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1_000_000_000},
                        {"name": "Bobby Bear", "votes": 999_999_999},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 1_999_999_999,
                },
            },
        },
        {
            "description": "Large number of additional ballots cast",
            "body": {
                "electionResults": {
                    "candidates": [
                        {"name": "Helga Hippo", "votes": 1000},
                        {"name": "Bobby Bear", "votes": 900},
                    ],
                    "numWinners": 1,
                    "totalBallotsCast": 2_000_000_000,
                },
            },
        },
    ]
    for test_case in test_cases:
        rv = client.post(
            "/api/public/sample-sizes",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_case["body"]),
        )
        assert rv.status_code == 200
        response = json.loads(rv.data)
        snapshot.assert_match(response, test_case["description"])


def upload_to_key(client: FlaskClient, key: str):
    return client.post(
        "/api/file-upload",
        data={"file": (io.BytesIO(b"a file"), "random.csv"), "key": key},
    )


def test_public_file_upload(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    original_storage_path = config.FILE_UPLOAD_STORAGE_PATH
    with tempfile.TemporaryDirectory() as temp_dir:
        config.FILE_UPLOAD_STORAGE_PATH = temp_dir
        try:
            set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
            election_key = f"audits/{election_id}/random.csv"
            assert_ok(upload_to_key(client, election_key))
            with open(f"{temp_dir}/{election_key}", "rb") as stored_file:
                assert stored_file.read() == b"a file"

            set_logged_in_user(
                client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
            )
            jurisdiction_key = (
                f"audits/{election_id}/jurisdictions/{jurisdiction_ids[0]}/random.csv"
            )
            assert_ok(upload_to_key(client, jurisdiction_key))
            with open(f"{temp_dir}/{jurisdiction_key}", "rb") as stored_file:
                assert stored_file.read() == b"a file"
        finally:
            config.FILE_UPLOAD_STORAGE_PATH = original_storage_path


def test_public_file_upload_forbidden(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str], org_id: str
):
    election_key = f"audits/{election_id}/random.csv"
    jurisdiction_key = (
        f"audits/{election_id}/jurisdictions/{jurisdiction_ids[0]}/random.csv"
    )
    ja_email = default_ja_email(election_id)
    create_org_and_admin("Other Org", "other-admin@example.com")

    forbidden_cases = [
        # (user_type, user_key, storage_key, expected_message)
        (
            UserType.AUDIT_BOARD,
            "fake-audit-board-id",
            jurisdiction_key,
            "Access forbidden for user type audit_board",
        ),
        # Jurisdiction admins can't upload election-level files...
        (
            UserType.JURISDICTION_ADMIN,
            ja_email,
            election_key,
            "Access forbidden for user type jurisdiction_admin",
        ),
        # ...nor upload to a jurisdiction they don't administer
        (
            UserType.JURISDICTION_ADMIN,
            ja_email,
            f"audits/{election_id}/jurisdictions/{jurisdiction_ids[2]}/random.csv",
            f"{ja_email} does not have access to jurisdiction {jurisdiction_ids[2]}",
        ),
        (
            UserType.AUDIT_ADMIN,
            "other-admin@example.com",
            jurisdiction_key,
            f"other-admin@example.com does not have access to organization {org_id}",
        ),
    ]
    for user_type, user_key, storage_key, expected_message in forbidden_cases:
        set_logged_in_user(client, user_type, user_key)
        rv = upload_to_key(client, storage_key)
        assert rv.status_code == 403, storage_key
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Forbidden", "message": expected_message}]
        }, storage_key


def test_public_file_upload_not_found(client: FlaskClient, election_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = upload_to_key(client, "audits/not-a-real-election-id/random.csv")
    assert rv.status_code == 404

    rv = upload_to_key(
        client,
        f"audits/{election_id}/jurisdictions/not-a-real-jurisdiction-id/random.csv",
    )
    assert rv.status_code == 404

    Election.query.get(election_id).deleted_at = datetime.now(timezone.utc)
    db_session.commit()
    rv = upload_to_key(client, f"audits/{election_id}/random.csv")
    assert rv.status_code == 404


def test_public_file_upload_invalid_key(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    invalid_keys = [
        "test_dir/random.csv",  # not under audits/
        f"audits/{election_id}/",  # missing file name
        f"audits/{election_id}/nested/random.csv",  # unrecognized subfolder
        f"audits/{election_id}/..",  # points at the audits folder
        f"audits/{election_id}/jurisdictions/{jurisdiction_ids[0]}/..",  # points at the jurisdictions folder
        "../test_dir/random.txt",  # path traversal above the storage root
    ]
    for invalid_key in invalid_keys:
        rv = upload_to_key(client, invalid_key)
        assert rv.status_code == 400, invalid_key
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": "Invalid storage path"}]
        }, invalid_key


def test_public_file_upload_unauthorized(client: FlaskClient):
    rv = client.post(
        "/api/file-upload",
        data={
            "file": (
                io.BytesIO(b"hello, I am a file"),
                "random.txt",
            ),
            "key": "test_dir/random.txt",
        },
    )
    assert rv.status_code == 401
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Unauthorized",
                "message": "Please log in to access Arlo",
            }
        ]
    }


def test_public_file_upload_error(client: FlaskClient):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(
        "/api/file-upload",
        data={
            "key": "test_dir/random.txt",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing required form parameter 'file'",
            }
        ]
    }

    rv = client.post(
        "/api/file-upload",
        data={
            "file": (
                io.BytesIO(b"hello, I am a file"),
                "random.txt",
            ),
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing required form parameter 'key'",
            }
        ]
    }


def test_public_file_upload_too_large(client: FlaskClient):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    original_max_size = client.application.config["MAX_CONTENT_LENGTH"]
    client.application.config["MAX_CONTENT_LENGTH"] = 1000
    try:
        rv = client.post(
            "/api/file-upload",
            data={
                "file": (
                    io.BytesIO(b"x" * 2000),
                    "too_large.csv",
                ),
                "key": "audits/election-id/too_large.csv",
            },
        )
        assert rv.status_code == 413
        response = json.loads(rv.data)
        assert response["errors"][0]["errorType"] == "Request Entity Too Large"
        assert response["errors"][0]["message"].startswith(
            "Upload cannot be larger than"
        )
    finally:
        client.application.config["MAX_CONTENT_LENGTH"] = original_max_size

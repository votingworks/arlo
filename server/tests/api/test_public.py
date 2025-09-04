import json
import io
import tempfile
from typing import Any, Dict, List, TypedDict

from flask.testing import FlaskClient
from ..helpers import *
from ... import config


def copy_dict_and_remove_key(input: Dict, key: str):
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
    test_cases: List[TestCase] = [
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

    test_cases: List[TestCase] = [
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


def test_public_file_upload(client: FlaskClient):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    with tempfile.TemporaryDirectory() as temp_dir:
        config.FILE_UPLOAD_STORAGE_PATH = temp_dir
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
        assert_ok(rv)
        with open(f"{temp_dir}/test_dir/random.txt", "rb") as stored_file:
            assert stored_file.read() == b"hello, I am a file"


def test_public_file_upload_path_traversal(client: FlaskClient):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(
        "/api/file-upload",
        data={
            "file": (
                io.BytesIO(b"hello, I am a file"),
                "random.txt",
            ),
            "key": "../test_dir/random.txt",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Invalid storage path",
            }
        ]
    }


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

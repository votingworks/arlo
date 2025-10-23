import io
import json
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *


def test_upload_standardized_contests(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    standardized_contests_file = (
        'Contest Name,Jurisdictions\nContest 1,all\nContest 2,"J1, J3"\nContest 3,J2 \n'
    )
    rv = upload_standardized_contests(
        client,
        io.BytesIO(standardized_contests_file.encode()),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/standardized-contests/file")
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("standardized_contests"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
        },
    )

    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) == [
        {"name": "Contest 1", "jurisdictionIds": jurisdiction_ids},
        {
            "name": "Contest 2",
            "jurisdictionIds": [jurisdiction_ids[0], jurisdiction_ids[2]],
        },
        {"name": "Contest 3", "jurisdictionIds": [jurisdiction_ids[1]]},
    ]

    rv = client.get(f"/api/election/{election_id}/standardized-contests/file/csv")
    assert rv.headers["Content-Disposition"].startswith(
        'attachment; filename="standardized_contests'
    )
    assert rv.data.decode("utf-8") == standardized_contests_file


def test_download_standardized_contests_file_before_upload(
    client: FlaskClient, election_id: str
):
    rv = client.get(f"/api/election/{election_id}/standardized-contests/file/csv")
    assert rv.status_code == 404


def test_standardized_contests_replace(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    rv = upload_standardized_contests(
        client,
        io.BytesIO(
            b"Contest Name,Jurisdictions\n"
            b"Contest 1,all\n"
            b'Contest 2,"J1, J3"\n'
            b"Contest 3,J2 \n"
        ),
        election_id,
    )
    assert_ok(rv)

    election = Election.query.get(election_id)
    file_id = election.standardized_contests_file_id
    standardized_contests = election.standardized_contests

    rv = upload_standardized_contests(
        client,
        io.BytesIO(b"Contest Name,Jurisdictions\nContest 4,all\n"),
        election_id,
    )
    assert_ok(rv)

    # The old file should have been deleted
    assert File.query.get(file_id) is None
    assert Election.query.get(election_id).standardized_contests_file_id != file_id
    assert (
        Election.query.get(election_id).standardized_contests != standardized_contests
    )

    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) == [
        {"name": "Contest 4", "jurisdictionIds": jurisdiction_ids},
    ]


def test_standardized_contests_bad_jurisdiction(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
):
    rv = upload_standardized_contests(
        client,
        io.BytesIO(
            b"Contest Name,Jurisdictions\n"
            b'Contest 1,"J1,not a real jurisdiction,another bad one"\n"'
        ),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/standardized-contests/file")
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("standardized_contests"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Invalid jurisdictions for contest Contest 1: another bad one, not a real jurisdiction",
            },
        },
    )

    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) is None


def test_standardized_contests_no_jurisdictions(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
):
    rv = upload_standardized_contests(
        client,
        io.BytesIO(b"Contest Name,Jurisdictions\nContest 1,"),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/standardized-contests/file")
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("standardized_contests"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "A value is required for the cell at column Jurisdictions, row 2.",
            },
        },
    )

    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) is None


def test_standardized_contests_missing_file(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
):
    rv = client.post(
        f"/api/election/{election_id}/standardized-contests/file/upload-complete",
        json={},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing required JSON parameter: storagePathKey",
            }
        ]
    }


def test_standardized_contests_bad_csv(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
):
    rv = client.post(
        f"/api/election/{election_id}/standardized-contests/file/upload-complete",
        json={
            "storagePathKey": "test_dir/random.txt",
            "fileName": "random.txt",
            "fileType": "text/csv",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "Invalid storage path",
                "errorType": "Bad Request",
            }
        ]
    }

    rv = client.post(
        f"/api/election/{election_id}/standardized-contests/file/upload-complete",
        json={
            "storagePathKey": f"{get_audit_folder_path(election_id)}/{timestamp_filename('standardized_contests', 'csv')}",
            "fileName": "random.txt",
            "fileType": "text/plain",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Please submit a valid CSV. If you are working with an Excel spreadsheet, make sure you export it as a .csv file before uploading.",
            }
        ]
    }


def test_standardized_contests_wrong_audit_type(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
):
    for audit_type in [AuditType.BALLOT_POLLING, AuditType.BATCH_COMPARISON]:
        # Hackily change the audit type
        election = Election.query.get(election_id)
        election.audit_type = audit_type
        db_session.add(election)
        db_session.commit()

        rv = upload_standardized_contests(
            client,
            io.BytesIO(b"Contest Name,Jurisdictions\nContest 1,all\n"),
            election_id,
        )
        assert rv.status_code == 409
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Conflict",
                    "message": "Can't upload standardized contests file for this audit type.",
                }
            ]
        }


def test_standardized_contests_before_jurisdictions(
    client: FlaskClient, election_id: str
):
    rv = upload_standardized_contests(
        client,
        io.BytesIO(b"Contest Name,Jurisdictions\nContest 1,all\n"),
        election_id,
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Must upload jurisdictions file before uploading standardized contests file.",
            }
        ]
    }


def test_standardized_contests_newlines(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    rv = upload_standardized_contests(
        client,
        io.BytesIO(
            b"Contest Name,Jurisdictions\n"
            b'"Contest\r\n1",all\n'
            b'Contest 2,"J1, J3"\n'
            b"Contest 3,J2\n"
        ),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) == [
        {"name": "Contest 1", "jurisdictionIds": jurisdiction_ids},
        {
            "name": "Contest 2",
            "jurisdictionIds": [jurisdiction_ids[0], jurisdiction_ids[2]],
        },
        {"name": "Contest 3", "jurisdictionIds": [jurisdiction_ids[1]]},
    ]


def test_standardized_contests_dominion_vote_for(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    rv = upload_standardized_contests(
        client,
        io.BytesIO(
            b"Contest Name,Jurisdictions\n"
            b'"Contest\r\n1 (Vote For=2)",all\n'
            b'Contest 2,"J1, J3"\n'
            b"Contest 3,J2\n"
        ),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) == [
        {"name": "Contest 1", "jurisdictionIds": jurisdiction_ids},
        {
            "name": "Contest 2",
            "jurisdictionIds": [jurisdiction_ids[0], jurisdiction_ids[2]],
        },
        {"name": "Contest 3", "jurisdictionIds": [jurisdiction_ids[1]]},
    ]


def test_standardized_contests_change_jurisdictions_file(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    standardized_contests_file = (
        "Contest Name,Jurisdictions\n"
        "Contest 1,all\n"
        'Contest 2,"J1, J3"\n'
        "Contest 3,all \n"
    )
    rv = upload_standardized_contests(
        client,
        io.BytesIO(standardized_contests_file.encode()),
        election_id,
    )
    assert_ok(rv)

    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids,
                "isTargeted": True,
            }
        ],
    )
    assert_ok(rv)

    # Remove a jurisdiction that isn't referenced directly in standardized contests
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            (
                "Jurisdiction,Admin Email\n"
                f"J3,j3-{election_id}@example.com\n"
                f"J1,{default_ja_email(election_id)}\n"
            ).encode()
        ),
        election_id,
    )
    assert_ok(rv)

    # Standardized contests should be automatically updated
    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) == [
        {
            "name": "Contest 1",
            "jurisdictionIds": [jurisdiction_ids[0], jurisdiction_ids[2]],
        },
        {
            "name": "Contest 2",
            "jurisdictionIds": [jurisdiction_ids[0], jurisdiction_ids[2]],
        },
        {
            "name": "Contest 3",
            "jurisdictionIds": [jurisdiction_ids[0], jurisdiction_ids[2]],
        },
    ]

    # Now remove a jurisdiction that is referenced directly in standardized contests
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            (f"Jurisdiction,Admin Email\nJ1,{default_ja_email(election_id)}\n").encode()
        ),
        election_id,
    )
    assert_ok(rv)

    # Standardized contests should be cleared
    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) is None

    # Error should be recorded
    rv = client.get(f"/api/election/{election_id}/standardized-contests/file")
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("standardized_contests"),
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Invalid jurisdictions for contest Contest 2: J3",
            },
        },
    )


def test_standardized_contests_parse_all(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    standardized_contests_file = (
        "Contest Name,Jurisdictions\n" + "Contest 1,All\n" + "Contest 2,  aLL \n"
    )
    rv = upload_standardized_contests(
        client,
        io.BytesIO(standardized_contests_file.encode()),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) == [
        {"name": "Contest 1", "jurisdictionIds": jurisdiction_ids},
        {
            "name": "Contest 2",
            "jurisdictionIds": jurisdiction_ids,
        },
    ]


def test_reupload_standardized_contests_after_contests_selected(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    manifests,
    cvrs,
):
    # Upload standardized contests
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    standardized_contests_file = (
        'Contest Name,Jurisdictions\nContest 1,J1\nContest 2,"J1, J3"\nContest 3,J2 \n'
    )
    rv = upload_standardized_contests(
        client,
        io.BytesIO(standardized_contests_file.encode()),
        election_id,
    )
    assert_ok(rv)

    # Select some contests
    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    standardized_contests = json.loads(rv.data)

    contest_1_id = str(uuid.uuid4())
    contest_2_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_1_id,
                **standardized_contests[0],
                "isTargeted": True,
                "numWinners": 1,
            },
            {
                "id": contest_2_id,
                **standardized_contests[1],
                "isTargeted": False,
                "numWinners": 1,
            },
        ],
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    compare_json(
        json.loads(rv.data),
        {
            "contests": [
                {
                    "id": contest_1_id,
                    "name": "Contest 1",
                    "isTargeted": True,
                    "numWinners": 1,
                    "totalBallotsCast": 15,
                    "votesAllowed": 1,
                    "choices": [
                        {"id": assert_is_id, "name": "Choice 1-1", "numVotes": 7},
                        {"id": assert_is_id, "name": "Choice 1-2", "numVotes": 3},
                    ],
                    "jurisdictionIds": [jurisdiction_ids[0]],
                },
                {
                    "id": contest_2_id,
                    "name": "Contest 2",
                    "isTargeted": False,
                    "numWinners": 1,
                    "totalBallotsCast": None,
                    "votesAllowed": None,
                    "choices": [],
                    "jurisdictionIds": [jurisdiction_ids[0], jurisdiction_ids[2]],
                },
            ]
        },
    )

    # Change standardized contests
    standardized_contests_file = (
        "Contest Name,Jurisdictions\n" + 'Contest 1,"J1,J2"\n' + "Contest 3,J2 \n"
    )
    rv = upload_standardized_contests(
        client,
        io.BytesIO(standardized_contests_file.encode()),
        election_id,
    )
    assert_ok(rv)

    # Contests should be updated (Contest 2 deleted, Contest 1 universe and metadata changed)
    rv = client.get(f"/api/election/{election_id}/contest")
    compare_json(
        json.loads(rv.data),
        {
            "contests": [
                {
                    "id": contest_1_id,
                    "name": "Contest 1",
                    "isTargeted": True,
                    "numWinners": 1,
                    "totalBallotsCast": 30,
                    "votesAllowed": 1,
                    "choices": [
                        {"id": assert_is_id, "name": "Choice 1-1", "numVotes": 14},
                        {"id": assert_is_id, "name": "Choice 1-2", "numVotes": 6},
                    ],
                    "jurisdictionIds": jurisdiction_ids[:2],
                }
            ]
        },
    )


def test_standardized_contests_get_upload_url_missing_file_type(
    client: FlaskClient, election_id: str
):
    set_logged_in_user(
        client,
        UserType.AUDIT_ADMIN,
        DEFAULT_AA_EMAIL,
    )
    rv = client.get(
        f"/api/election/{election_id}/standardized-contests/file/upload-url"
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing expected query parameter: fileType",
            }
        ]
    }


def test_standardized_contests_get_upload_url(client: FlaskClient, election_id: str):
    set_logged_in_user(
        client,
        UserType.AUDIT_ADMIN,
        DEFAULT_AA_EMAIL,
    )
    rv = client.get(
        f"/api/election/{election_id}/standardized-contests/file/upload-url",
        query_string={"fileType": "text/csv"},
    )
    assert rv.status_code == 200

    response_data = json.loads(rv.data)
    expected_url = "/api/file-upload"

    assert response_data["url"] == expected_url
    assert response_data["fields"]["key"].startswith(
        f"audits/{election_id}/standardized_contests_"
    )
    assert response_data["fields"]["key"].endswith(".csv")


def test_replace_standardized_contests_file_while_processing_jurisdictions_file_fails(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
):
    with no_automatic_task_execution():
        # upload jurisdictions file, but don't process it
        rv = upload_jurisdictions_file(
            client,
            io.BytesIO(b"does not matter"),
            election_id,
        )
        assert_ok(rv)

        # upload standardized contests file
        rv = upload_standardized_contests(
            client,
            io.BytesIO(b"does not matter"),
            election_id,
        )

        assert rv.status_code == 409
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Conflict",
                    "message": "Cannot replace standardized contests while jurisdictions file is processing.",
                }
            ]
        }

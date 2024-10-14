import io
import json
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


def test_upload_standardized_contests(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    standardized_contests_file = (
        "Contest Name,Jurisdictions\n"
        "Contest 1,all\n"
        'Contest 2,"J1, J3"\n'
        "Contest 3,J2 \n"
    )
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(standardized_contests_file.encode()),
                "standardized-contests.csv",
            )
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/standardized-contests/file")
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "standardized-contests.csv",
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
    assert (
        rv.headers["Content-Disposition"]
        == 'attachment; filename="standardized-contests.csv"'
    )
    assert rv.data.decode("utf-8") == standardized_contests_file


def test_download_standardized_contests_file_before_upload(
    client: FlaskClient, election_id: str
):
    rv = client.get(f"/api/election/{election_id}/standardized-contests/file/csv")
    assert rv.status_code == 404


def test_standardized_contests_replace(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(
                    b"Contest Name,Jurisdictions\n"
                    b"Contest 1,all\n"
                    b'Contest 2,"J1, J3"\n'
                    b"Contest 3,J2 \n"
                ),
                "standardized-contests.csv",
            )
        },
    )
    assert_ok(rv)

    election = Election.query.get(election_id)
    file_id = election.standardized_contests_file_id
    standardized_contests = election.standardized_contests

    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(b"Contest Name,Jurisdictions\n" b"Contest 4,all\n"),
                "standardized-contests.csv",
            )
        },
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
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(
                    b"Contest Name,Jurisdictions\n"
                    b'Contest 1,"J1,not a real jurisdiction,another bad one"\n"'
                ),
                "standardized-contests.csv",
            )
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/standardized-contests/file")
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "standardized-contests.csv",
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
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(b"Contest Name,Jurisdictions\n" b"Contest 1,"),
                "standardized-contests.csv",
            )
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/standardized-contests/file")
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "standardized-contests.csv",
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
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing required file parameter 'standardized-contests'",
            }
        ]
    }


def test_standardized_contests_bad_csv(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(b"not a csv"),
                "standardized-contests.txt",
            )
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
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    for audit_type in [AuditType.BALLOT_POLLING, AuditType.BATCH_COMPARISON]:
        # Hackily change the audit type
        election = Election.query.get(election_id)
        election.audit_type = audit_type
        db_session.add(election)
        db_session.commit()

        rv = client.put(
            f"/api/election/{election_id}/standardized-contests/file",
            data={
                "standardized-contests": (
                    io.BytesIO(b"Contest Name,Jurisdictions\n" b"Contest 1,all\n"),
                    "standardized-contests.csv",
                )
            },
        )
        assert rv.status_code == 409
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Conflict",
                    "message": "Can't upload CVR file for this audit type.",
                }
            ]
        }


def test_standardized_contests_before_jurisdictions(
    client: FlaskClient, election_id: str
):
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(b"Contest Name,Jurisdictions\n" b"Contest 1,all\n"),
                "standardized-contests.csv",
            )
        },
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
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(
                    b"Contest Name,Jurisdictions\n"
                    b'"Contest\r\n1",all\n'
                    b'Contest 2,"J1, J3"\n'
                    b"Contest 3,J2\n"
                ),
                "standardized-contests.csv",
            )
        },
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
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(
                    b"Contest Name,Jurisdictions\n"
                    b'"Contest\r\n1 (Vote For=2)",all\n'
                    b'Contest 2,"J1, J3"\n'
                    b"Contest 3,J2\n"
                ),
                "standardized-contests.csv",
            )
        },
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
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    standardized_contests_file = (
        "Contest Name,Jurisdictions\n"
        "Contest 1,all\n"
        'Contest 2,"J1, J3"\n'
        "Contest 3,all \n"
    )
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(standardized_contests_file.encode()),
                "standardized-contests.csv",
            )
        },
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
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    (
                        "Jurisdiction,Admin Email\n"
                        f"J3,j3-{election_id}@example.com\n"
                        f"J1,{default_ja_email(election_id)}\n"
                    ).encode()
                ),
                "jurisdictions.csv",
            )
        },
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
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    (
                        "Jurisdiction,Admin Email\n"
                        f"J1,{default_ja_email(election_id)}\n"
                    ).encode()
                ),
                "jurisdictions.csv",
            )
        },
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
                "name": "standardized-contests.csv",
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
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    standardized_contests_file = (
        "Contest Name,Jurisdictions\n" + "Contest 1,All\n" + "Contest 2,  aLL \n"
    )
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(standardized_contests_file.encode()),
                "standardized-contests.csv",
            )
        },
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
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    # Upload standardized contests
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    standardized_contests_file = (
        "Contest Name,Jurisdictions\n"
        "Contest 1,J1\n"
        'Contest 2,"J1, J3"\n'
        "Contest 3,J2 \n"
    )
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(standardized_contests_file.encode()),
                "standardized-contests.csv",
            )
        },
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
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(standardized_contests_file.encode()),
                "standardized-contests.csv",
            )
        },
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

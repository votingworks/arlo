import io
import json
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...bgcompute import bgcompute_update_standardized_contests_file


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
                "status": ProcessingStatus.READY_TO_PROCESS,
                "startedAt": None,
                "completedAt": None,
                "error": None,
            },
        },
    )

    bgcompute_update_standardized_contests_file(election_id)

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

    file_id = Election.query.get(election_id).standardized_contests_file_id

    bgcompute_update_standardized_contests_file(election_id)

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
    assert Election.query.get(election_id).standardized_contests is None

    bgcompute_update_standardized_contests_file(election_id)

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

    bgcompute_update_standardized_contests_file(election_id)

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


def test_standardized_contests_missing_file(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    rv = client.put(f"/api/election/{election_id}/standardized-contests/file", data={},)
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
                "standardized-contests.csv",
            )
        },
    )
    assert_ok(rv)

    bgcompute_update_standardized_contests_file(election_id)

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
                "error": "Please submit a valid CSV file with columns separated by commas.",
            },
        },
    )

    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) is None


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
                    "message": "Can only upload standardized contests file for ballot comparison audits.",
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

    bgcompute_update_standardized_contests_file(election_id)

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

    bgcompute_update_standardized_contests_file(election_id)

    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    assert json.loads(rv.data) == [
        {"name": "Contest 1", "jurisdictionIds": jurisdiction_ids},
        {
            "name": "Contest 2",
            "jurisdictionIds": [jurisdiction_ids[0], jurisdiction_ids[2]],
        },
        {"name": "Contest 3", "jurisdictionIds": [jurisdiction_ids[1]]},
    ]

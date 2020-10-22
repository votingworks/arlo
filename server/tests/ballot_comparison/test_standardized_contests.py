import io
import json
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...bgcompute import bgcompute_update_standardized_contests_file


def test_upload_standardized_contests(
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

    bgcompute_update_standardized_contests_file()

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

    bgcompute_update_standardized_contests_file()

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


# TODO - test more invalid cases

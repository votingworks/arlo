import io
import json
import uuid
from typing import Any
from flask.testing import FlaskClient
import pytest

from ...models import *
from ..helpers import *


@pytest.fixture
def election_id(client: FlaskClient, org_id: str, request) -> str:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    return create_election(
        client,
        audit_name=f"Test Audit {request.node.name}",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=getattr(request, "param", AuditMathType.CARD_STYLE_DATA),
        organization_id=org_id,
    )


def upload_manifest(
    client: FlaskClient, election_id: str, jurisdiction_id: str, manifest: bytes
) -> dict[str, Any]:
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_ballot_manifest(
        client, io.BytesIO(manifest), election_id, jurisdiction_id
    )
    assert_ok(rv)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/ballot-manifest"
    )
    return json.loads(rv.data)["processing"]


def num_ballots_by_contest_id_by_batch(
    jurisdiction_id: str,
) -> dict[str, dict[str, int] | None]:
    return {
        batch.name: batch.num_ballots_by_contest_id
        for batch in Batch.query.filter_by(jurisdiction_id=jurisdiction_id)
    }


def test_manifest_with_contest_ballot_counts(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
):
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots,Contest 1 - Number of Ballots\n"
        b"Batch 1,500,500\n"
        b"Batch 2,500,120\n"
        b"Batch 3,100,0\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    assert num_ballots_by_contest_id_by_batch(jurisdiction_ids[0]) == {
        "Batch 1": {contest_ids[0]: 500},
        "Batch 2": {contest_ids[0]: 120},
        "Batch 3": {contest_ids[0]: 0},
    }

    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[1],
        b"Batch Name,Number of Ballots\nBatch 1,500\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    assert num_ballots_by_contest_id_by_batch(jurisdiction_ids[1]) == {"Batch 1": None}
    assert Contest.query.get(contest_ids[0]).total_ballots_cast == 1100 + 500


def test_manifest_contest_ballot_count_exceeds_total(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],  # pylint: disable=unused-argument
):
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots,Contest 1 - Number of Ballots\n"
        b"Batch 1,500,500\n"
        b"Batch 2,500,501\n",
    )
    assert processing["status"] == ProcessingStatus.ERRORED
    assert (
        processing["error"]
        == 'Number of ballots in column "Contest 1 - Number of Ballots" (501) cannot exceed "Number of Ballots" (500) in row 3.'
    )


def test_manifest_contest_ballot_counts_require_every_row(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],  # pylint: disable=unused-argument
):
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots,Contest 1 - Number of Ballots\n"
        b"Batch 1,500,500\n"
        b"Batch 2,500,\n",
    )
    assert processing["status"] == ProcessingStatus.ERRORED
    assert (
        processing["error"]
        == "A value is required for the cell at column Contest 1 - Number of Ballots, row 3."
    )


def test_manifest_contest_ballot_counts_unknown_contest(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],  # pylint: disable=unused-argument
):
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots,Contest X - Number of Ballots\n"
        b"Batch 1,500,120\n",
    )
    assert processing["status"] == ProcessingStatus.ERRORED
    assert (
        processing["error"]
        == "Found unexpected columns. Allowed columns: Batch Name, Container, Contest 1 - Number of Ballots, Number of Ballots, Tabulator."
    )


def test_manifest_contest_ballot_counts_before_contests_assigned(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots,Contest 1 - Number of Ballots\n"
        b"Batch 1,500,120\n",
    )
    assert processing["status"] == ProcessingStatus.ERRORED
    assert (
        processing["error"]
        == "Found unexpected columns. Allowed columns: Batch Name, Container, Number of Ballots, Tabulator."
    )


@pytest.mark.parametrize("election_id", [AuditMathType.MACRO], indirect=True)
def test_manifest_contest_ballot_counts_without_card_style_data(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],  # pylint: disable=unused-argument
):
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots,Contest 1 - Number of Ballots\n"
        b"Batch 1,500,120\n",
    )
    assert processing["status"] == ProcessingStatus.ERRORED
    assert (
        processing["error"]
        == "Found unexpected columns. Allowed columns: Batch Name, Container, Number of Ballots, Tabulator."
    )


def test_manifest_contest_ballot_counts_for_some_contests(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    del contest["totalBallotsCast"]
    contest_2_id = str(uuid.uuid4())
    contest_2 = {
        **contest,
        "id": contest_2_id,
        "name": "Contest 2",
        "choices": [
            {**choice, "id": str(uuid.uuid4())} for choice in contest["choices"]
        ],
        "jurisdictionIds": [jurisdiction_ids[0]],
    }
    rv = put_json(client, f"/api/election/{election_id}/contest", [contest, contest_2])
    assert_ok(rv)

    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots,Contest 2 - Number of Ballots\n"
        b"Batch 1,500,120\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    assert num_ballots_by_contest_id_by_batch(jurisdiction_ids[0]) == {
        "Batch 1": {contest_2_id: 120}
    }


def test_contest_names_must_be_unique(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],  # pylint: disable=unused-argument
    contest_ids: list[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    del contest["totalBallotsCast"]
    duplicate = {
        **contest,
        "id": str(uuid.uuid4()),
        "name": "CONTEST 1",
        "choices": [
            {**choice, "id": str(uuid.uuid4())} for choice in contest["choices"]
        ],
    }
    rv = put_json(client, f"/api/election/{election_id}/contest", [contest, duplicate])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": 'Contest names must be unique in card style data audits. Duplicate contest name: "contest 1"',
            }
        ]
    }

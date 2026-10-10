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
    return get_file_processing(client, election_id, jurisdiction_id, "ballot-manifest")


def upload_tallies(
    client: FlaskClient, election_id: str, jurisdiction_id: str, tallies: bytes
) -> dict[str, Any]:
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_batch_tallies(client, io.BytesIO(tallies), election_id, jurisdiction_id)
    assert_ok(rv)
    return get_file_processing(client, election_id, jurisdiction_id, "batch-tallies")


# J1 lists how many ballots carry Contest 1 in each batch; J2 does not
def upload_contest_count_manifests(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots,Contest 1 - Number of Ballots\n"
        b"Batch 1,500,120\n"
        b"Batch 2,500,500\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[1],
        b"Batch Name,Number of Ballots\nBatch 1,500\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED


def upload_contest_count_tallies(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    processing = upload_tallies(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,100,50,50\n"
        b"Batch 2,300,100,100\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    processing = upload_tallies(
        client,
        election_id,
        jurisdiction_ids[1],
        b"Batch Name,candidate 1,candidate 2,candidate 3\nBatch 1,300,100,100\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED


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
    assert Contest.query.get(contest_ids[0]).total_ballots_cast == (500 + 120 + 0) + 500


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


def test_batch_tallies_use_contest_ballot_counts(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
):
    upload_contest_count_manifests(client, election_id, jurisdiction_ids)

    upload_contest_count_tallies(client, election_id, jurisdiction_ids)

    contest_id = contest_ids[0]
    batch_tallies = Jurisdiction.query.get(jurisdiction_ids[0]).batch_tallies
    assert batch_tallies["Batch 1"][contest_id]["ballots"] == 120
    assert batch_tallies["Batch 2"][contest_id]["ballots"] == 500
    batch_tallies = Jurisdiction.query.get(jurisdiction_ids[1]).batch_tallies
    assert batch_tallies["Batch 1"][contest_id]["ballots"] == 500


def test_batch_tallies_exceed_contest_ballot_counts(
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
    assert processing["status"] == ProcessingStatus.PROCESSED

    processing = upload_tallies(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,candidate 1,candidate 2,candidate 3\nBatch 1,200,50,0\n",
    )
    assert processing["status"] == ProcessingStatus.ERRORED
    assert (
        processing["error"]
        == 'The total votes for contest "Contest 1" in batch "Batch 1" (250 votes) cannot exceed 240 - the number of ballots for this contest from the manifest (120 ballots) multiplied by the number of votes allowed for the contest (2 votes per ballot).'
    )


def test_batch_tallies_keep_contest_ballot_counts_after_rename(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
):
    upload_contest_count_manifests(client, election_id, jurisdiction_ids)
    upload_contest_count_tallies(client, election_id, jurisdiction_ids)

    # Renaming the contest reprocesses the batch tallies, which still find the
    # counts since they are keyed by contest id
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    del contest["totalBallotsCast"]
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [{**contest, "name": "Contest One"}],
    )
    assert_ok(rv)

    processing = get_file_processing(
        client, election_id, jurisdiction_ids[0], "batch-tallies"
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    batch_tallies = Jurisdiction.query.get(jurisdiction_ids[0]).batch_tallies
    assert batch_tallies["Batch 1"][contest_ids[0]]["ballots"] == 120


def test_contest_total_ballots_from_contest_counts(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
):
    upload_contest_count_manifests(client, election_id, jurisdiction_ids)

    def total_ballots_cast() -> int:
        return Contest.query.get(contest_ids[0]).total_ballots_cast

    assert total_ballots_cast() == 120 + 500 + 500

    # Without the column, the batch total counts for every contest again
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots\nBatch 1,500\nBatch 2,500\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    assert total_ballots_cast() == 500 + 500 + 500


@pytest.mark.usefixtures("election_settings")
def test_audited_results_limited_by_contest_ballot_counts(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
):
    # Report totals that match the batch tallies below so the margin is sound
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    del contest["totalBallotsCast"]
    num_votes_by_name = {"candidate 1": 700, "candidate 2": 250, "candidate 3": 250}
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                **contest,
                "choices": [
                    {**choice, "numVotes": num_votes_by_name[choice["name"]]}
                    for choice in contest["choices"]
                ],
            }
        ],
    )
    assert_ok(rv)

    upload_contest_count_manifests(client, election_id, jurisdiction_ids)
    upload_contest_count_tallies(client, election_id, jurisdiction_ids)

    # Sample every batch so Batch 1 is certainly in the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_ids[0]: {"key": "custom", "size": 3, "prob": None}},
        },
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    round_id = json.loads(rv.data)["rounds"][0]["id"]
    choice_id_by_name = {
        choice.name: choice.id for choice in Contest.query.get(contest_ids[0]).choices
    }

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/batches"
    )
    batch_id = next(
        batch["id"]
        for batch in json.loads(rv.data)["batches"]
        if batch["name"] == "Batch 1"
    )
    # 250 votes fit in the batch's 500 ballots, but not in the 120 carrying the contest
    rv = put_batch_results(
        client,
        election_id,
        jurisdiction_ids[0],
        round_id,
        batch_id,
        [
            {
                choice_id_by_name["candidate 1"]: 200,
                choice_id_by_name["candidate 2"]: 50,
                choice_id_by_name["candidate 3"]: 0,
            }
        ],
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Total votes for batch Batch 1 contest Contest 1 should not exceed 240 - the number of ballots in the batch (120) times the number of votes allowed (2).",
            }
        ]
    }


def test_manifest_contest_ballot_counts_zero_in_every_batch(
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
        b"Batch 1,500,0\n"
        b"Batch 2,500,0\n",
    )
    assert processing["status"] == ProcessingStatus.ERRORED
    assert (
        processing["error"]
        == "Found 1 column with 0 ballots in every batch: Contest 1 - Number of Ballots. If this jurisdiction has no ballots for a contest, remove the jurisdiction from the contest instead."
    )

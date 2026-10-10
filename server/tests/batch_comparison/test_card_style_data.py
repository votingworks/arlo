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
def upload_manifests_with_contest_counts(
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


def test_total_ballots_cast_from_manifest_counts(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
):
    upload_manifests_with_contest_counts(client, election_id, jurisdiction_ids)
    assert Contest.query.get(contest_ids[0]).total_ballots_cast == 120 + 500 + 500

    # Without the column, the batch total counts for every contest again
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots\nBatch 1,500\nBatch 2,500\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    assert Contest.query.get(contest_ids[0]).total_ballots_cast == 500 + 500 + 500


def test_batch_tallies_use_contest_ballot_counts(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
):
    upload_manifests_with_contest_counts(client, election_id, jurisdiction_ids)

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
        == 'The total votes for contest "Contest 1" in batch "Batch 1" (250 votes) cannot exceed 240 - the number of ballots from the manifest (120 ballots) multiplied by the number of votes allowed for the contest (2 votes per ballot).'
    )


def test_batch_tallies_keep_contest_ballot_counts_after_rename(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
):
    upload_manifests_with_contest_counts(client, election_id, jurisdiction_ids)
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


@pytest.mark.usefixtures("election_settings")
def test_combined_batches_with_card_style_data(
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
    num_votes_by_name = {"candidate 1": 1600, "candidate 2": 190, "candidate 3": 190}
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

    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,Number of Ballots,Contest 1 - Number of Ballots\n"
        b"Batch 1,500,120\n"
        b"Batch 2,500,120\n"
        b"Batch 3,500,120\n"
        b"Batch 4,500,120\n"
        b"Batch 5,500,0\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    processing = upload_manifest(
        client,
        election_id,
        jurisdiction_ids[1],
        b"Batch Name,Number of Ballots\nBatch 1,500\nBatch 2,500\nBatch 3,500\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    processing = upload_tallies(
        client,
        election_id,
        jurisdiction_ids[0],
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,100,10,10\n"
        b"Batch 2,100,10,10\n"
        b"Batch 3,100,10,10\n"
        b"Batch 4,100,10,10\n"
        b"Batch 5,0,0,0\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED
    processing = upload_tallies(
        client,
        election_id,
        jurisdiction_ids[1],
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,400,50,50\n"
        b"Batch 2,400,50,50\n"
        b"Batch 3,400,50,50\n",
    )
    assert processing["status"] == ProcessingStatus.PROCESSED

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_ids[0]: {"key": "custom", "size": 2, "prob": None}},
        },
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]
    choice_id_by_name = {
        choice.name: choice.id for choice in Contest.query.get(contest_ids[0]).choices
    }

    # A batch's audited votes are capped by its ballots for the contest (120),
    # not all of its ballots (500)
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    batch_id = next(
        batch["id"]
        for batch in json.loads(rv.data)["batches"]
        if batch["name"] == "Batch 2"
    )
    rv = put_batch_results(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
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
                "message": "Total votes for batch Batch 2 contest Contest 1 should not exceed 240 - the number of ballots in the batch (120) times the number of votes allowed (2).",
            }
        ]
    }

    # A combined batch is capped by the sum of its sub-batches' ballots for the
    # contest, including Batch 5 with none
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = post_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
        {
            "name": "Combined Batch",
            "subBatchIds": [
                batch.id
                for batch in Batch.query.filter_by(jurisdiction_id=jurisdiction_ids[0])
            ],
        },
    )
    assert_ok(rv)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    batches = json.loads(rv.data)["batches"]
    assert [batch["name"] for batch in batches] == ["Combined Batch"]
    # 961 votes fit in the combined batch's 2500 ballots, but not in the
    # 4 x 120 + 0 carrying the contest
    rv = put_batch_results(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
        batches[0]["id"],
        [
            {
                choice_id_by_name["candidate 1"]: 800,
                choice_id_by_name["candidate 2"]: 161,
                choice_id_by_name["candidate 3"]: 0,
            }
        ],
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Total votes for batch Combined Batch contest Contest 1 should not exceed 960 - the number of ballots in the batch (480) times the number of votes allowed (2).",
            }
        ]
    }

    rv = put_batch_results(
        client,
        election_id,
        jurisdiction_ids[0],
        round_1_id,
        batches[0]["id"],
        [
            {
                choice_id_by_name["candidate 1"]: 400,
                choice_id_by_name["candidate 2"]: 40,
                choice_id_by_name["candidate 3"]: 40,
            }
        ],
    )
    assert_ok(rv)

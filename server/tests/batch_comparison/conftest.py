import io
import pytest

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...bgcompute import (
    bgcompute_update_batch_tallies_file,
    bgcompute_update_ballot_manifest_file,
)
from ...util.process_file import ProcessingStatus


@pytest.fixture
def election_id(client: FlaskClient, request):
    return create_election(
        client,
        audit_name=f"Test Audit {request.node.name}",
        audit_type=AuditType.BATCH_COMPARISON,
    )


@pytest.fixture
def contest_ids(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 600},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 500},
            ],
            "totalBallotsCast": 1500,
            "numWinners": 1,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


# We only support one contest for now, so this is a convenience fixture
@pytest.fixture
def contest_id(contest_ids: List[str]) -> str:
    return contest_ids[0]


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n"
                    b"Batch 1,200\n"
                    b"Batch 2,300\n"
                    b"Batch 3,400\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n" b"Batch 1,300\n" b"Batch 2,400\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_ballot_manifest_file()


@pytest.fixture
def batch_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    batch_tallies_file = (
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,1,10,100\n"
        b"Batch 2,2,20,200\n"
        b"Batch 3,3,30,300\n"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={"batchTallies": (io.BytesIO(batch_tallies_file), "batchTallies.csv",)},
    )
    batch_tallies_file = (
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,1,10,100\n"
        b"Batch 2,2,20,200\n"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/batch-tallies",
        data={"batchTallies": (io.BytesIO(batch_tallies_file), "batchTallies.csv",)},
    )
    assert_ok(rv)
    bgcompute_update_batch_tallies_file()


@pytest.fixture
def round_1_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_id: str,
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
):
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 200
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_size = sample_size_options[contest_id][0]["size"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_id: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    return rounds[0]["id"]

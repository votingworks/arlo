import io
import pytest

from ...app import app
from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


@pytest.fixture
def election_id(client: FlaskClient, org_id: str, request):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    return create_election(
        client,
        audit_name=f"Test Audit {request.node.name}",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
        organization_id=org_id,
    )


@pytest.fixture
def election_settings(client: FlaskClient, election_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    settings = {
        "electionName": "Test Election",
        "online": False,
        "randomSeed": "1234567890",
        "riskLimit": 10,
        "state": USState.California,
    }
    rv = put_json(client, f"/api/election/{election_id}/settings", settings)
    assert_ok(rv)


@pytest.fixture
def contest_ids(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 5000},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 2500},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 2500},
            ],
            "numWinners": 1,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(contest["id"]) for contest in contests]


# A convenience fixture for when there's only one contest
@pytest.fixture
def contest_id(contest_ids: List[str]) -> str:
    return contest_ids[0]


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n"
                    b"Batch 1,500\n"
                    b"Batch 2,500\n"
                    b"Batch 3,500\n"
                    b"Batch 4,500\n"
                    b"Batch 5,100\n"
                    b"Batch 6,100\n"
                    b"Batch 7,100\n"
                    b"Batch 8,100\n"
                    b"Batch 9,100\n"
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
                    b"Batch Name,Number of Ballots\n"
                    b"Batch 1,500\n"
                    b"Batch 2,500\n"
                    b"Batch 3,500\n"
                    b"Batch 4,500\n"
                    b"Batch 5,250\n"
                    b"Batch 6,250\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)


@pytest.fixture
def batch_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    batch_tallies_file = (
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,500,250,250\n"
        b"Batch 2,500,250,250\n"
        b"Batch 3,500,250,250\n"
        b"Batch 4,500,250,250\n"
        b"Batch 5,100,50,50\n"
        b"Batch 6,100,50,50\n"
        b"Batch 7,100,50,50\n"
        b"Batch 8,100,50,50\n"
        b"Batch 9,100,50,50\n"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(batch_tallies_file),
                "batchTallies.csv",
            )
        },
    )
    batch_tallies_file = (
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,500,250,250\n"
        b"Batch 2,500,250,250\n"
        b"Batch 3,500,250,250\n"
        b"Batch 4,500,250,250\n"
        b"Batch 5,100,50,50\n"
        b"Batch 6,100,50,50\n"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(batch_tallies_file),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)


@pytest.fixture
def round_1_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200
    sample_size_options = json.loads(rv.data)["sampleSizes"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contest_id: sample_size_options_for_contest[0]
                for contest_id, sample_size_options_for_contest in sample_size_options.items()
            },
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    return rounds[0]["id"]


@pytest.fixture
def tally_entry_user_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,  # pylint: disable=unused-argument
):
    # Use the second jurisdiction
    jurisdiction_id = jurisdiction_ids[1]

    # Turn on tally entry login, generating a login link passphrase
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.post(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert_ok(rv)

    rv = client.get(
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}"
    )
    assert rv.status_code == 200
    tally_entry_status = json.loads(rv.data)

    # As an un-logged-in user, visit the login link
    tally_entry_client = app.test_client()
    login_link = f"/tallyentry/{tally_entry_status['passphrase']}"
    rv = tally_entry_client.get(login_link)
    assert rv.status_code == 302

    # Load the jurisdiction info
    rv = tally_entry_client.get("/api/me")
    assert rv.status_code == 200
    tally_entry_me_response = json.loads(rv.data)

    # Enter tally entry user details and start login
    members = [
        dict(name="Alice", affiliation="DEM"),
        dict(name="Bob", affiliation=None),
    ]
    rv = post_json(tally_entry_client, "/auth/tallyentry/code", dict(members=members))
    assert_ok(rv)

    # Poll for login status
    rv = tally_entry_client.get("/api/me")
    assert rv.status_code == 200
    tally_entry_me_response = json.loads(rv.data)
    login_code = tally_entry_me_response["user"]["loginCode"]
    user_id = tally_entry_me_response["user"]["id"]

    # Tell login code to JA, who enters it on their screen
    rv = post_json(
        client,
        f"/auth/tallyentry/election/{election_id}/jurisdiction/{jurisdiction_id}/confirm",
        dict(tallyEntryUserId=user_id, loginCode=login_code),
    )
    assert_ok(rv)

    return user_id

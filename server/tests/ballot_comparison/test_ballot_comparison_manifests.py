import io
import json
from collections import defaultdict
from flask.testing import FlaskClient
import pytest

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...bgcompute import bgcompute_update_ballot_manifest_file


# In one jurisdiction, add the Container column to the manifest. In this
# jurisdiction, ballots should be divvied up between audit boards by container,
# not the usual tabulator+batch name.


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Container,Tabulator,Batch Name,Number of Ballots\n"
                    b"A,1,1,20\n"
                    b"A,1,2,20\n"
                    b"A,2,1,20\n"
                    b"A,2,2,20\n"
                    b"B,1,3,20\n"
                    b"B,1,4,20\n"
                    b"B,2,3,20\n"
                    b"B,2,4,20"
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
                    b"Tabulator,Batch Name,Number of Ballots\n"
                    b"1,1,50\n"
                    b"1,2,50\n"
                    b"2,1,50\n"
                    b"2,2,50"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_ballot_manifest_file()


def test_ballot_comparison_container_manifest(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # AA creates contests
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            },
        ],
    )
    assert_ok(rv)

    # AA selects a sample size and launches the audit
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    target_contest_id = contests[0]["id"]

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    sample_size = sample_size_options[target_contest_id][0]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {target_contest_id: sample_size["size"]}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # JAs create audit boards
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/audit-board",
            [
                {"name": "Audit Board #1"},
                {"name": "Audit Board #2"},
                {"name": "Audit Board #3"},
            ],
        )
        assert_ok(rv)

    # Check that the first jurisdiction's audit boards have ballots divvied up by container
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board"
    )
    audit_boards = json.loads(rv.data)["auditBoards"]

    audit_boards_by_container = defaultdict(set)
    for audit_board in audit_boards:
        set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board["id"])
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board['id']}/ballots"
        )
        ballots = json.loads(rv.data)["ballots"]
        for ballot in ballots:
            audit_boards_by_container[ballot["batch"]["container"]].add(
                audit_board["id"]
            )
    for audit_board_ids in audit_boards_by_container.values():
        assert (
            len(audit_board_ids) == 1
        ), "Different audit boards assigned ballots from the same container"

    # Check that the second jurisdiction's audit boards have ballots divvied up by tabulator+batch name
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board"
    )
    audit_boards = json.loads(rv.data)["auditBoards"]

    audit_boards_by_tabulator_and_name = defaultdict(set)
    for audit_board in audit_boards:
        set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board["id"])
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board/{audit_board['id']}/ballots"
        )
        ballots = json.loads(rv.data)["ballots"]
        for ballot in ballots:
            audit_boards_by_tabulator_and_name[
                (ballot["batch"]["tabulator"], ballot["batch"]["name"])
            ].add(audit_board["id"])
    for audit_board_ids in audit_boards_by_tabulator_and_name.values():
        assert (
            len(audit_board_ids) == 1
        ), "Different audit boards assigned ballots from the same tabulator+name"


def test_ballot_comparison_manifest_missing_tabulator(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Container,Batch Name,Number of Ballots\n"
                    b"A,1,20\n"
                    b"A,2,20\n"
                    b"A,1,20\n"
                    b"A,2,20\n"
                    b"B,3,20\n"
                    b"B,4,20\n"
                    b"B,3,20\n"
                    b"B,4,20"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    bgcompute_update_ballot_manifest_file()

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "manifest.csv", "uploadedAt": assert_is_date},
            "processing": {
                "completedAt": assert_is_date,
                "error": "Missing required column: Tabulator.",
                "startedAt": assert_is_date,
                "status": "ERRORED",
            },
        },
    )

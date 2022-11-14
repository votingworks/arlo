import io
import json
from collections import defaultdict
from flask.testing import FlaskClient
import pytest

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


# In one jurisdiction, add the Container column to the manifest. In this
# jurisdiction, ballots should be divvied up between audit boards by container,
# not the usual tabulator+batch name.


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
                    b"Container,Tabulator,Batch Name,Number of Ballots\n"
                    b"CONTAINER1,TABULATOR1,BATCH1,50\n"
                    b"CONTAINER1,TABULATOR1,BATCH2,50\n"
                    b"CONTAINER1,TABULATOR2,BATCH1,50\n"
                    b"CONTAINER1,TABULATOR2,BATCH2,50\n"
                    b"CONTAINER2,TABULATOR1,BATCH3,50\n"
                    b"CONTAINER2,TABULATOR1,BATCH4,50\n"
                    b"CONTAINER2,TABULATOR2,BATCH3,50\n"
                    b"CONTAINER2,TABULATOR2,BATCH4,50\n"
                    b"CONTAINER3,TABULATOR1,BATCH5,50\n"
                    b"CONTAINER4,TABULATOR1,BATCH6,50\n"
                    b"CONTAINER5,TABULATOR2,BATCH5,50\n"
                    b"CONTAINER6,TABULATOR2,BATCH6,50\n"
                    b"CONTAINER7,TABULATOR1,BATCH7,50\n"
                    b"CONTAINER8,TABULATOR1,BATCH8,50\n"
                    b"CONTAINER9,TABULATOR2,BATCH7,50\n"
                    b"CONTAINER0,TABULATOR2,BATCH8,50\n"
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
                    b"TABULATOR1,BATCH1,50\n"
                    b"TABULATOR1,BATCH2,50\n"
                    b"TABULATOR2,BATCH1,50\n"
                    b"TABULATOR2,BATCH2,50"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)


@pytest.fixture
def cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    j1_cvr_lines = [
        f"TABULATOR{tabulator},BATCH{batch},{ballot},{tabulator}-{batch}-{ballot},x,x,{tabulator % 2},0,0,1,0"
        for tabulator in range(1, 3)
        for batch in range(1, 9)
        for ballot in range(1, 51)
    ]
    j1_cvr = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,Choice 1-1,Choice 1-2,Choice 2-1,Choice 2-2,Choice 2-3
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,PrecinctPortion,BallotType,REP,DEM,LBR,IND,,
    """ + "\n".join(
        [f"{i},{line}" for i, line in enumerate(j1_cvr_lines)]
    )

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (io.BytesIO(j1_cvr.encode()), "cvrs.csv",),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    j2_cvr_lines = [
        f"TABULATOR{tabulator},BATCH{batch},{ballot},{tabulator}-{batch}-{ballot},x,x,0,0,0,0,0"
        for tabulator in range(1, 3)
        for batch in range(1, 3)
        for ballot in range(1, 51)
    ]
    j2_cvr = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,Choice 1-1,Choice 1-2,Choice 2-1,Choice 2-2,Choice 2-3
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,PrecinctPortion,BallotType,REP,DEM,LBR,IND,,
    """ + "\n".join(
        [f"{i},{line}" for i, line in enumerate(j2_cvr_lines)]
    )

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={
            "cvrs": (io.BytesIO(j2_cvr.encode()), "cvrs.csv",),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)


def test_ballot_comparison_container_manifest(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
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
                "numWinners": 1,
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

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    sample_size = sample_size_options[target_contest_id][0]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {target_contest_id: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # JAs create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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

    # Check that the first jurisdiction's retrieval list includes Container
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots/retrieval-list"
    )
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    assert len(json.loads(rv.data)["ballots"]) == len(retrieval_list.splitlines()) - 1

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

        # Ensure sorted by container
        containers = [ballot["batch"]["container"] for ballot in ballots]
        assert containers == sorted(containers)

        for ballot in ballots:
            audit_boards_by_container[ballot["batch"]["container"]].add(
                audit_board["id"]
            )
    for audit_board_ids in audit_boards_by_container.values():
        assert (
            len(audit_board_ids) == 1
        ), "Different audit boards assigned ballots from the same container"

    # Check that the second jurisdiction's audit boards have ballots divvied up by tabulator+batch name
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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

    # Check that ballots are ordered by audit board then container for JA
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    audit_boards_and_containers = [
        (ballot["auditBoard"]["name"], ballot["batch"]["container"])
        for ballot in ballots
    ]
    assert audit_boards_and_containers == sorted(audit_boards_and_containers)

    # Check that Container is included in the audit report
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)


def test_ballot_comparison_manifest_missing_tabulator(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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


def test_ballot_comparison_manifest_unexpected_cvr_column(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Container,Tabulator,Batch Name,Number of Ballots,CVR\n"
                    b"CONTAINER1,TABULATOR1,BATCH1,50,Yes\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "manifest.csv", "uploadedAt": assert_is_date},
            "processing": {
                "completedAt": assert_is_date,
                "error": "Found unexpected columns. Allowed columns: Batch Name, Container, Number of Ballots, Tabulator.",
                "startedAt": assert_is_date,
                "status": "ERRORED",
            },
        },
    )

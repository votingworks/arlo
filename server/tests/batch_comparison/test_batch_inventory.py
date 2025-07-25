import pytest
from flask.testing import FlaskClient
from ..helpers import *  # pylint: disable=wildcard-import
from ...models import BatchInventoryData
from ..ballot_comparison.test_cvrs import (
    ESS_BALLOTS_1,
    ESS_BALLOTS_2,
    ESS_BALLOTS_WITH_MACHINE_COLUMN,
    ESS_BALLOTS_WITH_MACHINE_COLUMN_AND_NO_METADATA_ROWS,
    ESS_BALLOTS_WITH_NO_METADATA_ROWS,
    ESS_CVR,
    build_hart_cvr,
)

TEST_CVR = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,,,,,,
,,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,,Choice 1-1,Choice 1-2,Write-In,Choice 2-1,Choice 2-2,Choice 2-3,Write-In
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM,LBR,IND,,
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,0,1,1,1,0,0
2,TABULATOR1,BATCH1,2,1-1-2,Election Day,12345,COUNTY,1,0,0,1,0,1,0
3,TABULATOR1,BATCH1,3,1-1-3,Election Day,12345,COUNTY,0,1,0,1,1,0,0
4,TABULATOR1,BATCH2,1,1-2-1,Election Day,12345,COUNTY,1,0,0,1,0,1,0
5,TABULATOR1,BATCH2,2,1-2-2,Election Day,12345,COUNTY,0,1,0,1,1,0,0
6,TABULATOR1,BATCH2,3,1-2-3,Election Day,12345,COUNTY,1,0,0,1,0,1,0
7,TABULATOR2,BATCH1,1,2-1-1,Election Day,12345,COUNTY,0,1,0,1,1,0,0
8,TABULATOR2,BATCH1,2,2-1-2,Mail,12345,COUNTY,1,0,0,1,0,1,0
9,TABULATOR2,BATCH1,3,2-1-3,Mail,12345,COUNTY,1,0,0,1,1,0,0
10,TABULATOR2,BATCH2,1,2-2-1,Election Day,12345,COUNTY,1,0,0,1,0,1,0
11,TABULATOR2,BATCH2,2,2-2-2,Election Day,12345,COUNTY,1,1,0,1,1,0,0
12,TABULATOR2,BATCH2,3,2-2-3,Election Day,12345,COUNTY,1,0,0,1,0,1,0
13,TABULATOR2,BATCH2,4,2-2-4,Election Day,12345,CITY,,,,1,0,1,0
14,TABULATOR2,BATCH2,5,2-2-5,Election Day,12345,CITY,,,,1,1,0,0
15,TABULATOR2,BATCH2,6,2-2-6,Election Day,12345,CITY,,,,1,0,1,0
"""

# Overvote for contest Contest 1 in row 11
TEST_CVRS_WITH_LEADING_EQUAL_SIGNS = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,,,,,,
,,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,,Choice 1-1,Choice 1-2,Write-In,Choice 2-1,Choice 2-2,Choice 2-3,Write-In
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM,LBR,IND,,
="1",="TABULATOR1",="BATCH1",="1",="1-1-1",Election Day,12345,COUNTY,0,0,1,1,1,0,0
="2",="TABULATOR1",="BATCH1",="2",="1-1-2",Election Day,12345,COUNTY,1,0,0,1,0,1,0
="3",="TABULATOR1",="BATCH1",="3",="1-1-3",Election Day,12345,COUNTY,0,1,0,1,1,0,0
="4",="TABULATOR1",="BATCH2",="1",="1-2-1",Election Day,12345,COUNTY,1,0,0,1,0,1,0
="5",="TABULATOR1",="BATCH2",="2",="1-2-2",Election Day,12345,COUNTY,0,1,0,1,1,0,0
="6",="TABULATOR1",="BATCH2",="3",="1-2-3",Election Day,12345,COUNTY,1,0,0,1,0,1,0
="7",="TABULATOR2",="BATCH1",="1",="2-1-1",Election Day,12345,COUNTY,0,1,0,1,1,0,0
="8",="TABULATOR2",="BATCH1",="2",="2-1-2",Mail,12345,COUNTY,1,0,0,1,0,1,0
="9",="TABULATOR2",="BATCH1",="3",="2-1-3",Mail,12345,COUNTY,1,0,0,1,1,0,0
="10",="TABULATOR2",="BATCH2",="1",="2-2-1",Election Day,12345,COUNTY,1,0,0,1,0,1,0
="11",="TABULATOR2",="BATCH2",="2",="2-2-2",Election Day,12345,COUNTY,1,1,0,1,1,0,0
="12",="TABULATOR2",="BATCH2",="3",="2-2-3",Election Day,12345,COUNTY,1,0,0,1,0,1,0
="13",="TABULATOR2",="BATCH2",="4",="2-2-4",Election Day,12345,CITY,,,,1,0,1,0
="14",="TABULATOR2",="BATCH2",="5",="2-2-5",Election Day,12345,CITY,,,,1,1,0,0
="15",="TABULATOR2",="BATCH2",="6",="2-2-6",Election Day,12345,CITY,,,,1,0,1,0
"""

TEST_CVRS_WITH_EXTRA_SPACES = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,,,,,,
,,,,,,,,Contest 1  (Vote For=1),Contest 1  (Vote For=1),Contest 1  (Vote For=1),Contest 2  (Vote For=2),Contest 2  (Vote For=2),Contest 2  (Vote For=2),Contest 2  (Vote For=2)
,,,,,,,,Choice 1-1 ,  Choice 1-2  ,Write-In,Choice 2-1,Choice 2-2,Choice 2-3,Write-In
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM,LBR,IND,,
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,0,1,1,1,0,0
2,TABULATOR1,BATCH1,2,1-1-2,Election Day,12345,COUNTY,1,0,0,1,0,1,0
3,TABULATOR1,BATCH1,3,1-1-3,Election Day,12345,COUNTY,0,1,0,1,1,0,0
4,TABULATOR1,BATCH2,1,1-2-1,Election Day,12345,COUNTY,1,0,0,1,0,1,0
5,TABULATOR1,BATCH2,2,1-2-2,Election Day,12345,COUNTY,0,1,0,1,1,0,0
6,TABULATOR1,BATCH2,3,1-2-3,Election Day,12345,COUNTY,1,0,0,1,0,1,0
7,TABULATOR2,BATCH1,1,2-1-1,Election Day,12345,COUNTY,0,1,0,1,1,0,0
8,TABULATOR2,BATCH1,2,2-1-2,Mail,12345,COUNTY,1,0,0,1,0,1,0
9,TABULATOR2,BATCH1,3,2-1-3,Mail,12345,COUNTY,1,0,0,1,1,0,0
10,TABULATOR2,BATCH2,1,2-2-1,Election Day,12345,COUNTY,1,0,0,1,0,1,0
11,TABULATOR2,BATCH2,2,2-2-2,Election Day,12345,COUNTY,1,1,0,1,1,0,0
12,TABULATOR2,BATCH2,3,2-2-3,Election Day,12345,COUNTY,1,0,0,1,0,1,0
13,TABULATOR2,BATCH2,4,2-2-4,Election Day,12345,CITY,,,,1,0,1,0
14,TABULATOR2,BATCH2,5,2-2-5,Election Day,12345,CITY,,,,1,1,0,0
15,TABULATOR2,BATCH2,6,2-2-6,Election Day,12345,CITY,,,,1,0,1,0
"""

TEST_TABULATOR_STATUS = """<?xml version="1.0" standalone="yes"?>
<ExportName>
   <Terminology Subdivision="District" Subdivisions="Districts" PollingSubdivision="Precinct" PollingSubdivisions="Precincts" ParentSubdivision="Parent District" MultiPollingSubdivisionCollection="Multi-Precinct Collection" />
   <Report_Info name="Test Election" Report="Tabulator Status" Create="2022-08-11 13:38:55" unofficial="Unofficial">
      <Information Description="Election Project Name">Test Election</Information>
      <Information Description="Report Name">Tabulator Status</Information>
      <Information Description="Creation Date">2022-08-11 13:38:55</Information>
      <Information Description="Note">Results are unofficial</Information>
   </Report_Info>
   <settings>
      <ch officialResults="0" useCustomTitle="0" showFilters="1" />
   </settings>
   <tabulators>
      <tb id="1" tid="TABULATOR1" name="Tabulator 1" />
      <tb id="2" tid="TABULATOR2" name="Tabulator 2" />
   </tabulators>
   <ballots>
      <bm tbid="1" num="6" />
      <bm tbid="2" num="9" />
   </ballots>
</ExportName>
"""


@pytest.fixture
def contest_id(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            # Double the actual number of votes in TEST_CVR to account for the two jurisdictions
            {"id": str(uuid.uuid4()), "name": "Choice 1-1", "numVotes": 14},
            {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 6},
            {"id": str(uuid.uuid4()), "name": "Write-In", "numVotes": 2},
        ],
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids[:2],
    }
    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert_ok(rv)
    return str(contest["id"])


@pytest.fixture
def contest_ids(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest1 = {
        "id": str(uuid.uuid4()),
        "name": "Contest 1",
        "isTargeted": True,
        "choices": [
            # Double the actual number of votes in TEST_CVR to account for the two jurisdictions
            {"id": str(uuid.uuid4()), "name": "Choice 1-1", "numVotes": 14},
            {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 6},
            {"id": str(uuid.uuid4()), "name": "Write-In", "numVotes": 0},
        ],
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids[:2],
    }
    contest2 = {
        "id": str(uuid.uuid4()),
        "name": "Contest 2",
        "isTargeted": True,
        "choices": [
            # Double the actual number of votes in TEST_CVR to account for the two jurisdictions
            {"id": str(uuid.uuid4()), "name": "Choice 2-1", "numVotes": 30},
            {"id": str(uuid.uuid4()), "name": "Choice 2-2", "numVotes": 14},
            {"id": str(uuid.uuid4()), "name": "Choice 2-3", "numVotes": 14},
            {"id": str(uuid.uuid4()), "name": "Write-In", "numVotes": 0},
        ],
        "numWinners": 1,
        "votesAllowed": 2,
        "jurisdictionIds": jurisdiction_ids[:2],
    }
    contests = [contest1, contest2]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(contest["id"]) for contest in contests]


def test_batch_inventory_happy_path(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Load batch inventory starting state (simulate JA loading the page)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    response = json.loads(rv.data)
    assert response == dict(systemType=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    cvr = json.loads(rv.data)
    assert cvr == dict(file=None, processing=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    tabulator_status = json.loads(rv.data)
    assert tabulator_status == dict(file=None, processing=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    sign_off = json.loads(rv.data)
    assert sign_off == dict(signedOffAt=None)

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    compare_json(json.loads(rv.data), {"systemType": CvrFileType.DOMINION})

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_inventory_cvrs"),
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

    # Upload tabulator status file
    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(TEST_TABULATOR_STATUS.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_inventory_tabulator_status"),
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

    # Download worksheet
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/worksheet"
    )
    snapshot.assert_match(rv.data.decode("utf-8"))

    # Sign off
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    compare_json(json.loads(rv.data), {"signedOffAt": assert_is_date})
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction_ids[0])
    assert (
        batch_inventory_data.sign_off_user_id
        == User.query.filter_by(email=default_ja_email(election_id)).one().id
    )

    # Download manifest
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/ballot-manifest"
    )
    ballot_manifest = rv.data.decode("utf-8")
    snapshot.assert_match(ballot_manifest)

    # Download batch tallies
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/batch-tallies"
    )
    batch_tallies = rv.data.decode("utf-8")
    snapshot.assert_match(batch_tallies)

    # Upload manifest
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(ballot_manifest.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
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

    # Upload batch tallies
    rv = upload_batch_tallies(
        client,
        io.BytesIO(batch_tallies.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_tallies"),
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

    # Download CVR file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr/file"
    )
    assert rv.data.decode("utf-8") == TEST_CVR

    # Download tabulator status file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status/file"
    )
    assert rv.data.decode("utf-8") == TEST_TABULATOR_STATUS


def test_batch_inventory_happy_path_cvrs_with_leading_equal_signs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Load batch inventory starting state (simulate JA loading the page)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    response = json.loads(rv.data)
    assert response == dict(systemType=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    cvr = json.loads(rv.data)
    assert cvr == dict(file=None, processing=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    tabulator_status = json.loads(rv.data)
    assert tabulator_status == dict(file=None, processing=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    sign_off = json.loads(rv.data)
    assert sign_off == dict(signedOffAt=None)

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    compare_json(json.loads(rv.data), {"systemType": CvrFileType.DOMINION})

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVRS_WITH_LEADING_EQUAL_SIGNS.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_inventory_cvrs"),
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

    # Upload tabulator status file
    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(TEST_TABULATOR_STATUS.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_inventory_tabulator_status"),
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

    # Download worksheet
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/worksheet"
    )
    snapshot.assert_match(rv.data.decode("utf-8"))

    # Sign off
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    compare_json(json.loads(rv.data), {"signedOffAt": assert_is_date})
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction_ids[0])
    assert (
        batch_inventory_data.sign_off_user_id
        == User.query.filter_by(email=default_ja_email(election_id)).one().id
    )

    # Download manifest
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/ballot-manifest"
    )
    ballot_manifest = rv.data.decode("utf-8")
    snapshot.assert_match(ballot_manifest)

    # Download batch tallies
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/batch-tallies"
    )
    batch_tallies = rv.data.decode("utf-8")
    snapshot.assert_match(batch_tallies)

    # Upload manifest
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(ballot_manifest.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
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

    # Upload batch tallies
    rv = upload_batch_tallies(
        client,
        io.BytesIO(batch_tallies.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_tallies"),
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

    # Download CVR file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr/file"
    )
    assert rv.data.decode("utf-8") == TEST_CVRS_WITH_LEADING_EQUAL_SIGNS

    # Download tabulator status file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status/file"
    )
    assert rv.data.decode("utf-8") == TEST_TABULATOR_STATUS


def test_batch_inventory_happy_path_cvrs_with_extra_spaces(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Load batch inventory starting state (simulate JA loading the page)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    response = json.loads(rv.data)
    assert response == dict(systemType=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    cvr = json.loads(rv.data)
    assert cvr == dict(file=None, processing=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    tabulator_status = json.loads(rv.data)
    assert tabulator_status == dict(file=None, processing=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    sign_off = json.loads(rv.data)
    assert sign_off == dict(signedOffAt=None)

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    compare_json(json.loads(rv.data), {"systemType": CvrFileType.DOMINION})

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVRS_WITH_EXTRA_SPACES.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_inventory_cvrs"),
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

    # Upload tabulator status file
    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(TEST_TABULATOR_STATUS.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_inventory_tabulator_status"),
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

    # Download worksheet
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/worksheet"
    )
    snapshot.assert_match(rv.data.decode("utf-8"))

    # Sign off
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    compare_json(json.loads(rv.data), {"signedOffAt": assert_is_date})
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction_ids[0])
    assert (
        batch_inventory_data.sign_off_user_id
        == User.query.filter_by(email=default_ja_email(election_id)).one().id
    )

    # Download manifest
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/ballot-manifest"
    )
    ballot_manifest = rv.data.decode("utf-8")
    snapshot.assert_match(ballot_manifest)

    # Download batch tallies
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/batch-tallies"
    )
    batch_tallies = rv.data.decode("utf-8")
    snapshot.assert_match(batch_tallies)

    # Upload manifest
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(ballot_manifest.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
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

    # Upload batch tallies
    rv = upload_batch_tallies(
        client,
        io.BytesIO(batch_tallies.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_tallies"),
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

    # Download CVR file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr/file"
    )
    assert rv.data.decode("utf-8") == TEST_CVRS_WITH_EXTRA_SPACES

    # Download tabulator status file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status/file"
    )
    assert rv.data.decode("utf-8") == TEST_TABULATOR_STATUS


def test_batch_inventory_happy_path_multi_contest_batch_comparison(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Load batch inventory starting state (simulate JA loading the page)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    response = json.loads(rv.data)
    assert response == dict(systemType=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    cvr = json.loads(rv.data)
    assert cvr == dict(file=None, processing=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    tabulator_status = json.loads(rv.data)
    assert tabulator_status == dict(file=None, processing=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    sign_off = json.loads(rv.data)
    assert sign_off == dict(signedOffAt=None)

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    compare_json(json.loads(rv.data), {"systemType": CvrFileType.DOMINION})

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_inventory_cvrs"),
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

    # Upload tabulator status file
    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(TEST_TABULATOR_STATUS.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_inventory_tabulator_status"),
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

    # Download worksheet
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/worksheet"
    )
    snapshot.assert_match(rv.data.decode("utf-8"))

    # Sign off
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    compare_json(json.loads(rv.data), {"signedOffAt": assert_is_date})
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction_ids[0])
    assert (
        batch_inventory_data.sign_off_user_id
        == User.query.filter_by(email=default_ja_email(election_id)).one().id
    )

    # Download manifest
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/ballot-manifest"
    )
    ballot_manifest = rv.data.decode("utf-8")
    snapshot.assert_match(ballot_manifest)

    # Download batch tallies
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/batch-tallies"
    )
    batch_tallies = rv.data.decode("utf-8")
    snapshot.assert_match(batch_tallies)

    # Upload manifest
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(ballot_manifest.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
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

    # Upload batch tallies
    rv = upload_batch_tallies(
        client,
        io.BytesIO(batch_tallies.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_tallies"),
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

    # Download CVR file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr/file"
    )
    assert rv.data.decode("utf-8") == TEST_CVR

    # Download tabulator status file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status/file"
    )
    assert rv.data.decode("utf-8") == TEST_TABULATOR_STATUS


def test_batch_inventory_download_before_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Try to download CVR file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr/file"
    )
    assert rv.status_code == 404

    # Try to download tabulator status file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status/file"
    )
    assert rv.status_code == 404


def test_batch_inventory_invalid_file_uploads(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    # Upload invalid CVR files
    invalid_cvrs = [
        (
            TEST_CVR.replace("Contest 1", "Contest X"),
            "Could not find contests in CVR file: Contest 1 (Vote For=1).",
        ),
        (
            # Expected contest name with the wrong number of allowed votes
            TEST_CVR.replace("Contest 1 (Vote For=1)", "Contest 1 (Vote For=2)"),
            "Could not find contests in CVR file: Contest 1 (Vote For=1).",
        ),
        (
            TEST_CVR.replace("Choice 1-1", "Choice X"),
            "Could not find contest choices in CVR file: Choice 1-1 for contest Contest 1.",
        ),
        (
            # Expected choice name under the wrong contest
            TEST_CVR.replace("Choice 1-1", "Choice X").replace(
                "Choice 2-1", "Choice 1-1"
            ),
            "Could not find contest choices in CVR file: Choice 1-1 for contest Contest 1.",
        ),
    ]
    for invalid_cvr, expected_error in invalid_cvrs:
        rv = upload_batch_inventory_cvr(
            client,
            io.BytesIO(invalid_cvr.encode()),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
        )
        cvr = json.loads(rv.data)
        assert cvr["processing"]["status"] == ProcessingStatus.ERRORED
        assert cvr["processing"]["error"] == expected_error

        rv = client.delete(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
        )
        assert_ok(rv)

    # Upload valid CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    cvr = json.loads(rv.data)
    assert cvr["processing"]["status"] == ProcessingStatus.PROCESSED

    # Upload tabulator status file with missing tabulator
    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(
            TEST_TABULATOR_STATUS.replace(
                '<tb id="1" tid="TABULATOR1" name="Tabulator 1" />', ""
            ).encode()
        ),
        election_id,
        jurisdiction_ids[0],
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    tabulator_status = json.loads(rv.data)
    assert tabulator_status["processing"]["status"] == ProcessingStatus.ERRORED
    assert (
        tabulator_status["processing"]["error"]
        == "Could not find some tabulators from CVR file in Tabulator Status file. Missing tabulator IDs: TABULATOR1."
    )

    # Re-upload CVR file without the missing tabulator
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    assert_ok(rv)

    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(
            TEST_CVR.replace(
                """1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,0,1,1,1,0,0
2,TABULATOR1,BATCH1,2,1-1-2,Election Day,12345,COUNTY,1,0,0,1,0,1,0
3,TABULATOR1,BATCH1,3,1-1-3,Election Day,12345,COUNTY,0,1,0,1,1,0,0
4,TABULATOR1,BATCH2,1,1-2-1,Election Day,12345,COUNTY,1,0,0,1,0,1,0
5,TABULATOR1,BATCH2,2,1-2-2,Election Day,12345,COUNTY,0,1,0,1,1,0,0
6,TABULATOR1,BATCH2,3,1-2-3,Election Day,12345,COUNTY,1,0,0,1,0,1,0
""",
                "",
            ).encode()
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    cvr = json.loads(rv.data)
    assert cvr["processing"]["status"] == ProcessingStatus.PROCESSED

    # Tabulator status should have been reprocessed
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    tabulator_status = json.loads(rv.data)
    assert tabulator_status["processing"]["status"] == ProcessingStatus.PROCESSED


def test_batch_inventory_missing_data_multi_contest_batch_comparison(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    invalid_cvrs = [
        (
            TEST_CVR.replace("Contest 2", "Contest X"),
            "Could not find contests in CVR file: Contest 2 (Vote For=2).",
        ),
        (
            # Expected contest name with the wrong number of allowed votes
            TEST_CVR.replace("Contest 2 (Vote For=2)", "Contest 2 (Vote For=1)"),
            "Could not find contests in CVR file: Contest 2 (Vote For=2).",
        ),
        (
            TEST_CVR.replace("Choice 2-1", "Choice X"),
            "Could not find contest choices in CVR file: Choice 2-1 for contest Contest 2.",
        ),
    ]
    for invalid_cvr, expected_error in invalid_cvrs:
        rv = upload_batch_inventory_cvr(
            client,
            io.BytesIO(invalid_cvr.encode()),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
        )
        cvr = json.loads(rv.data)
        assert cvr["processing"]["status"] == ProcessingStatus.ERRORED
        assert cvr["processing"]["error"] == expected_error

        rv = client.delete(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
        )
        assert_ok(rv)


def test_batch_inventory_excel_tabulator_status_file(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    # Upload tabulator status "To Excel" version
    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(
            b"""<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet" xmlns:html="http://www.w3.org/TR/REC-html40" xmlns:msxsl="urn:schemas-microsoft-com:xslt">
<Styles>
<Style ss:ID="Number">
<NumberFormat ss:Format="###,###,##0"/>
</Style>
<Style ss:ID="NumberBold">
<Font ss:FontName="Calibri" x:Family="Swiss" ss:Color="#000000" ss:Bold="1"/>
<NumberFormat ss:Format="###,###,##0"/>
</Style>
<Style ss:ID="StyleHeaderTop">
<Borders>
<Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1"/>
</Borders>
</Style>
<Style ss:ID="StyleHeaderBottom">
<Borders>
<Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1"/>
</Borders>
</Style>
<Style ss:ID="StyleClean"/>
<Style ss:ID="StyleRed">
<Borders>
<Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1"/>
<Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1"/>
<Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1"/>
<Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1"/>
</Borders>
<Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#FFFFFF" ss:Bold="1"/>
<Interior ss:Color="#C00000" ss:Pattern="Solid"/>
</Style>
<Style ss:ID="TitleBold">
<Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="14" ss:Color="#000000" ss:Bold="1"/>
</Style>
<Style ss:ID="HeaderBold">
<Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Bold="1"/>
</Style>
<Style ss:ID="TotalBold">
<Borders>
<Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1"/>
</Borders>
<Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Bold="1"/>
</Style>
<Style ss:ID="TextBold">
<Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000" ss:Bold="1"/>
</Style>
</Styles>
<Worksheet ss:Name="Tabulator Status">
<Table>
<Column ss:AutoFitWidth="0" ss:Width="90"/>
<Column ss:AutoFitWidth="0" ss:Width="300"/>
<Column ss:AutoFitWidth="0" ss:Width="90"/>
<Column ss:AutoFitWidth="0" ss:Width="150"/>
<Row ss:Height="15">
<Cell ss:StyleID="StyleHeaderTop">
<Data ss:Type="String">Tabulator Status</Data>
</Cell>
</Row>
<Row ss:Height="15">
<Cell>
<Data ss:Type="String">2022 11 08 Gen</Data>
</Cell>
</Row>
<Row ss:Height="15">
<Cell>
<Data ss:Type="String">Unofficial</Data>
</Cell>
</Row>
<Row ss:Height="15">
<Cell ss:StyleID="StyleHeaderBottom">
<Data ss:Type="String">2022-11-14 16:31:52</Data>
</Cell>
</Row>
<Row/>
<Row ss:Height="15">
<Cell ss:StyleID="HeaderBold">
<Data ss:Type="String"> Tabulator Id </Data>
</Cell>
<Cell ss:StyleID="HeaderBold">
<Data ss:Type="String"> Name </Data>
</Cell>
<Cell ss:StyleID="HeaderBold">
<Data ss:Type="String"> Load Status </Data>
</Cell>
<Cell ss:StyleID="HeaderBold">
<Data ss:Type="String"> Total Ballots Cast </Data>
</Cell>
</Row>
<Row>
<Cell>
<Data ss:Type="String">TABULATOR1</Data>
</Cell>
<Cell>
<Data ss:Type="String">Tabulator 1</Data>
</Cell>
<Cell>
<Data ss:Type="Number">1</Data>
</Cell>
<Cell ss:StyleID="Number">
<Data ss:Type="Number">123</Data>
</Cell>
</Row>
<Row>
<Cell>
<Data ss:Type="String">TABULATOR2</Data>
</Cell>
<Cell>
<Data ss:Type="String">Tabulator 2</Data>
</Cell>
<Cell>
<Data ss:Type="Number">1</Data>
</Cell>
<Cell ss:StyleID="Number">
<Data ss:Type="Number">456</Data>
</Cell>
</Row>
</Table>
</Worksheet>
</Workbook>
"""
        ),
        election_id,
        jurisdiction_ids[0],
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_inventory_tabulator_status"),
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

    # Download worksheet
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/worksheet"
    )
    snapshot.assert_match(rv.data.decode("utf-8"))


def test_batch_inventory_wrong_tabulator_status_file(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    # Upload tabulator status HTML version
    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(
            b"""<html xmlns:msxsl="urn:schemas-microsoft-com:xslt" xmlns:user="http://www.contoso.com">
  <head>
    <META http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Tabulator Status</title>
    <style>
body {font-family:Geneva, Arial, Helvetica, sans-serif; font-size:100%;}
list {font-family:Geneva, Arial, Helvetica, sans-serif; font-size:60%;}
h1 {  font-size: 1.5em; line-height=100%}
h2 {  font-size: 1.375e; line-height=100%}
h3 {  font-size: 0.625em; line-height=62.5%}
h4 {  font-size: 1em; line-height=100%}
h5 {  font-size: 0.9em; line-height=80%; text-decoration: underline;}
h6 {  font-size: 0.625em; line-height=20%;}
p { line-height=100%}
.contest {font-family:Geneva, Arial, Helvetica, sans-serif; font-size: 0.7em; text-decoration: underline;}
.stattable {font-family:Geneva, Arial, Helvetica, sans-serif; font-size: 0.7em;}
.num {text-align: right; }
.affiliation {text-align: right;}
.tabulator {font-family:Geneva, Arial, Helvetica, sans-serif; font-size: 0.6em; }
.total { font-weight: bold; }
.totalnum { font-weight: bold; text-align: right;}
</style>
  </head>
  <body>
    <table cellpadding="0" cellspacing="0">
      <tr>
        <td>
          <hr>
        </td>
      </tr>
      <tr>
        <td>
          <h1>
            <center>Tabulator Status</center>
          </h1>
        </td>
      </tr>
      <tr>
        <td>
          <h1>
            <center>2022 11 08 Gen</center>
          </h1>
        </td>
      </tr>
      <tr>
        <td>
          <h2>
            <center>Unofficial</center>
          </h2>
        </td>
      </tr>
      <tr>
        <td>
          <h3>
            <center>2022-11-14 18:58:16</center>
          </h3>
        </td>
      </tr>
      <tr>
        <td>
          <hr>
        </td>
      </tr>
    </table>
    <table class="stattable" border="1" bgcolor="#FFFFFF" cellspacing="0" cellborder="1">
      <tr>
        <td bgcolor="#CCCCCC">Tabulator ID</td>
        <td bgcolor="#CCCCCC">Name</td>
        <td bgcolor="#CCCCCC">Load Status</td>
        <td bgcolor="#CCCCCC">Total Ballots Cast</td>
      </tr>
      <tr>
        <td>10</td>
        <td>ED-ICP 1</td>
        <td>1</td>
        <td class="num">538</td>
      </tr>
    </table>
  </body>
</html>
"""
        ),
        election_id,
        jurisdiction_ids[0],
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    tabulator_status = json.loads(rv.data)
    assert tabulator_status["processing"]["status"] == ProcessingStatus.ERRORED
    assert (
        tabulator_status["processing"]["error"]
        == 'We could not parse this file. Please make sure you upload either the plain XML version or Excel version of the tabulator status report. The file name should end in ".xml".'
    )


def test_batch_inventory_undo_sign_off(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    # Upload tabulator status file
    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(TEST_TABULATOR_STATUS.encode()),
        election_id,
        jurisdiction_ids[0],
    )

    # Sign off
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    assert_ok(rv)

    # Undo sign off
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    assert_ok(rv)

    # Sign off should be cleared
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    sign_off = json.loads(rv.data)
    assert sign_off == dict(signedOffAt=None)


def test_batch_inventory_delete_cvr_after_sign_off(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    # Upload tabulator status file
    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(TEST_TABULATOR_STATUS.encode()),
        election_id,
        jurisdiction_ids[0],
    )

    # Sign off
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    assert_ok(rv)

    # Delete CVR file
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    assert_ok(rv)

    # Sign off should be cleared
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    sign_off = json.loads(rv.data)
    assert sign_off == dict(signedOffAt=None)


def test_batch_inventory_delete_tabulator_status_after_sign_off(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    # Upload tabulator status file
    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(TEST_TABULATOR_STATUS.encode()),
        election_id,
        jurisdiction_ids[0],
    )

    # Sign off
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    assert_ok(rv)

    # Delete tabulator status file
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    assert_ok(rv)

    # Sign off should be cleared
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    sign_off = json.loads(rv.data)
    assert sign_off == dict(signedOffAt=None)


def test_batch_inventory_upload_cvr_before_contests(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Jurisdiction does not have any contests assigned.",
            }
        ]
    }


def test_batch_inventory_upload_tabulator_status_before_cvr(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    rv = upload_batch_inventory_tabulator_status(
        client,
        io.BytesIO(TEST_TABULATOR_STATUS.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Must upload CVR file before uploading tabulator status file.",
            }
        ]
    }


def test_batch_inventory_cvr_get_upload_url_missing_file_type(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr/upload-url"
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing expected query parameter: fileType",
            }
        ]
    }


def test_batch_inventory_cvr_get_upload_url(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr/upload-url",
        query_string={"fileType": "text/csv"},
    )
    assert rv.status_code == 200

    response_data = json.loads(rv.data)
    expected_url = "/api/file-upload"

    assert response_data["url"] == expected_url
    assert response_data["fields"]["key"].startswith(
        f"audits/{election_id}/jurisdictions/{jurisdiction_ids[0]}/batch_inventory_cvrs_"
    )
    assert response_data["fields"]["key"].endswith(".csv")


def test_batch_inventory_tabulator_status_get_upload_url_missing_file_type(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status/upload-url"
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing expected query parameter: fileType",
            }
        ]
    }


def test_batch_inventory_tabulator_status_get_upload_url(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status/upload-url",
        query_string={"fileType": "application/xml"},
    )
    assert rv.status_code == 200

    response_data = json.loads(rv.data)
    expected_url = "/api/file-upload"

    assert response_data["url"] == expected_url
    assert response_data["fields"]["key"].startswith(
        f"audits/{election_id}/jurisdictions/{jurisdiction_ids[0]}/batch_inventory_tabulator_status_"
    )
    assert response_data["fields"]["key"].endswith(".xml")


def test_upload_tabulator_status_file_while_cvr_file_is_processing_fails(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    with no_automatic_task_execution():
        # upload CVR file, but don't process it
        rv = upload_batch_inventory_cvr(
            client,
            io.BytesIO(b"does not matter"),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        # upload tabulator status file
        rv = upload_batch_inventory_tabulator_status(
            client,
            io.BytesIO(b"does not matter"),
            election_id,
            jurisdiction_ids[0],
        )

        assert rv.status_code == 409
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Conflict",
                    "message": "Cannot upload tabulator status while CVR file is processing.",
                }
            ]
        }


def test_remove_tabulator_status_file_while_cvr_file_is_processing_fails(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    with no_automatic_task_execution():
        # Upload CVR file, but don't process it
        rv = upload_batch_inventory_cvr(
            client,
            io.BytesIO(b"does not matter"),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = client.delete(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
        )

        assert rv.status_code == 409
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Conflict",
                    "message": "Cannot remove tabulator status while CVR file is processing.",
                }
            ]
        }


def test_upload_cvr_file_while_tabulator_status_file_is_processing_fails(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    with no_automatic_task_execution():
        # Upload tabulator status file, but don't process it
        rv = upload_batch_inventory_tabulator_status(
            client,
            io.BytesIO(b"does not matter"),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = upload_batch_inventory_cvr(
            client,
            io.BytesIO(b"does not matter"),
            election_id,
            jurisdiction_ids[0],
        )

        assert rv.status_code == 409
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Conflict",
                    "message": "Cannot upload CVRs while tabulator status file is processing.",
                }
            ]
        }


def test_remove_cvr_file_while_tabulator_status_file_is_processing_fails(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.DOMINION},
    )
    assert_ok(rv)

    # Upload CVR file
    rv = upload_batch_inventory_cvr(
        client,
        io.BytesIO(TEST_CVR.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    with no_automatic_task_execution():
        # Upload tabulator status file, but don't process it
        rv = upload_batch_inventory_tabulator_status(
            client,
            io.BytesIO(b"does not matter"),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = client.delete(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
        )

        assert rv.status_code == 409
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Conflict",
                    "message": "Cannot remove CVRs while tabulator status file is processing.",
                }
            ]
        }


def test_batch_inventory_hart_cvr_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    response = json.loads(rv.data)
    assert response == dict(systemType=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    cvr = json.loads(rv.data)
    assert cvr == dict(file=None, processing=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    sign_off = json.loads(rv.data)
    assert sign_off == dict(signedOffAt=None)

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.HART},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    compare_json(json.loads(rv.data), {"systemType": CvrFileType.HART})

    hart_cvrs = [
        build_hart_cvr("BATCH1", "1", "1-1-1", "0,1,1,0,0"),
        build_hart_cvr("BATCH1", "2", "1-1-2", "1,0,1,0,0"),
        build_hart_cvr("BATCH1", "3", "1-1-3", "0,1,1,0,0"),
        build_hart_cvr(
            "BATCH1", "4", "1-1-4", "1,1,1,1,1"
        ),  # Overvote, ballot manifest should include in ballot count, candidate-totals-by-batch should not include in vote counts
        build_hart_cvr("BATCH2", "1", "1-2-1", "1,0,1,0,0"),
        build_hart_cvr("BATCH2", "2", "1-2-2", "0,1,0,1,0"),
        build_hart_cvr("BATCH2", "3", "1-2-3", "1,0,0,0,1"),
        build_hart_cvr("BATCH3", "1", "1-3-1", ",,1,0,0"),
        build_hart_cvr("BATCH3", "2", "1-3-2", ",,1,0,0"),
        build_hart_cvr("BATCH4", "1", "1-4-1", "1,0,0,0,1"),
        build_hart_cvr("BATCH4", "1", "1-4-1", "1,0,0,0,1", add_write_in=True),
    ]
    hart_zip = zip_hart_cvrs(hart_cvrs)

    # Upload HART CVR file
    rv = upload_batch_inventory_cvr(
        client,
        hart_zip,
        election_id,
        jurisdiction_ids[0],
        "application/zip",
    )
    assert_ok(rv)

    # Download manifest
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/ballot-manifest"
    )
    ballot_manifest = rv.data.decode("utf-8")
    snapshot.assert_match(ballot_manifest)

    # Download batch tallies
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/batch-tallies"
    )
    batch_tallies = rv.data.decode("utf-8")
    snapshot.assert_match(batch_tallies)

    # Upload manifest - should be a valid file
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(ballot_manifest.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
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

    # Upload batch tallies - should be a valid file
    rv = upload_batch_tallies(
        client,
        io.BytesIO(batch_tallies.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_tallies"),
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


def test_batch_inventory_hart_cvr_upload_multi_contest(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: str,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    response = json.loads(rv.data)
    assert response == dict(systemType=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    cvr = json.loads(rv.data)
    assert cvr == dict(file=None, processing=None)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/sign-off"
    )
    sign_off = json.loads(rv.data)
    assert sign_off == dict(signedOffAt=None)

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.HART},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    compare_json(json.loads(rv.data), {"systemType": CvrFileType.HART})

    hart_cvrs = [
        build_hart_cvr("BATCH1", "1", "1-1-1", "0,1,1,1,0"),
        build_hart_cvr("BATCH1", "2", "1-1-2", "1,0,1,0,1"),
        build_hart_cvr("BATCH1", "3", "1-1-3", "0,1,1,1,0"),
        build_hart_cvr("BATCH2", "1", "1-2-1", "1,0,1,0,1"),
        build_hart_cvr("BATCH2", "2", "1-2-2", "0,1,1,1,0"),
        build_hart_cvr("BATCH2", "3", "1-2-3", "1,0,1,0,1"),
        build_hart_cvr("BATCH3", "1", "1-3-1", ",,0,1,0"),
        build_hart_cvr("BATCH3", "2", "1-3-2", ",,0,0,1"),
        build_hart_cvr("BATCH4", "1", "1-4-1", "1,0,0,0,1"),
        build_hart_cvr("BATCH4", "1", "1-4-1", "1,0,0,0,1", add_write_in=True),
    ]
    hart_zip = zip_hart_cvrs(hart_cvrs)

    # Upload HART CVR file
    rv = upload_batch_inventory_cvr(
        client,
        hart_zip,
        election_id,
        jurisdiction_ids[0],
        "application/zip",
    )
    assert_ok(rv)

    # Download manifest
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/ballot-manifest"
    )
    ballot_manifest = rv.data.decode("utf-8")
    snapshot.assert_match(ballot_manifest)

    # Download batch tallies
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/batch-tallies"
    )
    batch_tallies = rv.data.decode("utf-8")
    snapshot.assert_match(batch_tallies)

    # Upload manifest - should be a valid file
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(ballot_manifest.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
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

    # Upload batch tallies - should be a valid file
    rv = upload_batch_tallies(
        client,
        io.BytesIO(batch_tallies.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_tallies"),
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


def test_batch_inventory_ess_cvr_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
    snapshot,
):
    # Set the logged-in user to Jurisdiction Admin
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.ESS},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    compare_json(json.loads(rv.data), {"systemType": CvrFileType.ESS})

    test_cases = [
        [
            (io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv"),
            (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv"),
            (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv"),
        ],
        [
            (io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv"),
            (io.BytesIO(ESS_BALLOTS_WITH_NO_METADATA_ROWS.encode()), "ess_ballots.csv"),
        ],
        [
            (io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv"),
            (io.BytesIO(ESS_BALLOTS_WITH_MACHINE_COLUMN.encode()), "ess_ballots.csv"),
        ],
        [
            (io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv"),
            (
                io.BytesIO(
                    ESS_BALLOTS_WITH_MACHINE_COLUMN_AND_NO_METADATA_ROWS.encode()
                ),
                "ess_ballots.csv",
            ),
        ],
    ]
    for cvrs in test_cases:

        # Upload ESS CVR file
        rv = upload_batch_inventory_cvr(
            client,
            zip_cvrs(cvrs),
            election_id,
            jurisdiction_ids[0],
            "application/zip",
        )
        assert_ok(rv)

        # Verify the uploaded CVR file
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
        )
        compare_json(json.loads(rv.data), {"systemType": CvrFileType.ESS})

        # Download manifest
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/ballot-manifest"
        )
        ballot_manifest = rv.data.decode("utf-8")
        snapshot.assert_match(ballot_manifest)

        # Download batch tallies
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/batch-tallies"
        )
        batch_tallies = rv.data.decode("utf-8")
        snapshot.assert_match(batch_tallies)

        # Upload manifest - should be a valid file
        rv = upload_ballot_manifest(
            client,
            io.BytesIO(ballot_manifest.encode()),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "name": asserts_startswith("manifest"),
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

        # Upload batch tallies - should be a valid file
        rv = upload_batch_tallies(
            client,
            io.BytesIO(batch_tallies.encode()),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "name": asserts_startswith("batch_tallies"),
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

        # Delete CVR file
        rv = client.delete(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
        )
        assert_ok(rv)

        # Delete ballot manifest
        rv = client.delete(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
        )
        assert_ok(rv)

        # Delete batch tallies
        rv = client.delete(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
        )
        assert_ok(rv)


ESS_CVR_WITH_BATCH_CVR_COLUMN = """Unknown Column,Cast Vote Record,Precinct,Ballot Style,Batch,Contest 1,Contest 2
x,1,p,bs,Batch 1,Choice 1-2,Choice 2-1
x,2,p,bs,Batch 1,Choice 1-1,Choice 2-1
x,3,p,bs,Batch 2,undervote,Choice 2-1
x,4,p,bs,Batch 2,overvote,Choice 2-1
x,5,p,bs,Batch 1,Write-in,Choice 2-1
x,6,p,bs,Batch 1,Choice 1-1,Choice 2-1
x,7,p,bs,Batch 2,Choice 1-2,Choice 2-1
x,8,p,bs,Batch 2,Choice 1-1,Choice 2-1
x,9,p,bs,Batch 2,Choice 1-2,Choice 2-2
x,10,p,bs,Batch 3,Write-in,Choice 2-2
x,11,p,bs,Batch 3,Choice 1-2,Choice 2-2
x,12,p,bs,Batch 3,Choice 1-1,Choice 2-2
x,13,p,bs,Batch 3,Choice 1-2,Choice 2-3
x,15,p,bs,Batch 3,Choice 1-1,Choice 2-3
"""

ESS_CVR_WITH_BATCH_NAME_CVR_COLUMN = """Unknown Column,Cast Vote Record,Precinct,Ballot Style,Batch Name,Contest 1,Contest 2
x,1,p,bs,Batch 1,Choice 1-2,Choice 2-1
x,2,p,bs,Batch 1,Choice 1-1,Choice 2-1
x,3,p,bs,Batch 2,undervote,Choice 2-1
x,4,p,bs,Batch 2,overvote,Choice 2-1
x,5,p,bs,Batch 1,Write-in,Choice 2-1
x,6,p,bs,Batch 1,Choice 1-1,Choice 2-1
x,7,p,bs,Batch 2,Choice 1-2,Choice 2-1
x,8,p,bs,Batch 2,Choice 1-1,Choice 2-1
x,9,p,bs,Batch 2,Choice 1-2,Choice 2-2
x,10,p,bs,Batch 3,Write-in,Choice 2-2
x,11,p,bs,Batch 3,Choice 1-2,Choice 2-2
x,12,p,bs,Batch 3,Choice 1-1,Choice 2-2
x,13,p,bs,Batch 3,Choice 1-2,Choice 2-3
x,15,p,bs,Batch 3,Choice 1-1,Choice 2-3
"""


def test_batch_inventory_ess_cvr_upload_no_ballot_file(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
    snapshot,
):
    # Set the logged-in user to Jurisdiction Admin
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.ESS},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    compare_json(json.loads(rv.data), {"systemType": CvrFileType.ESS})

    test_cases = [ESS_CVR_WITH_BATCH_CVR_COLUMN, ESS_CVR_WITH_BATCH_NAME_CVR_COLUMN]

    for test_case in test_cases:
        # Upload ESS CVR file
        rv = upload_batch_inventory_cvr(
            client,
            io.BytesIO(test_case.encode()),
            election_id,
            jurisdiction_ids[0],
            "text/csv",
        )
        assert_ok(rv)

        # Verify the uploaded CVR file
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
        )
        compare_json(json.loads(rv.data), {"systemType": CvrFileType.ESS})

        # Download manifest
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/ballot-manifest"
        )
        ballot_manifest = rv.data.decode("utf-8")
        snapshot.assert_match(ballot_manifest)

        # Download batch tallies
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/batch-tallies"
        )
        batch_tallies = rv.data.decode("utf-8")
        snapshot.assert_match(batch_tallies)

        # Upload manifest - should be a valid file
        rv = upload_ballot_manifest(
            client,
            io.BytesIO(ballot_manifest.encode()),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "name": asserts_startswith("manifest"),
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

        # Upload batch tallies - should be a valid file
        rv = upload_batch_tallies(
            client,
            io.BytesIO(batch_tallies.encode()),
            election_id,
            jurisdiction_ids[0],
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "name": asserts_startswith("batch_tallies"),
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


def test_batch_inventory_ess_cvr_upload_multi_contest(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: str,  # pylint: disable=unused-argument
    snapshot,
):
    # Set the logged-in user to Jurisdiction Admin
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Set system type
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type",
        {"systemType": CvrFileType.ESS},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    compare_json(json.loads(rv.data), {"systemType": CvrFileType.ESS})

    # Upload ESS CVR file
    rv = upload_batch_inventory_cvr(
        client,
        zip_cvrs(
            [
                (io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv"),
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv"),
                (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv"),
            ]
        ),
        election_id,
        jurisdiction_ids[0],
        "application/zip",
    )
    assert_ok(rv)

    # Verify the uploaded CVR file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/system-type"
    )
    compare_json(json.loads(rv.data), {"systemType": CvrFileType.ESS})

    # Download manifest
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/ballot-manifest"
    )
    ballot_manifest = rv.data.decode("utf-8")
    snapshot.assert_match(ballot_manifest)

    # Download batch tallies
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/batch-tallies"
    )
    batch_tallies = rv.data.decode("utf-8")
    snapshot.assert_match(batch_tallies)

    # Upload manifest - should be a valid file
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(ballot_manifest.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("manifest"),
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

    # Upload batch tallies - should be a valid file
    rv = upload_batch_tallies(
        client,
        io.BytesIO(batch_tallies.encode()),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": asserts_startswith("batch_tallies"),
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

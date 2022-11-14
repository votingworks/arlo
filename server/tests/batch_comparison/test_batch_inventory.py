import pytest
from flask.testing import FlaskClient
from ..helpers import *  # pylint: disable=wildcard-import
from ...models import BatchInventoryData

TEST_CVR = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,,,
,,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,,Choice 1-1,Choice 1-2,Write In Alice Adams,Write-in Bob Bates,Choice 2-1,Choice 2-2,Choice 2-3
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM,,,LBR,IND,,
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1,0,0,1,1,0
2,TABULATOR1,BATCH1,2,1-1-2,Election Day,12345,COUNTY,1,0,0,0,1,0,1
3,TABULATOR1,BATCH1,3,1-1-3,Election Day,12345,COUNTY,0,1,0,0,1,1,0
4,TABULATOR1,BATCH2,1,1-2-1,Election Day,12345,COUNTY,1,0,0,0,1,0,1
5,TABULATOR1,BATCH2,2,1-2-2,Election Day,12345,COUNTY,0,1,0,0,1,1,0
6,TABULATOR1,BATCH2,3,1-2-3,Election Day,12345,COUNTY,1,0,0,0,1,0,1
7,TABULATOR2,BATCH1,1,2-1-1,Election Day,12345,COUNTY,0,1,0,0,1,1,0
8,TABULATOR2,BATCH1,2,2-1-2,Mail,12345,COUNTY,1,0,0,0,1,0,1
9,TABULATOR2,BATCH1,3,2-1-3,Mail,12345,COUNTY,1,0,1,0,1,1,0
10,TABULATOR2,BATCH2,1,2-2-1,Election Day,12345,COUNTY,0,0,0,1,1,0,1
11,TABULATOR2,BATCH2,2,2-2-2,Election Day,12345,COUNTY,0,0,1,0,1,1,0
12,TABULATOR2,BATCH2,3,2-2-3,Election Day,12345,COUNTY,0,0,0,1,1,0,1
13,TABULATOR2,BATCH2,4,2-2-4,Election Day,12345,CITY,1,0,0,0,1,0,1
14,TABULATOR2,BATCH2,5,2-2-5,Election Day,12345,CITY,,,,,1,1,0
15,TABULATOR2,BATCH2,6,2-2-6,Election Day,12345,CITY,,,,,1,0,1
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
            # Double the actual number of votes in TEST_CVR
            {"id": str(uuid.uuid4()), "name": "Choice 1-1", "numVotes": 10},
            {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 8},
            {"id": str(uuid.uuid4()), "name": "Write-in", "numVotes": 6},
        ],
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids[:2],
    }
    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert_ok(rv)
    return str(contest["id"])


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

    # Upload CVR file
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr",
        data={"cvr": (io.BytesIO(TEST_CVR.encode()), "cvrs.csv",),},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "cvrs.csv", "uploadedAt": assert_is_date},
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
        },
    )

    # Upload tabulator status file
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status",
        data={
            "tabulatorStatus": (
                io.BytesIO(TEST_TABULATOR_STATUS.encode()),
                "tabulator-status.csv",
            ),
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "tabulator-status.csv", "uploadedAt": assert_is_date},
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
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (io.BytesIO(ballot_manifest.encode()), "ballot-manifest.csv",),
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "ballot-manifest.csv", "uploadedAt": assert_is_date},
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
        },
    )

    # Upload batch tallies
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (io.BytesIO(batch_tallies.encode()), "batch-tallies.csv",)
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "batch-tallies.csv", "uploadedAt": assert_is_date},
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


def test_batch_inventory_invalid_file_uploads(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Upload invalid CVR files
    invalid_cvrs = [
        (
            TEST_CVR.replace("Contest 1", "Contest X"),
            "Could not find contest in CVR file: Contest 1.",
        ),
        (
            TEST_CVR.replace("Choice 1-1", "Choice X"),
            "CVR contest choice names don't match the choice names for this audit. CVR contest choice names: Choice X, Choice 1-2. Audit contest choice names: Choice 1-1, Choice 1-2.",
        ),
    ]
    for invalid_cvr, expected_error in invalid_cvrs:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr",
            data={"cvr": (io.BytesIO(invalid_cvr.encode()), "cvrs.csv",)},
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
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr",
        data={"cvr": (io.BytesIO(TEST_CVR.encode()), "cvrs.csv",),},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr"
    )
    cvr = json.loads(rv.data)
    assert cvr["processing"]["status"] == ProcessingStatus.PROCESSED

    # Upload tabulator status file with missing tabulator
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status",
        data={
            "tabulatorStatus": (
                io.BytesIO(
                    TEST_TABULATOR_STATUS.replace(
                        '<tb id="1" tid="TABULATOR1" name="Tabulator 1" />', ""
                    ).encode()
                ),
                "tabulator-status.csv",
            ),
        },
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

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr",
        data={
            "cvr": (
                io.BytesIO(
                    TEST_CVR.replace(
                        """1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1,0,0,1,1,0
2,TABULATOR1,BATCH1,2,1-1-2,Election Day,12345,COUNTY,1,0,0,0,1,0,1
3,TABULATOR1,BATCH1,3,1-1-3,Election Day,12345,COUNTY,0,1,0,0,1,1,0
4,TABULATOR1,BATCH2,1,1-2-1,Election Day,12345,COUNTY,1,0,0,0,1,0,1
5,TABULATOR1,BATCH2,2,1-2-2,Election Day,12345,COUNTY,0,1,0,0,1,1,0
6,TABULATOR1,BATCH2,3,1-2-3,Election Day,12345,COUNTY,1,0,0,0,1,0,1
""",
                        "",
                    ).encode()
                ),
                "cvrs.csv",
            ),
        },
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


def test_batch_inventory_undo_sign_off(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Upload CVR file
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr",
        data={"cvr": (io.BytesIO(TEST_CVR.encode()), "cvrs.csv",),},
    )
    assert_ok(rv)

    # Upload tabulator status file
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status",
        data={
            "tabulatorStatus": (
                io.BytesIO(TEST_TABULATOR_STATUS.encode()),
                "tabulator-status.csv",
            ),
        },
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

    # Upload CVR file
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr",
        data={"cvr": (io.BytesIO(TEST_CVR.encode()), "cvrs.csv",),},
    )
    assert_ok(rv)

    # Upload tabulator status file
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status",
        data={
            "tabulatorStatus": (
                io.BytesIO(TEST_TABULATOR_STATUS.encode()),
                "tabulator-status.csv",
            ),
        },
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

    # Upload CVR file
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr",
        data={"cvr": (io.BytesIO(TEST_CVR.encode()), "cvrs.csv",),},
    )
    assert_ok(rv)

    # Upload tabulator status file
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status",
        data={
            "tabulatorStatus": (
                io.BytesIO(TEST_TABULATOR_STATUS.encode()),
                "tabulator-status.csv",
            ),
        },
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
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str],
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr",
        data={"cvr": (io.BytesIO(TEST_CVR.encode()), "cvrs.csv",),},
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Jurisdiction does not have any contests assigned",
            }
        ]
    }


def test_batch_inventory_download_files_before_sign_off(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Upload CVR and tabulator status files
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/cvr",
        data={"cvr": (io.BytesIO(TEST_CVR.encode()), "cvrs.csv",),},
    )
    assert_ok(rv)

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status",
        data={
            "tabulatorStatus": (
                io.BytesIO(TEST_TABULATOR_STATUS.encode()),
                "tabulator-status.csv",
            ),
        },
    )
    assert_ok(rv)

    # Try to download ballot manifest before signing off
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/ballot-manifest"
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Batch inventory must be signed off before downloading ballot manifest.",
            }
        ]
    }

    # Try to download batch tallies before signing off
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/batch-tallies"
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Batch inventory must be signed off before downloading batch tallies.",
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

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status",
        data={
            "tabulatorStatus": (
                io.BytesIO(TEST_TABULATOR_STATUS.encode()),
                "tabulator-status.csv",
            ),
        },
    )
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Must upload CVR file before uploading tabulator status file.",
            }
        ]
    }

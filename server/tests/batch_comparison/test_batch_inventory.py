import pytest
from flask.testing import FlaskClient
from ..helpers import *  # pylint: disable=wildcard-import
from ...models import BatchInventoryData

TEST_CVR = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,,Choice 1-1,Choice 1-2,Choice 2-1,Choice 2-2,Choice 2-3
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM,LBR,IND,,
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1,1,1,0
2,TABULATOR1,BATCH1,2,1-1-2,Election Day,12345,COUNTY,1,0,1,0,1
3,TABULATOR1,BATCH1,3,1-1-3,Election Day,12345,COUNTY,0,1,1,1,0
4,TABULATOR1,BATCH2,1,1-2-1,Election Day,12345,COUNTY,1,0,1,0,1
5,TABULATOR1,BATCH2,2,1-2-2,Election Day,12345,COUNTY,0,1,1,1,0
6,TABULATOR1,BATCH2,3,1-2-3,Election Day,12345,COUNTY,1,0,1,0,1
7,TABULATOR2,BATCH1,1,2-1-1,Election Day,12345,COUNTY,0,1,1,1,0
8,TABULATOR2,BATCH1,2,2-1-2,Mail,12345,COUNTY,1,0,1,0,1
9,TABULATOR2,BATCH1,3,2-1-3,Mail,12345,COUNTY,1,0,1,1,0
10,TABULATOR2,BATCH2,1,2-2-1,Election Day,12345,COUNTY,1,0,1,0,1
11,TABULATOR2,BATCH2,2,2-2-2,Election Day,12345,COUNTY,1,1,1,1,0
12,TABULATOR2,BATCH2,3,2-2-3,Election Day,12345,COUNTY,1,0,1,0,1
13,TABULATOR2,BATCH2,4,2-2-4,Election Day,12345,CITY,,,1,0,1
14,TABULATOR2,BATCH2,5,2-2-5,Election Day,12345,CITY,,,1,1,0
15,TABULATOR2,BATCH2,6,2-2-6,Election Day,12345,CITY,,,1,0,1
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
            {"id": str(uuid.uuid4()), "name": "Choice 1-1", "numVotes": 14},
            {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 8},
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
                "tabulator-status.xml",
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
            "file": {"name": "tabulator-status.xml", "uploadedAt": assert_is_date},
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
            "Could not find contest choices in CVR file: Choice 1-1.",
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
                "tabulator-status.xml",
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
                        """1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1,1,1,0
2,TABULATOR1,BATCH1,2,1-1-2,Election Day,12345,COUNTY,1,0,1,0,1
3,TABULATOR1,BATCH1,3,1-1-3,Election Day,12345,COUNTY,0,1,1,1,0
4,TABULATOR1,BATCH2,1,1-2-1,Election Day,12345,COUNTY,1,0,1,0,1
5,TABULATOR1,BATCH2,2,1-2-2,Election Day,12345,COUNTY,0,1,1,1,0
6,TABULATOR1,BATCH2,3,1-2-3,Election Day,12345,COUNTY,1,0,1,0,1
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


def test_batch_inventory_wrong_tabulator_status_file(
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

    # Upload tabulator status "To Excel" version
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status",
        data={
            "tabulatorStatus": (
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
<Data ss:Type="String">10</Data>
</Cell>
<Cell>
<Data ss:Type="String">ED-ICP 1</Data>
</Cell>
<Cell>
<Data ss:Type="Number">1</Data>
</Cell>
<Cell ss:StyleID="Number">
<Data ss:Type="Number">538</Data>
</Cell>
</Row>
</Table>
</Worksheet>
</Workbook>
"""
                ),
                "tabulator-status.xml",
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
        == 'This looks like the Excel version of the tabulator status report. Please upload the plain XML version (which has a file name ending in ".xml" and does not contain the words "To Excel").'
    )

    # Upload tabulator status HTML version
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-inventory/tabulator-status",
        data={
            "tabulatorStatus": (
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
                "tabulator-status.xml",
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
        == 'This looks like the HTML version of the tabulator status report. Please upload the XML version (which has a file name ending in ".xml").'
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
                "tabulator-status.xml",
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
                "tabulator-status.xml",
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
                "tabulator-status.xml",
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
                "tabulator-status.xml",
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
                "tabulator-status.xml",
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

import io, json
from typing import List
import pytest
from flask import session
from flask.testing import FlaskClient


from ...app import app
from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...api.cvrs import upload_cvrs
from ...auth import lib as auth_lib
from .conftest import TEST_CVRS


def test_dominion_cvr_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    # Test that the AA jurisdictions list includes empty CVRs
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    compare_json(
        jurisdictions[0]["cvrs"],
        {"file": None, "processing": None, "numBallots": None,},
    )
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    # Upload CVRs
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "cvrs.csv",
                "uploadedAt": assert_is_date,
                "cvrFileType": "DOMINION",
            },
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
                "workProgress": manifest_num_ballots,
                "workTotal": manifest_num_ballots,
            },
        },
    )

    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == manifest_num_ballots - 1
    snapshot.assert_match(
        [
            dict(
                batch_name=cvr.batch.name,
                tabulator=cvr.batch.tabulator,
                ballot_position=cvr.ballot_position,
                imprinted_id=cvr.imprinted_id,
                interpretations=cvr.interpretations,
            )
            for cvr in cvr_ballots
        ]
    )
    snapshot.assert_match(
        Jurisdiction.query.get(jurisdiction_ids[0]).cvr_contests_metadata
    )

    # Test that the AA jurisdictions list includes CVRs
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    compare_json(
        jurisdictions[0]["cvrs"],
        {
            "file": {
                "name": "cvrs.csv",
                "uploadedAt": assert_is_date,
                "cvrFileType": "DOMINION",
            },
            "processing": {
                "status": "PROCESSED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
                "workProgress": manifest_num_ballots,
                "workTotal": manifest_num_ballots,
            },
            "numBallots": manifest_num_ballots - 1,
        },
    )

    # Test that the AA can download the CVR file
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs/csv"
    )
    assert rv.status_code == 200
    assert rv.headers["Content-Disposition"] == 'attachment; filename="cvrs.csv"'
    assert rv.data == TEST_CVRS.encode()


COUNTING_GROUP_CVR = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
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


def test_cvrs_counting_group(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (io.BytesIO(COUNTING_GROUP_CVR.encode()), "cvrs.csv",),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "cvrs.csv",
                "uploadedAt": assert_is_date,
                "cvrFileType": "DOMINION",
            },
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
                "workProgress": manifest_num_ballots,
                "workTotal": manifest_num_ballots,
            },
        },
    )

    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == manifest_num_ballots
    snapshot.assert_match(
        [
            dict(
                batch_name=cvr.batch.name,
                tabulator=cvr.batch.tabulator,
                ballot_position=cvr.ballot_position,
                imprinted_id=cvr.imprinted_id,
                interpretations=cvr.interpretations,
            )
            for cvr in cvr_ballots
        ]
    )
    snapshot.assert_match(
        Jurisdiction.query.get(jurisdiction_ids[0]).cvr_contests_metadata
    )


def test_cvrs_replace(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).cvr_file_id

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO("\n".join(TEST_CVRS.splitlines()[:-2]).encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    # The old file should have been deleted
    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert File.query.get(file_id) is None
    assert jurisdiction.cvr_file_id != file_id

    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == len(TEST_CVRS.splitlines()) - 4 - 2


def test_cvrs_clear(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).cvr_file_id

    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    assert json.loads(rv.data) == {"file": None, "processing": None}

    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert jurisdiction.cvr_file_id is None
    assert File.query.get(file_id) is None
    assert jurisdiction.cvr_contests_metadata is None
    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == 0

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs/csv"
    )
    assert rv.status_code == 404


def test_cvrs_upload_missing_file(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs", data={},
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Missing required file parameter 'cvrs'",
            }
        ]
    }


def test_cvrs_upload_bad_csv(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (io.BytesIO(b"not a CSV file"), "random.txt"),
            "cvrFileType": "DOMINION",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Please submit a valid CSV. If you are working with an Excel spreadsheet, make sure you export it as a .csv file before uploading",
            }
        ]
    }


def test_cvrs_wrong_audit_type(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    for audit_type in [AuditType.BALLOT_POLLING, AuditType.BATCH_COMPARISON]:
        # Hackily change the audit type
        election = Election.query.get(election_id)
        election.audit_type = audit_type
        db_session.add(election)
        db_session.commit()

        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={"cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",)},
        )
        assert rv.status_code == 409
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "errorType": "Conflict",
                    "message": "Can't upload CVR file for this audit type.",
                }
            ]
        }


def test_cvrs_before_manifests(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str],
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={"cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",)},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Must upload ballot manifest before uploading CVR file.",
            }
        ]
    }


NEWLINE_CVR = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1
(Vote For=1)","Contest 1
(Vote For=1)",Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
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


def test_cvrs_newlines(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (io.BytesIO(NEWLINE_CVR.encode()), "cvrs.csv",),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "cvrs.csv",
                "uploadedAt": assert_is_date,
                "cvrFileType": "DOMINION",
            },
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
                "workProgress": manifest_num_ballots,
                "workTotal": manifest_num_ballots,
            },
        },
    )

    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == manifest_num_ballots
    snapshot.assert_match(
        [
            dict(
                batch_name=cvr.batch.name,
                tabulator=cvr.batch.tabulator,
                ballot_position=cvr.ballot_position,
                imprinted_id=cvr.imprinted_id,
                interpretations=cvr.interpretations,
            )
            for cvr in cvr_ballots
        ]
    )
    snapshot.assert_match(
        Jurisdiction.query.get(jurisdiction_ids[0]).cvr_contests_metadata
    )


def test_invalid_cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    invalid_cvrs = [
        ("", "CSV cannot be empty.", "DOMINION"),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (123)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Invalid contest name: Contest 1 (123). Contest names should have this format: Contest Name (Vote For=1).",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH001,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            (
                "Invalid TabulatorNum/BatchId for row with CvrNumber 1: TABULATOR1, BATCH001."
                " The TabulatorNum and BatchId fields in the CVR file must match the Tabulator and Batch Name"
                " fields in the ballot manifest. The closest match we found in the ballot manifest was:"
                " TABULATOR1, BATCH1. Please check your CVR file and ballot manifest thoroughly to make"
                " sure these values match - there may be a similar inconsistency in other rows in the CVR file."
            ),
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATO1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            (
                "Invalid TabulatorNum/BatchId for row with CvrNumber 1: TABULATO1, BATCH1."
                " The TabulatorNum and BatchId fields in the CVR file must match the Tabulator and Batch Name"
                " fields in the ballot manifest. The closest match we found in the ballot manifest was:"
                " TABULATOR1, BATCH1. Please check your CVR file and ballot manifest thoroughly to make"
                " sure these values match - there may be a similar inconsistency in other rows in the CVR file."
            ),
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,abc,123,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            (
                "Invalid TabulatorNum/BatchId for row with CvrNumber 1: abc, 123."
                " The TabulatorNum and BatchId fields in the CVR file must match the Tabulator and Batch Name"
                " fields in the ballot manifest."
                " Please check your CVR file and ballot manifest thoroughly to make"
                " sure these values match - there may be a similar inconsistency in other rows in the CVR file."
            ),
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column CvrNumber",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column TabulatorNum",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column BatchId",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column RecordId",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column ImprintedId",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column CvrNumber in row 1.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column TabulatorNum in row 1.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column BatchId in row 1.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column RecordId in row 1.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1,,Election Day,12345,COUNTY,0,1
""",
            "Missing required column ImprintedId in row 1.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote Fo=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1,,Election Day,12345,COUNTY,0,1
""",
            "Invalid contest name: Contest 1 (Vote Fo=1). Contest names should have this format: Contest Name (Vote For=1).",
            "DOMINION",
        ),
        (
            """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1,1-1-1,p,bs,ps,TABULATO1,s,r,0,1,1,1,0
""",
            (
                "Invalid ScanComputerName/BoxID for row with RowNumber 1: TABULATO1, BATCH1."
                " The ScanComputerName and BoxID fields in the CVR file must match the Tabulator and Batch Name"
                " fields in the ballot manifest. The closest match we found in the ballot manifest was:"
                " TABULATOR1, BATCH1. Please check your CVR file and ballot manifest thoroughly to make"
                " sure these values match - there may be a similar inconsistency in other rows in the CVR file."
            ),
            "CLEARBALLOT",
        ),
        (
            """BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
BATCH1,1,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column RowNumber",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,1,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column BoxID",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column BoxPosition",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BoxPosition,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column BallotID",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1,1-1-1,p,bs,ps,s,r,0,1,1,1,0
""",
            "Missing required column ScanComputerName",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
,BATCH1,1,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column RowNumber in row 1.",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,,1,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column BoxID in row 1.",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column BoxPosition in row 1.",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1,,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column BallotID in row 1.",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1,1-1-1,p,bs,ps,,s,r,0,1,1,1,0
""",
            "Missing required column ScanComputerName in row 1.",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Invalid contest header: Choice_1_1:Contest 1:Vote For 1:Choice 1-1",
            "CLEARBALLOT",
        ),
    ]

    for invalid_cvr, expected_error, cvr_file_type in invalid_cvrs:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={
                "cvrs": (io.BytesIO(invalid_cvr.encode()), "cvrs.csv",),
                "cvrFileType": cvr_file_type,
            },
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "name": "cvrs.csv",
                    "uploadedAt": assert_is_date,
                    "cvrFileType": cvr_file_type,
                },
                "processing": {
                    "status": ProcessingStatus.ERRORED,
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": expected_error,
                    "workProgress": 0,
                    "workTotal": manifest_num_ballots,
                },
            },
        )
        cvr_ballots = (
            CvrBallot.query.join(Batch)
            .filter_by(jurisdiction_id=jurisdiction_ids[0])
            .all()
        )
        assert len(cvr_ballots) == 0
        assert Jurisdiction.query.get(jurisdiction_ids[0]).cvr_contests_metadata is None


def test_cvr_reprocess_after_manifest_reupload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    # Reupload a manifest but remove a batch
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Tabulator,Batch Name,Number of Ballots\n"
                    b"TABULATOR2,BATCH2,6\n"
                    b"TABULATOR1,BATCH1,3\n"
                    b"TABULATOR1,BATCH2,3"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    # Error should be recorded for CVRs
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "cvrs.csv",
                "uploadedAt": assert_is_date,
                "cvrFileType": "DOMINION",
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Invalid TabulatorNum/BatchId for row with CvrNumber 7: TABULATOR2, BATCH1. The TabulatorNum and BatchId fields in the CVR file must match the Tabulator and Batch Name fields in the ballot manifest. The closest match we found in the ballot manifest was: TABULATOR2, BATCH2. Please check your CVR file and ballot manifest thoroughly to make sure these values match - there may be a similar inconsistency in other rows in the CVR file.",
                "workProgress": 0,
                "workTotal": manifest_num_ballots,
            },
        },
    )

    assert (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .count()
        == 0
    )
    assert Jurisdiction.query.get(jurisdiction_ids[0]).cvr_contests_metadata is None

    # Fix the manifest
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Tabulator,Batch Name,Number of Ballots\n"
                    b"TABULATOR1,BATCH1,3\n"
                    b"TABULATOR1,BATCH2,3\n"
                    b"TABULATOR2,BATCH1,3\n"
                    b"TABULATOR2,BATCH2,6"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    # CVRs should be fixed
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "cvrs.csv",
                "uploadedAt": assert_is_date,
                "cvrFileType": "DOMINION",
            },
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
                "workProgress": manifest_num_ballots,
                "workTotal": manifest_num_ballots,
            },
        },
    )

    assert (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .count()
        == manifest_num_ballots - 1
    )
    assert Jurisdiction.query.get(jurisdiction_ids[0]).cvr_contests_metadata is not None


CLEARBALLOT_CVR = """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
2,BATCH1,2,1-1-2,p,bs,ps,TABULATOR1,s,r,1,0,1,0,1
3,BATCH1,3,1-1-3,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
4,BATCH1,1,1-2-1,p,bs,ps,TABULATOR2,s,r,1,0,1,0,1
5,BATCH1,2,1-2-2,p,bs,ps,TABULATOR2,s,r,0,1,1,1,0
6,BATCH1,3,1-2-3,p,bs,ps,TABULATOR2,s,r,1,0,1,0,1
7,BATCH2,1,2-1-1,p,bs,ps,TABULATOR1,s,r,1,0,1,1,0
8,BATCH2,2,2-1-2,p,bs,ps,TABULATOR1,s,r,1,0,1,0,1
9,BATCH2,3,2-1-3,p,bs,ps,TABULATOR1,s,r,1,0,1,1,0
10,BATCH2,1,2-2-1,p,bs,ps,TABULATOR2,s,r,1,0,1,0,1
11,BATCH2,2,2-2-2,p,bs,ps,TABULATOR2,s,r,1,1,1,1,1
12,BATCH2,4,2-2-4,p,bs,ps,TABULATOR2,s,r,,,1,0,1
13,BATCH2,5,2-2-5,p,bs,ps,TABULATOR2,s,r,,,1,1,0
14,BATCH2,6,2-2-6,p,bs,ps,TABULATOR2,s,r,,,1,0,1
"""


def test_clearballot_cvr_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    # Upload CVRs
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (io.BytesIO(CLEARBALLOT_CVR.encode()), "cvrs.csv",),
            "cvrFileType": "CLEARBALLOT",
        },
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "cvrs.csv",
                "uploadedAt": assert_is_date,
                "cvrFileType": "CLEARBALLOT",
            },
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
                "workProgress": manifest_num_ballots,
                "workTotal": manifest_num_ballots,
            },
        },
    )

    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == manifest_num_ballots - 1
    snapshot.assert_match(
        [
            dict(
                batch_name=cvr.batch.name,
                tabulator=cvr.batch.tabulator,
                ballot_position=cvr.ballot_position,
                imprinted_id=cvr.imprinted_id,
                interpretations=cvr.interpretations,
            )
            for cvr in cvr_ballots
        ]
    )
    snapshot.assert_match(
        Jurisdiction.query.get(jurisdiction_ids[0]).cvr_contests_metadata
    )


ESS_CVR = """Cast Vote Record,Precinct,Ballot Style,Contest 1,Contest 2
1,p,bs,Choice 1-2,Choice 2-1
2,p,bs,Choice 1-1,Choice 2-1
3,p,bs,undervote,Choice 2-1
4,p,bs,overvote,Choice 2-1
5,p,bs,Choice 1-2,Choice 2-1
6,p,bs,Choice 1-1,Choice 2-1
7,p,bs,Choice 1-2,Choice 2-1
8,p,bs,Choice 1-1,Choice 2-1
9,p,bs,Choice 1-2,Choice 2-2
10,p,bs,Choice 1-1,Choice 2-2
11,p,bs,Choice 1-2,Choice 2-2
12,p,bs,Choice 1-1,Choice 2-2
13,p,bs,Choice 1-2,Choice 2-3
15,p,bs,Choice 1-1,Choice 2-3
"""

ESS_BALLOTS_1 = """Ballots,,,,,,,,,
GEN2111,,,,,,,,,
"Test County,Test State",,,,,,,,,
"November 5, 2021",,,,,,,,,
,,,,,,,,,
Cast Vote Record,Batch,Ballot Status,Original Ballot Exception,Remaining Ballot Exception,Write-in Type,Results Report,Reporting Group,Tabulator CVR,Precinct ID
1,BATCH1,Not Reviewed,,,,N,Election Day,0001013415,p
2,BATCH1,Not Reviewed,,,,N,Election Day,0001013416,p
3,BATCH1,Not Reviewed,Undervote,,,N,Election Day,0001013417,p
4,BATCH1,Not Reviewed,Overvote,,,N,Election Day,0002003171,p
5,BATCH1,Not Reviewed,,,,N,Election Day,0002003172,p
6,BATCH1,Not Reviewed,,,,N,Election Day,0002003173,p
7,BATCH2,Not Reviewed,,,,N,Election Day,0001000415,p
"""

ESS_BALLOTS_2 = """Ballots,,,,,,,,,
GEN2111,,,,,,,,,
"Test County,Test State",,,,,,,,,
"November 5, 2021",,,,,,,,,
,,,,,,,,,
Cast Vote Record,Batch,Ballot Status,Original Ballot Exception,Remaining Ballot Exception,Write-in Type,Results Report,Reporting Group,Tabulator CVR,Precinct ID
8,BATCH2,Not Reviewed,,,,N,Election Day,0001000416,p
9,BATCH2,Not Reviewed,,,,N,Election Day,0001000417,p
10,BATCH2,Not Reviewed,,,,N,Election Day,0002000171,p
11,BATCH2,Not Reviewed,,,,N,Election Day,0002000172,p
12,BATCH2,Not Reviewed,,,,N,Election Day,0002000173,p
13,BATCH2,Not Reviewed,,,,N,Election Day,0002000174,p
15,BATCH2,Not Reviewed,,,,N,Election Day,0002000175,p
"""


@pytest.fixture
def ess_manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    for jurisdiction_id in jurisdiction_ids[:2]:
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/ballot-manifest",
            data={
                "manifest": (
                    io.BytesIO(
                        b"Tabulator,Batch Name,Number of Ballots\n"
                        b"0001,BATCH1,3\n"
                        b"0001,BATCH2,3\n"
                        b"0002,BATCH1,3\n"
                        b"0002,BATCH2,6"
                    ),
                    "manifest.csv",
                )
            },
        )
        assert_ok(rv)


def test_ess_cvr_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    ess_manifests,  # pylint: disable=unused-argument
    snapshot,
):
    # Upload CVRs
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv",),
                (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv",),
            ],
            "cvrFileType": "ESS",
        },
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "cvr_files.zip",
                "uploadedAt": assert_is_date,
                "cvrFileType": "ESS",
            },
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
                "workProgress": manifest_num_ballots,
                "workTotal": manifest_num_ballots,
            },
        },
    )

    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == manifest_num_ballots - 1
    snapshot.assert_match(
        [
            dict(
                batch_name=cvr.batch.name,
                tabulator=cvr.batch.tabulator,
                ballot_position=cvr.ballot_position,
                imprinted_id=cvr.imprinted_id,
                interpretations=cvr.interpretations,
            )
            for cvr in cvr_ballots
        ]
    )
    snapshot.assert_match(
        Jurisdiction.query.get(jurisdiction_ids[0]).cvr_contests_metadata
    )


def test_ess_cvr_invalid(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    ess_manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    def remove_line(string: str, line: int) -> str:
        lines = string.splitlines()
        if line < 0:
            line = len(string.splitlines()) + line
        return "\n".join(lines[:line] + lines[line + 1 :])

    def replace_line(string: str, line: int, new_line: str) -> str:
        lines = string.splitlines()
        if line < 0:
            line = len(string.splitlines()) + line
        return "\n".join(lines[:line] + [new_line] + lines[line + 1 :])

    invalid_cvrs = [
        (
            [(io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv")],
            "Missing ballots files - at least one file should contain the list of tabulated ballots and their corresponding CVR identifiers.",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv",),
            ],
            "Missing CVR file - one exported file should contain the cast vote records for each ballot.",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv",),
                (io.BytesIO(ESS_CVR.encode()), "ess_cvr_1.csv",),
                (io.BytesIO(ESS_CVR.encode()), "ess_cvr_2.csv",),
            ],
            "Could not detect which files contain the list of ballots and which contains the CVR results. Please ensure you have one file with the cast vote records for each ballot and at least one file containing the list of tabulated ballots and their corresponding CVR identifiers.",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv",),
                (
                    io.BytesIO(
                        # Simulate leading zeros getting stripped from the tabulator column
                        replace_line(
                            ESS_BALLOTS_2,
                            -1,
                            "15,BATCH2,Not Reviewed,,,,N,Election Day,2000175,p",
                        ).encode()
                    ),
                    "ess_ballots_2.csv",
                ),
            ],
            "ess_ballots_2.csv: Tabulator CVR should be a ten-digit number. Got 2000175 for Cast Vote Record 15. Make sure any leading zeros have not been stripped from this field.",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv",),
                (
                    io.BytesIO(
                        replace_line(
                            ESS_BALLOTS_2,
                            -1,
                            "15,BATCH2,Not Reviewed,,,,N,Election Day,0003000175,p",
                        ).encode()
                    ),
                    "ess_ballots_2.csv",
                ),
            ],
            "ess_ballots_2.csv: Invalid Tabulator/Batch for row with Cast Vote Record 15: 0003, BATCH2. The Tabulator and Batch fields in the CVR file must match the Tabulator and Batch Name fields in the ballot manifest. The closest match we found in the ballot manifest was: 0002, BATCH2. Please check your CVR file and ballot manifest thoroughly to make sure these values match - there may be a similar inconsistency in other rows in the CVR file.",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (io.BytesIO(b""), "ess_cvr.csv",),
            ],
            "ess_cvr.csv: CSV cannot be empty.",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv",),
                (
                    io.BytesIO(remove_line(ESS_BALLOTS_2, 10).encode()),
                    "ess_ballots_2.csv",
                ),
            ],
            "Mismatch between CVR file and ballots files. Make sure the Cast Vote Record column in the CVR file and the ballots file match and include exactly the same set of ballots.",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv",),
                (
                    io.BytesIO(remove_line(ESS_BALLOTS_2, -1).encode()),
                    "ess_ballots_2.csv",
                ),
            ],
            "Mismatch between CVR file and ballots files. Make sure the Cast Vote Record column in the CVR file and the ballots file match and include exactly the same set of ballots.",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (io.BytesIO(remove_line(ESS_CVR, 10).encode()), "ess_cvr.csv",),
                (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv",),
            ],
            "Mismatch between CVR file and ballots files. Make sure the Cast Vote Record column in the CVR file and the ballots file match and include exactly the same set of ballots.",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (io.BytesIO(remove_line(ESS_CVR, -1).encode()), "ess_cvr.csv",),
                (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv",),
            ],
            "Mismatch between CVR file and ballots files. Make sure the Cast Vote Record column in the CVR file and the ballots file match and include exactly the same set of ballots.",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (
                    io.BytesIO(
                        replace_line(
                            ESS_CVR, 0, "Precinct,Ballot Style,Contest 1,Contest 2"
                        ).encode()
                    ),
                    "ess_cvr.csv",
                ),
                (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv",),
            ],
            "ess_cvr.csv: Missing required column Cast Vote Record",
        ),
        (
            [
                (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv",),
                (
                    io.BytesIO(
                        replace_line(
                            ESS_CVR,
                            0,
                            "Cast Vote Record\tPrecinct\tBallot Style\tContest 1\tContest 2",
                        ).encode()
                    ),
                    "ess_cvr.csv",
                ),
                (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv",),
            ],
            "ess_cvr.csv: Please submit a valid CSV file with columns separated by commas. This file has columns separated by tabs.",
        ),
    ]

    for invalid_cvr, expected_error in invalid_cvrs:
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={"cvrs": invalid_cvr, "cvrFileType": "ESS"},
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "name": "cvr_files.zip",
                    "uploadedAt": assert_is_date,
                    "cvrFileType": "ESS",
                },
                "processing": {
                    "status": ProcessingStatus.ERRORED,
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": expected_error,
                    "workProgress": 0,
                    "workTotal": manifest_num_ballots,
                },
            },
        )


def test_cvrs_unexpected_error(
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    # Duplicate a row to simulate an unexpected error
    cvrs = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
"""
    with app.test_request_context(
        path=f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (io.BytesIO(cvrs.encode()), "cvrs.csv",),
            "cvrFileType": "DOMINION",
        },
    ):
        auth_lib.set_loggedin_user(
            session, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        with pytest.raises(Exception, match="Could not parse CVR file"):
            # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
            upload_cvrs(election_id=election_id, jurisdiction_id=jurisdiction_ids[0])

    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == 0


def test_cvr_invalid_file_type(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",),
            "cvrFileType": "WRONG",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Bad Request", "message": "Invalid file type",}]
    }

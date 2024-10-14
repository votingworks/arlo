import io, json
from typing import BinaryIO, Dict, List, TypedDict, Tuple
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...util.file import zip_files
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
        {
            "file": None,
            "processing": None,
            "numBallots": None,
        },
    )
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    # Upload CVRs
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(TEST_CVRS.encode()),
                "cvrs.csv",
            ),
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
            "cvrs": (
                io.BytesIO(COUNTING_GROUP_CVR.encode()),
                "cvrs.csv",
            ),
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


DOMINION_UNIQUE_VOTING_IDENTIFIER_CVR = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,,Choice 1-1,Choice 1-2,Choice 2-1,Choice 2-2,Choice 2-3
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,PrecinctPortion,BallotType,UniqueVotingIdentifier,REP,DEM,LBR,IND,,
1,TABULATOR1,BATCH1,1,1-1-1,12345,COUNTY,,0,1,1,1,0
2,TABULATOR1,BATCH1,2,1-1-2,12345,COUNTY,,1,0,1,0,1
3,TABULATOR1,BATCH1,3,1-1-3,12345,COUNTY,,0,1,1,1,0
4,TABULATOR1,BATCH2,1,1-2-1,12345,COUNTY,,1,0,1,0,1
5,TABULATOR1,BATCH2,2,1-2-2,12345,COUNTY,,0,1,1,1,0
6,TABULATOR1,BATCH2,3,1-2-3,12345,COUNTY,,1,0,1,0,1
7,TABULATOR2,BATCH1,1,2-1-1,12345,COUNTY,,0,1,1,1,0
8,TABULATOR2,BATCH1,2,,Mail,12345,56_083-212,1,0,1,0,1
9,TABULATOR2,BATCH1,3,,Mail,12345,56_083-213,1,0,1,1,0
10,TABULATOR2,BATCH2,1,,12345,COUNTY,56_083-221,1,0,1,0,1
11,TABULATOR2,BATCH2,2,,12345,COUNTY,56_083-222,1,1,1,1,0
12,TABULATOR2,BATCH2,3,,12345,COUNTY,56_083-223,1,0,1,0,1
13,TABULATOR2,BATCH2,4,,12345,CITY,56_083-224,,,1,0,1
14,TABULATOR2,BATCH2,5,,12345,CITY,56_083-225,,,1,1,0
15,TABULATOR2,BATCH2,6,,12345,CITY,56_083-226,,,1,0,1
"""


def test_dominion_cvr_unique_voting_identifier(
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
            "cvrs": (
                io.BytesIO(DOMINION_UNIQUE_VOTING_IDENTIFIER_CVR.encode()),
                "cvrs.csv",
            ),
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


DOMINION_CVRS_WITH_LEADING_EQUAL_SIGNS = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,Choice 1-1,Choice 1-2,Choice 2-1,Choice 2-2,Choice 2-3
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,PrecinctPortion,BallotType,REP,DEM,LBR,IND,,
="1",="TABULATOR1",="BATCH1",="1",="1-1-1",12345,COUNTY,0,1,1,1,0
="2",="TABULATOR1",="BATCH1",="2",="1-1-2",12345,COUNTY,1,0,1,0,1
="3",="TABULATOR1",="BATCH1",="3",="1-1-3",12345,COUNTY,0,1,1,1,0
="4",="TABULATOR1",="BATCH2",="1",="1-2-1",12345,COUNTY,1,0,1,0,1
="5",="TABULATOR1",="BATCH2",="2",="1-2-2",12345,COUNTY,0,1,1,1,0
="6",="TABULATOR1",="BATCH2",="3",="1-2-3",12345,COUNTY,1,0,1,0,1
="7",="TABULATOR2",="BATCH1",="1",="2-1-1",12345,COUNTY,1,0,1,1,0
="8",="TABULATOR2",="BATCH1",="2",="2-1-2",12345,COUNTY,1,0,1,0,1
="9",="TABULATOR2",="BATCH1",="3",="2-1-3",12345,COUNTY,1,0,1,1,0
="10",="TABULATOR2",="BATCH2",="1",="2-2-1",12345,COUNTY,1,0,1,0,1
="11",="TABULATOR2",="BATCH2",="2",="2-2-2",12345,COUNTY,1,1,1,1,1
="12",="TABULATOR2",="BATCH2",="4",="2-2-4",12345,CITY,,,1,0,1
="13",="TABULATOR2",="BATCH2",="5",="2-2-5",12345,CITY,,,0,0,0
="14",="TABULATOR2",="BATCH2",="6",="2-2-6",12345,CITY,,,1,0,1
"""


def test_dominion_cvrs_with_leading_equal_signs(
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
            "cvrs": (
                io.BytesIO(DOMINION_CVRS_WITH_LEADING_EQUAL_SIGNS.encode()),
                "cvrs.csv",
            ),
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
            "cvrs": (
                io.BytesIO(TEST_CVRS.encode()),
                "cvrs.csv",
            ),
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


def test_cvrs_replace_as_audit_admin(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    # Check that AA can also get/put/clear batch tallies
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(TEST_CVRS.encode()),
                "cvrs.csv",
            ),
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

    # Now clear the CVRs and check they are deleted
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    assert json.loads(rv.data) == {"file": None, "processing": None}


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
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={},
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
                "message": "Please submit a valid CSV. If you are working with an Excel spreadsheet, make sure you export it as a .csv file before uploading.",
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
            data={
                "cvrs": (
                    io.BytesIO(TEST_CVRS.encode()),
                    "cvrs.csv",
                )
            },
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
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(TEST_CVRS.encode()),
                "cvrs.csv",
            )
        },
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
            "cvrs": (
                io.BytesIO(NEWLINE_CVR.encode()),
                "cvrs.csv",
            ),
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
            "Couldn't find a matching batch for TabulatorNum: TABULATOR1, BatchId: BATCH001 (CvrNumber: 1). The TabulatorNum and BatchId fields in the CVR file must match the Tabulator and Batch Name fields in the ballot manifest. The closest match we found in the ballot manifest was Tabulator: TABULATOR1, Batch Name: BATCH1. Please check your CVR file and ballot manifest thoroughly to make sure these values match - there may be a similar inconsistency in other rows in the CVR file.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATO1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Couldn't find a matching batch for TabulatorNum: TABULATO1, BatchId: BATCH1 (CvrNumber: 1). The TabulatorNum and BatchId fields in the CVR file must match the Tabulator and Batch Name fields in the ballot manifest. The closest match we found in the ballot manifest was Tabulator: TABULATOR1, Batch Name: BATCH1. Please check your CVR file and ballot manifest thoroughly to make sure these values match - there may be a similar inconsistency in other rows in the CVR file.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,abc,123,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Couldn't find a matching batch for TabulatorNum: abc, BatchId: 123 (CvrNumber: 1). The TabulatorNum and BatchId fields in the CVR file must match the Tabulator and Batch Name fields in the ballot manifest. Please check your CVR file and ballot manifest thoroughly to make sure these values match - there may be a similar inconsistency in other rows in the CVR file.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column CvrNumber.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column TabulatorNum.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column BatchId.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column RecordId.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1,Election Day,12345,COUNTY,0,1
""",
            "Missing required column ImprintedId.",
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
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,UniqueVotingIdentifier,REP,DEM
1,TABULATOR1,BATCH1,1,,,0,1
""",
            "Missing required column UniqueVotingIdentifier in row 1.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0 (0%),1 (97%)
""",
            "Unable to parse '0 (0%)' as an integer. Please export the CVR file with plain integer values.",
            "DOMINION",
        ),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0 (0),1 (97)
""",
            "Unable to parse '0 (0)' as an integer. Please export the CVR file with plain integer values.",
            "DOMINION",
        ),
        (
            """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1,1-1-1,p,bs,ps,TABULATO1,s,r,0,1,1,1,0
""",
            "Couldn't find a matching batch for ScanComputerName: TABULATO1, BoxID: BATCH1 (RowNumber: 1). The ScanComputerName and BoxID fields in the CVR file must match the Tabulator and Batch Name fields in the ballot manifest. The closest match we found in the ballot manifest was Tabulator: TABULATOR1, Batch Name: BATCH1. Please check your CVR file and ballot manifest thoroughly to make sure these values match - there may be a similar inconsistency in other rows in the CVR file.",
            "CLEARBALLOT",
        ),
        (
            """BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
BATCH1,1,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column RowNumber.",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,1,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column BoxID.",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1-1-1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column BoxPosition.",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BoxPosition,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1,p,bs,ps,TABULATOR1,s,r,0,1,1,1,0
""",
            "Missing required column BallotID.",
            "CLEARBALLOT",
        ),
        (
            """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
1,BATCH1,1,1-1-1,p,bs,ps,s,r,0,1,1,1,0
""",
            "Missing required column ScanComputerName.",
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
                "cvrs": (
                    io.BytesIO(invalid_cvr.encode()),
                    "cvrs.csv",
                ),
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
                "error": "Couldn't find a matching batch for TabulatorNum: TABULATOR2, BatchId: BATCH1 (CvrNumber: 7). The TabulatorNum and BatchId fields in the CVR file must match the Tabulator and Batch Name fields in the ballot manifest. The closest match we found in the ballot manifest was Tabulator: TABULATOR2, Batch Name: BATCH2. Please check your CVR file and ballot manifest thoroughly to make sure these values match - there may be a similar inconsistency in other rows in the CVR file.",
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


CLEARBALLOT_CVRS = """RowNumber,BoxID,BoxPosition,BallotID,PrecinctID,BallotStyleID,PrecinctStyleName,ScanComputerName,Status,Remade,Choice_1_1:Contest 1:Vote For 1:Choice 1-1:Non-Partisan,Choice_210_1:Contest 1:Vote For 1:Choice 1-2:Non-Partisan,Choice_34_1:Contest 2:Vote For 2:Choice 2-1:Non-Partisan,Choice_4_1:Contest 2:Vote For 2:Choice 2-2:Non-Partisan,Choice_173_1:Contest 2:Vote For 2:Choice 2-3:Non-Partisan
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

# This file is based on a real file that we once received, probably exported by Clear Ballot but
# not a Clear Ballot CVR file
CLEARBALLOT_CVRS_INVALID = """ChoiceID,ContestID,ChoiceName
1,1,Mike Wazowski
2,1,James 'Sulley' Sullivan
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
            "cvrs": (
                io.BytesIO(CLEARBALLOT_CVRS.encode()),
                "cvrs.csv",
            ),
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


def test_clearballot_cvr_upload_invalid(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    # Upload CVRs
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(CLEARBALLOT_CVRS_INVALID.encode()),
                "cvrs.csv",
            ),
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
                "cvrFileType": "CLEARBALLOT",
                "name": "cvrs.csv",
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "CVR file should have at least one column beginning with 'Choice_'",
                "workProgress": 0,
                "workTotal": manifest_num_ballots,
            },
        },
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

# ESS ballots files may or may not be ordered by Cast Vote Record, so here we
# simulate one unordered and one ordered
ESS_BALLOTS_1 = """Ballots,,,,,,,,,
GEN2111,,,,,,,,,
"Test County,Test State",,,,,,,,,
"November 5, 2021",,,,,,,,,
,,,,,,,,,
Cast Vote Record,Batch,Ballot Status,Original Ballot Exception,Remaining Ballot Exception,Write-in Type,Results Report,Reporting Group,Tabulator CVR,Precinct ID
5,BATCH1,Not Reviewed,,,,N,Election Day,0002003172,p
6,BATCH1,Not Reviewed,,,,N,Election Day,0002003173,p
7,BATCH2,Not Reviewed,,,,N,Election Day,0001000415,p
1,BATCH1,Not Reviewed,,,,N,Election Day,0001013415,p
2,BATCH1,Not Reviewed,,,,N,Election Day,0001013416,p
3,BATCH1,Not Reviewed,Undervote,,,N,Election Day,0001013417,p
4,BATCH1,Not Reviewed,Overvote,,,N,Election Day,0002003171,p
Total : 7,,,,,,,,,
,,,,,,,,,
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
Total : 7,,,,,,,,,
"""

ESS_BALLOTS_WITH_NO_METADATA_ROWS = """Cast Vote Record,Batch,Ballot Status,Original Ballot Exception,Remaining Ballot Exception,Write-in Type,Results Report,Reporting Group,Tabulator CVR,Precinct ID
1,BATCH1,Not Reviewed,,,,N,Election Day,0001013415,p
2,BATCH1,Not Reviewed,,,,N,Election Day,0001013416,p
3,BATCH1,Not Reviewed,Undervote,,,N,Election Day,0001013417,p
4,BATCH1,Not Reviewed,Overvote,,,N,Election Day,0002003171,p
5,BATCH1,Not Reviewed,,,,N,Election Day,0002003172,p
6,BATCH1,Not Reviewed,,,,N,Election Day,0002003173,p
7,BATCH2,Not Reviewed,,,,N,Election Day,0001000415,p
8,BATCH2,Not Reviewed,,,,N,Election Day,0001000416,p
9,BATCH2,Not Reviewed,,,,N,Election Day,0001000417,p
10,BATCH2,Not Reviewed,,,,N,Election Day,0002000171,p
11,BATCH2,Not Reviewed,,,,N,Election Day,0002000172,p
12,BATCH2,Not Reviewed,,,,N,Election Day,0002000173,p
13,BATCH2,Not Reviewed,,,,N,Election Day,0002000174,p
15,BATCH2,Not Reviewed,,,,N,Election Day,0002000175,p
"""

ESS_BALLOTS_WITH_MACHINE_COLUMN = """Ballots,,,,,,,,,
GEN2111,,,,,,,,,
"Test County,Test State",,,,,,,,,
"November 5, 2021",,,,,,,,,
,,,,,,,,,
Cast Vote Record,Batch,Ballot Status,Original Ballot Exception,Remaining Ballot Exception,Write-in Type,Results Report,Ballot Style,Reporting Group,Tabulator CVR,Audit Number,Type,Poll Place,Poll Place ID,Precinct,Precinct ID,Machine,Adjudicated By,
1,BATCH1,Not Reviewed,,,,N,REP 405,Election Day,02bc1dc7bc1e7774,7074480632,Card,Election Day,28,405,21,0001,
2,BATCH1,Not Reviewed,,,,N,REP 405,Election Day,039b31b93d9a8099,7074480632,Card,Election Day,28,405,21,0001,
3,BATCH1,Not Reviewed,"Undervote, Overvote",,,N,REP 405,Election Day,06348ce7b6d146d2,7074480632,Card,Election Day,28,405,21,0001,
4,BATCH1,Not Reviewed,Overvote,,,N,REP 405,Election Day,09809965339bad95,7074480632,Card,Election Day,28,405,21,0001,
5,BATCH1,Not Reviewed,,,,N,REP 405,Election Day,0002003172,7074480632,Card,Election Day,28,405,21,0002,
6,BATCH1,Not Reviewed,,,,N,REP 405,Election Day,0002003173,7074480632,Card,Election Day,28,405,21,0002,
7,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,19882855d197f6c2,7074480632,Card,Election Day,28,405,21,0001,
8,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,1dd6b0ff8462558c,7074480632,Card,Election Day,28,405,21,0001,
9,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,1f781b866b83de9b,7074480632,Card,Election Day,28,405,21,0001,
10,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,0002000171,7074480632,Card,Election Day,28,405,21,0002,
11,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,0002000172,7074480632,Card,Election Day,28,405,21,0002,
12,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,0002000173,7074480632,Card,Election Day,28,405,21,0002,
13,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,0002000174,7074480632,Card,Election Day,28,405,21,0002,
15,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,0002000175,7074480632,Card,Election Day,28,405,21,0002,
"""

ESS_BALLOTS_WITH_MACHINE_COLUMN_AND_NO_METADATA_ROWS = """Cast Vote Record,Batch,Ballot Status,Original Ballot Exception,Remaining Ballot Exception,Write-in Type,Results Report,Ballot Style,Reporting Group,Tabulator CVR,Audit Number,Type,Poll Place,Poll Place ID,Precinct,Precinct ID,Machine,Adjudicated By,
1,BATCH1,Not Reviewed,,,,N,REP 405,Election Day,02bc1dc7bc1e7774,7074480632,Card,Election Day,28,405,21,0001,
2,BATCH1,Not Reviewed,,,,N,REP 405,Election Day,039b31b93d9a8099,7074480632,Card,Election Day,28,405,21,0001,
3,BATCH1,Not Reviewed,"Undervote, Overvote",,,N,REP 405,Election Day,06348ce7b6d146d2,7074480632,Card,Election Day,28,405,21,0001,
4,BATCH1,Not Reviewed,Overvote,,,N,REP 405,Election Day,09809965339bad95,7074480632,Card,Election Day,28,405,21,0001,
5,BATCH1,Not Reviewed,,,,N,REP 405,Election Day,0002003172,7074480632,Card,Election Day,28,405,21,0002,
6,BATCH1,Not Reviewed,,,,N,REP 405,Election Day,0002003173,7074480632,Card,Election Day,28,405,21,0002,
7,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,19882855d197f6c2,7074480632,Card,Election Day,28,405,21,0001,
8,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,1dd6b0ff8462558c,7074480632,Card,Election Day,28,405,21,0001,
9,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,1f781b866b83de9b,7074480632,Card,Election Day,28,405,21,0001,
10,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,0002000171,7074480632,Card,Election Day,28,405,21,0002,
11,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,0002000172,7074480632,Card,Election Day,28,405,21,0002,
12,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,0002000173,7074480632,Card,Election Day,28,405,21,0002,
13,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,0002000174,7074480632,Card,Election Day,28,405,21,0002,
15,BATCH2,Not Reviewed,,,,N,REP 405,Election Day,0002000175,7074480632,Card,Election Day,28,405,21,0002,
"""

ESS_CVR_WITH_TABULATOR_CVR_COLUMN = """Unknown Column,Cast Vote Record,Precinct,Ballot Style,Tabulator CVR,Contest 1,Contest 2
x,1,p,bs,0001013415,Choice 1-2,Choice 2-1
x,2,p,bs,0001013416,Choice 1-1,Choice 2-1
x,3,p,bs,0001013417,undervote,Choice 2-1
x,4,p,bs,0002003171,overvote,Choice 2-1
x,5,p,bs,0002003172,Choice 1-2,Choice 2-1
x,6,p,bs,0002003173,Choice 1-1,Choice 2-1
x,7,p,bs,0001000415,Choice 1-2,Choice 2-1
x,8,p,bs,0001000416,Choice 1-1,Choice 2-1
x,9,p,bs,0001000417,Choice 1-2,Choice 2-2
x,10,p,bs,0002000171,Choice 1-1,Choice 2-2
x,11,p,bs,0002000172,Choice 1-2,Choice 2-2
x,12,p,bs,0002000173,Choice 1-1,Choice 2-2
x,13,p,bs,0002000174,Choice 1-2,Choice 2-3
x,15,p,bs,0002000175,Choice 1-1,Choice 2-3
"""


def test_ess_cvr_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    ess_manifests,  # pylint: disable=unused-argument
    snapshot,
):
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

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    for cvrs in test_cases:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={"cvrs": cvrs, "cvrFileType": "ESS"},
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "cvrFileType": "ESS",
                    "name": "cvr-files.zip",
                    "uploadedAt": assert_is_date,
                },
                "processing": {
                    "completedAt": assert_is_date,
                    "error": None,
                    "startedAt": assert_is_date,
                    "status": ProcessingStatus.PROCESSED,
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


def test_ess_cvr_upload_invalid(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    ess_manifests,  # pylint: disable=unused-argument
):
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

    test_cases = [
        (
            [(io.BytesIO(ESS_CVR.encode()), "ess_cvr.csv")],
            "Missing ballots files - at least one file should contain the list of tabulated ballots and their corresponding CVR identifiers. Identified CVR files: ess_cvr.csv. Identified ballots files: None.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(ESS_BALLOTS_2.encode()),
                    "ess_ballots_2.csv",
                ),
            ],
            "Missing CVR file - one file should contain the cast vote records for each ballot. We attempt to auto-detect this file, but if we are failing to do so, you can rename the file cvr.csv to ensure that we treat it as the CVR file. Identified CVR files: None. Identified ballots files: ess_ballots_1.csv, ess_ballots_2.csv.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(ESS_BALLOTS_2.encode()),
                    "ess_ballots_2.csv",
                ),
                (
                    io.BytesIO(ESS_CVR.encode()),
                    "ess_cvr_1.csv",
                ),
                (
                    io.BytesIO(ESS_CVR.encode()),
                    "ess_cvr_2.csv",
                ),
            ],
            "Identified multiple CVR files - please upload only one CVR file containing the cast vote records for each ballot, and at least one ballots file containing the list of tabulated ballots and their corresponding CVR identifiers. Identified CVR files: ess_cvr_1.csv, ess_cvr_2.csv. Identified ballots files: ess_ballots_1.csv, ess_ballots_2.csv.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(ESS_CVR.encode()),
                    "ess_cvr.csv",
                ),
                (
                    io.BytesIO(
                        # Simulate leading zeros getting stripped from the tabulator column
                        replace_line(
                            ESS_BALLOTS_2,
                            -2,
                            "15,BATCH2,Not Reviewed,,,,N,Election Day,2000175,p",
                        ).encode()
                    ),
                    "ess_ballots_2.csv",
                ),
            ],
            "ess_ballots_2.csv: Tabulator CVR should be a ten-digit number if there is no Machine column. Got 2000175 for Cast Vote Record 15. Make sure any leading zeros have not been stripped from this field.",
        ),
        (
            [
                (
                    io.BytesIO(
                        # Sometimes we see scientific notation instead of hex
                        replace_line(
                            ESS_BALLOTS_WITH_MACHINE_COLUMN_AND_NO_METADATA_ROWS,
                            2,
                            "1,BATCH1,Not Reviewed,,,,N,REP 405,Election Day,4.78822E+15,7074480632,Card,Election Day,28,405,21,0001,",
                        ).encode()
                    ),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(ESS_CVR.encode()),
                    "ess_cvr.csv",
                ),
            ],
            "ess_ballots_1.csv: Tabulator CVR should be a ten-digit number or a sixteen-character hexadecimal string. Got 4.78822E+15 for Cast Vote Record 1. If you opened this file in Excel, it may have changed the format of this field.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(ESS_CVR.encode()),
                    "ess_cvr.csv",
                ),
                (
                    io.BytesIO(
                        replace_line(
                            ESS_BALLOTS_2,
                            -2,
                            "15,BATCH2,Not Reviewed,,,,N,Election Day,0003000175,p",
                        ).encode()
                    ),
                    "ess_ballots_2.csv",
                ),
            ],
            "ess_ballots_2.csv: Couldn't find a matching batch for Tabulator: 0003, Batch: BATCH2 (Cast Vote Record: 15). The Tabulator and Batch fields in the CVR file must match the Tabulator and Batch Name fields in the ballot manifest. The closest match we found in the ballot manifest was: Tabulator: 0002, Batch Name: BATCH2. Please check your CVR file and ballot manifest thoroughly to make sure these values match - there may be a similar inconsistency in other rows in the CVR file.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(b""),
                    "ess_cvr.csv",
                ),
            ],
            "ess_cvr.csv: CSV cannot be empty.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_CVR.encode()),
                    "ess_cvr.csv",
                ),
                (
                    io.BytesIO(b"Ballots"),
                    "ess_ballots_1.csv",
                ),
            ],
            "ess_ballots_1.csv: Please submit a valid CSV file with columns separated by commas.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(ESS_CVR.encode()),
                    "ess_cvr.csv",
                ),
                (
                    io.BytesIO(remove_line(ESS_BALLOTS_2, 10).encode()),
                    "ess_ballots_2.csv",
                ),
            ],
            "Mismatch between CVR file and ballots files. Make sure the Cast Vote Record column in the CVR file and the ballots file match and include exactly the same set of ballots.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(ESS_CVR.encode()),
                    "ess_cvr.csv",
                ),
                (
                    io.BytesIO(remove_line(ESS_BALLOTS_2, -2).encode()),
                    "ess_ballots_2.csv",
                ),
            ],
            "Mismatch between CVR file and ballots files. Make sure the Cast Vote Record column in the CVR file and the ballots file match and include exactly the same set of ballots.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(remove_line(ESS_CVR, 10).encode()),
                    "ess_cvr.csv",
                ),
                (
                    io.BytesIO(ESS_BALLOTS_2.encode()),
                    "ess_ballots_2.csv",
                ),
            ],
            "Mismatch between CVR file and ballots files. Make sure the Cast Vote Record column in the CVR file and the ballots file match and include exactly the same set of ballots.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(remove_line(ESS_CVR, -1).encode()),
                    "ess_cvr.csv",
                ),
                (
                    io.BytesIO(ESS_BALLOTS_2.encode()),
                    "ess_ballots_2.csv",
                ),
            ],
            "Mismatch between CVR file and ballots files. Make sure the Cast Vote Record column in the CVR file and the ballots file match and include exactly the same set of ballots.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(
                        replace_line(
                            ESS_CVR, 0, "Precinct,Ballot Style,Contest 1,Contest 2"
                        ).encode()
                    ),
                    "ess_cvr.csv",
                ),
                (
                    io.BytesIO(ESS_BALLOTS_2.encode()),
                    "ess_ballots_2.csv",
                ),
            ],
            "ess_cvr.csv: Missing required column Cast Vote Record.",
        ),
        (
            [
                (
                    io.BytesIO(
                        (
                            ESS_BALLOTS_1
                            + ",BATCH1,Not Reviewed,,,,N,Election Day,0002003172,p"
                        ).encode()
                    ),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(ESS_CVR.encode()),
                    "ess_cvr.csv",
                ),
                (
                    io.BytesIO(ESS_BALLOTS_2.encode()),
                    "ess_ballots_2.csv",
                ),
            ],
            "ess_ballots_1.csv: Missing required column Cast Vote Record in row 8.",
        ),
        (
            [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
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
                (
                    io.BytesIO(ESS_BALLOTS_2.encode()),
                    "ess_ballots_2.csv",
                ),
            ],
            "ess_cvr.csv: Please submit a valid CSV file with columns separated by commas. This file has columns separated by tabs.",
        ),
    ]

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    for invalid_cvrs, expected_error in test_cases:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={"cvrs": invalid_cvrs, "cvrFileType": "ESS"},
        )
        assert_ok(rv)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {
                    "cvrFileType": "ESS",
                    "name": "cvr-files.zip",
                    "uploadedAt": assert_is_date,
                },
                "processing": {
                    "completedAt": assert_is_date,
                    "error": expected_error,
                    "startedAt": assert_is_date,
                    "status": ProcessingStatus.ERRORED,
                    "workProgress": 0,
                    "workTotal": manifest_num_ballots,
                },
            },
        )


def test_ess_cvr_upload_cvr_file_with_tabulator_cvr_column(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    ess_manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Expect this upload to err
    cvrs = [
        (io.BytesIO(ESS_CVR_WITH_TABULATOR_CVR_COLUMN.encode()), "ess_cvr.csv"),
        (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv"),
        (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv"),
    ]

    # Expect this upload to succeed
    cvrs_with_override_cvr_file_name = [
        (io.BytesIO(ESS_CVR_WITH_TABULATOR_CVR_COLUMN.encode()), "cvr.csv"),
        (io.BytesIO(ESS_BALLOTS_1.encode()), "ess_ballots_1.csv"),
        (io.BytesIO(ESS_BALLOTS_2.encode()), "ess_ballots_2.csv"),
    ]

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={"cvrs": cvrs, "cvrFileType": "ESS"},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "cvrFileType": "ESS",
                "name": "cvr-files.zip",
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "completedAt": assert_is_date,
                "error": "Missing CVR file - one file should contain the cast vote records for each ballot. "
                "We attempt to auto-detect this file, but if we are failing to do so, you can rename the file cvr.csv to ensure that we treat it as the CVR file. "
                "Identified CVR files: None. Identified ballots files: ess_cvr.csv, ess_ballots_1.csv, ess_ballots_2.csv.",
                "startedAt": assert_is_date,
                "status": ProcessingStatus.ERRORED,
                "workProgress": 0,
                "workTotal": manifest_num_ballots,
            },
        },
    )

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={"cvrs": cvrs_with_override_cvr_file_name, "cvrFileType": "ESS"},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "cvrFileType": "ESS",
                "name": "cvr-files.zip",
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "completedAt": assert_is_date,
                "error": None,
                "startedAt": assert_is_date,
                "status": ProcessingStatus.PROCESSED,
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


def build_hart_cvr(
    batch_name: str,
    batch_sequence: str,
    cvr_guid: str,
    interpretations_string: str,
    add_write_in: bool = False,
):
    def build_choice(choice_name: str):
        if add_write_in:
            return """
                <Option>
                    <WriteInData>
                        <Text /><ImageId>fake-image-id</ImageId>
                        <WriteInDataStatus>Unresolved</WriteInDataStatus>
                    </WriteInData>
                    <Id>fake-choice-id-write-in</Id>
                    <Value>1</Value>
                </Option>
            """
        return f"""
            <Option>
                <Name>{choice_name}</Name>
                <Id>fake-choice-id-{choice_name}</Id>
                <Value>1</Value>
            </Option>
            """

    def build_contest(contest_name: str, choice_names: List[str]):
        choices = "\n".join(build_choice(choice_name) for choice_name in choice_names)
        return f"""
            <Contest>
                <Name>{contest_name}</Name>
                <Id>fake-contest-id-{contest_name}</Id>
                <Options>{choices}</Options>
            </Contest>
            """

    interpretations = interpretations_string.split(",")
    contests = "\n".join(
        [
            build_contest(
                "Contest 1",
                (["Choice 1-1"] if interpretations[0] == "1" else [])
                + (["Choice 1-2"] if interpretations[1] == "1" else []),
            ),
            build_contest(
                "Contest 2",
                (["Choice 2-1"] if interpretations[2] == "1" else [])
                + (["Choice 2-2"] if interpretations[3] == "1" else [])
                + (["Choice 2-3"] if interpretations[4] == "1" else []),
            ),
        ]
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
        <Cvr xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://tempuri.org/CVRDesign.xsd">
            <Contests>{contests}</Contests>
            <BatchSequence>{batch_sequence}</BatchSequence>
            <SheetNumber>1</SheetNumber>
            <PrecinctSplit>
                <Name>100</Name>
                <Id>fake-precinct-split-id</Id>
            </PrecinctSplit>
            <BatchNumber>{batch_name}</BatchNumber>
            <CvrGuid>{cvr_guid}</CvrGuid>
        </Cvr>
        """


HART_CVRS = [
    build_hart_cvr("BATCH1", "1", "1-1-1", "0,1,1,0,0"),
    build_hart_cvr("BATCH1", "2", "1-1-2", "1,0,1,0,0"),
    build_hart_cvr("BATCH1", "3", "1-1-3", "0,1,1,0,0"),
    build_hart_cvr("BATCH2", "1", "1-2-1", "1,0,1,0,0"),
    build_hart_cvr("BATCH2", "2", "1-2-2", "0,1,0,1,0"),
    build_hart_cvr("BATCH2", "3", "1-2-3", "1,0,0,0,1"),
    build_hart_cvr("BATCH3", "1", "1-3-1", "1,0,0,1,0"),
    build_hart_cvr("BATCH3", "2", "1-3-2", "1,0,0,0,1"),
    build_hart_cvr("BATCH3", "3", "1-3-3", "1,0,0,1,0"),
    build_hart_cvr("BATCH4", "1", "1-4-1", "1,0,0,0,1"),
    build_hart_cvr("BATCH4", "2", "1-4-2", "1,1,1,1,1"),
    build_hart_cvr("BATCH4", "4", "1-4-4", ",,1,0,0"),
    build_hart_cvr("BATCH4", "5", "1-4-5", ",,1,0,0"),
    build_hart_cvr("BATCH4", "6", "1-4-6", ",,1,0,0", add_write_in=True),
]

HART_CVRS_DUPLICATE_BATCH_NAMES = {
    "TABULATOR1": [
        build_hart_cvr("BATCH1", "1", "1-1-1", "0,1,1,0,0"),
        build_hart_cvr("BATCH1", "2", "1-1-2", "1,0,1,0,0"),
        build_hart_cvr("BATCH1", "3", "1-1-3", "0,1,1,0,0"),
        build_hart_cvr("BATCH2", "1", "1-2-1", "1,0,1,0,0"),
        build_hart_cvr("BATCH2", "2", "1-2-2", "0,1,0,1,0"),
        build_hart_cvr("BATCH2", "3", "1-2-3", "1,0,0,0,1"),
    ],
    "TABULATOR2": [
        build_hart_cvr("BATCH1", "1", "1-3-1", "1,0,0,1,0"),
        build_hart_cvr("BATCH1", "2", "1-3-2", "1,0,0,0,1"),
        build_hart_cvr("BATCH1", "3", "1-3-3", "1,0,0,1,0"),
        build_hart_cvr("BATCH2", "1", "1-4-1", "1,0,0,0,1"),
        build_hart_cvr("BATCH2", "2", "1-4-2", "1,1,1,1,1"),
        build_hart_cvr("BATCH2", "4", "1-4-4", ",,1,0,0"),
        build_hart_cvr("BATCH2", "5", "1-4-5", ",,1,0,0"),
        build_hart_cvr("BATCH2", "6", "1-4-6", ",,1,0,0", add_write_in=True),
    ],
}

# Modeled after a real scanned ballot information CSV
HART_SCANNED_BALLOT_INFORMATION = """#FormatVersion 1
#BatchId,Workstation,VotingType,VotingMethod,ScanSequence,Precinct,PageNumber,UniqueIdentifier,VariationNumber,Language,Party,Status,RejectReason,VoterIntentIssues,vDriveDeviceDataId,CvrId
1,"TABULATOR1","Absentee Voting","Paper",1,"001",1,"unique-identifier-01",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-1-1"
1,"TABULATOR1","Absentee Voting","Paper",1,"001",2,"unique-identifier-01",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-1-1"
1,"TABULATOR1","Absentee Voting","Paper",2,"001",1,"unique-identifier-02",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-1-2"
1,"TABULATOR1","Absentee Voting","Paper",2,"001",2,"unique-identifier-02",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-1-2"
1,"TABULATOR1","Absentee Voting","Paper",3,"001",1,"unique-identifier-03",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-1-3"
1,"TABULATOR1","Absentee Voting","Paper",3,"001",2,"unique-identifier-03",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-1-3"
1,"TABULATOR1","Absentee Voting","Paper",4,"001",1,"unique-identifier-04",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-2-1"
1,"TABULATOR1","Absentee Voting","Paper",4,"001",2,"unique-identifier-04",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-2-1"
1,"TABULATOR1","Absentee Voting","Paper",5,"001",1,"unique-identifier-05",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-2-2"
1,"TABULATOR1","Absentee Voting","Paper",5,"001",2,"unique-identifier-05",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-2-2"
1,"TABULATOR1","Absentee Voting","Paper",6,"001",1,"unique-identifier-06",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-2-3"
1,"TABULATOR1","Absentee Voting","Paper",6,"001",2,"unique-identifier-06",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-2-3"
1,"TABULATOR2","Absentee Voting","Paper",7,"001",1,"unique-identifier-07",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-3-1"
1,"TABULATOR2","Absentee Voting","Paper",7,"001",2,"unique-identifier-07",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-3-1"
1,"TABULATOR2","Absentee Voting","Paper",8,"001",1,"unique-identifier-08",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-3-2"
1,"TABULATOR2","Absentee Voting","Paper",8,"001",2,"unique-identifier-08",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-3-2"
1,"TABULATOR2","Absentee Voting","Paper",9,"001",1,"unique-identifier-09",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-3-3"
1,"TABULATOR2","Absentee Voting","Paper",9,"001",2,"unique-identifier-09",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-3-3"
1,"TABULATOR2","Absentee Voting","Paper",10,"001",1,"unique-identifier-10",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-4-1"
1,"TABULATOR2","Absentee Voting","Paper",10,"001",2,"unique-identifier-10",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-4-1"
1,"TABULATOR2","Absentee Voting","Paper",11,"001",1,"unique-identifier-11",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-4-2"
1,"TABULATOR2","Absentee Voting","Paper",11,"001",2,"unique-identifier-11",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-4-2"
1,"TABULATOR2","Absentee Voting","Paper",12,"001",1,"unique-identifier-12",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-4-4"
1,"TABULATOR2","Absentee Voting","Paper",12,"001",2,"unique-identifier-12",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-4-4"
1,"TABULATOR2","Absentee Voting","Paper",13,"001",1,"unique-identifier-13",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-4-5"
1,"TABULATOR2","Absentee Voting","Paper",13,"001",2,"unique-identifier-13",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-4-5"
1,"TABULATOR2","Absentee Voting","Paper",14,"001",1,"unique-identifier-14",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-4-6"
1,"TABULATOR2","Absentee Voting","Paper",14,"001",2,"unique-identifier-14",0,"English",,"Scanned",,False,"ABCD-1234(ABCD[1234*AB","1-4-6"
"""

HART_SCANNED_BALLOT_INFORMATION_MINIMAL = """#FormatVersion 1
#CvrId,UniqueIdentifier,Workstation
"1-1-1","unique-identifier-01","TABULATOR1"
"1-1-2","unique-identifier-02","TABULATOR1"
"1-1-3","unique-identifier-03","TABULATOR1"
"1-2-1","unique-identifier-04","TABULATOR1"
"1-2-2","unique-identifier-05","TABULATOR1"
"1-2-3","unique-identifier-06","TABULATOR1"
"1-3-1","unique-identifier-07","TABULATOR2"
"1-3-2","unique-identifier-08","TABULATOR2"
"1-3-3","unique-identifier-09","TABULATOR2"
"1-4-1","unique-identifier-10","TABULATOR2"
"1-4-2","unique-identifier-11","TABULATOR2"
"1-4-4","unique-identifier-12","TABULATOR2"
"1-4-5","unique-identifier-13","TABULATOR2"
"1-4-6","unique-identifier-14","TABULATOR2"
"""

HART_SCANNED_BALLOT_INFORMATION_MINIMAL_TABULATOR_1 = """#FormatVersion 1
#CvrId,UniqueIdentifier,Workstation
"1-1-1","unique-identifier-01","TABULATOR1"
"1-1-2","unique-identifier-02","TABULATOR1"
"1-1-3","unique-identifier-03","TABULATOR1"
"1-2-1","unique-identifier-04","TABULATOR1"
"1-2-2","unique-identifier-05","TABULATOR1"
"1-2-3","unique-identifier-06","TABULATOR1"
"""


HART_SCANNED_BALLOT_INFORMATION_MINIMAL_TABULATOR_2 = """#FormatVersion 1
#CvrId,UniqueIdentifier,Workstation
"1-3-1","unique-identifier-07","TABULATOR2"
"1-3-2","unique-identifier-08","TABULATOR2"
"1-3-3","unique-identifier-09","TABULATOR2"
"1-4-1","unique-identifier-10","TABULATOR2"
"1-4-2","unique-identifier-11","TABULATOR2"
"1-4-4","unique-identifier-12","TABULATOR2"
"1-4-5","unique-identifier-13","TABULATOR2"
"1-4-6","unique-identifier-14","TABULATOR2"
"""

HART_SCANNED_BALLOT_INFORMATION_CONFLICTING_WITH_MINIMAL = """#FormatVersion 1
#CvrId,UniqueIdentifier,Workstation
"1-1-1","unique-identifier-01","CONFLICTING"
"""


def zip_hart_cvrs(cvrs: List[str]):
    files: Dict[str, BinaryIO] = {
        f"cvr-{i}.xml": io.BytesIO(cvr.encode()) for i, cvr in enumerate(cvrs)
    }
    # There's usually a WriteIns directory in the zip file - simulate that to
    # make sure it gets skipped
    files["WriteIns"] = io.BytesIO()
    return io.BytesIO(zip_files(files).read())


def test_hart_cvr_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    hart_manifests,  # pylint: disable=unused-argument
    snapshot,
):
    # Upload CVRs
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": [(zip_hart_cvrs(HART_CVRS), "cvrs.zip")],
            "cvrFileType": "HART",
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
                "name": "cvr-files.zip",
                "uploadedAt": assert_is_date,
                "cvrFileType": "HART",
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


def test_hart_cvr_upload_with_scanned_ballot_information(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    hart_manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    class TestCase(TypedDict):
        scanned_ballot_information_file_contents: List[str]
        expected_processing_status: ProcessingStatus
        expected_processing_error: Optional[str]

    test_cases: List[TestCase] = [
        {
            "scanned_ballot_information_file_contents": [
                HART_SCANNED_BALLOT_INFORMATION
            ],
            "expected_processing_status": ProcessingStatus.PROCESSED,
            "expected_processing_error": None,
        },
        {
            "scanned_ballot_information_file_contents": [
                HART_SCANNED_BALLOT_INFORMATION_MINIMAL
            ],
            "expected_processing_status": ProcessingStatus.PROCESSED,
            "expected_processing_error": None,
        },
        {
            "scanned_ballot_information_file_contents": [
                HART_SCANNED_BALLOT_INFORMATION_MINIMAL_TABULATOR_1
            ],
            "expected_processing_status": ProcessingStatus.PROCESSED,
            "expected_processing_error": None,
        },
        {
            "scanned_ballot_information_file_contents": [
                HART_SCANNED_BALLOT_INFORMATION_MINIMAL_TABULATOR_1,
                HART_SCANNED_BALLOT_INFORMATION_MINIMAL_TABULATOR_2,
            ],
            "expected_processing_status": ProcessingStatus.PROCESSED,
            "expected_processing_error": None,
        },
        {
            "scanned_ballot_information_file_contents": [
                HART_SCANNED_BALLOT_INFORMATION_MINIMAL,
                HART_SCANNED_BALLOT_INFORMATION_MINIMAL_TABULATOR_1,
                HART_SCANNED_BALLOT_INFORMATION_MINIMAL_TABULATOR_2,
            ],
            "expected_processing_status": ProcessingStatus.PROCESSED,
            "expected_processing_error": None,
        },
        {
            "scanned_ballot_information_file_contents": [
                HART_SCANNED_BALLOT_INFORMATION_MINIMAL,
                HART_SCANNED_BALLOT_INFORMATION_CONFLICTING_WITH_MINIMAL,
            ],
            "expected_processing_status": ProcessingStatus.ERRORED,
            "expected_processing_error": "Found conflicting information in scanned ballot information CSVs for CVR 1-1-1. {'CvrId': '1-1-1', 'UniqueIdentifier': 'unique-identifier-01', 'Workstation': 'CONFLICTING'} does not equal {'CvrId': '1-1-1', 'UniqueIdentifier': 'unique-identifier-01', 'Workstation': 'TABULATOR1'}.",
        },
        {
            "scanned_ballot_information_file_contents": [""],
            "expected_processing_status": ProcessingStatus.ERRORED,
            "expected_processing_error": "CSV cannot be empty.",
        },
        {
            "scanned_ballot_information_file_contents": [
                "CvrId,UniqueIdentifier,Workstation\n"
            ],
            "expected_processing_status": ProcessingStatus.ERRORED,
            "expected_processing_error": "Expected first line of scanned ballot information CSV to contain '#FormatVersion'.",
        },
        {
            "scanned_ballot_information_file_contents": ["#FormatVersion 1\n"],
            "expected_processing_status": ProcessingStatus.ERRORED,
            "expected_processing_error": "Please submit a valid CSV file with columns separated by commas.",
        },
        {
            "scanned_ballot_information_file_contents": [
                "#FormatVersion 1\nCvrId,UniqueIdentifier,Workstation\n"
            ],
            "expected_processing_status": ProcessingStatus.ERRORED,
            "expected_processing_error": "CSV must contain at least one row after headers.",
        },
        {
            "scanned_ballot_information_file_contents": [
                "#FormatVersion 1\nMissing,UniqueIdentifier,Workstation\ncvr-id-1,unique-identifier-1,workstation-1\n"
            ],
            "expected_processing_status": ProcessingStatus.ERRORED,
            "expected_processing_error": "Missing required column CvrId in scanned ballot information CSV.",
        },
        {
            "scanned_ballot_information_file_contents": [
                "#FormatVersion 1\nCvrId,Missing,Workstation\ncvr-id-1,unique-identifier-1,workstation-1\n"
            ],
            "expected_processing_status": ProcessingStatus.ERRORED,
            "expected_processing_error": "Missing required column UniqueIdentifier in scanned ballot information CSV.",
        },
        {
            "scanned_ballot_information_file_contents": [
                "#FormatVersion 1\nCvrId,UniqueIdentifier,Missing\ncvr-id-1,unique-identifier-1,workstation-1\n"
            ],
            "expected_processing_status": ProcessingStatus.ERRORED,
            "expected_processing_error": "Missing required column Workstation in scanned ballot information CSV.",
        },
    ]

    for test_case in test_cases:
        scanned_ballot_information_files = [
            (string_to_bytes_io(file_contents), f"scanned-ballot-information-{i}.csv")
            for i, file_contents in enumerate(
                test_case["scanned_ballot_information_file_contents"]
            )
        ]
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={
                "cvrs": [
                    (zip_hart_cvrs(HART_CVRS), "cvrs.zip"),
                    *scanned_ballot_information_files,
                ],
                "cvrFileType": "HART",
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
                    "cvrFileType": "HART",
                    "name": "cvr-files.zip",
                    "uploadedAt": assert_is_date,
                },
                "processing": {
                    "status": test_case["expected_processing_status"],
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": test_case["expected_processing_error"],
                    "workProgress": (
                        0
                        if test_case["expected_processing_status"]
                        == ProcessingStatus.ERRORED
                        else manifest_num_ballots
                    ),
                    "workTotal": manifest_num_ballots,
                },
            },
        )

        if test_case["expected_processing_status"] == ProcessingStatus.PROCESSED:
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


def test_hart_cvr_upload_with_duplicate_batch_names(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    # Use the regular manifests which have batches with the same name but different tabulator
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    class TestCase(TypedDict):
        files: List[Tuple[BinaryIO, str]]
        expected_processing_status: ProcessingStatus
        expected_processing_error: Optional[str]

    test_cases: List[TestCase] = [
        {
            # Extracting tabulator info from a scanned ballot information CSV
            "files": [
                (
                    zip_hart_cvrs(
                        [
                            *HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR1"],
                            *HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR2"],
                        ]
                    ),
                    "cvrs.zip",
                ),
                (
                    string_to_bytes_io(HART_SCANNED_BALLOT_INFORMATION),
                    "scanned-ballot-information.csv",
                ),
            ],
            "expected_processing_status": ProcessingStatus.PROCESSED,
            "expected_processing_error": None,
        },
        {
            # Extracting tabulator info from multiple scanned ballot information CSVs
            "files": [
                (
                    zip_hart_cvrs(
                        [
                            *HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR1"],
                            *HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR2"],
                        ]
                    ),
                    "cvrs.zip",
                ),
                (
                    string_to_bytes_io(
                        HART_SCANNED_BALLOT_INFORMATION_MINIMAL_TABULATOR_1
                    ),
                    "scanned-ballot-information-1.csv",
                ),
                (
                    string_to_bytes_io(
                        HART_SCANNED_BALLOT_INFORMATION_MINIMAL_TABULATOR_2
                    ),
                    "scanned-ballot-information-2.csv",
                ),
            ],
            "expected_processing_status": ProcessingStatus.PROCESSED,
            "expected_processing_error": None,
        },
        {
            # Extracting tabulator info from CVR ZIP file names
            "files": [
                (
                    zip_hart_cvrs(HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR1"]),
                    "TABULATOR1.zip",
                ),
                (
                    zip_hart_cvrs(HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR2"]),
                    "TABULATOR2.zip",
                ),
            ],
            "expected_processing_status": ProcessingStatus.PROCESSED,
            "expected_processing_error": None,
        },
        {
            # Failing to extract tabulator info
            "files": [
                (
                    zip_hart_cvrs(
                        [
                            *HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR1"],
                            *HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR2"],
                        ]
                    ),
                    "cvrs.zip",
                ),
            ],
            "expected_processing_status": ProcessingStatus.ERRORED,
            "expected_processing_error": "Couldn't find a tabulator name for CVR 1-1-1. Because the batch names in your ballot manifest are not unique, tabulator names are needed. These can be provided by uploading scanned ballot information CSVs or a CVR ZIP file per tabulator, where the ZIP file names are tabulator names.",
        },
    ]

    for test_case in test_cases:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={
                "cvrs": test_case["files"],
                "cvrFileType": "HART",
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
                    "cvrFileType": "HART",
                    "name": "cvr-files.zip",
                    "uploadedAt": assert_is_date,
                },
                "processing": {
                    "status": test_case["expected_processing_status"],
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": test_case["expected_processing_error"],
                    "workProgress": (
                        0
                        if test_case["expected_processing_status"]
                        == ProcessingStatus.ERRORED
                        else manifest_num_ballots
                    ),
                    "workTotal": manifest_num_ballots,
                },
            },
        )

        if test_case["expected_processing_status"] == ProcessingStatus.PROCESSED:
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


def test_hart_cvr_upload_no_batch_match(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    hart_manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    invalid_cvrs = [
        (
            [build_hart_cvr("bad batch", "1", "1-1-1", "0,1,1,0,0")],
            "Error in file: cvr-0.xml from cvrs.zip. Couldn't find a matching batch for BatchNumber: bad batch. The BatchNumber values in CVR files should match the Batch Name values in the ballot manifest.",
        ),
    ]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for invalid_cvr, expected_error in invalid_cvrs:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={
                "cvrs": [(zip_hart_cvrs(invalid_cvr), "cvrs.zip")],
                "cvrFileType": "HART",
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
                    "name": "cvr-files.zip",
                    "uploadedAt": assert_is_date,
                    "cvrFileType": "HART",
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


def test_hart_cvr_upload_no_tabulator_plus_batch_match(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    # Use the regular manifests which have batches with the same name but different tabulator
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    cvr_uploads = [
        (
            [
                (
                    zip_hart_cvrs(HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR1"]),
                    "TABULATOR1.zip",
                ),
                (
                    zip_hart_cvrs(HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR2"]),
                    "forgot-to-rename-this-to-match-tabulator-in-ballot-manifest.zip",
                ),
            ],
            "Error in file: cvr-0.xml from forgot-to-rename-this-to-match-tabulator-in-ballot-manifest.zip. Couldn't find a matching batch for Tabulator: forgot-to-rename-this-to-match-tabulator-in-ballot-manifest, BatchNumber: BATCH1. Either the Workstation values in scanned ballot information CSVs, if provided, or CVR ZIP file names, if multiple, should match the Tabulator values in the ballot manifest. Likewise, the BatchNumber values in CVR files should match the Batch Name values in the ballot manifest.",
        ),
        (
            [
                (
                    zip_hart_cvrs(HART_CVRS_DUPLICATE_BATCH_NAMES["TABULATOR1"]),
                    "TABULATOR1.zip",
                ),
                (
                    zip_hart_cvrs(
                        [build_hart_cvr("invalid-batch", "1", "1-1-1", "1,1,1,1,1")]
                    ),
                    "TABULATOR2.zip",
                ),
            ],
            "Error in file: cvr-0.xml from TABULATOR2.zip. Couldn't find a matching batch for Tabulator: TABULATOR2, BatchNumber: invalid-batch. Either the Workstation values in scanned ballot information CSVs, if provided, or CVR ZIP file names, if multiple, should match the Tabulator values in the ballot manifest. Likewise, the BatchNumber values in CVR files should match the Batch Name values in the ballot manifest.",
        ),
        (
            [(zip_hart_cvrs(HART_CVRS), "cvrs.zip")],
            "Couldn't find a tabulator name for CVR 1-1-1. Because the batch names in your ballot manifest are not unique, tabulator names are needed. These can be provided by uploading scanned ballot information CSVs or a CVR ZIP file per tabulator, where the ZIP file names are tabulator names.",
        ),
    ]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for cvr_upload, expected_error in cvr_uploads:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={
                "cvrs": cvr_upload,
                "cvrFileType": "HART",
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
                    "name": "cvr-files.zip",
                    "uploadedAt": assert_is_date,
                    "cvrFileType": "HART",
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


def test_hart_cvr_upload_basic_input_validation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    hart_manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    class TestCase(TypedDict):
        cvrs: List
        expected_status_code: int
        expected_response: Any

    test_cases: List[TestCase] = [
        {
            "cvrs": [(zip_hart_cvrs(HART_CVRS), "cvrs.csv")],
            "expected_status_code": 400,
            "expected_response": {
                "errors": [
                    {
                        "errorType": "Bad Request",
                        "message": "Please submit at least one ZIP file.",
                    }
                ]
            },
        },
        {
            "cvrs": [
                (zip_hart_cvrs(HART_CVRS), "cvrs.csv"),
                (
                    string_to_bytes_io(HART_SCANNED_BALLOT_INFORMATION),
                    "scanned-ballot-information.csv",
                ),
            ],
            "expected_status_code": 400,
            "expected_response": {
                "errors": [
                    {
                        "errorType": "Bad Request",
                        "message": "Please submit at least one ZIP file.",
                    }
                ]
            },
        },
        {
            "cvrs": [
                (zip_hart_cvrs(HART_CVRS), "cvrs.zip"),
                (
                    string_to_bytes_io(HART_SCANNED_BALLOT_INFORMATION),
                    "scanned-ballot-information.jpg",
                ),
            ],
            "expected_status_code": 400,
            "expected_response": {
                "errors": [
                    {
                        "errorType": "Bad Request",
                        "message": "Please submit only ZIP files and CSVs.",
                    }
                ]
            },
        },
        {
            "cvrs": [
                (
                    zip_hart_cvrs(HART_CVRS),
                    "cvrs.zip",
                    # Verify that the Windows ZIP mimetype works
                    "application/x-zip-compressed",
                ),
            ],
            "expected_status_code": 200,
            "expected_response": {"status": "ok"},
        },
    ]

    for test_case in test_cases:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={"cvrFileType": "HART", "cvrs": test_case["cvrs"]},
        )
        assert rv.status_code == test_case["expected_status_code"]
        assert json.loads(rv.data) == test_case["expected_response"]


def test_cvrs_unexpected_error(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    manifest_num_ballots = jurisdictions[0]["ballotManifest"]["numBallots"]

    # Duplicate a row to simulate an unexpected error
    cvrs = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (Vote For=1)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
"""
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(cvrs.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
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
                "cvrFileType": "DOMINION",
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Could not parse CVR file",
                "workProgress": 0,
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
            "cvrs": (
                io.BytesIO(TEST_CVRS.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "WRONG",
        },
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Invalid file type",
            }
        ]
    }

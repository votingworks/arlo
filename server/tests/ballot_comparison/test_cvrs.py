import io, json
from typing import List
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...worker.bgcompute import (
    bgcompute_update_cvr_file,
    bgcompute_update_ballot_manifest_file,
)
from ...util.process_file import ProcessingStatus
from .conftest import TEST_CVRS


def test_cvr_upload(
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

    # Upload CVRs
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={"cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",)},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "cvrs.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.READY_TO_PROCESS,
                "startedAt": None,
                "completedAt": None,
                "error": None,
            },
        },
    )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["cvrs"]["numBallots"] is None

    bgcompute_update_cvr_file(election_id)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "cvrs.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
        },
    )

    expected_num_cvr_ballots = len(TEST_CVRS.splitlines()) - 4

    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == expected_num_cvr_ballots
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
            "file": {"name": "cvrs.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": "PROCESSED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
            "numBallots": expected_num_cvr_ballots,
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
        data={"cvrs": (io.BytesIO(COUNTING_GROUP_CVR.encode()), "cvrs.csv",)},
    )
    assert_ok(rv)

    bgcompute_update_cvr_file(election_id)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "cvrs.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
        },
    )

    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == 15
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
        data={"cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",)},
    )
    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).cvr_file_id

    bgcompute_update_cvr_file(election_id)

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO("\n".join(TEST_CVRS.splitlines()[:-2]).encode()),
                "cvrs.csv",
            )
        },
    )
    assert_ok(rv)

    # The old file should have been deleted
    jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
    assert File.query.get(file_id) is None
    assert jurisdiction.cvr_file_id != file_id

    bgcompute_update_cvr_file(election_id)

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
        data={"cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",)},
    )
    assert_ok(rv)

    file_id = Jurisdiction.query.get(jurisdiction_ids[0]).cvr_file_id

    bgcompute_update_cvr_file(election_id)

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
        data={"cvrs": (io.BytesIO(b"not a CSV file"), "random.txt")},
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
        data={"cvrs": (io.BytesIO(NEWLINE_CVR.encode()), "cvrs.csv",)},
    )
    assert_ok(rv)

    bgcompute_update_cvr_file(election_id)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "cvrs.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
        },
    )

    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .order_by(CvrBallot.imprinted_id)
        .all()
    )
    assert len(cvr_ballots) == 15
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
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    invalid_cvrs = [
        ("", "CVR file cannot be empty.",),
        (
            """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,,"Contest 1 (Vote For=1)","Contest 1 (123)"
,,,,,,,,Choice 1-1,Choice 1-2
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1
""",
            "Invalid contest name: Contest 1 (123). Contest names should have this format: Contest Name (Vote For=1).",
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
        ),
    ]

    for invalid_cvr, expected_error in invalid_cvrs:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
            data={"cvrs": (io.BytesIO(invalid_cvr.encode()), "cvrs.csv",)},
        )
        assert_ok(rv)

        bgcompute_update_cvr_file(election_id)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
        )
        compare_json(
            json.loads(rv.data),
            {
                "file": {"name": "cvrs.csv", "uploadedAt": assert_is_date,},
                "processing": {
                    "status": ProcessingStatus.ERRORED,
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": expected_error,
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

    bgcompute_update_ballot_manifest_file(election_id)

    # Error should be recorded for CVRs
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "cvrs.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Invalid TabulatorNum/BatchId for row with CvrNumber 7: TABULATOR2, BATCH1. The TabulatorNum and BatchId fields in the CVR file must match the Tabulator and Batch Name fields in the ballot manifest. The closest match we found in the ballot manifest was: TABULATOR2, BATCH2. Please check your CVR file and ballot manifest thoroughly to make sure these values match - there may be a similar inconsistency in other rows in the CVR file.",
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

    bgcompute_update_ballot_manifest_file(election_id)

    # CVRs should be fixed
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {"name": "cvrs.csv", "uploadedAt": assert_is_date,},
            "processing": {
                "status": ProcessingStatus.PROCESSED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": None,
            },
        },
    )

    assert (
        CvrBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .count()
        == len(TEST_CVRS.splitlines()) - 4
    )
    assert Jurisdiction.query.get(jurisdiction_ids[0]).cvr_contests_metadata is not None

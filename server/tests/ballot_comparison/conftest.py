import io
import pytest
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...bgcompute import (
    bgcompute_update_ballot_manifest_file,
    bgcompute_update_cvr_file,
)

TEST_CVRS = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,Choice 1-1,Choice 1-2,Choice 2-1,Choice 2-2,Choice 2-3
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,PrecinctPortion,BallotType,REP,DEM,LBR,IND,,
1,TABULATOR1,BATCH1,1,1-1-1,12345,COUNTY,0,1,1,1,0
2,TABULATOR1,BATCH1,2,1-1-2,12345,COUNTY,1,0,1,0,1
3,TABULATOR1,BATCH1,3,1-1-3,12345,COUNTY,0,1,1,1,0
4,TABULATOR1,BATCH2,1,1-2-1,12345,COUNTY,1,0,1,0,1
5,TABULATOR1,BATCH2,2,1-2-2,12345,COUNTY,0,1,1,1,0
6,TABULATOR1,BATCH2,3,1-2-3,12345,COUNTY,1,0,1,0,1
7,TABULATOR2,BATCH1,1,2-1-1,12345,COUNTY,0,1,1,1,0
8,TABULATOR2,BATCH1,2,2-1-2,12345,COUNTY,1,0,1,0,1
9,TABULATOR2,BATCH1,3,2-1-3,12345,COUNTY,1,0,1,1,0
10,TABULATOR2,BATCH2,1,2-2-1,12345,COUNTY,1,0,1,0,1
11,TABULATOR2,BATCH2,2,2-2-2,12345,COUNTY,1,1,1,1,1
12,TABULATOR2,BATCH2,3,2-2-3,12345,COUNTY,1,0,1,0,1
13,TABULATOR2,BATCH2,4,2-2-4,12345,CITY,,,1,0,1
14,TABULATOR2,BATCH2,5,2-2-5,12345,CITY,,,1,1,0
15,TABULATOR2,BATCH2,6,2-2-6,12345,CITY,,,1,0,1
"""


@pytest.fixture
def election_id(client: FlaskClient, org_id: str, request):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    return create_election(
        client,
        audit_name=f"Test Audit {request.node.name}",
        audit_type=AuditType.BALLOT_COMPARISON,
        organization_id=org_id,
    )


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/ballot-manifest",
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
    bgcompute_update_ballot_manifest_file()


@pytest.fixture
def cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={"cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",)},
    )
    assert_ok(rv)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={"cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",)},
    )
    assert_ok(rv)
    bgcompute_update_cvr_file()

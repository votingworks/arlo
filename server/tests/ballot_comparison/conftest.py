import io
import pytest
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *

# Note that we intentionally leave out one row from the CVR to simulate what
# happens when a row is missing. This would be the ballot: TABULATOR2,BATCH2,3,2-2-3
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
7,TABULATOR2,BATCH1,1,2-1-1,12345,COUNTY,1,0,1,1,0
8,TABULATOR2,BATCH1,2,2-1-2,12345,COUNTY,1,0,1,0,1
9,TABULATOR2,BATCH1,3,2-1-3,12345,COUNTY,1,0,1,1,0
10,TABULATOR2,BATCH2,1,2-2-1,12345,COUNTY,1,0,1,0,1
11,TABULATOR2,BATCH2,2,2-2-2,12345,COUNTY,1,1,1,1,1
12,TABULATOR2,BATCH2,4,2-2-4,12345,CITY,,,1,0,1
13,TABULATOR2,BATCH2,5,2-2-5,12345,CITY,,,0,0,0
14,TABULATOR2,BATCH2,6,2-2-6,12345,CITY,,,1,0,1
"""

# Remove Choice 1-2
TEST_CVRS_WITH_CHOICE_REMOVED = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,Choice 1-1,Choice 2-1,Choice 2-2,Choice 2-3
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,PrecinctPortion,BallotType,REP,DEM,LBR,IND,,
1,TABULATOR1,BATCH1,1,1-1-1,12345,COUNTY,0,1,1,0
2,TABULATOR1,BATCH1,2,1-1-2,12345,COUNTY,1,1,0,1
3,TABULATOR1,BATCH1,3,1-1-3,12345,COUNTY,0,1,1,0
4,TABULATOR1,BATCH2,1,1-2-1,12345,COUNTY,1,1,0,1
5,TABULATOR1,BATCH2,2,1-2-2,12345,COUNTY,0,1,1,0
6,TABULATOR1,BATCH2,3,1-2-3,12345,COUNTY,1,1,0,1
7,TABULATOR2,BATCH1,1,2-1-1,12345,COUNTY,1,1,1,0
8,TABULATOR2,BATCH1,2,2-1-2,12345,COUNTY,1,1,0,1
9,TABULATOR2,BATCH1,3,2-1-3,12345,COUNTY,1,1,1,0
10,TABULATOR2,BATCH2,1,2-2-1,12345,COUNTY,1,1,0,1
11,TABULATOR2,BATCH2,2,2-2-2,12345,COUNTY,1,1,1,1
12,TABULATOR2,BATCH2,4,2-2-4,12345,CITY,,1,0,1
13,TABULATOR2,BATCH2,5,2-2-5,12345,CITY,,0,0,0
14,TABULATOR2,BATCH2,6,2-2-6,12345,CITY,,1,0,1
"""

# Add Choice 1-3
TEST_CVRS_WITH_EXTRA_CHOICE = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,Choice 1-1,Choice 1-2,Choice 1-3,Choice 2-1,Choice 2-2,Choice 2-3
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,PrecinctPortion,BallotType,REP,DEM,,LBR,IND,,
1,TABULATOR1,BATCH1,1,1-1-1,12345,COUNTY,0,1,0,1,1,0
2,TABULATOR1,BATCH1,2,1-1-2,12345,COUNTY,1,0,0,1,0,1
3,TABULATOR1,BATCH1,3,1-1-3,12345,COUNTY,0,1,0,1,1,0
4,TABULATOR1,BATCH2,1,1-2-1,12345,COUNTY,1,0,0,1,0,1
5,TABULATOR1,BATCH2,2,1-2-2,12345,COUNTY,0,1,0,1,1,0
6,TABULATOR1,BATCH2,3,1-2-3,12345,COUNTY,1,0,0,1,0,1
7,TABULATOR2,BATCH1,1,2-1-1,12345,COUNTY,1,0,0,1,1,0
8,TABULATOR2,BATCH1,2,2-1-2,12345,COUNTY,1,0,0,1,0,1
9,TABULATOR2,BATCH1,3,2-1-3,12345,COUNTY,1,0,0,1,1,0
10,TABULATOR2,BATCH2,1,2-2-1,12345,COUNTY,1,0,0,1,0,1
11,TABULATOR2,BATCH2,2,2-2-2,12345,COUNTY,1,1,0,1,1,1
12,TABULATOR2,BATCH2,4,2-2-4,12345,CITY,,,,1,0,1
13,TABULATOR2,BATCH2,5,2-2-5,12345,CITY,,,,0,0,0
14,TABULATOR2,BATCH2,6,2-2-6,12345,CITY,,,,1,0,1
"""


@pytest.fixture
def election_id(client: FlaskClient, org_id: str, request):
    params = getattr(request, "param", None) or {}
    audit_math_type = params.get("audit_math_type", AuditMathType.SUPERSIMPLE)
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    return create_election(
        client,
        audit_name=f"Test Audit {request.node.name}",
        audit_type=AuditType.BALLOT_COMPARISON,
        audit_math_type=audit_math_type,
        organization_id=org_id,
    )


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(
            b"Tabulator,Batch Name,Number of Ballots\n"
            b"TABULATOR1,BATCH1,3\n"
            b"TABULATOR1,BATCH2,3\n"
            b"TABULATOR2,BATCH1,3\n"
            b"TABULATOR2,BATCH2,6"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(
            b"Tabulator,Batch Name,Number of Ballots\n"
            b"TABULATOR1,BATCH1,3\n"
            b"TABULATOR1,BATCH2,3\n"
            b"TABULATOR2,BATCH1,3\n"
            b"TABULATOR2,BATCH2,6"
        ),
        election_id,
        jurisdiction_ids[1],
    )
    assert_ok(rv)


@pytest.fixture
def ess_manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    for jurisdiction_id in jurisdiction_ids[:2]:
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = upload_ballot_manifest(
            client,
            io.BytesIO(
                b"Tabulator,Batch Name,Number of Ballots\n"
                b"0001,BATCH1,3\n"
                b"0001,BATCH2,3\n"
                b"0002,BATCH1,3\n"
                b"0002,BATCH2,6"
            ),
            election_id,
            jurisdiction_id,
        )
        assert_ok(rv)


@pytest.fixture
def hart_manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    for jurisdiction_id in jurisdiction_ids[:2]:
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = upload_ballot_manifest(
            client,
            io.BytesIO(
                b"Tabulator,Batch Name,Number of Ballots\n"
                b"TABULATOR1,BATCH1,3\n"
                b"TABULATOR1,BATCH2,3\n"
                b"TABULATOR2,BATCH3,3\n"
                b"TABULATOR2,BATCH4,6"
            ),
            election_id,
            jurisdiction_id,
        )
        assert_ok(rv)


@pytest.fixture
def cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_cvrs(
        client,
        io.BytesIO(TEST_CVRS.encode()),
        election_id,
        jurisdiction_ids[0],
        "DOMINION",
    )
    assert_ok(rv)
    rv = upload_cvrs(
        client,
        io.BytesIO(TEST_CVRS.encode()),
        election_id,
        jurisdiction_ids[1],
        "DOMINION",
    )
    assert_ok(rv)

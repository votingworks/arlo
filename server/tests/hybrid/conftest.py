import io
from typing import List
import pytest

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ..ballot_comparison.conftest import TEST_CVRS


@pytest.fixture
def election_id(client: FlaskClient, org_id: str, request):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    return create_election(
        client,
        audit_name=f"Test Audit {request.node.name}",
        audit_type=AuditType.HYBRID,
        audit_math_type=AuditMathType.SUITE,
        organization_id=org_id,
    )


@pytest.fixture
def contest_ids(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
) -> List[str]:
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Choice 1-1",
                    "numVotes": 12 + 18,  # CVR + non-CVR
                },
                {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 8 + 2},
            ],
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 2",
            "isTargeted": False,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "Choice 2-1", "numVotes": 13 + 7},
                {"id": str(uuid.uuid4()), "name": "Choice 2-2", "numVotes": 6 + 2},
                {"id": str(uuid.uuid4()), "name": "Choice 2-3", "numVotes": 7 + 3},
            ],
            "numWinners": 2,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


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
                    b"Tabulator,Batch Name,Number of Ballots,CVR\n"
                    b"TABULATOR1,BATCH1,3,Y\n"
                    b"TABULATOR1,BATCH2,3,Y\n"
                    b"TABULATOR2,BATCH1,3,Y\n"
                    b"TABULATOR2,BATCH2,6,Y\n"
                    b"TABULATOR3,BATCH1,10,N"
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
                    b"Tabulator,Batch Name,Number of Ballots,CVR\n"
                    b"TABULATOR1,BATCH1,3,Y\n"
                    b"TABULATOR1,BATCH2,3,Y\n"
                    b"TABULATOR2,BATCH1,3,Y\n"
                    b"TABULATOR2,BATCH2,6,Y\n"
                    b"TABULATOR3,BATCH1,10,N"
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
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(TEST_CVRS.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

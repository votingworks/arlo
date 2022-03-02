import io
from typing import List
from flask.testing import FlaskClient
import pytest

from ..helpers import *  # pylint: disable=wildcard-import
from .test_ballot_comparison import (
    audit_all_ballots,
    check_discrepancies,
    generate_audit_results,
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
7,TABULATOR2,BATCH1,1,2-1-1,12345,COUNTY,1,0,1,1,0
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
        audit_math_type=AuditMathType.RAIRE,
        organization_id=org_id,
    )


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
            "cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={
            "cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)


def test_raire_ballot_comparison_two_rounds(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # AA uploads standardized contests file
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(
                    b"Contest Name,Jurisdictions\n"
                    b'Contest 1,"J1,J2"\n'
                    b'Contest 2,"J1,J2"\n'
                    b"Contest 3,J2\n"
                ),
                "standardized-contests.csv",
            )
        },
    )
    assert_ok(rv)

    # AA selects a contest to target from the standardized contest list
    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    standardized_contests = json.loads(rv.data)

    target_contest = standardized_contests[0]
    opportunistic_contest = standardized_contests[1]
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": target_contest["name"],
                "numWinners": 1,
                "jurisdictionIds": target_contest["jurisdictionIds"],
                "isTargeted": True,
            },
            # TODO disallow opportunistic contests
        ],
    )
    assert_ok(rv)

    # AA selects a sample size and launches the audit
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    target_contest_id = contests[0]["id"]
    # opportunistic_contest_id = contests[1]["id"]

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    sample_size = sample_size_options[target_contest_id][0]
    snapshot.assert_match(sample_size["size"])

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
    for jurisdiction_id in target_contest["jurisdictionIds"]:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/audit-board",
            [{"name": "Audit Board #1"}],
        )
        assert_ok(rv)

    # Audit boards audit all the ballots.
    # Our goal is to mostly make the audit board interpretations match the CVRs
    # for the target contest, messing up just a couple in order to trigger a
    # second round. For convenience, using the same format as the CVR to
    # specify our audit results.
    # Tabulator, Batch, Ballot, Choice 1-1, Choice 1-2, Choice 2-1, Choice 2-2, Choice 2-3
    # We also specify the expected discrepancies.
    audit_results = {
        ("J1", "TABULATOR1", "BATCH1", 1): ("0,1,1,1,0", (None, None)),
        ("J1", "TABULATOR1", "BATCH2", 2): ("0,1,1,1,0", (None, None)),
        ("J1", "TABULATOR1", "BATCH2", 3): ("1,1,1,0,1", (1, None),),  # CVR: 1,0,1,0,1
        ("J1", "TABULATOR2", "BATCH2", 2): ("1,1,1,1,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 3): ("1,0,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 4): ("not found", (2, None)),  # CVR: ,,1,0,1
        ("J1", "TABULATOR2", "BATCH2", 5): (",,1,1,0", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 6): (",,1,0,1", (None, None)),
        ("J2", "TABULATOR1", "BATCH1", 1): ("blank", (-1, None)),  # CVR: 0,1,1,1,0
        ("J2", "TABULATOR1", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR1", "BATCH1", 3): ("0,1,1,1,0", (None, None)),
        ("J2", "TABULATOR1", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR1", "BATCH2", 3): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH1", 1): ("1,0,1,1,0", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 2): ("1,1,1,1,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 3): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 5): (",,1,1,0", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 6): (",,1,0,1", (None, None)),
    }

    audit_all_ballots(round_1_id, audit_results, target_contest_id, None)

    # Check the audit report
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    check_discrepancies(rv.data, audit_results)

    # Start a second round
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    # For round 2, audit results should match the CVR exactly.
    audit_results = {
        ("J1", "TABULATOR1", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 4): (",,1,0,1", (None, None)),
    }

    audit_all_ballots(round_2_id, audit_results, target_contest_id, None)

    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    check_discrepancies(rv.data, audit_results)

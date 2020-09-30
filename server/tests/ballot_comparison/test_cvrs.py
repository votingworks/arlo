import io, json
from typing import List
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...bgcompute import bgcompute_update_cvr_file
from ...util.process_file import ProcessingStatus


TEST_CVRS = """Test Audit CVR Upload,5.2.16.1,,,,,,,,,,
,,,,,,,Contest 1 (Vote For=1),Contest 1 (Vote For=1),Contest 2 (Vote For=2),Contest 2 (Vote For=2),Contest 2 (Vote For=2)
,,,,,,,Choice 1-1,Choice 1-2,Choice 2-1,Choice 2-2,Choice 2-3
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,PrecinctPortion,BallotType,REP,DEM,LBR,IND,,
1,1,1,1,1-1-1,12345,COUNTY,0,1,1,1,0
2,1,1,3,1-1-3,12345,COUNTY,1,0,1,0,1
3,1,1,5,1-1-5,12345,COUNTY,0,1,1,1,0
4,1,2,2,1-2-2,12345,COUNTY,1,0,1,0,1
5,1,2,4,1-2-4,12345,COUNTY,0,1,1,1,0
6,1,2,6,1-2-6,12345,COUNTY,1,0,1,0,1
7,2,1,1,2-1-1,12345,COUNTY,0,1,1,1,0
8,2,1,3,2-1-3,12345,COUNTY,1,0,1,0,1
9,2,1,5,2-1-5,12345,COUNTY,0,1,1,1,0
10,2,2,2,2-2-2,12345,COUNTY,1,0,1,0,1
11,2,2,4,2-2-4,12345,COUNTY,0,1,1,1,0
12,2,2,6,2-2-6,12345,COUNTY,1,0,1,0,1
13,2,2,8,2-2-8,12345,CITY,,,1,0,1
14,2,2,10,2-2-10,12345,CITY,,,1,1,0
15,2,2,12,2-2-12,12345,CITY,,,1,0,1
"""


def test_cvr_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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

    bgcompute_update_cvr_file()

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
        CvrBallot.query.join(Batch).filter_by(jurisdiction_id=jurisdiction_ids[0]).all()
    )
    assert len(cvr_ballots) == 15
    snapshot.assert_match(
        [
            dict(
                batch_name=cvr.batch.name,
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


# TODO
# - copy all the tests from test_batch_tallies.py
# - test a bunch of CVR parse errors

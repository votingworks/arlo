import io
import uuid
from flask.testing import FlaskClient

from ..helpers import *


def test_support_get_round_progress_ballot_comparison(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    election_settings,
    manifests,
    cvrs,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = upload_standardized_contests(
        client,
        io.BytesIO(b'Contest Name,Jurisdictions\nContest 1,"J1,J2"\n'),
        election_id,
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    standardized_contest = json.loads(rv.data)[0]
    contest_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_id,
                "name": standardized_contest["name"],
                "numWinners": 1,
                "jurisdictionIds": standardized_contest["jurisdictionIds"],
                "isTargeted": True,
            },
        ],
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size = json.loads(rv.data)["sampleSizes"][contest_id][0]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_id: sample_size}},
    )
    assert_ok(rv)

    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = client.get(f"/api/support/elections/{election_id}/round-progress")
    # J3 isn't in the contest, so it has no ballots to audit and is complete
    assert json.loads(rv.data) == {
        "jurisdictions": {"numComplete": 1, "numTotal": 3},
        "discrepancyCount": 0,
    }

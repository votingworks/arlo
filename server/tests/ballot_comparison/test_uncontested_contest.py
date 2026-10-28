import io
import json
import uuid
from datetime import datetime, timezone
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *

UNCONTESTED_CVRS = (
    "Test Audit CVR Upload,5.2.16.1,,,,,,\n"
    ",,,,,,,Uncontested Contest (Vote For=1)\n"
    ",,,,,,,Only Candidate\n"
    "CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,PrecinctPortion,BallotType,REP\n"
    + "".join(
        f"{i + 1},{tabulator},{batch},{record},{tabulator[-1]}-{batch[-1]}-{record},12345,COUNTY,1\n"
        for i, (tabulator, batch, record) in enumerate(
            (tabulator, batch, record)
            for tabulator, batch, num_ballots in [
                ("TABULATOR1", "BATCH1", 3),
                ("TABULATOR1", "BATCH2", 3),
                ("TABULATOR2", "BATCH1", 3),
                ("TABULATOR2", "BATCH2", 6),
            ]
            for record in range(1, num_ballots + 1)
        )
    )
)


def audit_round(
    client: FlaskClient,
    election_id: str,
    round_id: str,
    contest_id: str,
    interpretation: Interpretation,
):
    jurisdiction_ids = {
        jurisdiction_id
        for (jurisdiction_id,) in SampledBallot.query.join(SampledBallotDraw)
        .filter_by(round_id=round_id)
        .join(Batch)
        .with_entities(Batch.jurisdiction_id)
    }

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in jurisdiction_ids:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/audit-board",
            [{"name": "Audit Board #1"}],
        )
        assert_ok(rv)

    ballots = (
        SampledBallot.query.join(SampledBallotDraw).filter_by(round_id=round_id).all()
    )
    contest = Contest.query.get(contest_id)
    for ballot in ballots:
        audit_ballot(
            ballot,
            contest_id,
            interpretation,
            contest.choices if interpretation == Interpretation.VOTE else [],
        )
    for audit_board in AuditBoard.query.filter_by(round_id=round_id).all():
        audit_board.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)


def test_ballot_comparison_uncontested_contest(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    election_settings,
    manifests,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = upload_cvrs(
            client,
            io.BytesIO(UNCONTESTED_CVRS.encode()),
            election_id,
            jurisdiction_id,
            "DOMINION",
        )
        assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = upload_standardized_contests(
        client,
        io.BytesIO(b'Contest Name,Jurisdictions\nUncontested Contest,"J1,J2"\n'),
        election_id,
    )
    assert_ok(rv)

    contest_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_id,
                "name": "Uncontested Contest",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            }
        ],
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    [contest] = json.loads(rv.data)["contests"]
    assert len(contest["choices"]) == 1
    assert contest["choices"][0]["numVotes"] == 30

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size = json.loads(rv.data)["sampleSizes"][contest_id][0]
    assert sample_size["size"] == 1

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_id: sample_size}},
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]
    assert SampledBallotDraw.query.filter_by(round_id=round_1_id).count() == 1

    # A blank ballot doesn't confirm the outcome
    audit_round(client, election_id, round_1_id, contest_id, Interpretation.BLANK)

    rv = client.get(f"/api/election/{election_id}/round")
    [round_1] = json.loads(rv.data)["rounds"]
    assert round_1["isAuditComplete"] is False
    assert (
        RoundContest.query.filter_by(round_id=round_1_id, contest_id=contest_id)
        .one()
        .end_p_value
        == 1
    )

    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    sample_size = json.loads(rv.data)["sampleSizes"][contest_id][0]
    assert sample_size["size"] == 1

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 2, "sampleSizes": {contest_id: sample_size}},
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    # A vote for the winner confirms the outcome
    audit_round(client, election_id, round_2_id, contest_id, Interpretation.VOTE)

    rv = client.get(f"/api/election/{election_id}/round")
    round_2 = json.loads(rv.data)["rounds"][1]
    assert round_2["isAuditComplete"] is True
    assert (
        RoundContest.query.filter_by(round_id=round_2_id, contest_id=contest_id)
        .one()
        .end_p_value
        == 0
    )

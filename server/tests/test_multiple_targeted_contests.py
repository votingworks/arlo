import uuid, json
from typing import List
import pytest
from flask.testing import FlaskClient

from .helpers import *  # pylint: disable=wildcard-import
from ..models import *  # pylint: disable=wildcard-import


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
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 600,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400,},
            ],
            "totalBallotsCast": 1600,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 2",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "Yes", "numVotes": 800,},
                {"id": str(uuid.uuid4()), "name": "No", "numVotes": 650,},
            ],
            "totalBallotsCast": 1600,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 3",
            "isTargeted": False,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 200,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 300,},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 100,},
            ],
            "totalBallotsCast": 600,
            "numWinners": 2,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


def test_sample_size_round_1(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_sizes = json.loads(rv.data)["sampleSizes"]
    contest_id_to_name = dict(Contest.query.values(Contest.id, Contest.name))
    snapshot.assert_match(
        {contest_id_to_name[id]: sizes for id, sizes in sample_sizes.items()}
    )


def test_two_rounds(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_sizes = json.loads(rv.data)["sampleSizes"]
    selected_sample_sizes = {
        contest_id: sizes[0]["size"] for contest_id, sizes in sample_sizes.items()
    }

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": selected_sample_sizes},
    )
    assert_ok(rv)
    round_1 = Round.query.filter_by(election_id=election_id).first()

    # Audit all the ballots for Contest 1 and meet the risk limit, but don't
    # audit any for Contest 2, which should still trigger a second round.
    run_audit_round(round_1.id, contest_ids[0], contest_ids, 0.7)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is not None
    assert rounds[0]["isAuditComplete"] is False

    # Check that the right number of ballots were sampled for each contest
    contest_1_ballots = SampledBallotDraw.query.filter_by(
        contest_id=contest_ids[0]
    ).count()
    contest_2_ballots = SampledBallotDraw.query.filter_by(
        contest_id=contest_ids[1]
    ).count()
    assert contest_1_ballots == selected_sample_sizes[contest_ids[0]]
    assert contest_2_ballots == selected_sample_sizes[contest_ids[1]]

    # Check that we're sampling ballots from the two jurisdictions that uploaded manifests
    sampled_jurisdictions = (
        SampledBallotDraw.query.join(SampledBallot)
        .join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election_id)
        .values(Jurisdiction.id.distinct())
    )
    assert set(j_id for j_id, in sampled_jurisdictions) == set(jurisdiction_ids[:2])

    round_contests = {
        round_contest.contest_id: round_contest
        for round_contest in RoundContest.query.filter_by(round_id=rounds[0]["id"])
        .order_by(RoundContest.created_at)
        .all()
    }
    assert round_contests[contest_ids[0]].is_complete is True
    assert round_contests[contest_ids[1]].is_complete is False
    assert round_contests[contest_ids[2]].is_complete is False
    snapshot.assert_match(
        {
            f"{result.contest.name} - {result.contest_choice.name}": result.result
            for round_contest in round_contests.values()
            for result in round_contest.results
        }
    )

    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2})
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]

    # Check that we used the correct sample size (90% prob for Contest 2)
    # Should only have samples for Contest 2
    contest_2_ballots = SampledBallotDraw.query.filter_by(
        round_id=rounds[1]["id"], contest_id=contest_ids[1]
    ).count()
    snapshot.assert_match(contest_2_ballots)

    # Run the second round, auditing all the ballots for the second contest to complete the audit
    run_audit_round(rounds[1]["id"], contest_ids[1], contest_ids[1:], 0.7)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[1]["endedAt"] is not None
    assert rounds[1]["isAuditComplete"] is True

    # Make sure the votes got counted correctly
    round_contests = {
        round_contest.contest_id: round_contest
        for round_contest in RoundContest.query.filter_by(round_id=rounds[1]["id"])
        .order_by(RoundContest.created_at)
        .all()
    }
    # Since Contest 1 met its risk limit in round 1, it shouldn't be in round 2
    assert contest_ids[0] not in round_contests
    assert round_contests[contest_ids[1]].is_complete is True
    assert round_contests[contest_ids[2]].is_complete is False
    snapshot.assert_match(
        {
            f"{result.contest.name} - {result.contest_choice.name}": result.result
            for round_contest in round_contests.values()
            for result in round_contest.results
        }
    )

    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

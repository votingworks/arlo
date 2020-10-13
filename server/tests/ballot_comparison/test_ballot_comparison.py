import io
import json
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...bgcompute import bgcompute_update_standardized_contests_file
from ...api.sample_sizes import set_contest_metadata_from_cvrs


def test_set_contest_metadata_from_cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_id,
                "name": "Contest 2",
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            }
        ],
    )
    assert_ok(rv)

    contest = Contest.query.get(contest_id)
    assert contest.total_ballots_cast is None
    assert contest.votes_allowed is None
    assert contest.num_winners is None
    assert contest.choices == []

    set_contest_metadata_from_cvrs(contest)

    snapshot.assert_match(
        dict(
            total_ballots_cast=contest.total_ballots_cast,
            votes_allowed=contest.votes_allowed,
            num_winners=contest.num_winners,
            choices=[
                dict(name=choice.name, num_votes=choice.num_votes,)
                for choice in contest.choices
            ],
        )
    )


def test_ballot_comparison_two_rounds(
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

    bgcompute_update_standardized_contests_file()

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
                "jurisdictionIds": target_contest["jurisdictionIds"],
                "isTargeted": True,
            },
            {
                "id": str(uuid.uuid4()),
                "name": opportunistic_contest["name"],
                "jurisdictionIds": opportunistic_contest["jurisdictionIds"],
                "isTargeted": False,
            },
        ],
    )
    assert_ok(rv)

    # AA selects a sample size and launches the audit
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    target_contest_id = contests[0]["id"]

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    sample_size = sample_size_options[target_contest_id][0]
    snapshot.assert_match(sample_size)

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {target_contest_id: sample_size["size"]}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # JAs create audit boards
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    for jurisdiction_id in target_contest["jurisdictionIds"]:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/audit-board",
            [{"name": "Audit Board #1"}],
        )
        assert_ok(rv)

    # Audit boards audit all the ballots
    def audit_all_ballots(round_id: str, vote_ratio: float):
        round = Round.query.get(round_id)
        for contest_id in [target_contest_id, contests[1]["id"]]:
            contest = Contest.query.get(contest_id)
            ballot_draws = (
                SampledBallotDraw.query.filter_by(round_id=round.id)
                .join(SampledBallot)
                .join(Batch)
                .order_by(Batch.name, SampledBallot.ballot_position)
                .all()
            )
            winner_votes = int(vote_ratio * len(ballot_draws))
            # There are a few CVR rows that are empty for our targeted contest.
            # The audit boards shouldn't record an interpretation for those
            # ballots, since it means the contest wasn't on that ballot.
            has_contest = lambda draw: not (
                draw.sampled_ballot.batch.name == "2 - 2"
                and draw.sampled_ballot.ballot_position in [4, 5, 6]
            )
            draws_with_contest = [d for d in ballot_draws if has_contest(d)]
            draws_without_contest = [d for d in ballot_draws if not has_contest(d)]
            for ballot_draw in draws_with_contest[:winner_votes]:
                audit_ballot(
                    ballot_draw.sampled_ballot,
                    contest.id,
                    Interpretation.VOTE,
                    [contest.choices[0]],
                )
            for ballot_draw in draws_with_contest[winner_votes:]:
                audit_ballot(
                    ballot_draw.sampled_ballot,
                    contest.id,
                    Interpretation.VOTE,
                    [contest.choices[1]],
                )
            for ballot_draw in draws_without_contest:
                ballot_draw.sampled_ballot.status = BallotStatus.AUDITED

        end_round(round.election, round)
        db_session.commit()

    audit_all_ballots(round_1_id, 0.4)

    # Check the audit report
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

    # Start a second round
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    audit_all_ballots(round_2_id, 0.9)

    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

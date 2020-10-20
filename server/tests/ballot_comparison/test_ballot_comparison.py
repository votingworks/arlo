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

    # Check jurisdiction status after starting the round
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # JAs create audit boards
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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
    # second round.
    def audit_all_ballots(round_id: str, num_wrong: int):
        round = Round.query.get(round_id)
        for contest_id in [target_contest_id, contests[1]["id"]]:
            contest = Contest.query.get(contest_id)
            ballots_and_cvrs = (
                SampledBallot.query.join(SampledBallotDraw)
                .filter_by(round_id=round.id)
                .join(Batch)
                .join(
                    CvrBallot,
                    and_(
                        CvrBallot.batch_id == SampledBallot.batch_id,
                        CvrBallot.ballot_position == SampledBallot.ballot_position,
                    ),
                )
                .order_by(Batch.tabulator, Batch.name, SampledBallot.ballot_position)
                .with_entities(SampledBallot, CvrBallot)
                .all()
            )
            for i, (ballot, cvr) in enumerate(ballots_and_cvrs):
                choice_1_str, choice_2_str, *_ = cvr.interpretations.split(",")
                ballot.status = BallotStatus.AUDITED
                choice_1 = int(choice_1_str) if choice_1_str else None
                choice_2 = int(choice_2_str) if choice_2_str else None
                if not (choice_1 or choice_2) or i < num_wrong:
                    continue
                if not any(
                    i for i in ballot.interpretations if i.contest_id == contest_id
                ):
                    ballot.interpretations = list(ballot.interpretations) + [
                        BallotInterpretation(
                            ballot_id=ballot.id,
                            contest_id=contest.id,
                            interpretation=Interpretation.VOTE,
                            selected_choices=([contest.choices[0]] if choice_1 else [])
                            + ([contest.choices[1]] if choice_2 else []),
                            is_overvote=bool(choice_1 and choice_2),
                        )
                    ]

        end_round(round.election, round)
        db_session.commit()

    audit_all_ballots(round_1_id, 2)

    # Check the audit report
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

    # Start a second round
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    audit_all_ballots(round_2_id, 0)

    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

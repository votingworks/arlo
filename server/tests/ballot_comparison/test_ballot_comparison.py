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
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            }
        ],
    )
    assert_ok(rv)

    contest = Contest.query.get(contest_id)
    assert contest.total_ballots_cast is None
    assert contest.votes_allowed is None
    assert contest.choices == []

    set_contest_metadata_from_cvrs(contest)

    snapshot.assert_match(
        dict(
            total_ballots_cast=contest.total_ballots_cast,
            votes_allowed=contest.votes_allowed,
            choices=[
                dict(name=choice.name, num_votes=choice.num_votes,)
                for choice in contest.choices
            ],
        )
    )


def test_require_cvr_uploads(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # AA creates contests
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            },
        ],
    )
    assert_ok(rv)

    # AA tries to select a sample size - should get an error because CVRs have
    # to be uploaded first
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Some jurisdictions haven't uploaded their CVRs yet.",
            }
        ]
    }


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

    bgcompute_update_standardized_contests_file(election_id)

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
            {
                "id": str(uuid.uuid4()),
                "name": opportunistic_contest["name"],
                "numWinners": 1,
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
    opportunistic_contest_id = contests[1]["id"]

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
    audit_results = {
        ("J1", "TABULATOR1", "BATCH1", 1): "0,1,1,1,0",
        ("J1", "TABULATOR1", "BATCH2", 2): "0,1,1,1,0",
        ("J1", "TABULATOR1", "BATCH2", 3): "1,1,0,1,1",  # CVR: 1,0,1,0,1
        ("J1", "TABULATOR2", "BATCH2", 1): "1,0,1,0,1",
        ("J1", "TABULATOR2", "BATCH2", 2): "1,1,1,1,1",
        ("J1", "TABULATOR2", "BATCH2", 3): "blank",  # CVR: 1,0,1,0,1
        ("J2", "TABULATOR1", "BATCH1", 1): "0,1,1,1,0",
        ("J2", "TABULATOR1", "BATCH1", 2): "1,0,1,0,1",
        ("J2", "TABULATOR1", "BATCH1", 3): "0,1,1,1,0",
        ("J2", "TABULATOR1", "BATCH2", 1): "1,0,1,0,1",
        ("J2", "TABULATOR1", "BATCH2", 3): "not found",  # CVR: 1,0,1,0,1
        ("J2", "TABULATOR2", "BATCH1", 1): "0,1,1,1,0",
        ("J2", "TABULATOR2", "BATCH2", 1): ",,,,",  # CVR:1,0,1,0,1
        ("J2", "TABULATOR2", "BATCH2", 2): "1,1,1,1,1",
        ("J2", "TABULATOR2", "BATCH2", 3): "1,0,1,0,1",
    }

    def ballot_key(ballot: SampledBallot):
        return (
            ballot.batch.jurisdiction.name,
            ballot.batch.tabulator,
            ballot.batch.name,
            ballot.ballot_position,
        )

    choice_1_1, choice_1_2 = Contest.query.get(target_contest_id).choices
    choice_2_1, choice_2_2, choice_2_3 = Contest.query.get(
        opportunistic_contest_id
    ).choices

    def audit_all_ballots(round_id: str, audit_results):
        round = Round.query.get(round_id)
        sampled_ballots = (
            SampledBallot.query.filter_by(status=BallotStatus.NOT_AUDITED)
            .join(SampledBallotDraw)
            .filter_by(round_id=round.id)
            .join(Batch)
            .order_by(Batch.tabulator, Batch.name, SampledBallot.ballot_position)
            .all()
        )
        sampled_ballot_keys = [ballot_key(ballot) for ballot in sampled_ballots]

        # Ballots that don't have a result recorded for the targeted contest shouldn't be sampled
        ballots_without_targeted_contest = [
            ("J1", "TABULATOR2", "BATCH2", 4),
            ("J1", "TABULATOR2", "BATCH2", 5),
            ("J1", "TABULATOR2", "BATCH2", 6),
            ("J2", "TABULATOR2", "BATCH2", 4),
            ("J2", "TABULATOR2", "BATCH2", 5),
            ("J2", "TABULATOR2", "BATCH2", 6),
        ]
        for bad_ballot_key in ballots_without_targeted_contest:
            assert bad_ballot_key not in sampled_ballot_keys

        assert sorted(sampled_ballot_keys) == sorted(list(audit_results.keys()))

        for ballot in sampled_ballots:
            interpretation_str = audit_results[ballot_key(ballot)]

            if interpretation_str == "not found":
                ballot.status = BallotStatus.NOT_FOUND
                continue

            ballot.status = BallotStatus.AUDITED

            if interpretation_str == "blank":
                audit_ballot(ballot, target_contest_id, Interpretation.BLANK)
                audit_ballot(ballot, opportunistic_contest_id, Interpretation.BLANK)

            else:
                (
                    vote_choice_1_1,
                    vote_choice_1_2,
                    vote_choice_2_1,
                    vote_choice_2_2,
                    vote_choice_2_3,
                ) = interpretation_str.split(",")

                target_choices = ([choice_1_1] if vote_choice_1_1 == "1" else []) + (
                    [choice_1_2] if vote_choice_1_2 == "1" else []
                )
                audit_ballot(
                    ballot,
                    target_contest_id,
                    (
                        Interpretation.VOTE
                        if vote_choice_1_1 != ""
                        else Interpretation.CONTEST_NOT_ON_BALLOT
                    ),
                    target_choices,
                )

                opportunistic_choices = (
                    ([choice_2_1] if vote_choice_2_1 == "1" else [])
                    + ([choice_2_2] if vote_choice_2_2 == "1" else [])
                    + ([choice_2_3] if vote_choice_2_3 == "1" else [])
                )
                audit_ballot(
                    ballot,
                    opportunistic_contest_id,
                    (
                        Interpretation.VOTE
                        if vote_choice_2_1 != ""
                        else Interpretation.CONTEST_NOT_ON_BALLOT
                    ),
                    opportunistic_choices,
                )

        end_round(round.election, round)
        db_session.commit()

    audit_all_ballots(round_1_id, audit_results)

    # Check the audit report
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

    # Start a second round
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    # Sample sizes endpoint should still return round 1 sample size
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    assert sample_size_options[target_contest_id][0] == sample_size

    # For round 2, audit results should match the CVR exactly.
    audit_results = {
        ("J1", "TABULATOR1", "BATCH1", 2): "1,0,1,0,1",
        ("J1", "TABULATOR1", "BATCH2", 1): "1,0,1,0,1",
        ("J1", "TABULATOR2", "BATCH1", 2): "1,0,1,0,1",
        ("J2", "TABULATOR1", "BATCH2", 2): "0,1,1,1,0",
        ("J2", "TABULATOR2", "BATCH1", 2): "1,0,1,0,1",
        ("J2", "TABULATOR2", "BATCH1", 3): "1,0,1,1,0",
    }

    audit_all_ballots(round_2_id, audit_results)

    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)


# This function can be used to generate the correct audit results in case you
# need to update the above test case.
# def generate_audit_results(round_id: str):
#     ballots_and_cvrs = (
#         SampledBallot.query.filter_by(status=BallotStatus.NOT_AUDITED)
#         .join(SampledBallotDraw)
#         .filter_by(round_id=round_id)
#         .join(Batch)
#         .join(Jurisdiction)
#         .join(
#             CvrBallot,
#             and_(
#                 CvrBallot.batch_id == SampledBallot.batch_id,
#                 CvrBallot.ballot_position == SampledBallot.ballot_position,
#             ),
#         )
#         .order_by(
#             Jurisdiction.name,
#             Batch.tabulator,
#             Batch.name,
#             SampledBallot.ballot_position,
#         )
#         .with_entities(SampledBallot, CvrBallot)
#         .all()
#     )
#     def ballot_key(ballot: SampledBallot):
#         return (
#             ballot.batch.jurisdiction.name,
#             ballot.batch.tabulator,
#             ballot.batch.name,
#             ballot.ballot_position,
#         )
#     print({ballot_key(ballot): cvr.interpretations for ballot, cvr in ballots_and_cvrs})


def test_ballot_comparison_cvr_metadata(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # AA creates contests
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 2",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": False,
            },
        ],
    )
    assert_ok(rv)

    # AA selects a sample size and launches the audit
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    target_contest_id = contests[0]["id"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {target_contest_id: 20}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # JA creates audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"},],
    )
    assert_ok(rv)

    # Check that the CVR metadata is included in the ballot retrieval list
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots/retrieval-list"
    )
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    assert len(json.loads(rv.data)["ballots"]) == len(retrieval_list.splitlines()) - 1

    # Check that the CVR metadata is included with each ballot for audit boards
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board"
    )
    audit_board = json.loads(rv.data)["auditBoards"][0]

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board["id"])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board['id']}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    assert ballots[0]["batch"]["name"] == "BATCH1"
    assert ballots[0]["batch"]["tabulator"] == "TABULATOR1"
    assert ballots[0]["position"] == 1
    assert ballots[0]["imprintedId"] == "1-1-1"
    assert ballots[0]["contestsOnBallot"] == [contests[0]["id"], contests[1]["id"]]

    ballot_missing_contest = next(b for b in ballots if b["imprintedId"] == "2-2-4")
    assert ballot_missing_contest["contestsOnBallot"] == [contests[0]["id"]]

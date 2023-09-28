from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


def test_not_found_ballots(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
    snapshot,
):
    round = Round.query.get(round_1_id)
    targeted_contest = Contest.query.get(contest_ids[0])
    opportunistic_contest = Contest.query.get(contest_ids[1])

    # First, audit all ballots for the winner and see what the p-value is
    ballot_draws = (
        SampledBallotDraw.query.filter_by(round_id=round_1_id)
        .order_by(SampledBallotDraw.ticket_number)
        .all()
    )
    for i, draw in enumerate(ballot_draws):
        audit_ballot(
            draw.sampled_ballot,
            targeted_contest.id,
            Interpretation.VOTE,
            [targeted_contest.choices[0]],
        )
        audit_ballot(
            draw.sampled_ballot,
            opportunistic_contest.id,
            Interpretation.VOTE,
            [opportunistic_contest.choices[i % 2]],
        )

    audit_boards = AuditBoard.query.filter_by(round_id=round_1_id).all()
    for audit_board in audit_boards:
        audit_board.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    all_audited_p_values = dict(
        RoundContest.query.filter_by(round_id=round_1_id).values(
            RoundContest.contest_id, RoundContest.end_p_value
        )
    )

    round = Round.query.get(round_1_id)
    for round_contest in round.round_contests:
        round_contest.results = []

    # Next, try the same thing with some of the ballots marked not found
    num_not_found = 10
    ballot_draws = (
        SampledBallotDraw.query.filter_by(round_id=round_1_id)
        .order_by(SampledBallotDraw.ticket_number)
        .all()
    )
    for draw in ballot_draws[:num_not_found]:
        draw.sampled_ballot.status = BallotStatus.NOT_FOUND

    # End the round
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    not_found_p_values = dict(
        RoundContest.query.filter_by(round_id=round_1_id).values(
            RoundContest.contest_id, RoundContest.end_p_value
        )
    )

    # Not found ballots should be counted as votes for the losers, which should
    # increase the p-value
    targeted_contest = Contest.query.get(contest_ids[0])
    opportunistic_contest = Contest.query.get(contest_ids[1])
    assert (
        all_audited_p_values[targeted_contest.id]
        < not_found_p_values[targeted_contest.id]
    )
    assert (
        all_audited_p_values[opportunistic_contest.id]
        < not_found_p_values[opportunistic_contest.id]
    )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

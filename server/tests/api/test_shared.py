from ...models import Contest, ContestChoice
from ...api.shared import ballot_vote_deltas


def ess_contest(votes_allowed: int = 1) -> Contest:
    return Contest(
        id="contest",
        votes_allowed=votes_allowed,
        choices=[ContestChoice(id="a"), ContestChoice(id="b"), ContestChoice(id="c")],
    )


def test_ballot_vote_deltas_ess_overvote_confirmed():
    contest = ess_contest()
    reported = {"contest": {"a": "o", "b": "o", "c": "o"}}
    audited = {"contest": {"a": "1", "b": "1", "c": "0"}}
    assert ballot_vote_deltas(contest, reported, audited) is None


def test_ballot_vote_deltas_ess_overvote_not_confirmed():
    contest = ess_contest()
    reported = {"contest": {"a": "o", "b": "o", "c": "o"}}
    audited = {"contest": {"a": "1", "b": "0", "c": "0"}}
    assert ballot_vote_deltas(contest, reported, audited) == {"a": -1, "b": 0, "c": 0}


def test_ballot_vote_deltas_ess_overvote_vote_for_two():
    contest = ess_contest(votes_allowed=2)
    reported = {"contest": {"a": "o", "b": "o", "c": "o"}}
    assert (
        ballot_vote_deltas(
            contest, reported, {"contest": {"a": "1", "b": "1", "c": "1"}}
        )
        is None
    )
    assert ballot_vote_deltas(
        contest, reported, {"contest": {"a": "1", "b": "1", "c": "0"}}
    ) == {"a": -1, "b": -1, "c": 0}

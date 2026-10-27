from ...models import Contest, ContestChoice
from ...api.shared import ballot_vote_deltas


def ess_contest() -> Contest:
    return Contest(
        id="contest",
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

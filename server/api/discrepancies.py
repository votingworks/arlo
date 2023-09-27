from typing import Dict, Optional, Union

from ..audit_math import supersimple, macro
from ..models import *  # pylint: disable=wildcard-import,unused-wildcard-import


# { choice_id: vote delta }
ContestVoteDeltas = Dict[str, int]


def ballot_vote_deltas(
    contest: Contest,
    reported_cvr: Optional[supersimple.CVR],
    audited_cvr: Optional[supersimple.CVR],
) -> Optional[Union[str, ContestVoteDeltas]]:
    if audited_cvr is None:
        return "Ballot not found"
    if reported_cvr is None:
        return "Ballot not in CVR"

    reported = reported_cvr.get(contest.id)
    audited = audited_cvr.get(contest.id)

    if audited is None and reported is None:
        return None
    if audited is None:
        audited = {choice.id: "0" for choice in contest.choices}
    if reported is None:
        reported = {choice.id: "0" for choice in contest.choices}

    deltas = {}
    for choice in contest.choices:
        reported_vote = (
            0 if reported[choice.id] in ["o", "u"] else int(reported[choice.id])
        )
        audited_vote = (
            0 if audited[choice.id] in ["o", "u"] else int(audited[choice.id])
        )
        deltas[choice.id] = reported_vote - audited_vote

    if all(delta == 0 for delta in deltas.values()):
        return None

    return deltas


def batch_vote_deltas(
    reported_results: macro.ChoiceVotes, audited_results: macro.ChoiceVotes
) -> Optional[ContestVoteDeltas]:
    deltas = {
        choice_id: reported_results[choice_id] - audited_results[choice_id]
        for choice_id in reported_results.keys()
        if choice_id != "ballots"
    }

    if all(delta == 0 for delta in deltas.values()):
        return None

    return deltas

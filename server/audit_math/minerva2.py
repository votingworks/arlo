"""
Library for performing a Minerva2 / PROVIDENCE ballot polling risk-limiting audit,
as described by Broadrick et al https://arxiv.org/abs/2210.08717
"""
import logging
from typing import Dict, List, Tuple, Optional

from r2b2.minerva2 import Minerva2
from r2b2.contest import Contest as R2B2_Contest, ContestType

from .sampler_contest import Contest
from .ballot_polling_types import SampleSizeOption


# The AUDIT_CACHE is used to store in-progress minerva2 audits. By keeping track of
# audits, we can reduce the amount of work needed when functions like
# get_sample_size or compute_risk are called.
AUDIT_CACHE = dict()  # type: ignore


def get_from_audit_cache(
    sample_results: Dict[int, Dict[int, str]], round_sizes: Dict[int, int],
) -> Optional[Minerva2]:
    # TODO: Implement
    pass


def set_audit_cache(
    sample_results: Dict[int, Dict[int, str]], round_sizes: Dict[int, int],
):
    # TODO: Implement
    pass


def make_r2b2_contest(arlo_contest: Contest):
    """Make an R2B2 contest object from an Arlo contest

    >>> arlo = minerva.make_arlo_contest({"a": 500, "b": 200, "c": 50})
    >>> r2b2_contest = minerva2.make_r2b2_contest(arlo)
    >>> r2b2_contest
    Contest
    -------
    Contest Ballots: 750
    Reported Tallies:
        a               500
        b               200
        c               50
    Reported Winners: ['a']
    Contest Type: ContestType.PLURALITY
    >>> r2b2_contest.tally
    {'a': 500, 'b': 200, 'c': 50}
    """
    reported_winners = list(arlo_contest.winners.keys())
    return R2B2_Contest(
        arlo_contest.ballots,
        arlo_contest.candidates,
        arlo_contest.num_winners,
        reported_winners,
        ContestType.MAJORITY,
    )


def make_minerva2_audit(arlo_contest: Contest, alpha: float):
    """Make an R2B2 Audit object from an Arlo contest
    TODO: Fill this in
    """
    r2b2_contest = make_r2b2_contest(arlo_contest)
    return Minerva2(alpha, 1.0, r2b2_contest)


def _run_minerva2_audit(
    audit: Minerva2,
    sample_results: Dict[int, Dict[str, int]],
    round_sizes: Dict[int, int],
):
    """Take a Minerva2 audit and run the sample results on it."""
    if round_sizes is not None:
        # dicts are sorted since Python 3.7 so this should be chill beans
        for round, size in round_sizes.items():
            logging.debug(f"round: {round}")
            mapping = sample_results[round]
            audit.execute_round(size, mapping)
            logging.debug(audit)


# TODO: sample_results uses str to index and round_sizes uses int. Unify these two.
def get_sample_size(
    risk_limit: int,
    contest: Contest,
    sample_results: Dict[int, Dict[str, int]],
    round_sizes: Dict[int, int],
    quants: List[float] = None,
) -> Dict[str, SampleSizeOption]:
    """
    Computes sample size for the next round, parameterized by likelihood that the
    sample will confirm the election result, assuming accurate results.

    Inputs:
        risk_limit:     maximum risk as an integer percentage
        contest:        a sampler_contest object of the contest being audited
        sample_results: map round ids to mapping of candidates to incremental votes
        round_sizes:    map round ids to incremental round sizes

    Outputs:
        samples:        dictionary mapping confirmation likelihood to next sample size
    """
    # Problem: r2b2's design assumes that the Minerva2 audit object is control of the entire
    # audit. The interface doesn't seem to easily allow us to just drop in halfway through,
    # passing in the previous results and round sizes.

    # Generally, there should only be one audit happening at once, right?
    # I could store the results in a db, store it in a global variable?
    if quants is None:
        quants = [0.9]
    alpha = risk_limit / 100
    audit = make_minerva2_audit(contest, alpha)

    if round_sizes is not None:
        _run_minerva2_audit(audit, sample_results, round_sizes)
    return {
        str(quant): {
            "type": None,
            "size": audit.next_sample_size(sprob=quant),
            "prob": quant,
        }
        for quant in quants
    }


def compute_risk(
    risk_limit: int,
    contest: Contest,
    sample_results: Dict[int, Dict[str, int]],
    round_sizes: Dict[int, int],
) -> Tuple[Dict[Tuple[str, str], float], bool]:
    """
    Computes the risk-value of <sample_results> based on results in <contest>.

    Computes sample size for the next round, parameterized by likelihood that the
    sample will confirm the election result, assuming accurate results.

    Inputs:
        risk_limit:     maximum risk as an integer percentage
        contest:        a sampler_contest object of the contest being measured
        sample_results: map round ids to mapping of candidates to incremental votes
        round_sizes:    map round ids to incremental round sizes

    Outputs:
        samples:        dictionary mapping confirmation likelihood to next sample size

    Outputs:
        measurements:   the p-value of the hypotheses that the election
                        result is correct based on the sample
        confirmed:      a boolean indicating whether the audit can stop
    """
    alpha = risk_limit / 100
    if alpha <= 0 or alpha >= 1:
        raise ValueError("The risk-limit must be greater than zero and less than 100!")

    audit = make_minerva2_audit(contest, alpha)

    if round_sizes is not None:
        _run_minerva2_audit(audit, sample_results, round_sizes)

    # FIXME: for now we're returning only the max p_value for the deciding pair,
    # since other audits only return a single p_value,
    # and rounds.py throws it out right away p_value = max(p_values.values())
    risk = audit.get_risk_level()
    return {("winner", "loser"): risk}, risk <= alpha

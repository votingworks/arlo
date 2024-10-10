"""
Library for performing a Providence ballot polling risk-limiting audit,
as described by Broadrick et al https://arxiv.org/abs/2210.08717
"""

from collections import defaultdict
import logging
from typing import Dict, Optional, Tuple

from r2b2.minerva2 import Minerva2 as Providence
from r2b2.contest import Contest as R2B2_Contest, ContestType

from .sampler_contest import Contest
from .ballot_polling_types import (
    SampleSizeOption,
    BALLOT_POLLING_ROUND_SIZES,
    BALLOT_POLLING_SAMPLE_RESULTS,
)

logger = logging.getLogger("arlo.audit_math.providence")


def make_r2b2_contest(arlo_contest: Contest):
    """Make an R2B2 contest object from an Arlo contest

    >>> arlo = Contest("contest", {"a": 500, "b": 200, "c": 50, "ballots": 750, "numWinners": 1, "votesAllowed": 1})
    >>> r2b2_contest = make_r2b2_contest(arlo)
    >>> r2b2_contest
    Contest: [750, {'a': 500, 'b': 200, 'c': 50}, 1, ['a'], <ContestType.MAJORITY: 1>]
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


def make_providence_audit(arlo_contest: Contest, alpha: float):
    """Make an R2B2 Providence Audit object from an Arlo contest.
    This audit object will run the providence audit.
    """
    r2b2_contest = make_r2b2_contest(arlo_contest)
    return Providence(alpha, 1.0, r2b2_contest)


def _run_providence_audit(
    audit: Providence,
    sample_results: Optional[BALLOT_POLLING_SAMPLE_RESULTS],
    round_sizes: Optional[BALLOT_POLLING_ROUND_SIZES],
):
    """Take a Providence audit and run the sample results on it.
    The audit object passed in is modified, this function doesn't return anything.

    Inputs:
        audit:          Providence audit object
        sample_results: map round ids to mapping of candidates to incremental votes
        round_sizes:    map round nums to tuples of round ids and incremental round sizes
    """
    if round_sizes is not None and sample_results:
        # Note: we need the key to sort the dict, even though we don't use
        # it in the loop explicitly.
        logger.debug("running sample_results on audit object")
        logger.debug(f"sample_results: {sample_results}")
        logger.debug(f"round_sizes: {round_sizes}")
        logger.debug(audit)
        # r2b2's audit object expects the votes each candidate receives to be cumulative
        mapping: Dict[str, int] = defaultdict(int)
        size = 0
        for _, round_info in sorted(round_sizes.items()):
            round_id = round_info.round_id
            size += round_info.round_size
            round_vote_mapping = sample_results[round_id]
            for k, v in round_vote_mapping.items():
                mapping[k] += v
            audit.execute_round(size, mapping)
            logging.debug(audit)


def get_sample_size(
    risk_limit: int,
    contest: Contest,
    sample_results: Optional[BALLOT_POLLING_SAMPLE_RESULTS],
    round_sizes: Optional[BALLOT_POLLING_ROUND_SIZES],
) -> Dict[str, SampleSizeOption]:
    """
    Computes sample size for the next round, parameterized by likelihood that the
    sample will confirm the election result, assuming accurate results.

    Inputs:
        risk_limit:     maximum risk as an integer percentage
        contest:        a sampler_contest object of the contest being audited
        sample_results: map round ids to mapping of candidates to incremental votes
        round_sizes:    map round nums to tuples of round ids and incremental round sizes

    Outputs:
        samples:        dictionary mapping confirmation likelihood to next sample size
    """
    quants = [0.7, 0.8, 0.9]
    alpha = risk_limit / 100
    audit = make_providence_audit(contest, alpha)

    if round_sizes:
        _run_providence_audit(audit, sample_results, round_sizes)
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
    sample_results: BALLOT_POLLING_SAMPLE_RESULTS,
    round_sizes: BALLOT_POLLING_ROUND_SIZES,
) -> Tuple[Dict[Tuple[str, str], float], bool]:
    """
    Computes the risk-value of <sample_results> based on results in <contest>.

    Computes sample size for the next round, parameterized by likelihood that the
    sample will confirm the election result, assuming accurate results.

    Inputs:
        risk_limit:     maximum risk as an integer percentage
        contest:        a sampler_contest object of the contest being measured
        sample_results: map round ids to mapping of candidates to incremental votes
        round_sizes:    map round nums to tuples of round ids and incremental round sizes

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

    audit = make_providence_audit(contest, alpha)

    _run_providence_audit(audit, sample_results, round_sizes)

    # FIXME: for now we're returning only the max p_value for the deciding pair,
    # since other audits only return a single p_value,
    # and rounds.py throws it out right away p_value = max(p_values.values())
    risk = audit.get_risk_level()
    return {("winner", "loser"): risk}, risk <= alpha

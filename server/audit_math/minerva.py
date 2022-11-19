# pylint: disable=invalid-name
"""
Library for performing a Minerva-style ballot polling risk-limiting audit,
as described by Zagórski et al https://arxiv.org/abs/2008.02315

Note that this library works for one contest at a time, as if each contest being
targeted is being audited completely independently.

TODO: ensure the no-losers case is handled
TODO: if necessary pull out risks for individual contests

"""
import logging
import math
from typing import List, Dict, Tuple, Optional

from athena.audit import Audit as AthenaAudit  # type: ignore
from .sampler_contest import Contest
from ..config import MINERVA_MULTIPLE


def make_arlo_contest(tally, num_winners=1, votes_allowed=1):
    """Return an Arlo Contest with the given tally (a dictionary of candidate_name:vote_counts)
    Treat "_undervote_" candidate as undervotes
    For testing purposes.
    """

    ballots = sum(tally.values())
    votes = {key: tally[key] for key in tally if key != "_undervote_"}
    return Contest(
        "c1",
        {
            "ballots": ballots,
            "numWinners": num_winners,
            "votesAllowed": votes_allowed,
            **votes,
        },
    )


def make_sample_results(
    contest: Contest, votes_per_round: List[List]
) -> Dict[str, Dict[str, int]]:
    """Make up sample_results for testing given Arlo contest based on votes.
    Note that athena's API relies on Python requiring dictionaries (of candidates and sample results)
    to be ordered since 3.7.
    """

    sample_results = {}
    for i, votes in enumerate(votes_per_round):
        sample_results[f"r{i}"] = dict(zip(contest.candidates, votes))

    return sample_results

def fix_landslide_arlo_contest(contest: Contest, alpha: int) -> Contest:
    """Add one vote to all candidates who received zero votes

    Athena's wald_k_min throws a ValueError if it finds a margin between candidates of 0 or 1.
    By ensuring all candidates have 1 vote, we can calculate first round sizes between candidates.
    If the margin is already a landslide, the difference of one vote shouldn't significantly
    affect the number of rounds needed to verify the winner.

    Warning will be generated if the round size is *increased* by the small size of the contest.
    Round size will never decrease because of a small contest, only increase.
    """
    new_candidate_dict = dict(contest.candidates)
    num_votes = sum(new_candidate_dict.values())

    # Experimentally found by calculating first round sizes for a variety of risks and landslide total votes and graphing
    # the point at which too few total votes grew the round sizes.
    # The relationship seems to be: when the risk factor is cut in half, minimum votes required goes up by 5
    risky_amount = math.ceil((3 + math.log(20, 2) - math.log(alpha, 2)) * 5)
    if num_votes <= risky_amount:
        logging.warning("Landslide contests with few total votes may produce larger first round sizes than expected")
        logging.warning(f"Landslide contest with {num_votes} total votes is being run.")
    for key, val in contest.margins["losers"].items():
        if val['s_l'] == 0:
            logging.debug(f"landslide margin detected, fixing candidate {key} from 0 to 1")
            new_candidate_dict[key] += 1
    return make_arlo_contest(new_candidate_dict)

def make_athena_audit(arlo_contest, alpha):
    """Make an Athena audit object, with associated contest and election, from an Arlo contest

    >>> c3 = make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    >>> audit = make_athena_audit(c3, 0.1)
    >>> audit.election.contests
    {'c1': {"contest_ballots": 0, "num_winners": 1, "reported_winners": ['a'], "contest_type": "PLURALITY", "tally": {'a': 600, 'b': 400, 'c': 100}, "declared_winners": [0], "declared_losers": [1, 2]}}
    >>> audit.alpha
    0.1
    """

    athena_contest = {
        "contest_ballots": arlo_contest.ballots,
        "tally": arlo_contest.candidates,
        "num_winners": arlo_contest.num_winners,
        "reported_winners": list(arlo_contest.margins["winners"].keys()),
        "contest_type": "PLURALITY",
    }

    contest_name = arlo_contest.name
    election = {
        "name": "ArloElection",
        "total_ballots": arlo_contest.ballots,
        "contests": {contest_name: athena_contest},
    }

    audit = AthenaAudit("minerva", alpha)
    audit.add_election(election)
    audit.load_contest(contest_name)

    return audit


def get_sample_size(
    risk_limit: int,
    contest: Contest,
    sample_results: Optional[Dict[str, Dict[str, int]]],
    round_sizes: Dict[int, int],
) -> Dict[str, "SampleSizeOption"]:  # type: ignore
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

    >>> c3 = make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    >>> get_sample_size(10, c3, None, [])
    {'0.7': {'type': None, 'size': 134, 'prob': 0.7}, '0.8': {'type': None, 'size': 166, 'prob': 0.8}, '0.9': {'type': None, 'size': 215, 'prob': 0.9}}
    >>> get_sample_size(20, c3, None, [])
    {'0.7': {'type': None, 'size': 87, 'prob': 0.7}, '0.8': {'type': None, 'size': 110, 'prob': 0.8}, '0.9': {'type': None, 'size': 156, 'prob': 0.9}}
    >>> get_sample_size(10, c3, make_sample_results(c3, [[55, 40, 3]]), {1: 100})
    {'0.9': {'type': None, 'size': 225, 'prob': 0.9}}
    """

    if sample_results is not None:
        # Construct round schedule as a function of only first round size.
        # and other information set at the start of the audit.

        # Minerva is not designed to be this formulaic in its round sizes,
        # but while we work on rigorously demonstrating that round sizes can be chosen freely
        # leveraging information on sample results in previous rounds, we offer this
        # approach which simply defines all round sizes uniformly based on the first
        # round size.

        first_round_size = round_sizes[1]
        prev_round_count = len(round_sizes)
        round_num = prev_round_count + 1

        # Get the ith round by multiplying the first round size
        next_round_size = int(first_round_size * MINERVA_MULTIPLE ** round_num)
        logging.debug(f"{round_sizes=}, {next_round_size=}")
        return {"0.9": {"type": None, "size": next_round_size, "prob": 0.9}}

    alpha = risk_limit / 100

    quants = [0.7, 0.8, 0.9]

    # If we're in a single-candidate race, set sample to -1
    if not contest.margins["losers"]:
        round_size_options = [-1 for quant in quants]
    else:
        try:
            # Check for a landslide condition.
            if max(val['s_l'] for val in contest.margins["losers"].values()) == 0:
                contest = fix_landslide_arlo_contest(contest, alpha)
            audit = make_athena_audit(contest, alpha)
            round_size_options = audit.find_next_round_size(quants)[
                "future_round_sizes"
            ]
        except ValueError as e:
            if str(e) == "Incorrect reported winners":
                # Tied election
                round_size_options = [contest.ballots for quant in quants]

    return {
        str(quant): {"type": None, "size": size, "prob": quant}
        for quant, size in zip(quants, round_size_options)
    }


def collect_risks(
    alpha: float,
    arlo_contest: Contest,
    round_schedule: List[int],
    sample_results: Dict[str, Dict[str, int]],
) -> Dict[Tuple[str, str], float]:
    """
    Collect risk levels for each pair of candidates.

    Inputs:
        alpha:           risk limit
        margins:         the margins for the contest being audited
        round_schedule:  the sizes of each round
        sample_results:  mapping of candidates to votes in each round

    Outputs:
        risks - Mapping of (winner, loser) pairs to their risk levels
    """

    logging.debug(
        f"minerva collect_risks {alpha=}, {arlo_contest=}, {round_schedule=}, {sample_results=})"
    )

    audit = make_athena_audit(arlo_contest, alpha)

    for round_size, sample in zip(round_schedule, sample_results.values()):
        obs = list(sample.values())
        # if round_size != sum(obs):
        #    raise ValueError(f"{round_size=} not equal to sum({obs=})")
        audit.set_observations(round_size, sum(obs), obs)

        # Check for the audit being over, otherwise athena will throw an error
        if audit.status[audit.active_contest].risks[-1] < alpha:
            break
        logging.debug(
            f"minerva  collect_risks: {audit.status[audit.active_contest].risks[-1]=}"
        )

    # FIXME: for now we're returning only the max p_value for the deciding pair,
    # since other audits only return a single p_value,
    # and rounds.py throws it out right away p_value = max(p_values.values())

    risks = {
        ("winner", "loser"): min(audit.status[audit.active_contest].risks[-1], 1.0)
    }
    logging.debug(f"minerva  collect_risks return: {risks=}")

    return risks


def compute_risk(
    risk_limit: int,
    contest: Contest,
    sample_results: Dict[str, Dict[str, int]],
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
    assert (
        0.0 < alpha < 1.0
    ), "The risk-limit must be greater than zero and less than one!"

    prev_round_schedule = [value for key, value in sorted(round_sizes.items())]
    logging.debug(f"{round_sizes=}, {prev_round_schedule=}")

    risks = collect_risks(alpha, contest, prev_round_schedule, sample_results)
    finished = all(risk <= alpha for risk in risks.values())
    return risks, finished

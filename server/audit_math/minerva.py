# pylint: disable=invalid-name
"""
Library for performing a Minerva-style ballot polling risk-limiting audit,
as described by Zagórski et al https://arxiv.org/abs/2008.02315

Note that this library works for one contest at a time, as if each contest being
targeted is being audited completely independently.

TODO: ensure the no-losers case is handled
TODO: if necessary pull out risks for individual contests

"""
from decimal import Decimal
from typing import List, Dict, Tuple, Optional

from athena.audit import Audit  # type: ignore
from .sampler_contest import Contest
from .shim import minerva_sample_sizes  # type: ignore

# FIXME: make this an environmental variable
MINERVA_MULTIPLE = 1.5


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


def minerva_round_size(first_round_size, round_num):
    """Return size of ith round based on first round size and round number
    """

    return int(first_round_size * MINERVA_MULTIPLE ** round_num)


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

    audit = Audit("minerva", alpha)
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
    Computes initial sample size parameterized by likelihood that the
    initial sample will confirm the election result, assuming no
    discrepancies.

    Inputs:
        risk_limit     - the risk-limit for this audit
        contest        - a sampler_contest object of the contest being audited
        sample_results - mapping of candidates to votes in the (cumulative)
                         sample:
                        {
                            candidate1: sampled_votes,
                            candidate2: sampled_votes,
                            ...
                        }

    Outputs:
        samples - dictionary mapping confirmation likelihood to sample size:
                {
                    likelihood1: sample_size,
                    likelihood2: sample_size,
                    ...
                }
    FIXME: add round size arguments and update tests

    >>> c3 = make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    >>> get_sample_size(10, c3, None, [])
    {'0.7': {'type': None, 'size': 134, 'prob': 0.7}, '0.8': {'type': None, 'size': 166, 'prob': 0.8}, '0.9': {'type': None, 'size': 215, 'prob': 0.9}}

    >>> get_sample_size(20, c3, None, [])
    {'0.7': {'type': None, 'size': 87, 'prob': 0.7}, '0.8': {'type': None, 'size': 110, 'prob': 0.8}, '0.9': {'type': None, 'size': 156, 'prob': 0.9}}

    One less than the kmin
    >>> get_sample_size(10, c3, make_sample_results(c3, [[56, 40, 3]]), {1: 100})
    {'0.9': {'type': None, 'size': 150, 'prob': 0.9}}
    """

    # from ..api.rounds import contest_results_by_round

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
        next_round_size = minerva_round_size(first_round_size, prev_round_count)
        return {"0.9": {"type": None, "size": next_round_size, "prob": 0.9}}

    alpha = Decimal(risk_limit) / 100
    assert alpha < 1, "The risk-limit must be less than one!"

    quants = [0.7, 0.8, 0.9]

    samples: Dict = {}

    p_w = Decimal("inf")
    p_l = Decimal(-1)

    margin = contest.margins
    # Get smallest p_w - p_l
    for winner in margin["winners"]:
        if margin["winners"][winner]["p_w"] < p_w:
            p_w = Decimal(margin["winners"][winner]["p_w"])

    for loser in margin["losers"]:
        if margin["losers"][loser]["p_l"] > p_l:
            p_l = Decimal(margin["losers"][loser]["p_l"])

    # If we're in a single-candidate race, set sample to 0
    if not margin["losers"]:
        for quant in quants:
            samples[str(quant)] = {"type": None, "size": -1.0, "prob": quant}

        return samples

    num_ballots = contest.ballots

    # Handles ties
    if p_w == p_l:
        for quant in quants:
            samples[str(quant)] = {"type": None, "size": num_ballots, "prob": quant}

        return samples

    # Handle landslides.   TODO: remove this case if fixed upstream
    if p_w == 1.0:
        samples["asn"] = {
            "type": "ASN",
            "size": 4,
            "prob": 1.0,
        }

        return samples

    # If we haven't returned yet, actually do the math for the first round
    for quant in quants:
        size = minerva_sample_sizes(alpha, p_w, p_l, 0, 0, quant)
        samples[str(quant)] = {"type": None, "size": size, "prob": quant}

    return samples


def collect_risks(
    alpha: float,
    arlo_contest: Contest,
    round_schedule: List[int],
    sample_results: Dict[str, Dict[str, int]],
) -> Dict[Tuple[str, str], float]:
    """
    Collect risk levels for each pair of candidates.

    Inputs:
        alpha          - risk limit
        margins        - the margins for the contest being audited
        round_schedule - the sizes of each round
        sample_results - mapping of candidates to votes in each round

    Outputs:
        risks - Mapping of (winner, loser) pairs to their risk levels

    >>> c3 = make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    >>> collect_risks(0.1, c3, [120], make_sample_results(c3, [[56, 40, 3]]))
    {('winner', 'loser'): 0.0933945799801079}
    >>> collect_risks(0.1, c3, [83], make_sample_results(c3, [[40, 40, 3]]))
    {('winner', 'loser'): 0.5596434615209632}
    >>> collect_risks(0.1, c3, [83, 200], make_sample_results(c3, [[40, 40, 3], [70, 30, 10]]))
    {('winner', 'loser'): 0.00638203150599862}

    # TODO: Make better test here of third-candidate surge, after not being eliminated earlier
    #>>> collect_risks(0.1, c3, [83, 200], make_sample_results(c3, [[40, 40, 3], [70, 30, 90]]))
    #surely not {('winner', 'loser'): 0.00638203150599862}
    >>> collect_risks(0.1, c3, [82], make_sample_results(c3, [[40, 40, 3]]))
    Traceback (most recent call last):
    ValueError: Incorrect number of valid ballots entered
    """

    audit = make_athena_audit(arlo_contest, alpha)
    for round_size, sample in zip(round_schedule, sample_results.values()):
        obs = list(sample.values())
        # if round_size != sum(obs):
        #    raise ValueError(f"{round_size=} not equal to sum({obs=})")
        audit.set_observations(round_size, sum(obs), obs)

        # TODO: check for the audit being over, after which it will throw an error

    # FIXME: for now we're returning only the max p_value for the deciding pair,
    # since other audits only return a single p_value,
    # and rounds.py throws it out right away p_value = max(p_values.values())

    risks = {("winner", "loser"): audit.status[audit.active_contest].risks[-1]}

    return risks


def compute_risk(
    risk_limit: int,
    contest: Contest,
    sample_results: Dict[str, Dict[str, int]],
    round_sizes: Dict[int, int],
) -> Tuple[Dict[Tuple[str, str], float], bool]:
    """
    Computes the risk-value of <sample_results> based on results in <contest>.

    Inputs:
        risk_limit     - the risk-limit for this audit - integer percentage
        contest        - a sampler_contest object for the contest being measured
        sample_results - mapping of candidates to votes in the sample:
                { "round": {
                    candidate1: sampled_votes,
                    candidate2: sampled_votes,
                    ...
                }}

    Outputs:
        measurements    - the p-value of the hypotheses that the election
                          result is correct based on the sample, for each
                          winner-loser pair.
        confirmed       - a boolean indicating whether the audit can stop

    >>> c3 = make_arlo_contest({"a": 600, "b": 400, "c": 100, "_undervote_": 100})
    >>> compute_risk(10, c3, make_sample_results(c3, [[56, 40, 3]]), {1: 100, 2: 150})
    ({('winner', 'loser'): 0.0933945799801079}, True)
    >>> compute_risk(10, c3, make_sample_results(c3, [[40, 40, 3]]), {1: 100, 2: 150})
    ({('winner', 'loser'): 0.5596434615209632}, False)
    >>> compute_risk(10, c3, make_sample_results(c3, [[40, 40, 3], [70, 30, 10]]), {1: 100, 2: 150, 3: 150})
    ({('winner', 'loser'): 0.00638203150599862}, True)
    """

    alpha = risk_limit / 100
    assert (
        0.0 < alpha < 1.0
    ), "The risk-limit must be greater than zero and less than one!"

    prev_round_schedule = [value for key, value in sorted(round_sizes.items())]

    risks = collect_risks(alpha, contest, prev_round_schedule, sample_results)
    finished = all(risk <= alpha for risk in risks.values())
    return risks, finished

"""
An implemenation of per-contest batch comparison audits, loosely based on MACRO. 
Since MACRO applies to all contests being audited (hence across-contest), this
code acts as if each contest is independently audited according it its maximum
relative overstatement (as if we did MACRO only one one contest).

MACRO was developed by Philip Stark
(see https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1443314 for the publication).
"""
import math
from .sampler_contest import Contest

from typing import Any, Dict, List, Tuple


def compute_error(
    batch_results: Dict[str, Dict[str, int]],
    contest: Contest,
    sampled_results: Dict[str, Dict[str, int]],
) -> float:
    """
    Computes the error in this batch

    Inputs:
        batch_results   - the reported votes in this batch
                          {
                              'contest': {
                                  'cand1': votes,
                                  'cand2': votes,
                                  ...
                              },
                              ...
                          }
        contest         - a sampler_contest object of the contest to compute 
                          the error for
        sampled_results - the actual votes in this batch after auditing, of the
                          same form as batch_results

    Outputs:
        the maximum across-contest relative overstatement for batch p
    """

    error = 0.0
    margins = contest.margins
    for winner in margins["winners"]:
        for loser in margins["losers"]:
            v_wp = batch_results[contest.name][winner]
            v_lp = batch_results[contest.name][loser]

            a_wp = sampled_results[contest.name][winner]
            a_lp = sampled_results[contest.name][loser]

            V_wl = contest.candidates[winner] - contest.candidates[loser]

            e_pwl = ((v_wp - v_lp) - (a_wp - a_lp)) / V_wl

            if e_pwl > error:
                error = e_pwl

    return error


def compute_max_error(
    batch_results: Dict[str, Dict[str, int]], contest: Contest
) -> float:
    """
    Computes the maximum possible error in this batch for this contest

    Inputs:
        batch_results   - the reported votes in this batch
                          {
                              'contest': {
                                  'cand1': votes,
                                  'cand2': votes,
                                  ...
                              },
                              ...
                          }
        contest         - a sampler_contest object of the contest to compute 
                          the error for

    Outputs:
        the maximum possible overstatement for batch p
    """

    error = 0.0

    # We only care about error in targeted contests
    if contest.name not in batch_results:
        return 0.0

    margins = contest.margins
    for winner in margins["winners"]:
        for loser in margins["losers"]:
            v_wp = batch_results[contest.name][winner]
            v_lp = batch_results[contest.name][loser]

            b_cp = batch_results[contest.name]["ballots"]

            V_wl = contest.candidates[winner] - contest.candidates[loser]

            u_pwl = ((v_wp - v_lp) + b_cp) / V_wl

            if u_pwl > error:
                error = u_pwl

    return error


def compute_U(
    reported_results: Dict[str, Dict[str, Dict[str, int]]], contest: Contest
) -> float:
    """
    Computes U, the sum of the batch-wise relative overstatement limits,
    i.e. the maximum amount of possible overstatement in a given election.
    Inputs:
        reported_results - the reported votes in every batch
                           { 
                               'batch': {
                                 'contest': {
                                     'cand1': votes,
                                     'cand2': votes,
                                     ...
                                 },
                                 ...
                               }
                               ...
                           }
        contest         - a sampler_contest object of the contest to compute 
                          the error for

    Outputs:
        U - the sum of the maximum possible overstatement for each batch
    """
    U = 0.0
    for batch in reported_results:
        U += compute_max_error(reported_results[batch], contest)

    return U


def get_sample_sizes(
    risk_limit: float,
    contest: Contest,
    reported_results: Dict[str, Dict[str, Dict[str, int]]],
    sample_results: Dict[str, Dict[str, Dict[str, int]]],
) -> float:
    """
    Computes initial sample sizes parameterized by likelihood that the
    initial sample will confirm the election result, assuming no
    discrepancies.

    Inputs:
        risk_limit       - the risk-limit for this audit
        contest          - a sampler_contest object of the contest to compute 
                           the error for
        reported_results - the reported votes in every batch
                           { 
                               'batch': {
                                 'contest': {
                                     'cand1': votes,
                                     'cand2': votes,
                                     ...
                                 },
                                 ...
                               }
                               ...
                           }
        sample_results - if a sample has already been drawn, this will
                         contain its results, of the same form as 
                         reported_results

    Outputs:
        samples - dictionary mapping confirmation likelihood to sample size:
                {
                   contest1:  {
                        likelihood1: sample_size,
                        likelihood2: sample_size,
                        ...
                    },
                    ...
                }
    """
    assert risk_limit < 1, "The risk-limit must be less than one!"

    # TODO: actually use past batch results

    U = compute_U(reported_results, contest)

    return math.ceil(math.log(risk_limit) / (math.log(1 - (1 / U))))


def compute_risk(
    risk_limit: float,
    contest: Contest,
    reported_results: Dict[str, Dict[str, Dict[str, int]]],
    sample_results: Dict[str, Dict[str, Dict[str, int]]],
) -> Tuple[float, bool]:
    """
    Computes the risk-value of <sample_results> based on results in <contest>.

    Inputs:
        risk_limit       - the risk-limit for this audit
        contest          - a sampler_contest object of the contest to compute 
                           the error for
        reported_results - the reported votes in every batch
                           { 
                               'batch': {
                                 'contest': {
                                     'cand1': votes,
                                     'cand2': votes,
                                     ...
                                 },
                                 ...
                               }
                               ...
                           }
        sample_results - if a sample has already been drawn, this will
                         contain its results, of the same form as 
                         reported_results
    Outputs:
        measurements    - the p-value of the hypotheses that the election
                          result is correct based on the sample for each 
                          winner-loser pair.
        confirmed       - a boolean indicating whether the audit can stop
    """
    assert risk_limit < 1, "The risk-limit must be less than one!"

    p = 1.0

    U = compute_U(reported_results, contest)

    for batch in sample_results:
        e_p = compute_error(reported_results[batch], contest, sample_results[batch])

        u_p = compute_max_error(reported_results[batch], contest)

        taint = e_p / u_p

        p *= (1 - 1 / U) / (1 - taint)

        if p < risk_limit:
            return p, True

    return p, p < risk_limit

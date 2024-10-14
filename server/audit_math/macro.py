# pylint: disable=invalid-name
"""
An implemenation of per-contest batch comparison audits, loosely based on
MACRO. Since MACRO applies to all contests being audited (hence
across-contest), this code acts as if each contest is independently audited
according it its maximum relative overstatement (as if we did MACRO only one
one contest).

MACRO was developed by Philip Stark (see
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1443314 for the
publication).
"""
from decimal import Decimal, ROUND_CEILING
from typing import Dict, Tuple, TypeVar, TypedDict, Optional, List, cast
from .sampler_contest import Contest

BatchKey = TypeVar("BatchKey")
# { choice_id: num_votes }
ChoiceVotes = Dict[str, int]
# { contest_id: ChoiceVotes }
BatchResults = Dict[str, ChoiceVotes]


class BatchError(TypedDict):
    counted_as: int
    weighted_error: Decimal


def compute_error(
    batch_results: BatchResults,
    sampled_results: BatchResults,
    contest: Contest,
) -> Optional[BatchError]:
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

    if contest.name not in batch_results:
        return None

    def error_for_candidate_pair(winner, loser) -> Optional[BatchError]:
        v_wp = batch_results[contest.name][winner]
        v_lp = batch_results[contest.name][loser]

        a_wp = sampled_results[contest.name][winner]
        a_lp = sampled_results[contest.name][loser]

        V_wl = contest.candidates[winner] - contest.candidates[loser]
        error = (v_wp - v_lp) - (a_wp - a_lp)
        if error == 0:
            return None

        weighted_error = Decimal(error) / Decimal(V_wl) if V_wl > 0 else Decimal("inf")
        return BatchError(counted_as=error, weighted_error=weighted_error)

    maybe_errors = [
        error_for_candidate_pair(winner, loser)
        for winner in contest.margins["winners"]
        for loser in contest.margins["losers"]
    ]
    errors: List[BatchError] = [error for error in maybe_errors if error is not None]
    if len(errors) == 0:
        return None
    return max(errors, key=lambda error: error["weighted_error"])


def compute_max_error(batch_results: BatchResults, contest: Contest) -> Decimal:
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

    error = Decimal(0.0)

    # We only care about error in targeted contests
    if contest.name not in batch_results:
        return Decimal(0.0)

    margins = contest.margins
    for winner in margins["winners"]:
        for loser in margins["losers"]:
            v_wp = batch_results[contest.name][winner]
            v_lp = batch_results[contest.name][loser]

            b_cp = batch_results[contest.name]["ballots"]

            V_wl = contest.candidates[winner] - contest.candidates[loser]

            if V_wl == 0:
                return Decimal("inf")

            u_pwl = Decimal((v_wp - v_lp) + b_cp) / Decimal(V_wl)

            if u_pwl > error:
                error = u_pwl

    return error


def compute_U(
    reported_results: Dict[BatchKey, BatchResults],
    sample_results: Dict[BatchKey, BatchResults],
    contest: Contest,
) -> Decimal:
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
    U = Decimal(0.0)
    for batch in reported_results:
        if batch in sample_results:
            error = compute_error(
                reported_results[batch], sample_results[batch], contest
            )
            # Count negative errors (errors in favor of the winner) as 0 to be conservative
            U += error["weighted_error"] if error and error["counted_as"] > 0 else 0
        else:
            U += compute_max_error(reported_results[batch], contest)

    return U


def get_sample_sizes(
    risk_limit: int,
    contest: Contest,
    reported_results: Dict[BatchKey, BatchResults],
    sample_results: Dict[BatchKey, BatchResults],
) -> int:
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
    alpha = Decimal(risk_limit) / 100
    assert alpha < 1, "The risk-limit must be less than one!"

    if len(reported_results) == len(sample_results):
        raise ValueError("All ballots have already been counted!")

    # Computing U with the max error for already sampled batches knocked out
    # to try to provide a sense of "how close" the audit is to finishing.
    U = compute_U(reported_results, sample_results, contest)

    if U == 0:
        return 1  # pragma: no cover
    elif U < 0 or U == Decimal("inf"):
        # This means we have a tie
        return len(reported_results)
    elif U == 1:
        # In this case, there is just enough potential error left to cause an
        # outcome change. Since U is so close to being less than one, we probably
        # only need to look at one more batch.
        return 1  # pragma: no cover

    retval = (
        int((alpha.ln() / ((1 - (1 / U))).ln()).quantize(Decimal(1), ROUND_CEILING))
        # Add one per a recommendation from Mark Lindeman
        + 1
    )

    return min(retval, len(reported_results))


def compute_risk(
    risk_limit: int,
    contest: Contest,
    reported_results: Dict[BatchKey, BatchResults],
    sample_results: Dict[BatchKey, BatchResults],
    sample_ticket_numbers: Dict[str, BatchKey],
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
        sample_results   - if a sample has already been drawn, this will
                           contain its results, of the same form as
                           reported_results
        sample_ticket_numbers - a mapping from ticket numbers to the batch
                           keys in sample_results
    Outputs:
        measurements    - the p-value of the hypotheses that the election
                          result is correct based on the sample for each
                          winner-loser pair.
        confirmed       - a boolean indicating whether the audit can stop
    """
    alpha = Decimal(risk_limit) / 100
    assert alpha < 1, "The risk-limit must be less than one!"

    # We've done a full hand recount
    if len(sample_results) == len(reported_results):
        return 0, True

    p = Decimal(1.0)

    # Computing U without the sample preserves conservative-ness
    U = compute_U(reported_results, cast(Dict, {}), contest)

    for _, batch in sorted(
        sample_ticket_numbers.items(), key=lambda entry: entry[0]  # ticket_number
    ):
        if contest.name not in sample_results[batch]:
            continue

        error = compute_error(reported_results[batch], sample_results[batch], contest)
        # Count negative errors (errors in favor of the winner) as 0 to be conservative
        e_p = (
            error["weighted_error"] if error and error["counted_as"] > 0 else Decimal(0)
        )

        u_p = compute_max_error(reported_results[batch], contest)

        # If this happens, we need a full hand recount
        if e_p == Decimal("inf") or u_p == Decimal("inf"):
            return 1.0, False

        taint = e_p / u_p

        if taint == 1:
            p = Decimal("inf")  # Our p-value blows up
        else:
            p *= (1 - 1 / U) / (1 - taint)

        if p <= alpha:
            return float(p), True

    return min(float(p), 1.0), p <= alpha

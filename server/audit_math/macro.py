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
from typing import Dict, Set, Tuple, TypeVar, TypedDict, Optional, List
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

    def error_for_candidate_pair(winner, loser) -> Optional[BatchError]:
        v_wp = batch_results[contest.name][winner]
        v_lp = batch_results[contest.name][loser]

        a_wp = sampled_results[contest.name][winner]
        a_lp = sampled_results[contest.name][loser]

        V_wl = contest.candidates[winner] - contest.candidates[loser]

        # Conservatively assume that any pending ballots would be tallied as
        # votes for the loser, reducing the reported margin.
        if contest.pending_ballots:
            V_wl -= contest.pending_ballots

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

            # Conservatively assume that any pending ballots would be tallied as
            # votes for the loser, reducing the reported margin.
            if contest.pending_ballots:
                V_wl -= contest.pending_ballots

            if V_wl == 0:
                return Decimal("inf")

            u_pwl = Decimal((v_wp - v_lp) + b_cp) / Decimal(V_wl)

            if u_pwl > error:
                error = u_pwl

    return error


def compute_U(
    reported_results: Dict[BatchKey, BatchResults],
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
        U += compute_max_error(reported_results[batch], contest)

    return U


def get_sample_sizes(
    risk_limit: int,
    contest: Contest,
    reported_results: Dict[BatchKey, BatchResults],
    sample_results: Dict[BatchKey, BatchResults],
    ticket_numbers: Dict[str, BatchKey],
    combined_batches: List[Set[BatchKey]],
) -> int:
    """
    Computes a sample size expected to confirm the election result
    (attain the risk limit). The base computation assumes no discrepancies;
    1 is added to accommodate small discrepancies. For rounds after the first,
    the sample size depends on the measured risk so far.

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
        combined_batches - a list of combined batches, where each combined batch
                           is a set of the sub-batch keys (may include
                           non-sampled batches)

    Outputs:
        sample_size - sample size (currently a single integer value)
    """
    alpha = Decimal(risk_limit) / 100
    assert alpha < 1, "The risk-limit must be less than one!"

    if len(reported_results) == len(sample_results):
        raise ValueError("All ballots have already been counted!")

    U = compute_U(reported_results, contest)
    if U.is_infinite():
        return len(reported_results)  # tied: full hand count
    p_mult = 1 - 1 / U

    risk, risk_attained = compute_risk(
        risk_limit,
        contest,
        reported_results,
        sample_results,
        ticket_numbers,
        combined_batches,
    )
    if risk_attained is True:
        return 0

    # For the first round, assuming no discrepancies, the required sample size n must
    # satisfy p_mult**n <= alpha; for subsequent rounds, it must satisfy
    # risk * p_mult**n <= alpha, where risk is the measured risk (p-value) in
    # completed rounds including observed taint values. Taking natural logs:
    # ln(risk) + n * ln(p_mult) <= ln(alpha), so n >= (ln(alpha) - ln(risk) / p_mult.
    # Note that ln(p_mult) is negative, hence the reversal from <= to =>.
    # Before the first round, risk = 1, so ln(risk) = 0.

    est_sample_size = (alpha.ln() - Decimal(risk).ln()) / p_mult.ln()

    # Add 1 to allow for small discrepancies (may be very conservative if sample size is small)
    retval = int(est_sample_size.quantize(Decimal(1), ROUND_CEILING) + 1)

    return min(retval, len(reported_results))


def compute_risk(
    risk_limit: int,
    contest: Contest,
    reported_results: Dict[BatchKey, BatchResults],
    sample_results: Dict[BatchKey, BatchResults],
    sample_ticket_numbers: Dict[str, BatchKey],
    combined_batches: List[Set[BatchKey]],
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
        combined_batches - a list of combined batches, where each combined batch
                           is a set of the sub-batch keys (may include
                           non-sampled batches)
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

    U = compute_U(reported_results, contest)

    for _, batch in sorted(
        sample_ticket_numbers.items(), key=lambda entry: entry[0]  # ticket_number
    ):
        if contest.name not in sample_results[batch]:
            continue

        # If this batch was part of a combined batch, then the sample results
        # will contain vote counts from all the ballots in the sub-batches of
        # the combined batch. Thus, to compute the error, we need to also sum
        # the reported tallies across sub-batches.
        # Note: To be conservative, we *don't* do this for the max error,
        # instead using the original batch's max error.
        combined_batch = next(
            (
                combined_batch
                for combined_batch in combined_batches
                if batch in combined_batch
            ),
            None,
        )
        if combined_batch:
            batch_reported_results = {
                contest.name: {
                    choice: sum(
                        reported_results[batch][contest.name][choice]
                        for batch in combined_batch
                    )
                    for choice in reported_results[batch][contest.name]
                }
            }
        else:
            batch_reported_results = reported_results[batch]

        error = compute_error(batch_reported_results, sample_results[batch], contest)
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

    return min(float(p), 1.0), p <= alpha

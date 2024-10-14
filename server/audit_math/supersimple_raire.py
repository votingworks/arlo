# pylint: disable=invalid-name
from decimal import Decimal, ROUND_CEILING
from typing import Dict, Tuple, Optional, List
import math

from .sampler_contest import Contest
from .supersimple import Discrepancy
from .raire_utils import RaireAssertion, CVR, CVRS, SAMPLECVRS

l: Decimal = Decimal(0.5)
gamma: Decimal = Decimal(1.03905)  # This gamma is used in Stark's tool, AGI, and CORLA

# This sets the expected number of one-vote misstatements at 1 in 1000
o1: Decimal = Decimal(0.001)
u1: Decimal = Decimal(0.001)

# This sets the expected two-vote misstatements at 1 in 10000
o2: Decimal = Decimal(0.0001)
u2: Decimal = Decimal(0.0001)


def nMin(
    alpha: Decimal, margin: Decimal, o1: Decimal, o2: Decimal, u1: Decimal, u2: Decimal
) -> Decimal:
    """
    Computes a sample size parameterized by expected under and overstatements
    and the margin.
    """
    return (o1 + o2 + u1 + u2).max(
        math.ceil(
            -2
            * gamma
            * (
                alpha.ln()
                + o1 * (1 - 1 / (2 * gamma)).ln()
                + o2 * (1 - 1 / gamma).ln()
                + u1 * (1 + 1 / (2 * gamma)).ln()
                + u2 * (1 + 1 / gamma).ln()
            )
            / Decimal(margin)
        ),
    )


def compute_discrepancies(
    cvrs: CVRS, sample_cvr: SAMPLECVRS, assertion: RaireAssertion
) -> Dict[str, Discrepancy]:
    """
    Iterates through a given sample and returns the discrepancies found.

    Inputs:
        contests       - the contests and results being audited
        cvrs           - mapping of ballot_id to votes:
                {
                    'ballot_id': {
                        'contest': {
                            'candidate1': 1,
                            'candidate2': 2,
                            ...
                        }
                    ...
                }

        sample_cvr - the CVR of the audited ballots
                {
                    'ballot_id': {
                        'times_sampled': 1,
                        'cvr': {
                            'contest': {
                                'candidate1': 1,
                                'candidate2': 2,
                                ...
                            }
                    }
                    ...
                }

    Outputs:
        discrepancies   - A mapping of ballot ids to their discrepancies. This
                          includes entries for ballots in the sample that have discrepancies
                          only.
                        'ballot_id': {
                            'counted_as': -1, # The maximum value for a discrepancy
                            'weighted_error': -0.0033 # Weighted error used for p-value calculation
                        }
                    }
    """
    V = compute_margin_for_assertion(cvrs, assertion)

    discrepancies: Dict[str, Discrepancy] = {}
    for ballot, ballot_sample_cvr in sample_cvr.items():
        ballot_discrepancy = discrepancy(
            cvrs.get(ballot),
            ballot_sample_cvr["cvr"],
            assertion,
            V,
        )
        if ballot_discrepancy is not None:
            discrepancies[ballot] = ballot_discrepancy

    return discrepancies


def normalize_cvr(cvr: CVR) -> CVR:
    """
    This function normalizes a CVR according to the following rules:
        1. No candidates may have the same rank.
        2. Ranks must begin at 1 and be consecutive.

    CVRS that do not comply with this function will be fixed by the following
    transformations:
        1. Any candidates who share a rank will have their rank set to 0.
           Additionally, all candidates with ranks lower than the duplicate rank
           will have their rank set to 0.
        2. If the highest rank is not 1, all ranks will be decremented until
           the highest rank is 1. If other ranks are not consecutive, they
           will be mapped accordingly. E.g., if a ballot is ranked 2, 4, 5, it
           will be normalized as 1, 2, 3.
    """

    output: CVR = {}
    for contest in cvr:
        output[contest] = {}

        # If there's an overvote (i.e. duplicate rank), zero it out (as well as any ranks below it)
        non_zero_ranks = [rank for rank in cvr[contest].values() if rank != 0]
        duplicate_ranks = {
            rank for rank in non_zero_ranks if non_zero_ranks.count(rank) > 1
        }
        highest_duplicate_rank = min(duplicate_ranks) if duplicate_ranks else None
        for candidate, rank in cvr[contest].items():
            if highest_duplicate_rank and rank >= highest_duplicate_rank:
                output[contest][candidate] = 0
            else:
                output[contest][candidate] = rank

        # Normalize ranks so that the highest rank is 1 and all ranks are consecutive
        ranked_candidates = {
            candidate: rank for candidate, rank in output[contest].items() if rank != 0
        }
        sorted_ranked_candidates = sorted(
            ranked_candidates.items(), key=lambda pair: pair[1]
        )
        for i, (candidate, _) in enumerate(sorted_ranked_candidates):
            output[contest][candidate] = i + 1

    return output


def discrepancy(
    reported: Optional[CVR],
    audited: Optional[CVR],
    assertion: RaireAssertion,
    margin: Decimal,
) -> Optional[Discrepancy]:
    # Special cases: if ballot wasn't in CVR or ballot can't be found by
    # audit board, count it as a two-vote overstatement
    if reported is None or audited is None:
        error = 2
    else:
        reported_v = normalize_cvr(reported)
        audited_v = normalize_cvr(audited)
        v_w, v_l = (
            assertion.is_vote_for_winner(reported_v),
            assertion.is_vote_for_loser(reported_v),
        )
        a_w, a_l = (
            assertion.is_vote_for_winner(audited_v),
            assertion.is_vote_for_loser(audited_v),
        )
        error = (v_w - a_w) - (v_l - a_l)

    if error == 0:
        return None

    weighted_error = Decimal(error) / Decimal(margin) if margin > 0 else Decimal("inf")

    return Discrepancy(counted_as=error, weighted_error=weighted_error)


def get_sample_sizes(
    risk_limit: int,
    contest: Contest,
    cvrs: CVRS,
    sample_results: Optional[Dict[RaireAssertion, Dict[str, int]]],
    assertions: List[RaireAssertion],
) -> int:
    """
    Computes initial sample sizes parameterized by likelihood that the
    initial sample will confirm the election result, assuming no
    discrepancies.

    Inputs:
        total_ballots  - the total number of ballots cast in the election
        sample_results - if a sample has already been drawn, this will
                         contain its results, of the form:
                         {
                            assertion: {
                                'sample_size': n,
                                '1-under':     u1,
                                '1-over':      o1,
                                '2-under':     u2,
                                '2-over':      o2,
                            },
                            ...
                         }


    Outputs:
        sample_size    - the sample size needed for this audit
    """
    alpha = Decimal(risk_limit) / 100
    assert alpha < 1

    stopping_size = 0

    for assertion in assertions:
        margin = compute_margin_for_assertion(cvrs, assertion) / contest.ballots
        if not sample_results:
            obs_o1 = Decimal(0)
            obs_o2 = Decimal(0)
            num_sampled = Decimal(0)
        else:
            obs_o1 = Decimal(sample_results[assertion].get("1-over", 0))
            obs_o2 = Decimal(sample_results[assertion].get("2-over", 0))
            num_sampled = Decimal(sample_results[assertion].get("sample_size", 0))
        # We want to be conservative, so we will ignore understatements (i.e. errors
        # that favor the winner) which are negative.
        obs_u1 = 0
        obs_u2 = 0

        if num_sampled:
            r1 = obs_o1 / num_sampled
            r2 = obs_o2 / num_sampled
            s1 = obs_u1 / num_sampled
            s2 = obs_u2 / num_sampled
        else:
            r1 = o1
            r2 = o2
            s1 = u1
            s2 = u2

        denom = (
            (1 - Decimal(margin) / (2 * gamma)).ln()
            - r1 * (1 - 1 / (2 * gamma)).ln()
            - r2 * (1 - 1 / gamma).ln()
            - s1 * (1 + 1 / (2 * gamma)).ln()
            - s2 * (1 + 1 / gamma).ln()
        )

        if denom >= 0:
            asrtn_stopping_size = contest.ballots
        else:
            n0 = math.ceil(alpha.ln() / denom)

            # Round up one-vote differences.
            r1 = (r1 * n0).quantize(Decimal(1), ROUND_CEILING)
            s1 = (s1 * n0).quantize(Decimal(1), ROUND_CEILING)

            asrtn_stopping_size = min(
                int(nMin(alpha, margin, r1, r2, s1, s2)), contest.ballots
            )

        stopping_size = max(asrtn_stopping_size - int(num_sampled), stopping_size)

    return stopping_size


def compute_margin_for_assertion(cvrs: CVRS, assertion: RaireAssertion) -> Decimal:
    v_w, v_l = 0, 0
    for cvr in cvrs:
        # Typechecker shenanigans. cvrs[cvr] can never be None since we're only
        # computing this function on provided CVRs.
        val = cvrs[cvr]
        assert val is not None
        v_w += assertion.is_vote_for_winner(val)
        v_l += assertion.is_vote_for_loser(val)
    margin = Decimal(v_w) - Decimal(v_l)

    return margin


def compute_risk(
    risk_limit: int,
    contest: Contest,
    cvrs: CVRS,
    sample_cvr: SAMPLECVRS,
    assertions: List[RaireAssertion],
) -> Tuple[float, bool]:
    """
    Computes the risk-value of <sample_results> based on results in <contest>.

    Inputs:
        contests       - the contests and results being audited
        cvrs           - mapping of ballot_id to votes:
                {
                    'ballot_id': {
                        'contest': {
                            'candidate1': 1,
                            'candidate2': 0,
                            ...
                        }
                    ...
                }

        sample_cvr - the CVR of the audited ballots
                {
                    'ballot_id': {
                        'times_sampled': 1,
                        'contest': {
                            'candidate1': 1,
                            'candidate2': 0,
                            ...
                        }
                    ...
                }

    Outputs:
        measurements    - the p-value of the hypotheses that the election
                          result is correct based on the sample, for each winner-loser pair.
        confirmed       - a boolean indicating whether the audit can stop
    """
    alpha = Decimal(risk_limit) / 100
    assert alpha < 1

    N = contest.ballots
    max_p = Decimal(0.0)
    result = False
    for assertion in assertions:
        p = Decimal(1.0)

        V = compute_margin_for_assertion(cvrs, assertion)
        margin = V / N

        discrepancies = compute_discrepancies(cvrs, sample_cvr, assertion)

        for ballot in sample_cvr:
            if ballot in discrepancies:
                # We want to be conservative, so we will ignore understatements (i.e. errors
                # that favor the winner) which are negative.
                e_r = max(discrepancies[ballot]["weighted_error"], Decimal(0))
            else:
                e_r = Decimal(0)

            # Note that a tie is never possible in this part of the code, so
            # margin will never be 0.
            U = 2 * gamma / Decimal(margin)
            denom = (2 * gamma) / V
            p_b = (1 - 1 / U) / (1 - (e_r / denom))

            multiplicity = sample_cvr[ballot]["times_sampled"]
            p *= p_b**multiplicity

        # Get the largest p-value across all assertions
        if p > max_p:
            max_p = p

    if 0 < max_p < alpha:
        result = True

    # Special case if the sample size equals all the ballots (i.e. a full hand tally)
    if sum(ballot["times_sampled"] for ballot in sample_cvr.values()) >= N:
        return 0, True

    return min(float(max_p), 1.0), result

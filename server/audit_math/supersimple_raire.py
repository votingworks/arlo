# pylint: disable=invalid-name
from decimal import Decimal
from typing import Dict, Tuple, Optional, List

from .sampler_contest import Contest, CVRS, SAMPLECVRS, CVR

from .supersimple import Discrepancy
from .raire_utils import RaireAssertion

l: Decimal = Decimal(0.5)
gamma: Decimal = Decimal(1.03905)  # This gamma is used in Stark's tool, AGI, and CORLA

# This sets the expected number of one-vote misstatements at 1 in 1000
o1: Decimal = Decimal(0.001)
u1: Decimal = Decimal(0.001)

# This sets the expected two-vote misstatements at 1 in 10000
o2: Decimal = Decimal(0.0001)
u2: Decimal = Decimal(0.0001)


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
    v_w, v_l = 0, 0
    for cvr in cvrs:
        # Typechecker shenanigans
        val = cvrs[cvr]
        assert val is not None
        v_w += assertion.is_vote_for_winner(val)
        v_l += assertion.is_vote_for_loser(val)
    V = v_w - v_l
    print(V)

    discrepancies: Dict[str, Discrepancy] = {}
    for ballot, ballot_sample_cvr in sample_cvr.items():
        ballot_discrepancy = discrepancy(
            cvrs.get(ballot), ballot_sample_cvr["cvr"], assertion, V,
        )
        if ballot_discrepancy is not None:
            discrepancies[ballot] = ballot_discrepancy

    return discrepancies


def discrepancy(
    reported: Optional[CVR],
    audited: Optional[CVR],
    assertion: RaireAssertion,
    margin: int,
) -> Optional[Discrepancy]:
    # Special cases: if ballot wasn't in CVR or ballot can't be found by
    # audit board, count it as a two-vote overstatement
    if reported is None or audited is None:
        error = 2
    else:
        v_w, v_l = (
            assertion.is_vote_for_winner(reported),
            assertion.is_vote_for_loser(reported),
        )
        a_w, a_l = (
            assertion.is_vote_for_winner(audited),
            assertion.is_vote_for_loser(audited),
        )
        error = (v_w - a_w) - (v_l - a_l)

    if error == 0:
        return None

    # TODO: this seems wrong - V_wl here is defined as the first-round tallies for winner and loser
    weighted_error = Decimal(error) / Decimal(margin) if margin > 0 else Decimal("inf")

    return Discrepancy(counted_as=error, weighted_error=weighted_error)


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

        v_w, v_l = 0, 0
        for cvr in cvrs:
            # Typechecker shenanigans
            val = cvrs[cvr]
            assert val is not None
            v_w += assertion.is_vote_for_winner(val)
            v_l += assertion.is_vote_for_loser(val)
        V = v_w - v_l

        margin = V / N

        discrepancies = compute_discrepancies(cvrs, sample_cvr, assertion)

        for ballot in sample_cvr:
            if ballot in discrepancies:
                # We want to be conservative, so we will ignore understatements (i.e. errors
                # that favor the winner) which are negative.
                e_r = max(discrepancies[ballot]["weighted_error"], Decimal(0))
            else:
                e_r = Decimal(0)

            if margin:
                U = 2 * gamma / Decimal(margin)
                denom = (2 * gamma) / V
                p_b = (1 - 1 / U) / (1 - (e_r / denom))
            else:
                # If the contest is a tie, this step results in 1 - 1/(infinity)
                # divided by 1 - e_r/infinity, i.e. 1
                p_b = Decimal(1.0)

            multiplicity = sample_cvr[ballot]["times_sampled"]
            p *= p_b ** multiplicity

        # Get the largest p-value across all assertions
        if p > max_p:
            max_p = p
        print(f"{assertion} p-value: {p}")

    if 0 < max_p < alpha:
        result = True

    # Special case if the sample size equals all the ballots (i.e. a full hand tally)
    if sum(ballot["times_sampled"] for ballot in sample_cvr.values()) >= N:
        return 0, True

    return min(float(max_p), 1.0), result

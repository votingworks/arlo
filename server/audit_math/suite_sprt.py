from __future__ import division
import math
import numpy as np
import numpy.random
import scipy as sp
import scipy.stats
import scipy.optimize

from typing import Dict, Tuple
from decimal import Decimal
from .bravo import *
from .sampler_contest import Contest, Stratum


def ballot_polling_sprt(
                        contest: Contest,
                        stratum: Stratum,
                        null_margins: Dict[Tuple[str,str], Decimal],
                    ) -> float:
    """
    Code adapted from the SUITE repo.

    Wald's SPRT for the difference in true number of votes for the winner, n_w,
    and the loser, n_l:

    H_0: n_w = n_l + null_margin
    H_1: n_w = Vw, n_l = Vl

    The type II error rate, usually denoted beta, is set to 0%: if the data do
    not support rejecting the null, there is a full hand count. Because beta=0,
    the reciprocal of the likelihood ratio is a conservative p-value.

    Inputs:
        contest         - the contest being audited
        stratum         - data about the set of ballots being audited
        null margins    - a dictionary of margins under the null hypotehsis for every
                          winner-loser pair. This is needed for optimizing the
                          Fisher's combined p-value.

    Outputs:
        pvalue          - the largest observed p-value

    """

    # Set parameters
    popsize = stratum.contest.ballots

    p_values = {}

    for winner,loser in null_margins:
        # Set up likelihood for null and alternative hypotheses
        n = stratum.sample_size
        sample = compute_cumulative_sample(stratum.sample)
        n_w = sample[winner]
        n_l = sample[loser]
        n_u = n - n_w - n_l

        v_w = stratum.contest.winners[winner]
        v_l = stratum.contest.losers[loser]
        v_u = popsize - v_w - v_l

        null_margin = null_margins[(winner,loser)]

        assert v_w >= n_w and v_l >= n_l and v_u >= n_u, "Alternative hypothesis isn't consistent with the sample"

        alt_logLR = np.sum(np.log(v_w - np.arange(n_w))) + \
                    np.sum(np.log(v_l - np.arange(n_l))) + \
                    np.sum(np.log(v_u - np.arange(n_u)))

        null_logLR = lambda Nw: (n_w > 0)*np.sum(np.log(Nw - np.arange(n_w))) + \
                    (n_l > 0)*np.sum(np.log(Nw - null_margin - np.arange(n_l))) + \
                    (n_u > 0)*np.sum(np.log(popsize - 2*Nw + null_margin - np.arange(n_u)))

        upper_n_w_limit = (popsize - n_u + null_margin)/2
        lower_n_w_limit = np.max([n_w, n_l+null_margin])

        # For extremely small or large null_margins, the limits do not
        # make sense with the sample values.
        if upper_n_w_limit < n_w or (upper_n_w_limit - null_margin) < n_l:
            raise Exception('Null is impossible, given the sample')


        if lower_n_w_limit > upper_n_w_limit:
            lower_n_w_limit, upper_n_w_limit = upper_n_w_limit, lower_n_w_limit

        LR_derivative = lambda Nw: np.sum([1/(Nw - i) for i in range(n_w)]) + \
                    np.sum([1/(Nw - null_margin - i) for i in range(n_l)]) - \
                    2*np.sum([1/(popsize - 2*Nw + null_margin - i) for i in range(n_u)])

        # Sometimes the upper_n_w_limit is too extreme, causing illegal 0s.
        # Check and change the limit when that occurs.
        if np.isinf(null_logLR(upper_n_w_limit)) or np.isinf(LR_derivative(upper_n_w_limit)):
            upper_n_w_limit -= 1

        # Check if the maximum occurs at an endpoint: deriv has no sign change
        if LR_derivative(upper_n_w_limit)*LR_derivative(lower_n_w_limit) > 0:
            nuisance_param = upper_n_w_limit if null_logLR(upper_n_w_limit)>=null_logLR(lower_n_w_limit) else lower_n_w_limit
        # Otherwise, find the (unique) root of the derivative of the log likelihood ratio
        else:
            nuisance_param = sp.optimize.brentq(LR_derivative, lower_n_w_limit, upper_n_w_limit)
        number_invalid = popsize - nuisance_param*2 + null_margin
        logLR = alt_logLR - null_logLR(nuisance_param)
        LR = np.exp(logLR)

        p_values[(winner,loser)] = 1.0/LR if 1.0/LR < 1 else 1

    return max(p_values.values())

# pylint: disable=invalid-name
import math

l = 0.5
gamma = 1.03905  # This gamma is used in Stark's tool, AGI, and CORLA

# This sets the expected number of one-vote misstatements at 1 in 1000
o1 = 0.001
u1 = 0.001

# This sets the expected two-vote misstatements at 1 in 10000
o2 = 0.0001
u2 = 0.0001


def nMin(risk_limit, contest, o1, o2, u1, u2):
    """
    Computes a sample size parameterized by expected under and overstatements
    and the margin.
    """
    return max(
        o1 + o2 + u1 + u2,
        math.ceil(
            -2
            * gamma
            * (
                math.log(risk_limit)
                + o1 * math.log(1 - 1 / (2 * gamma))
                + o2 * math.log(1 - 1 / gamma)
                + u1 * math.log(1 + 1 / (2 * gamma))
                + u2 * math.log(1 + 1 / gamma)
            )
            / contest.diluted_margin
        ),
    )


def get_sample_sizes(risk_limit, contest, sample_results):
    """
    Computes initial sample sizes parameterized by likelihood that the
    initial sample will confirm the election result, assuming no
    discrepancies.

    Inputs:
        total_ballots  - the total number of ballots cast in the election
        sample_results - if a sample has already been drawn, this will
                         contain its results, of the form:
                         {
                            'sample_size': n,
                            '1-under':     u1,
                            '1-over':      o1,
                            '2-under':     u2,
                            '2-over':      o2,
                         }

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

    obs_o1 = sample_results["1-over"]
    obs_u1 = sample_results["1-under"]
    obs_o2 = sample_results["2-over"]
    obs_u2 = sample_results["2-under"]
    num_sampled = sample_results["sample_size"]

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
        math.log(1 - contest.diluted_margin / (2 * gamma))
        - r1 * math.log(1 - 1 / (2 * gamma))
        - r2 * math.log(1 - 1 / gamma)
        - s1 * math.log(1 + 1 / (2 * gamma))
        - s2 * math.log(1 + 1 / gamma)
    )

    if denom >= 0:
        return contest.ballots

    n0 = math.ceil(math.log(risk_limit) / denom)

    # Round up one-vote differences.
    r1 = math.ceil(r1 * n0)
    s1 = math.ceil(s1 * n0)

    return nMin(risk_limit, contest, r1, r2, s1, s2)


def compute_risk(risk_limit, contest, cvrs, sample_cvr):
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

        sample_cvr - the CVR of the audited ballot
                {
                    'ballot_id': {
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

    p = 1

    V = contest.diluted_margin * len(cvrs)

    U = 2 * gamma / contest.diluted_margin

    result = False
    for ballot in sample_cvr:
        e_r = 0

        if contest.name not in sample_cvr[ballot]:
            continue
        for winner in contest.winners:
            for loser in contest.losers:
                v_w = cvrs[ballot][contest.name][winner]
                a_w = sample_cvr[ballot][contest.name][winner]

                v_l = cvrs[ballot][contest.name][loser]
                a_l = sample_cvr[ballot][contest.name][loser]

                V_wl = contest.candidates[winner] - contest.candidates[loser]

                e = ((v_w - a_w) - (v_l - a_l)) / V_wl
                if e > e_r:
                    e_r = e

        denom = (2 * gamma) / V
        p_b = (1 - 1 / U) / (1 - (e_r / denom))
        p *= p_b

    if 0 < p < risk_limit:
        result = True

    return p, result

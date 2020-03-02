"""

An implemenation of MACRO for batch comparison audits.

MACRO was developed by Philip Stark
(see https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1443314 for the publication).


"""

import math
from typing import Dict
from audits.audit import RiskLimitingAudit


class MACRO(RiskLimitingAudit):
    """
    Concrete implementation of the RLA class implementing batch audits

    """

    reported_results: Dict[str, Dict]

    def __init__(self, risk_limit, reported_results):
        super().__init__(risk_limit)

        self.reported_results = reported_results

    def compute_error(self, batch_name, contests, margins, sampled_results):
        """
        Computes the error in this batch

        Inputs:
            contests - the contests in the election
            margins - the margins for the election
            reported_results - the reported votes in this batch
            sampled_results - the actual votes in this batch after auditing

        Outputs:
            the maximum across-contest relative overstatement for batch p
        """

        error = 0
        for contest in self.reported_results[batch_name]:
            for winner in margins[contest]['winners']:
                for loser in margins[contest]['losers']:
                    v_wp = self.reported_results[batch_name][contest][winner]
                    v_lp = self.reported_results[batch_name][contest][loser]

                    a_wp = sampled_results[contest][winner]
                    a_lp = sampled_results[contest][loser]

                    V_wl = contests[contest][winner] - contests[contest][loser]

                    e_pwl = ((v_wp - v_lp) - (a_wp - a_lp)) / V_wl

                    if e_pwl > error:
                        error = e_pwl

        return error

    def compute_max_error(self, batch_name, contests, margins):
        """
        Computes the maximum possible error in this batch

        Inputs:
            batch_name - the name of this batch
            margins - the margins for the election
            reported_results - the reported votes in this batch

        Outputs:
            the maximum possible overstatement for batch p
        """

        error = 0
        for contest in self.reported_results[batch_name]:
            for winner in margins[contest]['winners']:
                for loser in margins[contest]['losers']:
                    v_wp = self.reported_results[batch_name][contest][winner]
                    v_lp = self.reported_results[batch_name][contest][loser]

                    b_cp = self.reported_results[batch_name][contest]['ballots']

                    V_wl = contests[contest][winner] - contests[contest][loser]

                    u_pwl = ((v_wp - v_lp) + b_cp) / V_wl

                    if u_pwl > error:
                        error = u_pwl

        return error

    def compute_U(self, contests, margins):
        """
        Computes U, the sum of the batch-wise relative overstatement limits,
        i.e. the maximum amount of possible overstatement in a given election.
        """

        U = 0
        for batch in self.reported_results:

            U += self.compute_max_error(batch, contests, margins)

        return U

    def get_sample_sizes(self, contests, margins, sample_results):
        """
        Computes initial sample sizes parameterized by likelihood that the
        initial sample will confirm the election result, assuming no
        discrepancies.

        Inputs:
            sample_results - if a sample has already been drawn, this will
                             contain its results.

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

        U = self.compute_U(contests, margins)

        return math.ceil(math.log(self.risk_limit) / (math.log(1 - (1 / U))))

    def compute_risk(self, contests, margins, sample_results):
        """
        Computes the risk-value of <sample_results> based on results in <contest>.

        Inputs:
            contests       - the contests and results being audited
            margins        - the margins for the contest being audited
            sample_results - mapping of candidates to votes in the (cumulative)
                             sample:

                    {
                        candidate1: sampled_votes,
                        candidate2: sampled_votes,
                        ...
                    }

        Outputs:
            measurements    - the p-value of the hypotheses that the election
                              result is correct based on the sample, for each winner-loser pair.
            confirmed       - a boolean indicating whether the audit can stop
        """

        p = 1

        U = self.compute_U(contests, margins)

        for batch in sample_results:
            e_p = self.compute_error(batch, \
                                     contests, \
                                     margins,  \
                                     sample_results[batch])

            u_p = self.compute_max_error(batch, contests, margins)

            taint = e_p / u_p

            p *= (1 - 1 / U) / (1 - taint)

            if p < self.risk_limit:
                return p, True

        return p, p < self.risk_limit

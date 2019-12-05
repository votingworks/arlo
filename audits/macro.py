import math
from scipy import stats
from audits.audit import RiskLimitingAudit

class MACRO(RiskLimitingAudit):

    def __init__(self, risk_limit):
        super().__init__(risk_limit)

    def compute_error(self, contests, margins, reported_results, sampled_results):
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
        for contest in reported_results:
            for winner in margins[contest]['winners']:
                for loser in margins[contest]['losers']:
                    v_wp = reported_results[contest][winner]
                    v_lp = reported_results[contest][loser]


                    a_wp = sampled_results[contest][winner]
                    a_lp = sampled_results[contest][loser]

                    V_wl = contests[contest][winner] - contests[contest][loser]

                    e_pwl = ((v_wp - v_lp) - (a_wp - a_lp))/V_wl

                    if e_pwl > error:
                        error = e_pwl

        return error


    def compute_max_error(self, contests, margins, reported_results):
        """
        Computes the maximum error in this batch

        Inputs:
            margins - the margins for the election
            reported_results - the reported votes in this batch
        
        Outputs:
            the maximum possible overstatement for batch p
        """
        
        error = 0
        for contest in reported_results:
            for winner in margins[contest]['winners']:
                for loser in margins[contest]['losers']:
                    v_wp = reported_results[contest][winner]
                    v_lp = reported_results[contest][loser]

                    b_cp = reported_results[contest]['ballots']

                    V_wl = contests[contest][winner] - contests[contest][loser]

                    u_pwl = ((v_wp - v_lp) + b_cp)/V_wl

                    if u_pwl > error:
                        error = u_pwl

        return error

    def compute_u_minus(self, contests, margins, reported_results):
        """
        Computes the maximum error in this batch

        Inputs:
            margins - the margins for the election
            reported_results - the reported votes in this batch
        
        Outputs:
            the maximum possible overstatement for batch p
        """
        
        u_minus = 0

        for contest in reported_results:
            for winner in margins[contest]['winners']:
                for loser in margins[contest]['losers']:
                    v_wp = reported_results[contest][winner]
                    v_lp = reported_results[contest][loser]

                    b_cp = reported_results[contest]['ballots']

                    V_wl = contests[contest][winner] - contests[contest][loser]


                    u_p_minus = float((v_wp - v_lp) - b_cp)/V_wl

                    if u_p_minus > u_minus:
                        u_minus = u_p_minus

        return u_minus

    def compute_U(self, contests, margins, reported_results):

        U = 0
        for batch in reported_results:

            U += self.compute_max_error(contests, margins, reported_results[batch])

        return U       

    def get_sample_sizes(self, contests, margins, reported_results, sample_results):
        """
        Computes initial sample sizes parameterized by likelihood that the
        initial sample will confirm the election result, assuming no
        discrpancies.

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


        tau_minus = 10**7

        for batch in reported_results:
            u_p = self.compute_max_error(contests, margins, reported_results[batch])

            u_minus = self.compute_u_minus(contests, margins, reported_results[batch])

            if u_minus/u_p < tau_minus:
                tau_minus = u_minus/u_p

        U = self.compute_U(contests, margins, reported_results)

        return math.ceil(math.log(self.risk_limit)/(math.log(1 - (1/U)) - math.log(1 - tau_minus)))


    def compute_risk(self, contests, margins, reported_results, sample_results):
        """
        Computes the risk-value of <sample_results> based on results in <contest>.

        Inputs: 
            contests       - the contests and results being audited
            margins        - the margins for the contest being audited
            reported_results - mapping of candidates to reported votes
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


        U = self.compute_U(contests, margins, reported_results)

        for ctr,batch in enumerate(sample_results):
            e_p = self.compute_error(contests, margins, reported_results[batch], sample_results[batch])
            u_p = self.compute_max_error(contests, margins, reported_results[batch])

            taint = e_p/u_p
            print(taint, ctr)

            p *= (1 - 1/U)/(1 - taint)

            if p < self.risk_limit:
               return p, True

        return p, p < self.risk_limit

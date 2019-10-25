import math
from scipy import stats
from audits.audit import RiskLimitingAudit

class Bravo(RiskLimitingAudit):
    def __init__(self, risk_limit):
        super().__init__(risk_limit)

    def get_expected_sample_sizes(self, margins, contests):
        """
        Returns the expected sample size for a BRAVO audit of each contest in contests.

        Input:
            margins - a dict of the margins for each contest passed from Sampler
            contests - a dict of the contests passed in from Sampler

        Output:
            expected sample sizes - dict of computed expected sample size for each contest:
                {
                    contest1: asn1,
                    contest3: asn2,
                    ...
                }
        """
        asns = {}
        for contest in contests:
            margin = margins[contest]
            p_w = 10**7
            s_w = 0 
            p_l = 0
            # Get smallest p_w - p_l
            for winner in margin['winners']:
                if margin['winners'][winner]['p_w'] < p_w:
                    p_w = margin['winners'][winner]['p_w']

            if not margin['losers']:
                asns[contest] = -1
                continue

            for loser in margin['losers']:
                if margin['losers'][loser]['p_l'] > p_l:
                    p_l = margin['losers'][loser]['p_l']


            s_w = p_w/(p_w + p_l) 
            s_l = 1 - s_w

            print(p_w, p_l, s_w, s_l)

            if p_w == 1:
                # Handle single-candidate or crazy landslides
                asns[contest] = -1
            elif p_w == p_l:
                asns[contest] = contests[contest]['ballots']
            else: 
                z_w = math.log(2 * s_w)
                z_l = math.log(2 - 2 * s_w)
                p = p_w + s_l
                asns[contest] = math.ceil((math.log(1.0/self.risk_limit) + (z_w / 2.0)) / (p_w*z_w + p_l*z_l))

        return asns

    def bravo_sample_sizes(self, p_w, p_r, sample_w, sample_r, p_completion):
        """
        Analytic calculation for BRAVO round completion assuming the election
        outcome is correct. Written by Mark Lindeman. 

        Inputs:
            p_w             - the fraction of vote share for the winner 
            p_r             - the fraction of vote share for the loser 
            sample_w        - the number of votes for the winner that have already 
                              been sampled
            sample_r        - the number of votes for the runner-up that have 
                              already been sampled
            p_completion    - the desired chance of completion in one round,
                              if the outcome is correct

        Outputs:
            sample_size     - the expected sample size for the given chance
                              of completion in one round
        """

        # calculate the "two-way" share of p_w
        p_wr = p_w + p_r
        p_w2 = p_w / p_wr
        p_r2 = 1 - p_w2
        
        # set up the basic BRAVO math
        plus = math.log(p_w2 / 0.5)
        minus = math.log(p_r2 / 0.5)
        threshold = math.log(1 / self.risk_limit) - (sample_w * plus + sample_r * minus)
    
        # crude condition trapping:
        if threshold <= 0:
            return 0 
        
        z = -stats.norm.ppf(p_completion)
        
        # The basic equation is E_x = R_x where 
        # E_x: expected # of successes at the 1-p_completion quantile
        # R_x: smallest x (given n) that attains the risk limit
        
        # E_x = n * p_w2 + z * sqrt(n * p_w2 * p_r2)
        # R_x = (threshold - minus * n) / (plus - minus)
        
        # (Both sides are continuous approximations to discrete functions.)
        # We set these equal, rewrite as a quadratic in n, and take the
        # larger of the two zeros (roots).
        
        # These parameters are useful in simplifying the quadratic.
        d = p_w2 * p_r2
        f = threshold / (plus - minus)
        g = minus / (plus - minus) + p_w2
        
        # The three coefficients of the quadratic:
        q_a = g**2
        q_b = -(z**2 * d + 2 * f * g)
        q_c = f**2
        
        # Apply the quadratic formula.
        # We want the larger root for p_completion > 0.5, the
        # smaller root for p_completion < 0.5; they are equal
        # when p_completion = 0.
        # max here handles cases where, due to rounding error,
        # the base (content) of the radical is trivially
        # negative for p_completion very close to 0.5.
        radical = math.sqrt(max(0, q_b**2 - 4 * q_a * q_c))
        
        if p_completion > 0.5:
            size = math.floor((-q_b + radical) / (2 * q_a))
        else:
            size = math.floor((-q_b - radical) / (2 * q_a)) 

        # This is a reasonable estimate, but is not guaranteed.
        # Get a guarantee. (Perhaps contrary to intuition, using 
        # math.ceil instead of math.floor can lead to a 
        # larger sample.)
        searching = True
        while searching:
            x_c = stats.binom.ppf(1.0 - p_completion, size, p_w2)
            test_stat = x_c * plus + (size - x_c) * minus
            if test_stat > threshold:
                searching = False
            else:
                size += 1
                
        # The preceding fussiness notwithstanding, we use a simple
        # adjustment to account for "other" votes beyond p_w and p_r.

        size_adj = math.ceil(size / p_wr)
                
        return(size_adj)

    def expected_prob(self, p_w, p_r, sample_w, sample_r, asn):
        """ 
        Analytic calculation for BRAVO round completion of the expected value, assuming
        the election outcome is correct. Adapted Mark Lindeman. 

        Inputs:
            asn             - the expected value
            p_w             - the fraction of vote share for the winner 
            p_r             - the fraction of vote share for the loser 
            sample_w        - the number of votes for the winner that have already 
                              been sampled
            sample_r        - the number of votes for the runner-up that have 
                              already been sampled

        Outputs:
            sample_size     - the expected sample size for the given chance
                              of completion in one round

        """

        # calculate the "two-way" share of p_w
        p_wr = p_w + p_r
        p_w2 = p_w / p_wr
        p_r2 = 1 - p_w2
        
        # set up the basic BRAVO math
        plus = math.log(p_w2 / 0.5)
        minus = math.log(p_r2 / 0.5)
        threshold = math.log(1 / self.risk_limit) - (sample_w * plus + sample_r * minus)
    
        # crude condition trapping:
        if threshold <= 0:
            return 0 
        
        n = asn 
        # The basic equation is E_x = R_x where 
        # E_x: expected # of successes at the 1-p_completion quantile
        # R_x: smallest x (given n) that attains the risk limit
        
        # E_x = n * p_w2 + z * sqrt(n * p_w2 * p_r2)
        # R_x = (threshold - minus * n) / (plus - minus)
        
        # (Both sides are continuous approximations to discrete functions.)
        # We set these equal, and solve for z

        R_x = (threshold - minus * n) / (plus - minus)

        print('R_x: {}, n*p_w2: {}'.format(R_x, n*p_w2))

        z =  (R_x - n*p_w2)/math.sqrt(n*p_w2*p_r2)

        # Invert the PPF used to compute z from the sample prob
        return stats.norm.cdf(-z)        

    def get_sample_sizes(self, contests, margins, sample_results):
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
        quants = [.7, .8, .9]

        samples = {}

        asns = self.get_expected_sample_sizes(margins, contests)
        for contest in contests:
            samples[contest] = {}

            p_w = 10**7
            s_w = 0 
            p_l = 0
            best_loser = ''
            worse_winner = ''


            # For multi-winner, do nothing
            if 'numWinners' not in contests[contest] or contests[contest]['numWinners'] != 1:
                samples[contest] = {
                    'asn': {
                        'size': asns[contest],
                        'prob': None
                    }
                }
                return samples

            margin = margins[contest]
            # Get smallest p_w - p_l
            for winner in margin['winners']:
                if margin['winners'][winner]['p_w'] < p_w:
                    p_w = margin['winners'][winner]['p_w']
                    worse_winner = winner

            for loser in margin['losers']:
                if margin['losers'][loser]['p_l'] > p_l:
                    p_l = margin['losers'][loser]['p_l']
                    best_loser = loser

            # If we're in a single-candidate race, set sample to 0
            if not margin['losers']:
                samples[contest]['asn'] = {
                    'size': -1,
                    'prob': -1
                }
                for quant in quants:
                    samples[contest][quant] = -1

                continue
            s_w = p_w/(p_w + p_l) 
            s_l = 1 - s_w


            num_ballots = contests[contest]['ballots']
            
            # Handles ties
            if p_w == p_l:
                samples[contest]['asn'] = {
                    'size': num_ballots,
                    'prob': 1,
                }

                for quant in quants:
                    samples[contest][quant] = num_ballots
                continue


            sample_w = sample_results[contest][worse_winner]
            sample_l = sample_results[contest][best_loser]
           
            samples[contest]['asn'] = {
                'size': asns[contest],
                'prob': self.expected_prob(p_w, p_l, sample_w, sample_l, asns[contest])
                }

            for quant in quants:
                samples[contest][quant] = self.bravo_sample_sizes(p_w, p_l, sample_w, sample_l, quant)

        return samples

    def compute_risk(self, margins, sample_results):
        """
        Computes the risk-value of <sample_results> based on results in <contest>.

        Inputs: 
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
        winners = margins['winners']
        losers = margins['losers']

        T = {}

        # Setup pair-wise Ts:
        for winner in winners:
            for loser in losers:
                T[(winner, loser)] = 1

        # Handle the no-losers case
        if not losers:
            for winner in winners:
                T[(winner,)] = 1

        for cand, votes in sample_results.items():
            if cand in winners:
                for loser in losers:
                    T[(cand, loser)] *= (winners[cand]['swl'][loser]/0.5)**votes
            elif cand in losers:
                for winner in winners:
                    T[(winner, cand)] *= ((1 - winners[winner]['swl'][cand])/0.5)**votes

        measurements = {}
        finished = True
        for pair in T:
            measurements[pair] = 1/T[pair]
            if measurements[pair] > self.risk_limit:
                finished = False
        return measurements, finished 


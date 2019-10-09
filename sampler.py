# Handles generating sample sizes and taking samples
from cryptorandom.cryptorandom import SHA256
import math
import numpy as np
from scipy import stats
import consistent_sampler
import operator

class Sampler:
    def __init__(self, seed, risk_limit, contests):
        """
        Initializes PRNG, computes margins, and returns initial sample
        sizes parameterized by likelihood that the initial sample will confirm the
        election result, assuming no discrpancies.

        Inputs:
            seed - seed used to initialized random functions
            risk_limit - the risk-limit to compute sample sizes from
            contests - dictionary of targeted contests. Maps:
                        {
                            contest: {
                                candidate1: votes,
                                candidate2: votes,
                                ...
                                'ballots': ballots, # total ballots cast
                                'winners': winners # number of winners in this contest
                            }
                            ...
                        }

        Outputs:
        """
        self.seed = seed
        self.prng = SHA256(seed)
        self.risk_limit = risk_limit
        self.contests = contests
        self.margins = self.compute_margins()

    def compute_margins(self):
        """
        Method that computes all margins for the contests in <contests>, and 
        returns a mapping of contest name to margin info. 

        Input:
            contests - dictionary of targeted contests. Maps:
                        {
                            contest: {
                                candidate1: votes,
                                candidate2: votes,
                                ...
                                'ballots': ballots,
                                'winners': winners
                            }
                            ...
                        }
        Output:
            margins - dictionary of diluted margin info:
                        {
                            contest: {
                                'winners': {
                                    winner1: {
                                              'p_w': p_w,     # Proportion of ballots for this winner
                                              's_w': 's_w'    # proportion of votes for this winner 
                                              'swl': {      # fraction of votes for w among (w, l)
                                                    'loser1':  s_w/(s_w + s_l1),
                                                    ...,
                                                    'losern':  s_w/(s_w + s_ln)
                                                }
                                              }, 
                                    ..., 
                                    winnern: {...} ] 
                                'losers': {
                                    loser1: {
                                              'p_l': p_l,     # Proportion of votes for this loser
                                              's_l': s_l,     # Proportion of ballots for this loser
                                              }, 
                                    ..., 
                                    losern: {...} ] 
                                
                            }
                        }

        """

        margins = {}
        for contest in self.contests:
            margins[contest] = {'winners':{}, 'losers':{}}

            cand_vec = sorted(
                    [(cand, self.contests[contest][cand]) 
                        for cand in self.contests[contest]
                            if cand not in ['winners', 'ballots']
                    ], 
            key=operator.itemgetter(1), reverse = True)

            num_winners = self.contests[contest]['winners']
            winners = cand_vec[:num_winners]
            losers = cand_vec[num_winners:]

            ballots = self.contests[contest]['ballots']

            v_wl = sum([c[1] for c in winners + losers])

            margins[contest]['winners']: {}
            margins[contest]['losers']: {}


            for loser in losers:
                margins[contest]['losers'][loser[0]] = {
                    'p_l': loser[1]/ballots,
                    's_l': loser[1]/v_wl

                }

            for winner in winners:
                s_w = winner[1]/v_wl

                swl = {}
                for loser in margins[contest]['losers']:
                    s_l = margins[contest]['losers'][loser]['s_l']
                    swl[loser] = s_w/(s_w + s_l)

                margins[contest]['winners'][winner[0]] = {
                    'p_w': winner[1]/ballots,
                    's_w': s_w,
                    'swl' : swl

                }

        return margins


    def get_asns(self):
        """
        Returns the ASN for a BRAVO audit of each contest in  self.contests.

        Input:
            None

        Output:
            ASNs - dict of computed ASN for each contest:
                {
                    contest1: asn1,
                    contest2: asn2,
                    ...
                }
        """
        asns = {}
        margins = self.margins
        for contest in self.contests:
            p_w = margins[contest]['p_w']
            p_r = margins[contest]['p_r']
            s_w = margins[contest]['s_w']

            if p_w == 1:
                # Handle single-candidate or crazy landslides
                asns[contest] = 0
            elif p_w == p_r:
                asns[contest] = self.contests[contest]['ballots']
            else: 
                z_w = math.log(2 * s_w)
                z_l = math.log(2 - 2 * s_w)
                asns[contest] = math.ceil((math.log(1/self.risk_limit) + (z_w / 2)) / ((p_w * z_w) + (p_r * z_l)))

        return asns

    def bravo_sample_size(self, p_w, p_r, sample_w, sample_r, p_completion):
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

    def bravo_asn_prob(self, p_w, p_r, sample_w, sample_r, asn):
        """ 
        Analytic calculation for BRAVO round completion of ASN, assuming
        the election outcome is correct. Adapted Mark Lindeman. 

        Inputs:
            asn             - the ASN
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
    
    def get_sample_sizes(self, sample_results):
        """
        Computes initial sample sizes parameterized by likelihood that the
        initial sample will confirm the election result, assuming no
        discrpancies.

        Inputs:
            sample_results - if a sample has already been drawn, this will
                             contain its results. 

            TODO: could take in likelihood parameters instead of hardcoding

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
        # TODO Note this treats each contest separately instead of together

        # TODO Do we want these hard-coded or parameterized?
        quants = [.7, .8, .9]

        samples = {}

        asns = self.get_asns()
        for contest in self.contests:
            samples[contest] = {}

            winner = self.margins[contest]['winner']
            runner_up = self.margins[contest]['runner_up']

            # If we're in a single-candidate race, set sample to 0
            if not runner_up:
                samples[contest]['asn'] = {
                    'size': 0,
                    'prob': 0
                }
                for quant in quants:
                    samples[contest][quant] = 0 

                continue

            p_w = self.margins[contest]['p_w']
            p_r = self.margins[contest]['p_r']
            s_w = self.margins[contest]['s_w']
            num_ballots = self.contests[contest]['ballots']
            
            # Handles ties
            if p_w == p_r:
                samples[contest]['asn'] = {
                    'size': num_ballots,
                    'prob': 1,
                }

                for quant in quants:
                    samples[contest][quant] = num_ballots
                continue


            sample_w = sample_results[contest][winner]
            sample_r = sample_results[contest][runner_up]
           
            samples[contest]['asn'] = {
                'size': asns[contest],
                'prob': self.bravo_asn_prob(p_w, p_r, sample_w, sample_r, asns[contest])
                }

            for quant in quants:
                samples[contest][quant] = self.bravo_sample_size(p_w, p_r, sample_w, sample_r, quant)

        return samples


    def draw_sample(self, manifest, sample_size, num_sampled=0):
        """
        Draws uniform random sample with replacement of size <sample_size> from the
        provided ballot manifest.

        Inputs:
            sample_size - number of ballots to randomly draw
            num_sampled - number of ballots that have already been sampled
            manifest - mapping of batches to the ballots they contain:
                        { 
                            batch1: num_balots,
                            batch2: num_ballots,
                            ...
                        }
                    
        Outputs:
            sample - list of (<batch>, <ballot number>) tuples to sample, with duplicates, ballot position is 0-indexed
                    [   
                        (batch1, 1),
                        (batch2, 49),
                        ...
                    ]

        """
        ballots = []
        # First build a faux list of ballots
        for batch in manifest:
            for i in range(manifest[batch]):
                ballots.append((batch, i))

        sample =  list(consistent_sampler.sampler(ballots, 
                                                  seed=self.seed, 
                                                  take=sample_size + num_sampled, 
                                                  with_replacement=True,
                                                  output='id'))[num_sampled:]
        
        # TODO this is sort of a hack to get the list sorted right. Maybe it's okay?
        return sorted(sample)

    def compute_risk(self, contest, sample_results):
        """
        Computes the risk-value of <sample_results> based on results in <contest>.

        Inputs: 
            contest        - the name of the contest that is targeted
            sample_results - mapping of candidates to votes in the (cumulative)
                             sample:

                    {
                        candidate1: sampled_votes,
                        candidate2: sampled_votes,
                        ...
                    }

        Outputs:
            risk            - the p-value of the hypotheses that the election
                              result is correct based on the sample. 
            confirmed       - a boolean indicating whether the audit can stop
        """
        
        # TODO: also a risk-calculation that isn't a p-value?

        # TODO Do we assume sample_results is cumulative? 
        margins = self.margins[contest]
        T = 1
        for cand, votes in sample_results.items():
            if cand == margins['winner']:
                T *= (2*margins['s_w'])**(votes)
            elif cand == margins['runner_up']:
                T *= (2 - 2*margins['s_w'])**(votes)

        return 1/T, 1/T < self.risk_limit


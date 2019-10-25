# Handles generating sample sizes and taking samples
from cryptorandom.cryptorandom import SHA256
import math
import numpy as np
from scipy import stats
import consistent_sampler
import operator
from audits.audit import RiskLimitingAudit
from audits.bravo import Bravo

class Sampler:

    audit: RiskLimitingAudit

    def __init__(self, audit_type, seed, risk_limit, contests):
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
        self.contests = contests
        self.margins = self.compute_margins()

        if audit_type == 'BRAVO':
            self.audit = Bravo(risk_limit)

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
                            if cand not in ['numWinners', 'ballots']
                    ], 
            key=operator.itemgetter(1), reverse = True)

            if 'numWinners' not in self.contests[contest]:
                num_winners = 1
            else:
                num_winners = self.contests[contest]['numWinners']
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
        return self.audit.get_sample_sizes(contests=self.contests, margins=self.margins, sample_results=sample_results)

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
            measurements    - the p-value of the hypotheses that the election
                              result is correct based on the sample, for each winner-loser pair. 
            confirmed       - a boolean indicating whether the audit can stop
        """
        return self.audit.compute_risk(self.margins[contest], sample_results)

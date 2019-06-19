# Handles generating sample sizes and taking samples
from cryptorandom.cryptorandom import SHA256
import math


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
                                'ballots': ballots # total ballots cast
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
                                'ballots': ballots
                            }
                            ...
                        }
        Output:
            margins - dictionary of diluted margin info:
                        {
                            contest: {
                                'p_w': p_w # The proportion of votes for winner
                                'p_r': p_r # proportion of votes for runner up
                                
                            }
                        }

        """

        margins = {}
        for contest in self.contests:
            winner = ''
            win_votes = 0
            runner_up = ''
            rup_votes = 0

            ballots = self.contests[contest]['ballots']

            # Find the winner and runner up
            for cand in self.contests[contest]:
                if cand == 'ballots':
                    continue
                
                votes = self.contests[contest][cand]
                if votes > win_votes:
                    runner_up = winner
                    rup_votes = win_votes

                    winner = cand
                    win_votes = votes
                elif votes > rup_votes:
                    runner_up = cand
                    rup_votes = votes

            # Find the diluted margins and margin of valid votes for winner
            v_wl = win_votes + rup_votes
            margins[contest] = {
                'p_w': win_votes/v_wl,
                'p_r': rup_votes/v_wl,
                's_w': win_votes/ballots,
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
        margins = self.compute_margins()
        for contest in self.contests:
            p_w = margins[contest]['p_w']
            p_r = margins[contest]['p_r']
            s_w = margins[contest]['s_w']

            if p_w == 1:
                # Handle single-candidate or crazy landslides
                asns[contest] = 0
            else: 
                z_w = math.log(2 * s_w)
                z_l = math.log(2 - 2 * s_w)
                asns[contest] = math.ceil((math.log(1/self.risk_limit) + (z_w / 2)) / ((p_w * z_w) + (p_r * z_l)))

        return asns
    

    
    def get_sample_sizes(self):
        """
        Computes initial sample sizes parameterized by likelihood that the
        initial sample will confirm the election result, assuming no
        discrpancies.

        Inputs:
            None
            TODO: could take in likelihood parameters instead of hardcoding

        Outputs:
            samples - dictionary mapping confirmation likelihood to sample size:
                        { 
                            likelihood1: sample_size,
                            likelihood2: sample_size,
                            ...
                        }
        """


    def draw_sample(self, manifest, sample_size):
        """
        Draws uniform random sample with replacement of size <sample_size> from the
        provided ballot manifest.

        Inputs:
            sample_size: number of ballots to randomly draw
            manifest - mapping of batches to the ballots they contain:
                        { 
                            batch1: num_balots,
                            batch2: num_ballots,
                            ...
                        }
                    
        Outputs:
            sample - list of <batch>-<ballot number> pairs to sample, with duplicates
                    [   
                        batch1: ballot1,
                        batch2: ballot49,
                        ...
                    ]

        """

        # TODO: Use Rivest's consistent-sampler


    def compute_risk(self, contest, sample_results):
        """
        Computes the risk-value of <sample_results> based on results in <contest>.

        Inputs: 
            contest - the name of the contest that is targeted
            sample_results - mapping of candidates to votes in the sample:
                    {
                        candidate1: sampled_votes,
                        candidate2: sampled_votes,
                        ...
                    }

        Outputs:
            risk - the p-value of the hypotheses that the election result is 
                   correct based on the sample. 
        """
        
        # TODO: also a risk-calculation






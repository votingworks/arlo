# Handles generating sample sizes and taking samples
from cryptorandom.cryptorandom import SHA256


class Sampler:
    def __init__(self, seed, risk_limit, contests):
        """
        Initializes PRNG, computes margins, and returns initial sample
        sizes parameterized by likelihood that the initial sample will confirm the
        election result, assuming no discrpancies.

        Inputs:
            seed - seed used to initialized random functions
            risk_limit - the risk-limit to compute sample sizes from
            contest - dictionary of targeted contests. Maps:
                        {
                            contest: {
                                candidate1: votes,
                                candidate2: votes,
                                ...
                            }
                            ...
                        }

        Outputs:
        """
        self.seed = seed
        self.prng = SHA256(seed)
        self.risk_limit = risk_limit
        self.contests = contests

    
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
            risk - the risk-calculation of the election result based on the sample
        """







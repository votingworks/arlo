# Handles generating sample sizes and taking samples
from cryptorandom.cryptorandom import SHA256
import math
import numpy as np
from scipy import stats
import consistent_sampler
from joblib import Parallel, delayed
import multiprocessing


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
        self.num_cores =  multiprocessing.cpu_count()

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
                                's_w': s_w # the proportion of total ballots for the winner
                                'winner': winner # the name of the winner
                                'runner_up': runner_up # name of the runner up
                                
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
                'winner': winner,
                'runner_up': runner_up
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
            else: 
                z_w = math.log(2 * s_w)
                z_l = math.log(2 - 2 * s_w)
                asns[contest] = math.ceil((math.log(1/self.risk_limit) + (z_w / 2)) / ((p_w * z_w) + (p_r * z_l)))

        return asns


    def simulate_bravo(self, num_ballots, p_w, sample_w, sample_r, iterations=10000):
        """
        Runs <iterations> trials of random elections with <num_ballots> ballots
        for contest with diluted margin p_w. Returns sample sizes of all trials.

        Input:
            num_ballots - the number of ballots in the contest
            p_w         - the fraction of vote share for the winner 
            sample_w    - the number of votes for the winner that have already 
                          been sampled
            sample_r    - the number of votes for the runner-up that have 
                          already been sampled
            iterations  - the number of trials to run

        Output:
            trials      - an array of sample sizes
        """
        # TODO We should probably be using more like 10**7 iterations


        return Parallel(n_jobs=self.num_cores)(delayed(run_bravo_trial)(self.prng.randint(0, 2**32, 1)[0], p_w, num_ballots, sample_w, sample_r, self.risk_limit) \
                    for i in range(iterations))

    
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
                    'size':0,
                    'prob': '0%'
                }
                for quant in quants:
                    quant_str = str(int(100*quant)) + '%'
                    samples[contest][quant_str] = 0 

                continue

            p_w = self.margins[contest]['p_w']
            num_ballots = self.contests[contest]['ballots']

            sample_w = sample_results[contest][winner]
            sample_r = sample_results[contest][runner_up]
           
            # TODO is there a way to do this that isn't simulation?
            trials = sorted(self.simulate_bravo(num_ballots, p_w, sample_w, sample_r))
            
            for i, n in enumerate(trials):
                if n > asns[contest]:
                    samples[contest]['asn'] = {
                        'size': asns[contest],
                        'prob': str(int(100*float(i/len(trials))))+ '%'
                    }
                    break
            #samples[contest]['asn'] = asns[contest]   
            for quant in quants: 
                quant_str = str(int(100*quant)) + '%'
                samples[contest][quant_str] = np.quantile(trials, quant)

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



def run_bravo_trial(seed, p_w, num_ballots, sample_w, sample_r, risk_limit):
    """
    A paralellizable trial function for bravo simulations
    """
    # This is a hack for efficient sample generation w/ repeatability 
    np.random.seed(seed)

    # Start our test-statistic based on previously audited stuff
    test = ((2*p_w)**sample_w)*((2 - 2*p_w)**sample_r)
    c_samp = 0
    votes = stats.binom.rvs(1, p_w, size=num_ballots)

    for vote in votes:
        if test >= 1/risk_limit:
            break
        if vote:
            test = test*p_w/.5
        else:
            test = test*(1 - p_w)/.5

        c_samp += 1

    return c_samp

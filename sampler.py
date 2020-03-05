# Handles generating sample sizes and taking samples
import math
import numpy as np
from scipy import stats
import consistent_sampler
import operator

import audits.macro as macro


def draw_sample(seed, contest, manifest, sample_size, num_sampled=0, batch_results=None):
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
        sample - list of 'tickets', consisting of:
                [
                    (
                        '0.235789114', # ticket number
                        (<batch>, <ballot number>), # id, here a tuple (batch, ballot)
                        1                           # number of times this item has been picked
                    ),
                    ...
                ]
    """

    ballots = []
    # First build a faux list of ballots
    for batch in manifest:
        for i in range(manifest[batch]):
            ballots.append((batch, i))

    return list(
        consistent_sampler.sampler(ballots,
                                   seed=seed,
                                   take=sample_size + num_sampled,
                                   with_replacement=True,
                                   output='tuple'))[num_sampled:]


def draw_ppeb_sample(seed, contest, manifest, sample_size, num_sampled=0, batch_results=None):
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
        sample - list of 'tickets', consisting of:
                [
                    (
                        '0.235789114', # ticket number
                        (<batch>, <ballot number>), # id, here a tuple (batch, ballot)
                        1                           # number of times this item has been picked
                    ),
                    ...
                ]
    """

    # Here we do PPEB.
    margins = contest.margins

    assert batch_results, 'Must have batch-level results to use MACRO'

    U = macro.compute_U(batch_results, contest)

    # Map each batch to its weighted probability of being picked
    batch_to_prob = {}
    min_prob = 1
    # Get u_ps
    for batch in batch_results:
        error = macro.compute_max_error(batch_results[batch], contest)

        # Probability of being picked is directly related to how much this
        # batch contributes to the overall possible error
        batch_to_prob[batch] = error / U

        if error / U < min_prob:
            min_prob = error / U

    sample_from = []
    # Now build faux list of batches, where each batch appears a number of
    # times proportional to its prob
    for batch in batch_to_prob:
        times = int(batch_to_prob[batch] / min_prob)

        for i in range(times):
            # We have to create "unique" records for the sampler, so we add
            # a '.n' to the batch name so we know which duplicate it is.
            sample_from.append('{}.{}'.format(batch, i))

    # Now draw the sample
    faux_sample = list(
        consistent_sampler.sampler(sample_from,
                                   seed=seed,
                                   take=sample_size + num_sampled,
                                   with_replacement=True,
                                   output='tuple'))[num_sampled:]

    # here we take off the decimals.
    sample = []
    for i in faux_sample:
        sample.append((i[0], i[1].split('.')[0], i[2]))

    return sample

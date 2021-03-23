# pylint: disable=invalid-name
# Handles generating sample sizes and taking samples
from typing import cast, Any, Dict, List, Tuple
from decimal import Decimal
import consistent_sampler

from . import macro
from .sampler_contest import Contest


def draw_sample(
    seed: str,
    manifest: Dict[Any, List[int]],
    sample_size: int,
    num_sampled: int = 0,
    with_replacement: bool = True,
) -> List[Tuple[str, Tuple[Any, int], int]]:
    """
    Draws uniform random sample with replacement of size <sample_size> from the
    provided ballot manifest.

    Inputs:
        seed - random seed
        manifest - mapping of batches to the ballots they contain:
                    {
                        batch1: num_balots,
                        batch2: num_ballots,
                        ...
                    }
        sample_size - number of tickets to randomly draw
        num_sampled - number of tickets that have already been sampled

    Outputs:
        sample - list of 'tickets', consisting of:
                [
                    (
                        '0.235789114',              # ticket number
                        (<batch>, <ballot number>), # id, here a tuple (batch, ballot)
                        1                           # number of times this item has been picked
                    ),
                    ...
                ]
    """

    # First build a list of ballots
    ballots: List[Tuple[Any, int]] = [
        (batch, ballot_position)
        for batch, ballot_positions in manifest.items()
        for ballot_position in ballot_positions
    ]

    return cast(
        # The signature of `consistent_sampler.sampler` can't be represented by
        # mypy yet, so it is typed as a less specific version of what it really
        # is. This casts it back to the more specific version.
        List[Tuple[str, Tuple[Any, int], int]],
        list(
            consistent_sampler.sampler(
                ballots,
                seed=seed,
                take=sample_size + num_sampled,
                with_replacement=with_replacement,
                output="tuple",
                digits=18,
            )
        )[num_sampled:],
    )


def draw_ppeb_sample(
    seed: str,
    contest: Contest,
    sample_size: int,
    num_sampled: int,
    batch_results: Dict[Any, Dict[str, Dict[str, int]]],
) -> List[Tuple[str, Tuple[str, int], int]]:
    """
    Draws sample with replacement of size <sample_size> from the
    provided ballot manifest using proportional-with-error-bound (PPEB) sampling.
    PPEB was developed by Aslam, Popa and Rivest here: https://www.usenix.org/legacy/event/evt08/tech/full_papers/aslam/aslam.pdf
    Stark further applied PPEB to batch audits here: https://www.stat.berkeley.edu/~stark/Preprints/ppebwrwd08.pdf
    For use with batch audits like MACRO.

    Inputs:
        seed    - the random seed to use in sampling
        sample_size - number of ballots to randomly draw
        num_sampled - number of ballots that have already been sampled
        batch_results - the result of the election, per batch:
                        {
                            'batch': {
                                'contest': {
                                    'cand1': votes,
                                    ...
                                }
                            }
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

    assert batch_results, "Must have batch-level results to use MACRO"

    U = macro.compute_U(batch_results, {}, contest)

    # This can only be the case if we've already recounted
    if U == 0:
        return []

    # Map each batch to its weighted probability of being picked
    batch_to_prob: Dict[str, Decimal] = {}
    min_prob = Decimal(1.0)
    # Get u_ps
    for batch in batch_results:
        error = macro.compute_max_error(batch_results[batch], contest)

        # Set a floor on the error so it can't go to 0
        if error == 0:
            error = Decimal(1) / Decimal(contest.ballots)

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
            # a 'n' to the batch name so we know which duplicate it is.
            sample_from.append((batch, i))

    # Now draw the sample
    faux_sample = list(
        consistent_sampler.sampler(
            sample_from,
            seed=seed,
            take=sample_size + num_sampled,
            with_replacement=True,
            output="tuple",
        )
    )[num_sampled:]

    # here we take off the decimals.
    sample = []
    for item in faux_sample:
        sample.append((item[0], item[1][0], item[2]))

    return sample

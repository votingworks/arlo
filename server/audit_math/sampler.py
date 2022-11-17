# pylint: disable=invalid-name
# Handles generating sample sizes and taking samples
from typing import cast, Any, Dict, List, Tuple
from numpy.random import default_rng
import consistent_sampler

from . import macro
from .sampler_contest import Contest


BatchKey = Tuple[str, str]  # (jurisdiction name, batch name)


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
    previously_sampled_batch_keys: List[BatchKey],
    batch_results: Dict[BatchKey, Dict[str, Dict[str, int]]],
) -> List[Tuple[Any, BatchKey]]:
    """
    Draws sample with replacement of size <sample_size> from the
    provided ballot manifest using proportional-with-error-bound (PPEB) sampling.
    PPEB was developed by Aslam, Popa and Rivest here: https://www.usenix.org/legacy/event/evt08/tech/full_papers/aslam/aslam.pdf
    Stark further applied PPEB to batch audits here: https://www.stat.berkeley.edu/~stark/Preprints/ppebwrwd08.pdf
    For use with batch audits like MACRO.

    Inputs:
        seed    - the random seed to use in sampling
        sample_size - number of ballots to randomly draw
        previously_sampled_batch_keys - the keys (jurisdiction name, batch name) of batches sampled
            in previous rounds
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
                    ),
                    ...
                ]
    """

    assert batch_results, "Must have batch-level results to use MACRO"

    # Convert seed into something numpy can use
    int_seed = int(consistent_sampler.sha256_hex(seed), 16)  # type: ignore
    generator = default_rng(int_seed)

    U = macro.compute_U(batch_results, cast(Dict, {}), contest)

    # Should only be possible if the specified contest isn't in any batches
    if U == 0:
        return []

    # Map each batch to its weighted probability of being picked
    weighted_errors = [
        float(macro.compute_max_error(batch_results[batch], contest) / U)
        for batch in batch_results
    ]

    is_full_hand_tally = sample_size >= len(batch_results)
    num_previously_sampled_batches = len(previously_sampled_batch_keys)

    sampled_batch_keys_including_previously_sampled: List[BatchKey] = (
        (
            previously_sampled_batch_keys
            # When the sample size indicates a full hand tally, ensure that we draw all batches,
            # minus batches already audited in previous rounds
            + sorted(list(batch_results.keys() - previously_sampled_batch_keys))
        )
        if is_full_hand_tally
        # Otherwise, sample as usual
        else cast(
            List[BatchKey],
            (
                tuple(sampled_batch_key)
                for sampled_batch_key in generator.choice(
                    list(batch_results.keys()),
                    num_previously_sampled_batches + sample_size,
                    p=weighted_errors,
                    replace=True,
                )
            ),
        )
    )

    # Now create "ticket numbers" for each item in the sample

    # Map seen batches to counts
    counts: Dict[Any, int] = {}
    tickets: Dict[Any, List[str]] = {}

    sampled_batch_keys_including_previously_sampled_with_ticket_numbers: List[
        Tuple[Any, BatchKey]
    ] = []

    for batch_key in sampled_batch_keys_including_previously_sampled:
        count = counts.get(batch_key, 0) + 1

        ticket = (
            consistent_sampler.first_fraction(batch_key, seed)  # type: ignore
            if count == 1
            else consistent_sampler.next_fraction(tickets.get(batch_key)[-1])  # type: ignore
        )

        # Trim the ticket number
        ticket = consistent_sampler.trim(ticket, 18)  # type: ignore

        sampled_batch_keys_including_previously_sampled_with_ticket_numbers.append(
            (ticket, batch_key)
        )
        counts[batch_key] = count

        if batch_key in tickets:
            tickets[batch_key].append(ticket)
        else:
            tickets[batch_key] = [ticket]

    return sampled_batch_keys_including_previously_sampled_with_ticket_numbers[
        num_previously_sampled_batches:
    ]

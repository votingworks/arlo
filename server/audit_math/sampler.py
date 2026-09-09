# Handles generating sample sizes and taking samples
from typing import cast, Any
import numpy as np
from numpy.random import default_rng
import consistent_sampler

from . import macro
from .sampler_contest import Contest


BatchKey = tuple[str, str]  # (jurisdiction name, batch name)


def draw_sample(
    seed: str,
    manifest: dict[Any, list[int]],
    sample_size: int,
    num_sampled: int = 0,
    with_replacement: bool = True,
) -> list[tuple[str, tuple[Any, int], int]]:
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
    ballots: list[tuple[Any, int]] = [
        (batch, ballot_position)
        for batch, ballot_positions in manifest.items()
        for ballot_position in ballot_positions
    ]

    return cast(
        # The signature of `consistent_sampler.sampler` can't be represented by
        # mypy yet, so it is typed as a less specific version of what it really
        # is. This casts it back to the more specific version.
        list[tuple[str, tuple[Any, int], int]],
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


# Where a draw landed on the PPEB "ruler": the index of the batch whose
# probability slice contains the uniform draw, and how far into that slice it
# fell. The offset is uniform on [0, weight of that batch).
PpebPosition = tuple[int, float]


def ppeb_weights(
    contest: Contest,
    batch_results: dict[BatchKey, dict[str, dict[str, int]]],
    batch_keys: list[BatchKey],
) -> list[float]:
    U = macro.compute_U(batch_results, contest)
    if U == 0:
        return [0.0] * len(batch_keys)
    unauditable_ballots = macro.compute_unauditable_ballots(batch_results, contest)
    return [
        float(
            macro.compute_max_error(
                batch_results.get(batch_key, {}), contest, unauditable_ballots
            )
            / U
        )
        for batch_key in batch_keys
    ]


def draw_ppeb_positions(
    seed: str, weights: list[float], num_draws: int
) -> list[PpebPosition]:
    int_seed = int(consistent_sampler.sha256_hex(seed), 16)  # type: ignore
    generator = default_rng(int_seed)
    # Mirror numpy's Generator.choice(p=weights) step for step so the batches
    # drawn are identical to what it produced before we tracked offsets.
    cdf = np.cumsum(weights)
    cdf /= cdf[-1]
    uniforms = generator.random(num_draws)
    indexes = cdf.searchsorted(uniforms, side="right")
    slice_starts = np.concatenate(([0.0], cdf[:-1]))
    return [
        (int(index), float(uniform - slice_starts[index]))
        for index, uniform in zip(indexes, uniforms)
    ]


def full_hand_tally_batch_keys(
    previously_sampled_batch_keys: list[BatchKey],
    batch_results: dict[BatchKey, dict[str, dict[str, int]]],
) -> list[BatchKey]:
    return previously_sampled_batch_keys + sorted(
        batch_results.keys() - previously_sampled_batch_keys
    )


def assign_ticket_numbers(
    seed: str, batch_keys: list[BatchKey]
) -> list[tuple[str, BatchKey]]:
    tickets: dict[BatchKey, list[str]] = {}
    batch_keys_with_ticket_numbers: list[tuple[str, BatchKey]] = []
    for batch_key in batch_keys:
        ticket: str = consistent_sampler.trim(  # type: ignore
            consistent_sampler.next_fraction(tickets[batch_key][-1])  # type: ignore
            if batch_key in tickets
            else consistent_sampler.first_fraction(batch_key, seed),  # type: ignore
            18,
        )
        batch_keys_with_ticket_numbers.append((ticket, batch_key))
        tickets.setdefault(batch_key, []).append(ticket)
    return batch_keys_with_ticket_numbers


def draw_ppeb_sample(
    seed: str,
    contest: Contest,
    sample_size: int,
    previously_sampled_batch_keys: list[BatchKey],
    batch_results: dict[BatchKey, dict[str, dict[str, int]]],
) -> list[tuple[Any, BatchKey]]:
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

    # Sort batch keys so that the sampling is independent of the uploaded file's ordering
    batch_keys = sorted(batch_results.keys())
    weights = ppeb_weights(contest, batch_results, batch_keys)
    # Should only be possible if the specified contest isn't in any batches
    if not any(weights):
        return []

    num_previously_sampled_batches = len(previously_sampled_batch_keys)
    cumulative_sample_size = num_previously_sampled_batches + sample_size
    if cumulative_sample_size >= len(batch_results):
        sampled_batch_keys = full_hand_tally_batch_keys(
            previously_sampled_batch_keys, batch_results
        )
    else:
        positions = draw_ppeb_positions(seed, weights, cumulative_sample_size)
        sampled_batch_keys = [batch_keys[index] for index, _ in positions]

    return assign_ticket_numbers(seed, sampled_batch_keys)[
        num_previously_sampled_batches:
    ]

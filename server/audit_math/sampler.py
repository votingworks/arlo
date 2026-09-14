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


def ppeb_weights(
    contest: Contest,
    batch_results: dict[BatchKey, dict[str, dict[str, int]]],
    batch_keys: list[BatchKey],
) -> list[float]:
    U = macro.compute_U(batch_results, contest)
    if U == 0:
        return [0.0] * len(batch_keys)

    # Map each batch to its weighted probability of being picked
    unauditable_ballots = macro.compute_unauditable_ballots(batch_results, contest)
    return [
        float(
            macro.compute_max_error(batch_results[batch], contest, unauditable_ballots)
            / U
        )
        for batch in batch_keys
    ]


def draw_ppeb_positions(
    seed: str, weights: list[float], sample_size: int
) -> tuple[np.ndarray, np.ndarray]:
    # Convert seed into something numpy can use
    int_seed = int(consistent_sampler.sha256_hex(seed), 16)  # type: ignore
    generator = default_rng(int_seed)
    # Mirror numpy's Generator.choice(p=weights) step for step so the batches
    # drawn are identical to what it produced.
    # https://github.com/numpy/numpy/blob/v1.26.4/numpy/random/_generator.pyx#L841-L846
    #
    # cdf is the running total of probabilities, used to determine which batch
    # each random draw falls into, giving each batch a range.
    # The intuition is that cdf[i] - cdf[i-1] is the probability of selecting
    # batch i, aside from when i=0, then it is just cdf[0].
    cdf = np.cumsum(weights)
    cdf /= cdf[-1]
    # Pull the draws. Each draw is represented by a random number in [0, 1)
    random_draws = generator.random(sample_size)
    # Each random number maps to the batch whose range it falls in
    sampled_batch_indexes = cdf.searchsorted(random_draws, side="right")
    # For each sampled batch, find the start of its range. This is used to
    # compute the offset of the random number into the batch's range.
    sampled_range_starts = [
        cdf[index - 1] if index > 0 else 0.0 for index in sampled_batch_indexes
    ]
    # A draw's offset is how far into its batch's range the random number fell,
    # which is required in the nesting step to determine whether the child
    # contest can reuse the parent draw or needs to redirect it.
    offsets = random_draws - np.array(sampled_range_starts)
    return sampled_batch_indexes, offsets


def selection_probabilities(weights: list[float]) -> np.ndarray:
    # Normalized exactly as draw_ppeb_positions normalizes its cumulative
    # vector, so an offset from one contest's draw can be compared against
    # another contest's selection probabilities
    cdf = np.cumsum(weights)
    cdf /= cdf[-1]
    return np.diff(cdf, prepend=0.0)


def nest_ppeb_positions(
    parent_batch_indexes: np.ndarray,
    parent_offsets: np.ndarray,
    parent_weights: list[float],
    child_weights: list[float],
) -> tuple[np.ndarray, np.ndarray]:
    """
    Derives a child contest's PPEB draws from a parent contest's, so that the
    child reuses the parent's batches as often as possible while every batch
    keeps exactly its own selection probability for the child.

    This relies on one fact about offsets: a draw's offset is equally likely to
    fall anywhere in its batch's range, from 0 up to the batch's selection
    probability.

    Each parent draw becomes one child draw. Suppose the two contests have
    these selection probabilities:

                    parent    child
        Batch 1       0.50     0.30
        Batch 2       0.30     0.30
        Batch 3       0.20     0.40

    - Parent draws Batch 2 at offset 0.17. That fits under the child's 0.30,
      so the child reuses Batch 2, keeping the same offset.
    - Parent draws Batch 3. Its offset is always under 0.20, so the child
      always reuses Batch 3. But that alone selects Batch 3 for the child only
      20% of the time, and it needs 40%.
    - Parent draws Batch 1 at offset 0.42. That doesn't fit under 0.30, so
      the draw "falls through" and is redirected to a batch where the child's
      probability exceeds the parent's, in proportion to that excess
      (max(0, child - parent), here 0.20 for Batch 3 and 0 elsewhere). Batch 1
      falls through 20% of the time, exactly the 20% Batch 3 was short.

    In general, reuse gives each batch min(parent, child); the total
    fall-through probability equals the total excess because both vectors sum
    to 1; and redirecting in proportion to excess tops each batch up to exactly
    its child probability. Each child draw depends only on its own parent
    draw, so the child's draws remain independent of one another.
    """
    parent_p = selection_probabilities(parent_weights)
    child_p = selection_probabilities(child_weights)
    excess = np.maximum(0.0, child_p - parent_p)
    cumulative_excess = np.cumsum(excess)
    base_excess = np.concatenate(([0.0], cumulative_excess[:-1]))
    total_excess = cumulative_excess[-1]

    child_batch_indexes = []
    child_offsets = []
    for batch_index, offset in zip(parent_batch_indexes, parent_offsets):
        if offset < child_p[batch_index] or total_excess == 0:
            child_batch_indexes.append(batch_index)
            child_offsets.append(offset)
            continue
        # Given that the draw fell through, its offset is uniform on
        # [child_p, parent_p), so rescaling it onto [0, total_excess) picks the
        # redirect target without drawing any new randomness
        redirect_p = (
            (offset - child_p[batch_index])
            / (parent_p[batch_index] - child_p[batch_index])
            * total_excess
        )
        target = min(
            int(cumulative_excess.searchsorted(redirect_p, side="right")),
            len(excess) - 1,
        )
        # Place the redirected offset in [parent_p, child_p) of the target
        # batch. Reused draws of that batch have offsets in [0, parent_p), so
        # together the child's offsets stay uniform on [0, child_p) and the
        # child can in turn be a parent.
        child_batch_indexes.append(target)
        child_offsets.append(parent_p[target] + redirect_p - base_excess[target])
    return np.array(child_batch_indexes, dtype=int), np.array(
        child_offsets, dtype=float
    )


def full_hand_tally_batch_keys(
    previously_sampled_batch_keys: list[BatchKey],
    batch_results: dict[BatchKey, dict[str, dict[str, int]]],
) -> list[BatchKey]:
    # When the cumulative sample size indicates that a full hand tally is needed, ensure
    # that we draw all batches, minus batches already audited in previous rounds
    return previously_sampled_batch_keys + sorted(
        list(batch_results.keys() - previously_sampled_batch_keys)
    )


def assign_ticket_numbers(
    seed: str, batch_keys: list[BatchKey]
) -> list[tuple[Any, BatchKey]]:
    # Map seen batches to counts
    counts: dict[Any, int] = {}
    tickets: dict[Any, list[str]] = {}

    batch_keys_with_ticket_numbers: list[tuple[Any, BatchKey]] = []

    for batch_key in batch_keys:
        count = counts.get(batch_key, 0) + 1

        ticket = (
            consistent_sampler.first_fraction(batch_key, seed)  # type: ignore
            if count == 1
            else consistent_sampler.next_fraction(tickets.get(batch_key)[-1])  # type: ignore
        )

        # Trim the ticket number
        ticket = consistent_sampler.trim(ticket, 18)  # type: ignore

        batch_keys_with_ticket_numbers.append((ticket, batch_key))
        counts[batch_key] = count

        if batch_key in tickets:
            tickets[batch_key].append(ticket)
        else:
            tickets[batch_key] = [ticket]

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

    weighted_errors = ppeb_weights(contest, batch_results, batch_keys)
    # Should only be possible if the specified contest isn't in any batches
    if not any(weighted_errors):
        return []

    num_previously_sampled_batches = len(previously_sampled_batch_keys)
    cumulative_sample_size = num_previously_sampled_batches + sample_size
    is_full_hand_tally_needed = cumulative_sample_size >= len(batch_results)

    sampled_batch_keys_including_previously_sampled: list[BatchKey]
    if is_full_hand_tally_needed:
        sampled_batch_keys_including_previously_sampled = full_hand_tally_batch_keys(
            previously_sampled_batch_keys, batch_results
        )
    else:
        # Otherwise, sample as usual
        batch_indexes, _ = draw_ppeb_positions(
            seed, weighted_errors, cumulative_sample_size
        )
        sampled_batch_keys_including_previously_sampled = [
            batch_keys[index] for index in batch_indexes
        ]

    return assign_ticket_numbers(seed, sampled_batch_keys_including_previously_sampled)[
        num_previously_sampled_batches:
    ]

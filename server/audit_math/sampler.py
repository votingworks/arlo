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
) -> tuple[list[int], list[float]]:
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
    return sampled_batch_indexes.tolist(), offsets.tolist()


def draw_nested_ppeb_positions(
    parent_sampled_batch_indexes: list[int],
    parent_offsets: list[float],
    parent_weights: list[float],
    child_weights: list[float],
) -> tuple[list[int], list[float]]:
    """
    Derives a child contest's PPEB draws from a parent contest's, so that the
    child reuses the parent's batches as often as possible while every batch
    keeps its own selection probability for the child.

    Each parent draw becomes one child draw. Suppose the two contests have
    these selection probabilities:

                  parent  child  excess  cumulative_excess  base_excess
        Batch 1     0.40   0.30    0.00               0.00         0.00
        Batch 2     0.30   0.20    0.00               0.00         0.00
        Batch 3     0.15   0.25    0.10               0.10         0.00
        Batch 4     0.15   0.25    0.10               0.20         0.10

    - Parent draws Batch 1 at offset 0.12. That fits under the child's 0.30,
      so the child reuses Batch 1, keeping the same offset.
    - Parent draws Batch 3, which happens on 15% of draws. Its offset is
      always under 0.15, so it is also always under the child's 0.25, and the
      child reuses every one of those draws. But the child needs Batch 3 on
      25% of draws, and reuse alone can only give it the parent's 15%. The
      other 10% has to come from somewhere else. The same goes for Batch 4.
    - Parent draws Batch 1 at offset 0.33. That doesn't fit under 0.30, so the
      draw "falls through" and is redirected to a batch with excess. The offset
      overshoots the child's 0.30 by 0.03, which is 0.3 of the way through the
      0.10 overshoot the parent has over the child, so redirect_p is 0.3 of the
      total excess. The total excess is 0.20, so 0.3 * 0.20 = 0.06. That lands
      in Batch 3's excess range within cumulative_excess, so the child gets
      Batch 3 at offset 0.15 + 0.06 = 0.21.

    Reuse gives each batch min(parent, child). The total fall-through
    probability equals the total excess. Redirecting in proportion to excess
    therefore tops each batch up to exactly its child probability.
    """
    # excess[i] is the amount by which the child's probability for batch i
    # exceeds the parent's, or 0 if the parent is larger.
    excess = np.maximum(0.0, np.subtract(child_weights, parent_weights))
    # cumulative_excess is the parallel of cdf in the excess distribution, to
    # then be used for redirecting fall-through draws. If a fall-through draw
    # lands between cumulative_excess[i-1] and cumulative_excess[i], it gets
    # redirected to batch i.
    cumulative_excess = np.cumsum(excess)
    # base_excess shifts cumulative_excess by one position to the right, with 0
    # at the start, used to determine the offset for fall-through draws
    base_excess = np.concatenate(([0.0], cumulative_excess[:-1]))
    # total_excess is the sum of all individual excesses, i.e., the total
    # probability mass that needs to be redistributed
    total_excess = cumulative_excess[-1]

    child_sampled_batch_indexes = []
    child_offsets = []
    for batch_index, offset in zip(parent_sampled_batch_indexes, parent_offsets):
        if offset < child_weights[batch_index]:
            child_sampled_batch_indexes.append(batch_index)
            child_offsets.append(offset)
            continue
        # Given that the parent draw fell through, redirect it to a batch where
        # the child's probability exceeds the parent's
        overshoot = offset - child_weights[batch_index]
        overshoot_fraction = overshoot / (
            parent_weights[batch_index] - child_weights[batch_index]
        )
        redirect_p = overshoot_fraction * total_excess
        # The batch whose excess range redirect_p falls in, the same way a
        # random draw is matched to a batch in draw_ppeb_positions
        fall_through_sampled_batch_index = int(
            cumulative_excess.searchsorted(redirect_p, side="right")
        )
        # Rounding can push redirect_p to exactly total_excess, which would
        # point one past the last batch
        fall_through_sampled_batch_index = min(
            fall_through_sampled_batch_index, len(excess) - 1
        )
        fall_through_offset = redirect_p - base_excess[fall_through_sampled_batch_index]
        # Add the fall-through offset to the parent weight to get the child's
        # offset, needed if the child is also a parent
        child_sampled_batch_indexes.append(fall_through_sampled_batch_index)
        child_offsets.append(
            parent_weights[fall_through_sampled_batch_index] + fall_through_offset
        )
    return child_sampled_batch_indexes, child_offsets


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
    assert any(weighted_errors), (
        f"Contest {contest.name} has no results in any batch, so there is nothing"
        " to sample from"
    )

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

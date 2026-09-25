import random
import pytest
from ...audit_math import sampler
from ...audit_math.sampler_contest import Contest

SEED = "12345678901234567890abcdefghijklmnopqrstuvwxyz😊"
RISK_LIMIT = 0.1
CONTEST_NAME = "Contest"
CLOSE_CONTEST_NAME = "Close Contest"
OTHER_CONTEST_NAME = "Other Contest"


@pytest.fixture
def macro_batches():
    batches = {}

    # 10 batches will have max error of .08
    for i in range(10):
        batches[("Jx 1", "pct {}".format(i))] = {
            CONTEST_NAME: {"cand1": 40, "cand2": 10, "ballots": 50}
        }
        # 10 batches will have max error of .04
    for i in range(11, 20):
        batches[("Jx 1", "pct {}".format(i))] = {
            CONTEST_NAME: {"cand1": 20, "cand2": 30, "ballots": 50}
        }

    return batches


@pytest.fixture
def close_macro_batches():
    batches = {}

    batches[("Jx 1", "pct {}".format(1))] = {
        CLOSE_CONTEST_NAME: {"cand1": 100, "cand2": 0, "ballots": 100}
    }
    batches[("Jx 1", "pct {}".format(2))] = {
        CLOSE_CONTEST_NAME: {"cand1": 100, "cand2": 0, "ballots": 100}
    }
    batches[("Jx 1", "pct {}".format(3))] = {
        CLOSE_CONTEST_NAME: {"cand1": 0, "cand2": 100, "ballots": 100}
    }
    batches[("Jx 1", "pct {}".format(4))] = {
        CLOSE_CONTEST_NAME: {"cand1": 0, "cand2": 98, "ballots": 98}
    }
    return batches


@pytest.fixture
def macro_contest():
    name = CONTEST_NAME

    info_dict = {
        "cand1": 600,
        "cand2": 400,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    return Contest(name, info_dict)


@pytest.fixture
def close_macro_contest():
    name = CLOSE_CONTEST_NAME

    info_dict = {
        "cand1": 200,
        "cand2": 198,
        "ballots": 400,
        "numWinners": 1,
        "votesAllowed": 1,
    }

    return Contest(name, info_dict)


def test_draw_sample(snapshot):
    # Test getting a sample
    manifest = {
        "pct 1": list(range(1, 26)),
        "pct 2": list(range(1, 26)),
        "pct 3": list(range(1, 26)),
        "pct 4": list(range(1, 26)),
    }

    sample = sampler.draw_sample(SEED, manifest, 20, 0)
    snapshot.assert_match(sample)


def test_draw_more_samples(snapshot):
    # Test getting a sample
    manifest = {
        "pct 1": list(range(1, 26)),
        "pct 2": list(range(1, 26)),
        "pct 3": list(range(1, 26)),
        "pct 4": list(range(1, 26)),
    }

    sample = sampler.draw_sample(SEED, manifest, 10, 0)
    snapshot.assert_match(sample)

    sample = sampler.draw_sample(SEED, manifest, 10, num_sampled=10)
    snapshot.assert_match(sample)


def test_draw_macro_sample(macro_batches, macro_contest, snapshot):
    # Test getting a sample
    sample = sampler.draw_ppeb_sample(
        SEED,
        macro_contest,
        10,
        previously_sampled_batch_keys=[],
        batch_results=macro_batches,
    )
    snapshot.assert_match(sample)


def test_draw_more_macro_sample(macro_batches, macro_contest, snapshot):
    # Test getting a sample
    sample = sampler.draw_ppeb_sample(
        SEED,
        macro_contest,
        5,
        previously_sampled_batch_keys=[],
        batch_results=macro_batches,
    )
    snapshot.assert_match(sample)

    sample = sampler.draw_ppeb_sample(
        SEED,
        macro_contest,
        5,
        previously_sampled_batch_keys=[
            ("Jx 1", "pct8"),
            ("Jx 1", "pct6"),
            ("Jx 1", "pct8"),
            ("Jx 1", "pct0"),
            ("Jx 1", "pct9"),
        ],
        batch_results=macro_batches,
    )
    snapshot.assert_match(sample)


def test_draw_macro_full_hand_tally(close_macro_batches, close_macro_contest, snapshot):
    sample = sampler.draw_ppeb_sample(
        SEED,
        close_macro_contest,
        len(close_macro_batches),  # All batches
        previously_sampled_batch_keys=[],
        batch_results=close_macro_batches,
    )
    snapshot.assert_match(sample)

    sample = sampler.draw_ppeb_sample(
        SEED,
        close_macro_contest,
        len(close_macro_batches),  # All batches
        previously_sampled_batch_keys=[("Jx 1", "pct 1")],
        batch_results=close_macro_batches,
    )
    snapshot.assert_match(sample)

    sample = sampler.draw_ppeb_sample(
        SEED,
        close_macro_contest,
        len(close_macro_batches),  # All batches
        previously_sampled_batch_keys=[("Jx 1", "pct 2"), ("Jx 1", "pct 4")],
        batch_results=close_macro_batches,
    )
    snapshot.assert_match(sample)

    sample = sampler.draw_ppeb_sample(
        SEED,
        close_macro_contest,
        # The sample size is less than all batches, but the cumulative sample size is all batches
        len(close_macro_batches) - 2,
        previously_sampled_batch_keys=[("Jx 1", "pct 2"), ("Jx 1", "pct 4")],
        batch_results=close_macro_batches,
    )
    snapshot.assert_match(sample)


def test_draw_macro_multiple_contests(macro_batches, snapshot):
    info_dict = {
        "cand1": 400,
        "cand2": 100,
        "ballots": 500,
        "numWinners": 1,
        "votesAllowed": 1,
    }
    other_contest = Contest(OTHER_CONTEST_NAME, info_dict)

    for batch in macro_batches:
        pct = int(batch[1].split(" ")[-1])
        if pct < 10:
            macro_batches[batch][OTHER_CONTEST_NAME] = {
                "cand1": 40,
                "cand2": 10,
                "ballots": 50,
            }

    # By including a contest that isn't contained in every batch, those batches
    # will get a maximum possible error (U) of zero for that contest.
    sample = sampler.draw_ppeb_sample(
        SEED,
        other_contest,
        10,
        previously_sampled_batch_keys=[],
        batch_results=macro_batches,
    )
    snapshot.assert_match(sample)


def test_draw_macro_contest_not_in_any_batches(macro_batches):
    info_dict = {
        "cand1": 400,
        "cand2": 100,
        "ballots": 500,
        "numWinners": 1,
        "votesAllowed": 1,
    }
    other_contest = Contest(OTHER_CONTEST_NAME, info_dict)

    with pytest.raises(AssertionError, match="has no results in any batch"):
        _ = sampler.draw_ppeb_sample(
            SEED,
            other_contest,
            10,
            previously_sampled_batch_keys=[],
            batch_results=macro_batches,
        )


NESTED_PARENT_WEIGHTS = [0.40, 0.30, 0.15, 0.15]
NESTED_CHILD_WEIGHTS = [0.30, 0.20, 0.25, 0.25]


def test_draw_nested_ppeb_positions():
    child_sampled_batch_indexes, child_offsets = sampler.draw_nested_ppeb_positions(
        parent_sampled_batch_indexes=[0, 2, 0, 1],
        parent_offsets=[0.12, 0.07, 0.33, 0.27],
        parent_weights=NESTED_PARENT_WEIGHTS,
        child_weights=NESTED_CHILD_WEIGHTS,
    )
    # Batch 1 at 0.12 and Batch 3 at 0.07 fit under the child's weight and are
    # reused. Batch 1 at 0.33 overshoots the child's 0.30 by 0.03, i.e. 0.3 of
    # the parent's 0.10 overshoot, so redirect_p is 0.3 * 0.20 = 0.06, which
    # lands in Batch 3's excess range, at offset 0.15 + 0.06. Batch 2 at 0.27
    # overshoots by 0.07, i.e. 0.7 of the parent's 0.10 overshoot, so redirect_p
    # is 0.14, which lands 0.04 into Batch 4's excess range, at offset 0.15 +
    # 0.04.
    assert child_sampled_batch_indexes == [0, 2, 2, 3]
    assert child_offsets == pytest.approx([0.12, 0.07, 0.21, 0.19])


def batch_frequencies(sampled_batch_indexes: list[int], num_batches: int):
    return [
        sampled_batch_indexes.count(batch_index) / len(sampled_batch_indexes)
        for batch_index in range(num_batches)
    ]


def test_draw_nested_ppeb_positions_preserves_selection_probabilities():
    # The child has no weight in the first batch and the parent has none in the
    # last, so the child can only reach the last batch by falling through
    parent_weights = [0.30, 0.25, 0.20, 0.15, 0.10, 0.00]
    child_weights = [0.00, 0.20, 0.20, 0.25, 0.15, 0.20]
    grandchild_weights = [0.10, 0.10, 0.30, 0.20, 0.20, 0.10]
    sample_size = 100_000

    parent = sampler.draw_ppeb_positions(SEED, parent_weights, sample_size)
    child = sampler.draw_nested_ppeb_positions(*parent, parent_weights, child_weights)
    grandchild = sampler.draw_nested_ppeb_positions(
        *child, child_weights, grandchild_weights
    )

    for (sampled_batch_indexes, offsets), weights in [
        (child, child_weights),
        (grandchild, grandchild_weights),
    ]:
        assert len(sampled_batch_indexes) == len(offsets) == sample_size
        assert batch_frequencies(sampled_batch_indexes, len(weights)) == pytest.approx(
            weights, abs=0.01
        )
        assert all(
            0 <= offset < weights[batch_index]
            for batch_index, offset in zip(sampled_batch_indexes, offsets)
        )

    child_sampled_batch_indexes, _ = child
    assert 0 not in child_sampled_batch_indexes
    assert 5 in child_sampled_batch_indexes


def test_draw_nested_ppeb_positions_reuses_min_of_parent_and_child():
    parent_weights = [0.30, 0.25, 0.20, 0.15, 0.10, 0.00]
    child_weights = [0.00, 0.20, 0.20, 0.25, 0.15, 0.20]
    sample_size = 100_000

    parent_sampled_batch_indexes, parent_offsets = sampler.draw_ppeb_positions(
        SEED, parent_weights, sample_size
    )
    child_sampled_batch_indexes, _ = sampler.draw_nested_ppeb_positions(
        parent_sampled_batch_indexes, parent_offsets, parent_weights, child_weights
    )

    reused = sum(
        parent_batch_index == child_batch_index
        for parent_batch_index, child_batch_index in zip(
            parent_sampled_batch_indexes, child_sampled_batch_indexes
        )
    )
    # A draw is reused with probability min(parent, child) for its batch, which
    # is the most reuse any method could achieve
    expected_reuse = sum(
        min(parent_weight, child_weight)
        for parent_weight, child_weight in zip(parent_weights, child_weights)
    )
    assert reused / sample_size == pytest.approx(expected_reuse, abs=0.01)


def test_draw_nested_ppeb_positions_identical_weights_reuse_every_draw():
    parent = sampler.draw_ppeb_positions(SEED, NESTED_PARENT_WEIGHTS, 1000)
    assert (
        sampler.draw_nested_ppeb_positions(
            *parent, NESTED_PARENT_WEIGHTS, NESTED_PARENT_WEIGHTS
        )
        == parent
    )


BatchResults = dict[sampler.BatchKey, dict[str, dict[str, int]]]

OTHER_CONTEST_INFO = {
    "cand1": 400,
    "cand2": 100,
    "ballots": 500,
    "numWinners": 1,
    "votesAllowed": 1,
}


@pytest.fixture
def other_contest() -> Contest:
    return Contest(OTHER_CONTEST_NAME, OTHER_CONTEST_INFO)


# The other contest is only in the first ten batches, like a contest that is
# only on the ballot in some jurisdictions
@pytest.fixture
def other_contest_batches(macro_batches: BatchResults) -> BatchResults:
    return {
        batch_key: {OTHER_CONTEST_NAME: {"cand1": 40, "cand2": 10, "ballots": 50}}
        for batch_key in macro_batches
        if int(batch_key[1].split(" ")[-1]) < 10
    }


def nested_spec(
    contest: Contest,
    sample_size: int,
    batch_results: BatchResults,
    nested_under_contest_id: str | None = None,
    previously_sampled_batch_keys: list[sampler.BatchKey] | None = None,
) -> sampler.ContestSampleSpec:
    return sampler.ContestSampleSpec(
        contest=contest,
        sample_size=sample_size,
        previously_sampled_batch_keys=previously_sampled_batch_keys or [],
        batch_results=batch_results,
        nested_under_contest_id=nested_under_contest_id,
    )


def test_draw_nested_ppeb_samples_root_is_unchanged_by_children(
    macro_batches: BatchResults,
    macro_contest: Contest,
    other_contest: Contest,
    other_contest_batches: BatchResults,
):
    samples = sampler.draw_nested_ppeb_samples(
        SEED,
        [
            nested_spec(macro_contest, 5, macro_batches),
            # A child with a bigger sample than its parent
            nested_spec(other_contest, 8, other_contest_batches, CONTEST_NAME),
        ],
    )
    assert samples[CONTEST_NAME] == sampler.draw_ppeb_sample(
        SEED, macro_contest, 5, [], macro_batches
    )
    assert len(samples[OTHER_CONTEST_NAME]) == 8
    assert all(
        batch_key in other_contest_batches
        for _, batch_key in samples[OTHER_CONTEST_NAME]
    )


def test_draw_nested_ppeb_samples_child_continues_after_parent_finishes(
    macro_batches: BatchResults,
    macro_contest: Contest,
    other_contest: Contest,
    other_contest_batches: BatchResults,
):
    round_1 = sampler.draw_nested_ppeb_samples(
        SEED,
        [
            nested_spec(macro_contest, 5, macro_batches),
            nested_spec(other_contest, 4, other_contest_batches, CONTEST_NAME),
        ],
    )
    # The parent met its risk limit, so it draws nothing new, but it still has
    # to be passed so the child's draws can be derived from it
    round_2 = sampler.draw_nested_ppeb_samples(
        SEED,
        [
            nested_spec(
                macro_contest,
                0,
                macro_batches,
                previously_sampled_batch_keys=[k for _, k in round_1[CONTEST_NAME]],
            ),
            nested_spec(
                other_contest,
                3,
                other_contest_batches,
                CONTEST_NAME,
                previously_sampled_batch_keys=[
                    k for _, k in round_1[OTHER_CONTEST_NAME]
                ],
            ),
        ],
    )
    assert round_2[CONTEST_NAME] == []
    all_at_once = sampler.draw_nested_ppeb_samples(
        SEED,
        [
            nested_spec(macro_contest, 5, macro_batches),
            nested_spec(other_contest, 7, other_contest_batches, CONTEST_NAME),
        ],
    )
    assert (
        round_1[OTHER_CONTEST_NAME] + round_2[OTHER_CONTEST_NAME]
        == all_at_once[OTHER_CONTEST_NAME]
    )


def test_draw_nested_ppeb_samples_full_hand_tally_is_per_contest(
    macro_batches: BatchResults,
    macro_contest: Contest,
    other_contest: Contest,
    other_contest_batches: BatchResults,
):
    samples = sampler.draw_nested_ppeb_samples(
        SEED,
        [
            nested_spec(macro_contest, 5, macro_batches),
            nested_spec(
                other_contest,
                len(other_contest_batches),
                other_contest_batches,
                CONTEST_NAME,
            ),
        ],
    )
    assert len(samples[CONTEST_NAME]) == 5
    assert [k for _, k in samples[OTHER_CONTEST_NAME]] == sorted(other_contest_batches)


def test_draw_nested_ppeb_samples_rejects_missing_parent_and_cycles(
    macro_batches: BatchResults,
    macro_contest: Contest,
    other_contest: Contest,
    other_contest_batches: BatchResults,
):
    with pytest.raises(AssertionError, match="not being sampled"):
        _ = sampler.draw_nested_ppeb_samples(
            SEED, [nested_spec(other_contest, 5, other_contest_batches, CONTEST_NAME)]
        )
    with pytest.raises(AssertionError, match="cycle"):
        _ = sampler.draw_nested_ppeb_samples(
            SEED,
            [
                nested_spec(macro_contest, 5, macro_batches, OTHER_CONTEST_NAME),
                nested_spec(other_contest, 5, other_contest_batches, CONTEST_NAME),
            ],
        )


def random_manifest():
    rand = random.Random(12345)
    return {
        f"pct {n}": list(range(1, rand.randint(2, 11)))
        for n in range(rand.randint(1, 10))
    }


def test_ballot_labels():
    for _ in range(100):
        manifest = random_manifest()
        sample = sampler.draw_sample(SEED, manifest, 100, 0)
        for _, (batch, ballot_number), _ in sample:
            assert 1 <= ballot_number <= max(manifest[batch])

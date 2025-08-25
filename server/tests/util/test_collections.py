from ...util.collections import (
    diff_file_lists_ignoring_order_and_case,
    find_first_duplicate,
    group_by,
)


def test_group_by():
    assert group_by([]) == {}
    assert group_by([{"a": 1}], lambda item: item["a"]) == {1: [{"a": 1}]}
    assert group_by([{"a": 1, "b": 1}, {"a": 1, "b": 2}], lambda item: item["a"]) == {
        1: [{"a": 1, "b": 1}, {"a": 1, "b": 2}],
    }
    assert group_by([{"a": 1, "b": 1}, {"a": 2, "b": 2}], lambda item: item["a"]) == {
        1: [{"a": 1, "b": 1}],
        2: [{"a": 2, "b": 2}],
    }
    assert group_by(
        [{"a": 1, "b": 1}, {"a": 2, "b": 2}, {"a": 1, "b": 3}], lambda item: item["a"]
    ) == {1: [{"a": 1, "b": 1}, {"a": 1, "b": 3}], 2: [{"a": 2, "b": 2}]}


def test_find_first_duplicate():
    assert find_first_duplicate([]) is None
    assert find_first_duplicate([1]) is None
    assert find_first_duplicate([1, 2, 3]) is None
    assert find_first_duplicate([1, 1]) == 1
    assert find_first_duplicate([1, 2, 1]) == 1
    assert find_first_duplicate([2, 1, 1, 2]) == 1
    assert find_first_duplicate(("a", "b", "a")) == "a"


def test_diff_file_lists_ignoring_order_and_case():
    assert diff_file_lists_ignoring_order_and_case([], []) == ([], [], [])
    assert diff_file_lists_ignoring_order_and_case(["a"], ["b"]) == ([], ["b"], ["a"])
    assert diff_file_lists_ignoring_order_and_case(["a"], ["a"]) == (["a"], [], [])
    assert diff_file_lists_ignoring_order_and_case(["a"], []) == ([], [], ["a"])

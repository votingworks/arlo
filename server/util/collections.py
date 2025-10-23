from typing import TypeVar
from collections.abc import Iterable
import itertools

T = TypeVar("T")


def group_by_iter(items: Iterable[T], key=None):
    return itertools.groupby(sorted(items, key=key), key=key)


# group_by groups items in a collection according to a key function.
def group_by(items: Iterable[T], key=None):
    return {k: list(vs) for k, vs in group_by_iter(items, key=key)}


# find_first_duplicate returns the first item in a collection that is a duplicate.
def find_first_duplicate(list: Iterable[T]) -> T | None:
    seen = set()
    for item in list:
        if item in seen:
            return item
        seen.add(item)
    return None


def diff_file_lists_ignoring_order_and_case(
    expected_files: list[str], actual_files: list[str]
) -> tuple[list[str], list[str], list[str]]:
    """Determine which files in `actual_files` are present in `expected_files`,
    which expected files are missing, and which are present in both. Uses a
    case-insensitive comparison of filenames and does not expect `actual_files`
    to be in `expected_files` order.

    The returned tuple is:
    1. The list of files in both lists, in the order of `expected_files`.
    2. The list of files in `actual_files` but not `expected_files`.
    3. The list of files in `expected_files` but not `actual_files`.
    """
    overlapping_files: list[str] = []
    unexpected_files = actual_files.copy()
    missing_files = expected_files.copy()

    for expected_file in expected_files:
        for actual_file in actual_files:
            if expected_file.casefold() == actual_file.casefold():
                overlapping_files.append(actual_file)
                unexpected_files.remove(actual_file)
                missing_files.remove(expected_file)
                break

    return (overlapping_files, unexpected_files, missing_files)

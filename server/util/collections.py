# pylint: disable=invalid-name
from typing import Optional, TypeVar, Iterable
import itertools

T = TypeVar("T")


def group_by_iter(items: Iterable[T], key=None):
    return itertools.groupby(sorted(items, key=key), key=key)


# group_by groups items in a collection according to a key function.
def group_by(items: Iterable[T], key=None):
    return {k: list(vs) for k, vs in group_by_iter(items, key=key)}


# find_first_duplicate returns the first item in a collection that is a duplicate.
def find_first_duplicate(list: Iterable[T]) -> Optional[T]:
    seen = set()
    for item in list:
        if item in seen:
            return item
        seen.add(item)
    return None

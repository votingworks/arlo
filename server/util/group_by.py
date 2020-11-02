from typing import TypeVar, Iterable
import itertools

T = TypeVar("T")  # pylint: disable=invalid-name


def group_by_iter(items: Iterable[T], key=None):
    return itertools.groupby(sorted(items, key=key), key=key)


def group_by(items: Iterable[T], key=None):
    return {k: list(vs) for k, vs in group_by_iter(items, key=key)}

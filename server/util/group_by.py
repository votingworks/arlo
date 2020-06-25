from typing import TypeVar, Iterable, Optional, Callable, Any
import itertools

T = TypeVar("T")  # pylint: disable=invalid-name


def group_by_iter(items: Iterable[T], key: Optional[Callable[[T], Any]] = None):
    return itertools.groupby(sorted(items, key=key), key=key)


def group_by(items: Iterable[T], key: Optional[Callable[[T], Any]] = None):
    return {k: list(vs) for k, vs in group_by_iter(items, key=key)}

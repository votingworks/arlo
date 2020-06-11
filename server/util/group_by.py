import itertools


def group_by_iter(items, key=None):
    return itertools.groupby(sorted(items, key=key), key=key)


def group_by(items, key=None):
    return {k: list(vs) for k, vs in group_by_iter(items, key=key)}

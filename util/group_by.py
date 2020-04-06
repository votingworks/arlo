import itertools


def group_by_iter(xs, key=None):
    return itertools.groupby(sorted(xs, key=key), key=key)


def group_by(xs, key=None):
    return {k: list(vs) for k, vs in group_by_iter(xs, key=key)}

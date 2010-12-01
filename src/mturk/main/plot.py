import itertools


def repair(data, is_anomaly):
    """Return iterator to repaired list of given data

    If any data is considered broken, remove it from the iterated list.

    `is_anomaly` should be function that takes 3 arguments (3 elements from
    given list) and return `True` if the second argument object is anomaly.

    This will never return first and last two items from the given list, but
    you shouldn't care for large amount of data anyway.
    """
    # zip 3 values from list sorder by indexes: [i, i+1, i+2]
    iter = itertools.izip(data, itertools.islice(data, 1, None),
            itertools.islice(data, 2, None))

    for a, b, c in iter:
        if not is_anomaly(a, b, c):
            yield b

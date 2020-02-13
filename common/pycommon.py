def pairwise(it):
    """
    Transform an iterator into another iterator that yields successive adjacent pairs.

        >>> list(pairwise([1, 2, 3, 4]))
        [(1, 2), (2, 3), (3, 4)]
    """
    it = iter(it)
    first = next(it)
    second = next(it)
    while True:
        yield (first, second)
        first = second
        second = next(it)

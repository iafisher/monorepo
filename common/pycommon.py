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


def plural(n, word, suffix="s"):
    return f"{n} {word}" if n == 1 else f"{n} {word}{suffix}"


_COLOR_RED = "91"
_COLOR_BLUE = "94"
_COLOR_GREEN = "92"
_COLOR_RESET = "0"


def red(text):
    """Return a string that will display as red using ANSI color codes."""
    return _colored(text, _COLOR_RED)


def blue(text):
    """Return a string that will display as blue using ANSI color codes."""
    return _colored(text, _COLOR_BLUE)


def green(text):
    """Return a string that will display as green using ANSI color codes."""
    return _colored(text, _COLOR_GREEN)


def _colored(text, color):
    return f"\033[{color}m{text}\033[{_COLOR_RESET}m"

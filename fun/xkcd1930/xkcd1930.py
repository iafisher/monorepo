#!/usr/bin/env python3
"""Generate random strings from the template at xkcd.com/1930/."""
import random
import re
import shutil
import textwrap
from collections import namedtuple


XKCD_STRING = """\
Did you know that (the (fall|spring) equinox|the (summer|winter) solstice|the
 (Summer|Winter) Olympics|the (earliest|latest) (sunrise|sunset)|Daylight
 (Saving|Savings) Time|leap (day|year)|Easter|the (harvest|super|blood) moon|Toyota Truck
 Month|Shark Week) (happens (earlier|later|at the wrong time) every year|drifts out of
 sync with the (Sun|Moon|zodiac|(Gregorian|Mayan|Lunar|iPhone) calendar|atomic clock in
 Colorado)|might (not happen|happen twice) this year) because of (time zone legislation
 in (Indiana|Arizona|Russia)|a decree by the Pope in the 1500s|(precession|libration|
nutation|libation|eccentricity|obliquity) of the (Moon|Sun|Earth's axis|Equator|Prime
 Meridian|(International Date|Mason-Dixon) Line)|magnetic field reversal|an arbitrary
 decision by (Benjamin Franklin|Isaac Newton|FDR))? Apparently (it causes a predictable
 increase in car accidents|that's why we have leap seconds|scientists are really worried
|it was even more extreme during the (Bronze Age|Ice Age|Cretaceous|1990s)|there's a
 proposal to fix it, but it (will never happen|actually make things worse|is stalled in
 Congress|might be unconstitutional)|it's getting worse and no one knows why).
"""

XKCD_STRING = XKCD_STRING.replace("\n", "")


def random_calendar_fact():
    """Generate a random calendar fact, as a string."""
    tokenizer = Tokenizer(XKCD_STRING)
    return choose_sentence(tokenizer)


def choose_sentence(tokenizer):
    """
    Given a tokenizer whose `current_token` is one before the first token of a sentence
    (a sentence is a combination of text and (...|...|...) expressions), return a string
    with the choice expressions replaced by randomly selecting one of the clauses.

    This function will leave `tokenizer.current_token` at one past the last token of the
    sentence.
    """
    ret = []
    try:
        while True:
            tkn = next(tokenizer)
            if tkn.kind == "LPAREN":
                ret.append(choose_from(tokenizer))
            elif tkn.kind == "TEXT":
                ret.append(tkn.value)
            else:
                break
    except StopIteration:
        pass
    return "".join(ret)


def choose_from(tokenizer):
    """
    Given a tokenizer whose `current_token` is the first token of a (...|...|...)
    expression (i.e., the first parenthesis), return a random selection from the
    clauses. The clauses themselves may contain choice expression.

    This function will leave `tokenizer.current_token` at the last token of the choice
    expression (i.e., the last parenthesis).
    """
    choices = []
    while True:
        choices.append(choose_sentence(tokenizer))
        if tokenizer.current_token.kind == "RPAREN":
            break
    return random.choice(choices)


Token = namedtuple("Token", ["kind", "value"])


class Tokenizer:
    TOKENS = (
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("BAR", r"\|"),
        ("TEXT", r"[^()|]+"),
        ("MISMATCH", r"."),
    )
    REGEX = re.compile("|".join("(?P<{}>{})".format(*tkn) for tkn in TOKENS))

    def __init__(self, string):
        self.rep = self.REGEX.finditer(string)
        self.current_token = None

    def __iter__(self):
        return self

    def __next__(self):
        mo = next(self.rep)
        self.current_token = Token(mo.lastgroup, mo.group(0))
        return self.current_token


if __name__ == "__main__":
    fact = random_calendar_fact()
    columns, _ = shutil.get_terminal_size()
    print("\n".join(textwrap.wrap(fact, width=columns)))

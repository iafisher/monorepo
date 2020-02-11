"""
A Python implementation of the board game [Boggle](https://en.wikipedia.org/wiki/Boggle).

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2019
"""
import argparse
import bisect
import math
import os
import random
import readline
import shutil
import sys
import textwrap
import time
import unittest


# Bazel orchestrates the runtime environment so that the dictionary files can be found
# in this folder.
#
# If not running with Bazel, use
#
#   os.path.join(os.path.dirname(os.path.abspath(__file__)), "words")
#
# instead.
DICTIONARY_FOLDER = "fun/boggle/words"
DICTIONARY_EN = os.path.join(DICTIONARY_FOLDER, "en_abridged.txt")
DICTIONARY_RU = os.path.join(DICTIONARY_FOLDER, "ru.txt")
GAME_DURATION_IN_SECS = 3*60
BOARD_SIDE_LENGTH = 4
MIN_WORD_LENGTH = 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--duration", type=int, default=GAME_DURATION_IN_SECS,
        help="Duration of the game, in seconds")
    parser.add_argument(
        "--min", type=int, default=MIN_WORD_LENGTH,
        help="Minimum length for a word to count.")
    parser.add_argument(
        "--russian", action="store_true",
        help="Use the Russian alphabet for the board.")
    parser.add_argument(
        "--size", type=int, default=BOARD_SIDE_LENGTH,
        help="Number of letters per side of board")
    parser.add_argument("--words", default="", help="Path to dictionary file.")
    args = parser.parse_args()

    if args.duration <= 0:
        sys.stderr.write("Error: --duration must be a positive integer.\n")
        sys.exit(1)

    if args.size < 3:
        sys.stderr.write("Error: --size must be at least 3.\n")
        sys.exit(1)

    if not args.words:
        if args.russian:
            args.words = DICTIONARY_RU
        else:
            args.words = DICTIONARY_EN

    dct = open_dictionary(args.words)
    best_possible_score = 0
    while best_possible_score == 0:
        # Loop until we find a board with at least 1 possible word.
        board = Board(size=args.size, russian=args.russian)
        all_possible_words = board.all_words(dct, min_length=args.min)
        best_possible_score = sum(map(score, all_possible_words))

    board.display()
    print("Enter !p to print the board again.")
    print()
    start = now()
    end = time_add(start, args.duration)
    your_words = set()
    your_score = 0
    while True:
        minutes, seconds = divmod(time_diff(end, now()), 60)
        minutes = int(minutes)
        seconds = int(seconds)

        try:
            response = input(f"({minutes}:{seconds:0>2}) > ")
        except (KeyboardInterrupt, EOFError):
            print()
            break
        else:
            response = response.strip().lower()

        if now() >= end:
            print("Time is up.")
            break

        if response == "!p":
            board.display()
        elif response == "!s":
            perc = your_score / best_possible_score
            print(f"{your_score} / {best_possible_score} ({perc:.1%})")
        elif response == "!ps" or response == "!sp":
            board.display()
            perc = your_score / best_possible_score
            print(f"{your_score} / {best_possible_score} ({perc:.1%})")
        elif response:
            if response in your_words:
                print("You already said that.")
            else:
                if len(response) < args.min:
                    print(f"Too short. (minimum length: {args.min})")
                    continue

                if not board.check(response):
                    print("Not on the board.")
                    continue

                if not check_dictionary(dct, response):
                    print("Not in dictionary.")
                    continue

                your_words.add(response)
                your_score += score(response)

    missed = sorted(all_possible_words - your_words)
    perc = your_score / best_possible_score
    print()
    print(f"Your score:         {your_score}")
    print(f"Max possible score: {best_possible_score}")
    print(f"Efficiency:         {perc:.1%}")
    print()
    width = shutil.get_terminal_size()[0]
    print(textwrap.fill("MISSED: " + ", ".join(missed), width=width))


class Board:
    LETTERS = (
        (["a"] * 9) + (["b"] * 2)  + (["c"] * 2) + (["d"] * 4) + (["e"] * 12) +
        (["f"] * 2) + (["g"] * 3)  + (["h"] * 2) + (["i"] * 9) + (["j"] * 1) +
        (["k"] * 1) + (["l"] * 4)  + (["m"] * 2) + (["n"] * 6) + (["o"] * 8) +
        (["p"] * 2) + (["qu"] * 2) + (["r"] * 6) + (["s"] * 4) + (["t"] * 6) +
        (["u"] * 4) + (["v"] * 2)  + (["w"] * 2) + (["x"] * 1) + (["y"] * 2) +
        (["z"] * 1)
    )

    # From https://en.wikipedia.org/wiki/Scrabble_letter_distributions#Russian
    LETTERS_RU = (
        (["а"] * 8) + (["б"] * 2) + (["в"] * 4) + (["г"] * 2) + (["д"] * 4) +
        (["е"] * 8) + (["ё"] * 1) + (["ж"] * 1) + (["з"] * 2) + (["и"] * 5) +
        (["й"] * 1) + (["к"] * 4) + (["л"] * 4) + (["м"] * 3) + (["н"] * 5) +
        (["о"] * 10) + (["п"] * 4) + (["р"] * 5) + (["с"] * 5) + (["т"] * 5) +
        (["у"] * 4) + (["ф"] * 1) + (["х"] * 1) + (["ц"] * 1) + (["ч"] * 1) +
        (["ш"] * 1) + (["щ"] * 1) + (["ъ"] * 1) + (["ы"] * 2) + (["ь"] * 2) +
        (["э"] * 1) + (["ю"] * 1) + (["я"] * 2)
    )

    def __init__(self, *, size=BOARD_SIDE_LENGTH, russian=False):
        self.english = not russian
        letter_set = self.LETTERS if self.english else self.LETTERS_RU
        self.letters = random.sample(letter_set, size * size)
        self.size = size

    @classmethod
    def from_list(cls, letters):
        size = int(math.sqrt(len(letters)))
        self = cls(size=size)
        self.letters = letters
        return self

    def check(self, word):
        if self.english and word.startswith("qu"):
            first, rest = word[:2], word[2:]
        else:
            first, rest = word[0], word[1:]

        index = find(self.letters, first)
        while index != -1:
            if self._check_helper(rest, index, frozenset([index])):
                return True
            index = find(self.letters, first, index+1)

        return False

    def _check_helper(self, word, last_index, already_used):
        """
        Return True if `word` can be spelled on the board started at `last_index` and
        not using any of the indices in `already_used`.
        """
        if not word:
            return True

        for index in self.adjacent(last_index):
            if index in already_used:
                continue

            letter = self.letters[index]
            if word.startswith(letter):
                result = self._check_helper(
                    word[len(letter):], index, already_used | {index})

                if result:
                    return True

        return False

    def all_words(self, dct, *, min_length=MIN_WORD_LENGTH):
        """
        Return all words in the dictionary `dct` that can be legally formed on the
        board and are at least `min_length` characters in length.
        """
        words = set()
        for i in range(self.size * self.size):
            letter = self.letters[i]
            words |= set(
                self._all_words_helper(dct, letter, i, frozenset([i]), min_length)
            )
        return words


    def _all_words_helper(self, dct, word, last_index, already_used, min_length):
        """
        Yield every word beginning with `word` that can be made starting at `last_index`
        without using any indices in `already_used`, and that is at least `min_length`
        characters in length.
        """
        dct_index = bisect.bisect_left(dct, word)
        if dct_index == len(dct):
            return

        if dct[dct_index] == word and len(word) >= min_length:
            yield word

        if not dct[dct_index].startswith(word):
            # No word in the dictionay starts with this sequence, so we can prematurely
            # terminate.
            return

        for adjacent_index in self.adjacent(last_index):
            if adjacent_index in already_used:
                continue

            word2 = word + self.letters[adjacent_index]
            already_used2 = already_used | {adjacent_index}
            yield from self._all_words_helper(
                dct, word2, adjacent_index, already_used2, min_length,
            )

    def adjacent(self, index):
        """Yield the indices adjacent to `index` on the board."""
        if not self.top_edge(index):
            if not self.left_edge(index):
                yield self.above(self.left(index))

            yield self.above(index)

            if not self.right_edge(index):
                yield self.above(self.right(index))

        if not self.left_edge(index):
            yield self.left(index)

        if not self.right_edge(index):
            yield self.right(index)

        if not self.bottom_edge(index):
            if not self.left_edge(index):
                yield self.below(self.left(index))

            yield self.below(index)

            if not self.right_edge(index):
                yield self.below(self.right(index))


    def top_edge(self, index): return index < self.size
    def bottom_edge(self, index): return index >= (self.size * (self.size - 1))
    def left_edge(self, index): return index % self.size == 0
    def right_edge(self, index): return index % self.size == self.size - 1

    def above(self, index): return index - self.size
    def below(self, index): return index + self.size
    def left(self, index): return index - 1
    def right(self, index): return index + 1

    def display(self):
        print()
        for i in range(self.size):
            print("  ", end="")
            for j in range(self.size):
                letter = self.letters[i*self.size+j].upper()
                if len(letter) == 2:
                    print(letter + " ", end="")
                else:
                    print(letter + "  ", end="")
            print()
        print()


def score(word):
    if len(word) == 3 or len(word) == 4:
        return 1
    elif len(word) == 5:
        return 2
    elif len(word) == 6:
        return 3
    elif len(word) == 7:
        return 5
    elif len(word) >= 8:
        return 11
    else:
        return 0


def check_dictionary(dct, word):
    """Return True if `word` is in `dct`."""
    index = bisect.bisect_left(dct, word)
    return index < len(dct) and dct[index] == word


def find(lst, item, start=0):
    """
    Return the first index greater than or equal to `start` of `item` in `lst`, or -1
    if no element of `lst` is equal to `item`.
    """
    for i, x in enumerate(lst):
        if x == item and i >= start:
            return i
    return -1


def open_dictionary(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().split("\n")


def now():
    return time.monotonic()


def time_diff(t1, t2):
    return t1 - t2


def time_add(t, secs):
    return t + secs


class BoggleTest(unittest.TestCase):
    """Run with `./boggle --test`."""

    @classmethod
    def setUpClass(cls):
        cls.dct = open_dictionary(DICTIONARY_EN)

    def test_adjacent(self):
        #  0   1   2   3
        #  4   5   6   7
        #  8   9  10  11
        # 12  13  14  15
        board = Board(size=4)
        self.assertEqual(set(board.adjacent(0)), {1, 4, 5})
        self.assertEqual(set(board.adjacent(1)), {0, 2, 4, 5, 6})
        self.assertEqual(set(board.adjacent(4)), {0, 1, 5, 8, 9})
        self.assertEqual(set(board.adjacent(9)), {4, 5, 6, 8, 10, 12, 13, 14})
        self.assertEqual(set(board.adjacent(12)), {8, 9, 13})
        self.assertEqual(set(board.adjacent(15)), {10, 11, 14})

    def test_check_board(self):
        # E Z O A
        # L T A R
        # N E L K
        # T S I B
        board = Board.from_list(list("ezoaltarnelktsib"))
        self.assertTrue(board.check("a"))
        self.assertTrue(board.check("tar"))
        self.assertTrue(board.check("sent"))
        self.assertTrue(board.check("listen"))
        self.assertTrue(board.check("rates"))
        self.assertFalse(board.check("tore"))
        self.assertFalse(board.check("quest"))
        # Cannot use the same 'T' twice.
        self.assertFalse(board.check("TAT"))

    def test_check_dictionary(self):
        self.assertTrue(check_dictionary(self.dct, "mat"))
        self.assertFalse(check_dictionary(self.dct, "jkldfalkb"))

    def test_check_board_regressions(self):
        # U N E N
        # E E Q S
        # R Y N H
        # O P K R
        board = Board.from_list(list("uneneeqsrynhopkr"))
        self.assertTrue(board.check("pore"))

        # L  N  I  G
        # O  K  QU I
        # I  E  N  H
        # B  N  U  S
        board = Board.from_list(list("lnigok") + ["qu"] + list("iienhbnus"))
        self.assertTrue(board.check("unique"))
        self.assertFalse(board.check("bib"))

    def test_all_words(self):
        # L  N  I  G
        # O  K  QU I
        # I  E  N  H
        # B  N  U  S
        board = Board.from_list(list("lnigok") + ["qu"] + list("iienhbnus"))
        words = board.all_words(self.dct)
        self.assertIn("unique", words)
        self.assertNotIn("bib", words)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        unittest.main(argv=["boggle"])
    else:
        main()

import unittest

from common import pycommon


class PairwiseTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(list(pycommon.pairwise([1, 2, 3])), [(1, 2), (2, 3)])
        self.assertEqual(
            list(pycommon.pairwise([1, 2, 3, 4])), [(1, 2), (2, 3), (3, 4)]
        )

    def test_empty(self):
        self.assertEqual(list(pycommon.pairwise([])), [])

    def test_with_single_element(self):
        self.assertEqual(list(pycommon.pairwise([1])), [])

    def test_with_two_elements(self):
        self.assertEqual(list(pycommon.pairwise([1, 2])), [(1, 2)])

    def test_with_non_list_iterator(self):
        self.assertEqual(
            list(pycommon.pairwise(range(10))),
            [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)],
        )


class PluralTests(unittest.TestCase):
    def test_default_plural(self):
        self.assertEqual(pycommon.plural(0, "cat"), "0 cats")
        self.assertEqual(pycommon.plural(1, "cat"), "1 cat")
        self.assertEqual(pycommon.plural(2, "cat"), "2 cats")
        self.assertEqual(pycommon.plural(10, "cat"), "10 cats")

    def test_custom_plural(self):
        self.assertEqual(pycommon.plural(0, "child", suffix="ren"), "0 children")
        self.assertEqual(pycommon.plural(1, "child", suffix="ren"), "1 child")
        self.assertEqual(pycommon.plural(2, "child", suffix="ren"), "2 children")
        self.assertEqual(pycommon.plural(10, "child", suffix="ren"), "10 children")


if __name__ == "__main__":
    unittest.main()

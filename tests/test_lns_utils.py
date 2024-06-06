"""
Test cases for lns utilities.
"""

# pylint: disable=duplicate-code
from unittest import TestCase

from clingo.symbol import Function, Number, String

import large_neighbourhood_search as lns_pkg
from large_neighbourhood_search import LNS


class TestLNSUtils(TestCase):
    """
    Test cases for lns utilities.
    """

    def test_variability(self):
        """
        Test variability calculation.
        """
        LNS(["./tests/ref/golf.lp"])
        l1 = [0, 1, 2, 3, 4, 5]
        l2 = [1, 3]
        self.assertEqual(lns_pkg.lib.lns_utils.calculate_variability(l1, l2), 0)
        l2 = [0, 2, 6, 7]
        self.assertEqual(lns_pkg.lib.lns_utils.calculate_variability(l1, l2), 0.5)
        self.assertEqual(lns_pkg.lib.lns_utils.calculate_variability(l2, l1), 0.5)

    def test_calc_opt_val_weighted_sum(self):
        """
        Test optimization value calculation using weighted sum.
        """
        model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
                Function("plays", [Number(5), Number(1), Number(1)], True),
                Function("plays", [Number(9), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function("meets", [Number(7), Number(9), Number(3)], True),
                Function("meets", [Number(8), Number(9), Number(3)], True),
                Function(
                    "_lns_priority",
                    [
                        String("min"),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min"),
                        Function("", [Number(1), Number(2)], True),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min"),
                        Function("", [Number(3), Number(5)], True),
                        Number(2),
                    ],
                    True,
                ),
                Function(
                    "_lns_priority",
                    [
                        String("min2"),
                        Number(2),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min2"),
                        Function("", [Number(1), Number(2)], True),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min2"),
                        Function("", [Number(3), Number(5)], True),
                        Number(2),
                    ],
                    True,
                ),
            ],
        }
        self.assertEqual(lns_pkg.lib.lns_utils.calc_opt_val_weighted_sum(model), 6)

    def test_calc_opt_val_lexicographic(self):
        """
        Test optimization value calculation using lexicographic ordering.
        """
        model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
                Function("plays", [Number(5), Number(1), Number(1)], True),
                Function("plays", [Number(9), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function("meets", [Number(7), Number(9), Number(3)], True),
                Function("meets", [Number(8), Number(9), Number(3)], True),
                Function(
                    "_lns_priority",
                    [
                        String("min"),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min"),
                        Function("", [Number(1), Number(2)], True),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min"),
                        Function("", [Number(3), Number(5)], True),
                        Number(2),
                    ],
                    True,
                ),
                Function(
                    "_lns_priority",
                    [
                        String("min2"),
                        Number(3),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min2"),
                        Function("", [Number(1), Number(2)], True),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_priority",
                    [
                        String("min3"),
                        Number(2),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min3"),
                        Function("", [Number(3), Number(5)], True),
                        Number(2),
                    ],
                    True,
                ),
            ],
        }
        ref = {1: 3, 3: 1, 2: 2}
        self.assertDictEqual(
            lns_pkg.lib.lns_utils.calc_opt_val_lexicographic(model), ref
        )

    def test_lexi_comparison(self):
        """
        Test comparison of lexicographic values.
        """
        val1 = {2: 10}
        val2 = {3: 1, 1: 1}
        self.assertTrue(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val1, val2))
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val2, val1))
        val1 = {3: 2}
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val1, val2))
        self.assertTrue(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val2, val1))
        val1 = {3: 1, 1: 2}
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val1, val2))
        self.assertTrue(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val2, val1))
        val1 = val2
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val1, val2))
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val2, val1))
        val1 = {}
        self.assertTrue(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val1, val2))
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val2, val1))

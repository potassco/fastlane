"""
Test utilities.
"""

import logging
from io import StringIO
from unittest import TestCase

from clingo.symbol import Function, Infimum, Number, String, Supremum

from large_neighbourhood_search.lib.solvers.clingo_dl_solver import ClingoDLSolver
from large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd import (
    HCWeightedSumRnd,
)
from large_neighbourhood_search.lib.utils import (
    calculate_variability,
    check_smaller_lexicographic,
    fix_symbols,
    str_to_symbols,
    symbol_to_str,
)
from large_neighbourhood_search.utils.logger import setup_logger
from large_neighbourhood_search.utils.parser import get_parser


class TestUtils(TestCase):
    """
    Test cases for utilities.
    """

    def test_logger(self):
        """
        Test the logger.
        """
        log = setup_logger("global", logging.INFO)
        sio = StringIO()
        for handler in log.handlers:
            handler.setStream(sio)
        log.info("test123")
        self.assertRegex(sio.getvalue(), "test123")

    def test_parser(self):
        """
        Test the parser.
        """
        parser = get_parser()
        ret = parser.parse_args(["--log", "info", "-i", "x.lp"])
        self.assertEqual(ret.log, logging.INFO)
        ret = parser.parse_args(["-r", "0.4", "-i", "x.lp"])
        self.assertEqual(ret.relax_rate, 0.4)
        ret = parser.parse_args(["--relax_rate", "0.5", "-i", "x.lp"])
        self.assertEqual(ret.relax_rate, 0.5)
        ret = parser.parse_args(["--solver", "ClingoDLSolver", "-i", "x.lp"])
        self.assertIsInstance(ret.solver, ClingoDLSolver)
        ret = parser.parse_args(["--strategy", "HCWeightedSumRnd", "-i", "x.lp"])
        self.assertIsInstance(ret.strategy, HCWeightedSumRnd)
        ret = parser.parse_args(["--time_limit", "12", "-i", "x.lp"])
        self.assertEqual(ret.time_limit, 12)
        ret = parser.parse_args(["--solve_time_limit", "14", "-i", "x.lp"])
        self.assertEqual(ret.solve_time_limit, 14)
        ret = parser.parse_args(["--max_steps", "30", "-i", "x.lp"])
        self.assertEqual(ret.max_steps, 30)
        ret = parser.parse_args(["--no_improv", "20", "-i", "x.lp"])
        self.assertEqual(ret.no_improv, 20)
        ret = parser.parse_args(["--seed", "213", "-i", "x.lp"])
        self.assertEqual(ret.seed, 213)
        ret = parser.parse_args(["--vari_accept", "0.2", "-i", "x.lp"])
        self.assertEqual(ret.vari_accept, 0.2)


class TestLNSUtils(TestCase):
    """
    Test cases for lns utilities.
    """

    def test_variability(self):
        """
        Test variability calculation.
        """
        l1 = [0, 1, 2, 3, 4, 5]
        l2 = [1, 3]
        self.assertEqual(calculate_variability(l1, l2), 0)
        l2 = [0, 2, 6, 7]
        self.assertEqual(calculate_variability(l1, l2), 0.5)
        self.assertEqual(calculate_variability(l2, l1), 0.5)

    def test_lexi_comparison(self):
        """
        Test comparison of lexicographic values.
        """
        val1 = {2: 10}
        val2 = {3: 1, 1: 1}
        self.assertTrue(check_smaller_lexicographic(val1, val2))
        self.assertFalse(check_smaller_lexicographic(val2, val1))
        val1 = {3: 2}
        self.assertFalse(check_smaller_lexicographic(val1, val2))
        self.assertTrue(check_smaller_lexicographic(val2, val1))
        val1 = {3: 1, 1: 2}
        self.assertFalse(check_smaller_lexicographic(val1, val2))
        self.assertTrue(check_smaller_lexicographic(val2, val1))
        val1 = val2
        self.assertFalse(check_smaller_lexicographic(val1, val2))
        self.assertFalse(check_smaller_lexicographic(val2, val1))
        val1 = {}
        self.assertTrue(check_smaller_lexicographic(val1, val2))
        self.assertFalse(check_smaller_lexicographic(val2, val1))

    def test_symbol_to_str(self):
        """
        Test symbol to str conversion.
        """
        s = Function(
            "test",
            [Function("inner", [Number(2)]), String("string"), Infimum, Supremum],
        )
        self.assertEqual(symbol_to_str(s), 'test(inner(2),"string",#inf,#sup)')

    def test_str_to_symbols(self):
        """
        Test str to symbols conversion.
        """
        s = 'test(inner(2),"string",#inf,#sup) second(3)'
        self.assertEqual(
            str_to_symbols(s),
            [
                Function(
                    "test",
                    [
                        Function("inner", [Number(2)]),
                        String("string"),
                        Infimum,
                        Supremum,
                    ],
                    True,
                ),
                Function("second", [Number(3)], True),
            ],
        )

    def test_fix_symbols(self):
        """
        test fix_symbols function.
        """
        s = [
            Function(
                "test",
                [Function("inner", [Number(2)]), String("string"), Infimum, Supremum],
                True,
            ),
            Function("second", [Number(3)], True),
        ]
        self.assertEqual(
            fix_symbols(s),
            [
                (
                    Function(
                        "test",
                        [
                            Function("inner", [Number(2)]),
                            String("string"),
                            Infimum,
                            Supremum,
                        ],
                        True,
                    ),
                    True,
                ),
                (
                    Function("second", [Number(3)], True),
                    True,
                ),
            ],
        )

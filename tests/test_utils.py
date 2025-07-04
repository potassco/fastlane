"""
Test utilities.
"""

import logging
from io import StringIO
from unittest import TestCase

from clingo.symbol import Function, Infimum, Number, String, Supremum

from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lib.utils import calculate_variability, fix_symbols
from mod_lns.utils.conversions import args_to_dict, str_to_symbols, symbol_to_str
from mod_lns.utils.logger import setup_logger
from mod_lns.utils.parser import get_parser


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
        ret = parser.parse_args(["-i", "x.lp"])
        self.assertEqual(ret.input_files, ["x.lp"])
        ret = parser.parse_args(["-r", "0.4", "-i", "x.lp"])
        self.assertEqual(ret.relax_rate, 0.4)
        ret = parser.parse_args(["--relax_rate", "0.5", "-i", "x.lp"])
        self.assertEqual(ret.relax_rate, 0.5)
        ret = parser.parse_args(["--solver", "ClingoDLSolver", "-i", "x.lp"])
        self.assertIsInstance(ret.solver, ClingoDLSolver)
        ret = parser.parse_args(["--strategy", "DefaultStrategy", "-i", "x.lp"])
        self.assertIsInstance(ret.strategy, DefaultStrategy)
        ret = parser.parse_args(["--time_limit", "12", "-i", "x.lp"])
        self.assertEqual(ret.time_limit, 12)
        ret = parser.parse_args(["--solve_time_limit", "14", "-i", "x.lp"])
        self.assertEqual(ret.solve_time_limit, 14)
        ret = parser.parse_args(["--max_steps", "30", "-i", "x.lp"])
        self.assertEqual(ret.max_steps, "30")
        ret = parser.parse_args(["--first_time_limit", "12", "-i", "x.lp"])
        self.assertEqual(ret.first_time_limit, 12)
        ret = parser.parse_args(["--first_model_limit", "12", "-i", "x.lp"])
        self.assertEqual(ret.first_model_limit, 12)
        ret = parser.parse_args(["--seed", "213", "-i", "x.lp"])
        self.assertEqual(ret.seed, 213)
        ret = parser.parse_args(["--heuristics", "-i", "x.lp"])
        self.assertTrue(ret.heuristics)
        ret = parser.parse_args(["--constrained", "-i", "x.lp"])
        self.assertTrue(ret.constrained)
        ret = parser.parse_args(["--declarative", "-i", "x.lp"])
        self.assertTrue(ret.declarative)

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

    def test_args_to_dict(self):
        """
        Test args to dict conversion.
        """
        s = "-a --test=5 -g=3 --help howefow"
        self.assertDictEqual(
            args_to_dict(s), {"a": True, "test": "5", "g": "3", "help": True}
        )


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

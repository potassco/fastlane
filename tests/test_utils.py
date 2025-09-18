"""
Test utilities.
"""

import logging
from io import StringIO
from unittest import TestCase

from clingo.symbol import Function, Infimum, Number, String, Supremum

from mod_lns.lib.parser.framework_parser import get_framework_parser
from mod_lns.lib.utils import calculate_variability, fix_symbols, get_unique_list, clamp
from mod_lns.utils.conversions import args_to_dict, str_to_symbols, symbol_to_str
from mod_lns.utils.logger import setup_logger

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

    def test_framework_parser(self):
        """
        Test the parser.
        """
        parser = get_framework_parser()
        ret = parser.parse_args(["--log-level", "info", "x.lp", "default"])
        self.assertEqual(ret.log_level, logging.INFO)
       

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
        self.assertEqual(calculate_variability(l1, l2), 50)
        self.assertEqual(calculate_variability(l2, l1), 50)

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
    
    def test_get_unique_list(self):
        """
        Test get_unique_list function.
        """
        l = [2, 1, 2, 2, 3, 1, 4, 5, 5]
        self.assertEqual(get_unique_list(l), [2, 1, 3, 4, 5])
    
    def test_clamp(self):
        """
        Test clamp function.
        """
        self.assertEqual(clamp(5, 1, 10), 5)
        self.assertEqual(clamp(-14, 1, 10), 1)
        self.assertEqual(clamp(15, 1, 10), 10)
        self.assertEqual(clamp(5.5, 1, 10), 5.5)

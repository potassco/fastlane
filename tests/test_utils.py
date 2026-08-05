"""
Test utilities.
"""

import logging
from io import StringIO
from unittest import TestCase

from clingo.symbol import Function, Infimum, Number, String, Supremum

from fastlane.utils.conversions import args_to_dict, str_to_symbols, symbol_to_str
from fastlane.utils.logger import setup_logger


class TestLogger(TestCase):
    """
    Test cases for the logger.
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


class TestConversions(TestCase):
    """
    Test cases for the conversions.
    """

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

    def test_symbol_to_str(self):
        """
        Test symbol to str conversion.
        """
        s = Function(
            "test",
            [Function("inner", [Number(2)]), String("string"), Infimum, Supremum],
        )
        self.assertEqual(symbol_to_str(s), 'test(inner(2),"string",#inf,#sup)')

    def test_args_to_dict(self):
        """
        Test args to dict conversion.
        """
        s = "-a --test=5 -g=3 --help howefow"
        self.assertDictEqual(args_to_dict(s), {"a": True, "test": "5", "g": "3", "help": True})

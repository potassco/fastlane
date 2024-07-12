"""
Test utilities.
"""

import logging
from io import StringIO
from unittest import TestCase

from large_neighbourhood_search.lib.utils import (
    calculate_variability,
    check_smaller_lexicographic,
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
        ret = parser.parse_args(["--log", "info"])
        self.assertEqual(ret.log, logging.INFO)


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

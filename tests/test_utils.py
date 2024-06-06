"""
Test utilities.
"""

import logging
from io import StringIO
from unittest import TestCase

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

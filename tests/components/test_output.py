"""
Test cases for the output component.
"""

from unittest import TestCase

from fastlane.lib.components.output import get_output_format


class TestOutputComponents(TestCase):
    """
    Test cases for the output component.
    """

    def test_get_output_format(self):
        """
        Test get_output_format function.
        """
        cost_str = "20 3 50"
        time_limit = 1000000
        max_steps = 10000000

        header, iter_format = get_output_format(cost_str, time_limit, max_steps)
        self.assertEqual(header, "{0:>11} - {1:>8}: {2:>7}")
        self.assertEqual(iter_format, "{0:>11.3f} - {1:>8}: {2:>7}")

        # Test with None values for time_limit and max_steps
        header_none, iter_format_none = get_output_format(cost_str, None, None)
        self.assertEqual(header_none, "{0:>9} - {1:>7}: {2:>7}")
        self.assertEqual(iter_format_none, "{0:>9.3f} - {1:>7}: {2:>7}")

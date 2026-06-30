"""
Test cases for the constrained components of the LNS framework.
"""

from unittest import TestCase

from mod_lns.lib.components.constrained import get_opt_bound


class TestConstrainedComponents(TestCase):
    """
    Test cases for the constrained components of the LNS framework.
    """

    def setUp(self) -> None:
        """
        Set up the test case.
        """
        self.cost = [10, 20, 30]
        self.opt_mode = "opt"
        self.opt_nf = 5

    def test_get_opt_bound_static(self):
        """
        Test get_opt_bound function with static optimization modifier.
        """
        opt_modifier = "static"
        expected_bound = "opt,5"
        self.assertEqual(get_opt_bound(self.cost, self.opt_mode, opt_modifier, self.opt_nf), expected_bound)

    def test_get_opt_bound_dynamic(self):
        """
        Test get_opt_bound function with dynamic optimization modifier.
        """
        opt_modifier = "dynamic"
        expected_bound = "opt,10,20,31"
        self.assertEqual(get_opt_bound(self.cost, self.opt_mode, opt_modifier, self.opt_nf), expected_bound)

    def test_get_opt_bound_invalid_modifier(self):
        """
        Test get_opt_bound function with an invalid optimization modifier.
        """
        opt_modifier = "invalid"
        expected_bound = "opt"
        self.assertEqual(get_opt_bound(self.cost, self.opt_mode, opt_modifier, self.opt_nf), expected_bound)

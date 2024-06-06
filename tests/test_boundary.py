"""
Test cases for boundary components.
"""

from unittest import TestCase

import large_neighbourhood_search as lns_pkg
from large_neighbourhood_search import LNS


class TestBoundary(TestCase):
    """
    Test cases for boundary components.
    """

    def test_boundary_overall_init(self):
        """
        Test "init" action of boundary_overall.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertTrue(lns_pkg.lib.boundary.boundary_overall(lns, "init"))
        self.assertEqual(lns.boundary_dict["bound"], lns.param_values["bound"])
        self.assertEqual(lns.boundary_dict["step"], 0)
        s_time = lns.boundary_dict["start_time"]
        self.assertEqual(type(s_time), float)
        self.assertEqual(lns.boundary_dict["no_improvement"], 0)

    def test_boundary_overall_update(self):
        """
        Test "update" action of boundary_overall.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns_pkg.lib.boundary.boundary_overall(lns, "init")
        s_time = lns.boundary_dict["start_time"]
        self.assertTrue(lns_pkg.lib.boundary.boundary_overall(lns, "update"))
        self.assertEqual(lns.boundary_dict["bound"], lns.param_values["bound"])
        self.assertEqual(lns.boundary_dict["step"], 1)
        self.assertEqual(lns.boundary_dict["start_time"], s_time)
        self.assertEqual(lns.boundary_dict["no_improvement"], 0)

    def test_boundary_overall_improvement(self):
        """
        Test "improvement" action of boundary_overall.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns_pkg.lib.boundary.boundary_overall(lns, "init")
        lns_pkg.lib.boundary.boundary_overall(lns, "update")
        s_time = lns.boundary_dict["start_time"]
        self.assertTrue(lns_pkg.lib.boundary.boundary_overall(lns, "improvement"))
        self.assertEqual(lns.boundary_dict["bound"], lns.param_values["bound"])
        self.assertEqual(lns.boundary_dict["step"], 1)
        self.assertEqual(lns.boundary_dict["start_time"], s_time)
        self.assertEqual(lns.boundary_dict["no_improvement"], 0)

    def test_boundary_overall_improvement_nobound(self):
        """
        Test "improvement" action of boundary_overall without bound.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.set_params({"bound": None})
        lns_pkg.lib.boundary.boundary_overall(lns, "init")
        self.assertIsNone(lns.boundary_dict["bound"])
        lns_pkg.lib.boundary.boundary_overall(lns, "update")
        s_time = lns.boundary_dict["start_time"]
        self.assertTrue(lns_pkg.lib.boundary.boundary_overall(lns, "improvement"))
        self.assertEqual(lns.boundary_dict["bound"], lns.param_values["bound"])
        self.assertEqual(lns.boundary_dict["step"], 1)
        self.assertEqual(lns.boundary_dict["start_time"], s_time)
        self.assertEqual(lns.boundary_dict["no_improvement"], 0)

    def test_boundary_overall_no_improvement(self):
        """
        Test "no_improvement" action of boundary_overall.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.param_values["relax_rates"] = [0.2, 0.4]
        lns.param_values["current_relax_rate"] = 0.2
        lns.param_values["switch_rr_after_no_improv"] = 1
        lns_pkg.lib.boundary.boundary_overall(lns, "init")
        s_time = lns.boundary_dict["start_time"]
        self.assertTrue(lns_pkg.lib.boundary.boundary_overall(lns, "no_improvement"))
        self.assertEqual(lns.boundary_dict["bound"], lns.param_values["bound"])
        self.assertEqual(lns.boundary_dict["step"], 0)
        self.assertEqual(lns.boundary_dict["start_time"], s_time)
        self.assertEqual(lns.boundary_dict["no_improvement"], 1)
        self.assertEqual(lns.param_values["current_relax_rate"], 0.4)
        self.assertTrue(lns_pkg.lib.boundary.boundary_overall(lns, "no_improvement"))
        self.assertEqual(lns.param_values["current_relax_rate"], 0.2)

        self.assertFalse(lns_pkg.lib.boundary.boundary_overall(lns, "invalid_action"))

    def test_check_stop_steps(self):
        """
        Test check_stop_steps.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns_pkg.lib.boundary.boundary_overall(lns, "init")
        lns.boundary_dict["step"] = 1
        self.assertFalse(lns_pkg.lib.boundary.check_stop_steps(lns))
        lns.boundary_dict["bound"] = 0
        self.assertTrue(lns_pkg.lib.boundary.check_stop_steps(lns))

    def test_check_stop_time(self):
        """
        Test check_stop_time.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns_pkg.lib.boundary.boundary_overall(lns, "init")
        self.assertFalse(lns_pkg.lib.boundary.check_stop_time(lns))
        lns.param_values["overall_time_limit"] = 0
        self.assertTrue(lns_pkg.lib.boundary.check_stop_time(lns))

    def test_finish(self):
        """
        Test finishing of search.
        """

        def helper(model):
            _ = model
            return 2

        lns = LNS(["./tests/ref/golf.lp"], {"calc_opt_value": helper})
        lns.callables["boundary_handling"](lns, "init")
        lns.models["best_model"] = {"shown": ["shown_test"]}
        lns_pkg.boundary.finish(lns)
        lns.models["best_model"] = {
            "shown": ["shown_test"],
            "assignments": ["assignment_test"],
        }
        lns_pkg.boundary.finish(lns)

"""
Test cases for LNS class.
"""

# pylint: disable=duplicate-code
import signal
from unittest import TestCase

import large_neighbourhood_search as lns_pkg
from large_neighbourhood_search import LNS


class TestLNS(TestCase):
    """
    Test cases for LNS class.
    """

    def test_init(self):
        """
        Test LNS initialization.
        """
        ref_config_values = {
            "files": ["./tests/ref/golf.lp"],
            "seed": None,
            "relax_rates": [0.2, 0.4, 0.6],
            "max_steps": 2000,
            "switch_rr_after_no_improv": 3,
            "clingo_args": {"rand-freq": 0.8},
            "time_limit": 20,
            "overall_time_limit": 600,
        }

        ref_callables = {
            "setup": lns_pkg.lib.theory.setup_clingo,
            "relax": lns_pkg.lib.search.relax_random,
            "repair": lns_pkg.lib.theory.repair_clingo,
            "calc_opt_value": lns_pkg.lib.lns_utils.calc_opt_val_weighted_sum,
            "get_first_solution": lns_pkg.lib.search.get_first_solution_hc_weighted_sum,
            "check_accept": lns_pkg.lib.search.check_accept_always,
            "check_better": lns_pkg.lib.search.check_better_always,
            "better_solution_found": lns_pkg.lib.search.better_solution_found_hc_weighted_sum,
            "boundary_handling": lns_pkg.lib.boundary.boundary_overall,
            "check_stop": lns_pkg.lib.boundary.check_stop_steps,
            "finish": lns_pkg.lib.boundary.finish,
            "check_stuck": lns_pkg.lib.search.check_stuck_never,
            "is_stuck": lns_pkg.lib.search.is_stuck,
            "timeout": lns_pkg.lib.search.timeout,
        }

        lns = LNS(["./tests/ref/golf.lp"])
        self.assertDictEqual(lns.param_values, ref_config_values)
        self.assertDictEqual(lns.callables, ref_callables)

        ref_callables = {**ref_callables, **{"test": print, "on_model": print}}
        lns = LNS(
            ["./tests/ref/golf.lp"],
            {"test": print, "on_model": print},
        )
        self.assertDictEqual(lns.callables, ref_callables)

    def test_get_set_params(self):
        """
        Test parameter getter and setter.
        """
        ref_config_values = {
            "files": ["./tests/ref/golf.lp"],
            "seed": None,
            "relax_rates": [0.2, 0.4, 0.6],
            "max_steps": 2000,
            "switch_rr_after_no_improv": 3,
            "clingo_args": {"rand-freq": 0.8},
            "time_limit": 20,
            "overall_time_limit": 600,
        }
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertDictEqual(lns.get_params(), ref_config_values)
        lns.set_params({"seed": 123, "new_param": "new"})
        self.assertDictEqual(
            lns.get_params(), {**ref_config_values, **{"seed": 123, "new_param": "new"}}
        )

    def test_set_seed(self):
        """
        Test seed setter.
        """
        seed = 42
        lns = LNS(["./tests/ref/golf.lp"])
        lns.set_seed(seed)
        self.assertEqual(lns.param_values["seed"], seed)
        self.assertDictEqual(
            lns.param_values["clingo_args"], {"seed": 42, "rand-freq": 0.8}
        )

    def test_stats(self):
        """
        Test stats getter. WIP
        """
        lns = lns = LNS(["./tests/ref/golf.lp"])
        test_ctl = lns_pkg.lib.theory.setup_clingo(lns)[0]
        self.assertEqual(type(lns.get_stats(test_ctl)), dict)

    def test_interrupt_handling(self):
        """
        Test interrupt handling.
        """

        def helper(lns_object):
            lns_object.param_values["inter"] = True

        lns = LNS(["./tests/ref/golf_big.lp"], {"finish": helper})
        signal.signal(signal.SIGINT, lns.interrupt_handler)
        with self.assertRaises(SystemExit):
            signal.raise_signal(signal.SIGINT)

        self.assertTrue(lns.param_values["inter"])

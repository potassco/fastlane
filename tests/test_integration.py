"""
Integration tests.
"""

from unittest import TestCase

import large_neighbourhood_search as lns_pkg
from large_neighbourhood_search import LNS


class TestIntegration(TestCase):
    """
    Integration tests.
    """

    def test_default_run(self):
        """
        Test default execution.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.main()

    def test_hc_weighted_sum(self):
        """
        Test execution with hard constraints and weighted sum.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            {
                "check_better": lns_pkg.lib.search.check_better_always,
                "better_solution_found": lns_pkg.lib.search.better_solution_found_hc_weighted_sum,
                "get_first_solution": lns_pkg.lib.search.get_first_solution_hc_weighted_sum,
            },
        )
        lns.set_params({"seed": 123})
        lns.main()

    def test_hc_lexicographic(self):
        """
        Test execution with hard constraints and lexicographic optimization.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            {
                "check_better": lns_pkg.lib.search.check_better_always,
                "better_solution_found": lns_pkg.lib.search.better_solution_found_hc_lexicographic,
                "get_first_solution": lns_pkg.lib.search.get_first_solution_hc_lexicographic,
                "calc_opt_value": lns_pkg.lib.lns_utils.calc_opt_val_lexicographic,
            },
        )
        lns.set_params({"seed": 123})
        lns.main()

    def test_classic_weighted_sum(self):
        """
        Test classic execution with weighted sum.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            {
                "check_better": lns_pkg.lib.search.check_better_weighted_sum,
                "better_solution_found": lns_pkg.lib.search.better_solution_found_classic,
                "get_first_solution": lns_pkg.lib.search.get_first_solution_classic,
            },
        )
        lns.set_params({"seed": 456})
        lns.main()

    def test_classic_lexicographic(self):
        """
        Test classic execution with lexicographic optimization.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            {
                "check_better": lns_pkg.lib.search.check_better_lexicographic,
                "better_solution_found": lns_pkg.lib.search.better_solution_found_classic,
                "get_first_solution": lns_pkg.lib.search.get_first_solution_classic,
                "calc_opt_value": lns_pkg.lib.lns_utils.calc_opt_val_lexicographic,
            },
        )
        lns.set_params({"seed": 123})
        lns.main()

    def test_clingo_dl(self):
        """
        Test clingo-dl execution.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            {
                "setup": lns_pkg.lib.theory.setup_clingo_dl,
                "repair": lns_pkg.lib.theory.repair_clingo_dl,
            },
        )
        lns.set_params({"seed": 123})
        lns.main()

    def test_stop_time(self):
        """
        WIP Test stop time.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            {"check_stop": lns_pkg.lib.boundary.check_stop_time},
        )
        lns.set_params({"seed": 123})
        lns.main()

    def test_stuck(self):
        """
        Test execution getting stuck.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            {
                "check_better": lns_pkg.lib.search.check_better_weighted_sum,
                "better_solution_found": lns_pkg.lib.search.better_solution_found_classic,
                "get_first_solution": lns_pkg.lib.search.get_first_solution_classic,
                "check_stuck": lns_pkg.lib.search.check_stuck,
            },
        )
        lns.set_params({"seed": 123})
        lns.main()

    def test_timeout(self):
        """
        Test execution timeout.
        """
        lns = LNS(
            ["./tests/ref/golf_big.lp"],
        )
        lns.set_params({"seed": 123, "time_limit": 1})
        with self.assertRaises(SystemExit):
            lns.main()

    def test_clingo_dl_timeout(self):
        """
        Test clingo-dl execution timeout.
        """
        lns = LNS(
            ["./tests/ref/golf_big.lp"],
            {
                "setup": lns_pkg.lib.theory.setup_clingo_dl,
                "repair": lns_pkg.lib.theory.repair_clingo_dl,
            },
        )
        lns.set_params({"seed": 123, "time_limit": 1})
        with self.assertRaises(SystemExit):
            lns.main()

    def test_invalid_params(self):
        """
        Test execution with invalid params handling.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.param_values = {}
        with self.assertRaises(SystemExit):
            lns.main()

        lns = LNS(["./tests/ref/golf.lp"])
        lns.param_values["relax_rates"] = "a"
        with self.assertRaises(SystemExit):
            lns.main()

        lns = LNS(["./tests/ref/golf.lp"])
        lns.param_values["relax_rates"] = []
        with self.assertRaises(SystemExit):
            lns.main()

    def test_faulty_encoding(self):
        """
        Test execution with faulty encoding.
        """
        lns = LNS(["./tests/ref/bad_encoding.lp"])
        lns.set_params({"seed": 123})
        lns.main()

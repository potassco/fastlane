"""
Test cases for search components.
"""

# pylint: disable=duplicate-code
import random
from unittest import TestCase

from clingo.symbol import Function, Number, String

import large_neighbourhood_search as lns_pkg
from large_neighbourhood_search import LNS


class TestSearch(TestCase):
    """
    Test cases for search components.
    """

    def test_relax(self):
        """
        Test atom relaxation. Seed: 123
        """
        model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
                Function("plays", [Number(5), Number(1), Number(1)], True),
                Function("plays", [Number(9), Number(1), Number(1)], True),
                Function("plays", [Number(1), Number(2), Number(1)], True),
            ],
            "true": [
                Function("_lns_select", [Number(1)], True),
                Function("_lns_select", [Number(2)], True),
                Function("_lns_select", [Number(3)], True),
                Function(
                    "_lns_fix",
                    [
                        Function("plays", [Number(1), Number(1), Number(3)], True),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_fix",
                    [
                        Function("plays", [Number(2), Number(1), Number(3)], True),
                        Number(2),
                    ],
                    True,
                ),
                Function(
                    "_lns_fix",
                    [
                        Function("plays", [Number(3), Number(1), Number(1)], True),
                        Number(3),
                    ],
                    True,
                ),
            ],
        }
        seed = 123
        random.seed(seed)
        ref = [
            (Function("plays", [Number(5), Number(1), Number(1)], True), True),
            (Function("plays", [Number(1), Number(2), Number(1)], True), True),
        ]
        self.assertListEqual(
            lns_pkg.lib.search.relax_random(model, {"relax_rate": 0.2}), ref
        )

        random.seed(seed)
        ref = [(Function("plays", [Number(2), Number(1), Number(3)], True), True)]
        self.assertListEqual(
            lns_pkg.lib.search.relax_declarative(model, {"relax_rate": 0.2}), ref
        )

    def test_check_better(self):
        """
        Test check_better.
        """
        old_model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Function("", [Number(1), Number(2)], True),
                        Number(2),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min2"),
                        Number(2),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min2"),
                        Function("", [Number(3), Number(5)], True),
                        Number(1),
                    ],
                    True,
                ),
            ],
        }
        better_model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Function("", [Number(1), Number(2)], True),
                        Number(2),
                    ],
                    True,
                ),
            ],
        }
        worse_model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Function("", [Number(1), Number(2)], True),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min2"),
                        Number(3),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min2"),
                        Function("", [Number(3), Number(5)], True),
                        Number(4),
                    ],
                    True,
                ),
            ],
        }
        lns = LNS(["./tests/ref/golf.lp"])

        self.assertTrue(
            lns_pkg.lib.search.check_better_weighted_sum(lns, better_model, old_model)
        )
        self.assertFalse(
            lns_pkg.lib.search.check_better_weighted_sum(lns, worse_model, old_model)
        )

        lns = LNS(
            ["./tests/ref/golf.lp"],
            {"calc_opt_value": lns_pkg.lib.lns_utils.calc_opt_val_lexicographic},
        )

        self.assertTrue(
            lns_pkg.lib.search.check_better_lexicographic(lns, better_model, old_model)
        )
        self.assertFalse(
            lns_pkg.lib.search.check_better_lexicographic(lns, worse_model, old_model)
        )

        self.assertTrue(
            lns_pkg.lib.search.check_better_always(lns, better_model, old_model)
        )
        self.assertTrue(
            lns_pkg.lib.search.check_better_always(lns, worse_model, old_model)
        )

    def test_check_acceptance(self):
        """
        Test acceptance checks.
        """
        best_model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Function("", [Number(1), Number(2)], True),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Function("", [Number(3), Number(5)], True),
                        Number(1),
                    ],
                    True,
                ),
            ],
        }
        new_model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Function("", [Number(1), Number(2)], True),
                        Number(1),
                    ],
                    True,
                ),
            ],
        }
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertTrue(
            lns_pkg.lib.search.check_better_always(lns, new_model, best_model)
        )

        self.assertFalse(
            lns_pkg.lib.search.check_accept_variability(lns, new_model, best_model)
        )
        new_model = {
            "shown": [
                Function("plays", [Number(2), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(6), Number(8), Number(3)], True),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_opt",
                    [
                        String("min"),
                        Function("", [Number(1), Number(2)], True),
                        Number(1),
                    ],
                    True,
                ),
            ],
        }
        self.assertTrue(
            lns_pkg.lib.search.check_accept_variability(lns, new_model, best_model)
        )

    def test_first_solution(self):
        """
        Test finding of first solution.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.set_params({"seed": 123})
        ctl, thy = lns_pkg.lib.theory.setup_clingo(lns)
        self.assertEqual(
            lns_pkg.lib.search.get_first_solution_hc_weighted_sum(lns, ctl, thy), True
        )
        self.assertIsNotNone(lns.models["new_model"])
        self.assertEqual(type(lns.models["new_model"]), dict)
        self.assertIsNotNone(lns.models["current_model"])
        self.assertEqual(type(lns.models["current_model"]), dict)
        self.assertIsNotNone(lns.models["best_model"])
        self.assertEqual(type(lns.models["best_model"]), dict)

        lns = LNS(["./tests/ref/bad_encoding.lp"])
        lns.set_params({"seed": 123})
        ctl = lns_pkg.lib.theory.setup_clingo(lns)[0]
        self.assertEqual(
            lns_pkg.lib.search.get_first_solution_hc_weighted_sum(lns, ctl, thy), False
        )

        lns = LNS(
            ["./tests/ref/golf.lp"],
            {"calc_opt_value": lns_pkg.lib.lns_utils.calc_opt_val_lexicographic},
        )
        lns.set_params({"seed": 123})
        ctl, thy = lns_pkg.lib.theory.setup_clingo(lns)
        self.assertEqual(
            lns_pkg.lib.search.get_first_solution_hc_lexicographic(lns, ctl, thy), True
        )
        self.assertIsNotNone(lns.models["new_model"])
        self.assertEqual(type(lns.models["new_model"]), dict)
        self.assertIsNotNone(lns.models["current_model"])
        self.assertEqual(type(lns.models["current_model"]), dict)
        self.assertIsNotNone(lns.models["best_model"])
        self.assertEqual(type(lns.models["best_model"]), dict)

        lns = LNS(["./tests/ref/bad_encoding.lp"])
        lns.set_params({"seed": 123})
        ctl = lns_pkg.lib.theory.setup_clingo(lns)[0]
        self.assertEqual(
            lns_pkg.lib.search.get_first_solution_hc_lexicographic(lns, ctl, thy), False
        )

        lns = LNS(["./tests/ref/golf.lp"])
        lns.set_params({"seed": 123})
        ctl, thy = lns_pkg.lib.theory.setup_clingo(lns)
        self.assertEqual(
            lns_pkg.lib.search.get_first_solution_classic(lns, ctl, thy), True
        )
        self.assertIsNotNone(lns.models["new_model"])
        self.assertEqual(type(lns.models["new_model"]), dict)
        self.assertIsNotNone(lns.models["current_model"])
        self.assertEqual(type(lns.models["current_model"]), dict)
        self.assertIsNotNone(lns.models["best_model"])
        self.assertEqual(type(lns.models["best_model"]), dict)

        lns = LNS(["./tests/ref/bad_encoding.lp"])
        lns.set_params({"seed": 123})
        ctl, thy = lns_pkg.lib.theory.setup_clingo(lns)
        self.assertEqual(
            lns_pkg.lib.search.get_first_solution_classic(lns, ctl, thy), False
        )

    def test_stuck(self):
        """
        Test stuck detection and handling.
        """

        def helper(lns_object):
            lns_object.param_values["stuck"] = True

        lns = LNS(["./tests/ref/golf.lp"], {"finish": helper})
        lns.callables["boundary_handling"](lns, "init")
        self.assertFalse(lns_pkg.search.check_stuck(lns))
        lns.boundary_dict["no_improvement"] = 20000
        self.assertTrue(lns_pkg.search.check_stuck(lns))
        lns_pkg.lib.search.is_stuck(lns)
        self.assertTrue(lns.param_values["stuck"])

    def test_timeout(self):
        """
        Test timeout handling.
        """

        def helper(lns_object):
            _ = lns_object

        lns = LNS(["./tests/ref/golf.lp"], {"is_stuck": helper})
        lns.callables["boundary_handling"](lns, "init")
        lns_pkg.search.time_out(lns)
        self.assertEqual(lns.boundary_dict["timeout"], 1)
        lns.boundary_dict["timeout"] = 5
        with self.assertRaises(SystemExit):
            lns_pkg.search.time_out(lns)

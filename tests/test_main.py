"""
Test cases for main application functionality.
"""

# pylint: disable=protected-access, too-many-public-methods, duplicate-code
import logging
import random
import signal
from io import StringIO
from unittest import TestCase

import clingo
import clingodl
from clingo.symbol import Function, Number

import large_neighbourhood_search as lns_pkg
from large_neighbourhood_search import LNS
from large_neighbourhood_search.utils.logger import setup_logger
from large_neighbourhood_search.utils.parser import get_parser


class TestMain(TestCase):
    """
    Test cases for main application functionality.
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

    def test_lns_init(self):
        """
        Test LNS initialization.
        """
        ref_config_values = {
            "files": ["./tests/ref/golf.lp"],
            "seed": None,
            "relax_rates": [0.2, 0.4, 0.6],
            "bound": 2000,
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
            "better_solution_found": lns_pkg.lib.search.better_solution_found_hc,
            "boundary_handling": lns_pkg.lib.boundary.boundary_overall,
            "check_stop": lns_pkg.lib.boundary.check_stop_steps,
            "finish": lns_pkg.lib.boundary.finish,
            "check_stuck": lns_pkg.lib.search.check_stuck_never,
            "is_stuck": lns_pkg.lib.search.is_stuck,
            "time_out": lns_pkg.lib.search.time_out,
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
            "bound": 2000,
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

    def test_setup_clingo(self):
        """
        Test the clingo setup for LNS.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.set_params({"seed": 123})
        test_ctl, test_thy = lns_pkg.lib.theory.setup_clingo(lns)
        self.assertDictEqual(
            lns.param_values["clingo_args"], {"rand-freq": 0.8, "seed": 123}
        )
        self.assertIsInstance(test_ctl, clingo.control.Control)
        self.assertIsNone(test_thy)

        lns = LNS(["./tests/ref/golf.lp"])
        test_ctl, test_thy = lns_pkg.lib.theory.setup_clingo(lns)
        self.assertDictEqual(lns.param_values["clingo_args"], {"rand-freq": 0.8})
        self.assertIsInstance(test_ctl, clingo.control.Control)
        self.assertIsNone(test_thy)

    def test_setup_clingo_dl(self):
        """
        Test the clingo-dl setup for LNS.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
        )
        lns.set_params({"seed": 123})
        test_ctl, test_thy = lns_pkg.lib.theory.setup_clingo_dl(lns)
        self.assertDictEqual(
            lns.param_values["clingo_args"], {"rand-freq": 0.8, "seed": 123}
        )
        self.assertIsInstance(test_ctl, clingo.control.Control)
        self.assertIsInstance(test_thy, clingodl.ClingoDLTheory)

        lns = LNS(["./tests/ref/golf.lp"])
        test_ctl, test_thy = lns_pkg.lib.theory.setup_clingo_dl(lns)
        self.assertDictEqual(lns.param_values["clingo_args"], {"rand-freq": 0.8})
        self.assertIsInstance(test_ctl, clingo.control.Control)
        self.assertIsInstance(test_thy, clingodl.ClingoDLTheory)

    def test_variability(self):
        """
        Test variability calculation.
        """
        LNS(["./tests/ref/golf.lp"])
        l1 = [0, 1, 2, 3, 4, 5]
        l2 = [1, 3]
        self.assertEqual(lns_pkg.lib.lns_utils.calculate_variability(l1, l2), 0)
        l2 = [0, 2, 6, 7]
        self.assertEqual(lns_pkg.lib.lns_utils.calculate_variability(l1, l2), 0.5)
        self.assertEqual(lns_pkg.lib.lns_utils.calculate_variability(l2, l1), 0.5)

    def test_stats(self):
        """
        Test stats getter. WIP
        """
        lns = lns = LNS(["./tests/ref/golf.lp"])
        test_ctl = lns_pkg.lib.theory.setup_clingo(lns)[0]
        self.assertEqual(type(lns.get_stats(test_ctl)), dict)

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

    def test_calc_opt_val_weighted_sum(self):
        """
        Test optimization value calculation using weighted sum.
        """
        model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
                Function("plays", [Number(5), Number(1), Number(1)], True),
                Function("plays", [Number(9), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function("meets", [Number(7), Number(9), Number(3)], True),
                Function("meets", [Number(8), Number(9), Number(3)], True),
                Function(
                    "_opt",
                    [
                        Function("", [Number(1), Number(2)], True),
                        Function("", [Number(1), Number(1)], True),
                    ],
                    True,
                ),
                Function(
                    "_opt",
                    [
                        Function("", [Number(3), Number(5)], True),
                        Function("", [Number(1), Number(2)], True),
                    ],
                    True,
                ),
                Function(
                    "_opt",
                    [
                        Function("", [Number(4), Number(5)], True),
                        Function("", [Number(3), Number(1)], True),
                    ],
                    True,
                ),
                Function(
                    "_opt",
                    [
                        Function("", [Number(7), Number(8)], True),
                        Function("", [Number(2), Number(2)], True),
                    ],
                    True,
                ),
            ],
        }
        self.assertEqual(lns_pkg.lib.lns_utils.calc_opt_val_weighted_sum(model), 6)

    def test_calc_opt_val_lexicographic(self):
        """
        Test optimization value calculation using lexicographic ordering.
        """
        model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
                Function("plays", [Number(5), Number(1), Number(1)], True),
                Function("plays", [Number(9), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function("meets", [Number(7), Number(9), Number(3)], True),
                Function("meets", [Number(8), Number(9), Number(3)], True),
                Function(
                    "_opt",
                    [
                        Function("", [Number(1), Number(2)], True),
                        Function("", [Number(1), Number(1)], True),
                    ],
                    True,
                ),
                Function(
                    "_opt",
                    [
                        Function("", [Number(3), Number(5)], True),
                        Function("", [Number(1), Number(2)], True),
                    ],
                    True,
                ),
                Function(
                    "_opt",
                    [
                        Function("", [Number(4), Number(5)], True),
                        Function("", [Number(3), Number(1)], True),
                    ],
                    True,
                ),
                Function(
                    "_opt",
                    [
                        Function("", [Number(7), Number(8)], True),
                        Function("", [Number(2), Number(2)], True),
                    ],
                    True,
                ),
            ],
        }
        ref = {1: 3, 3: 1, 2: 2}
        self.assertDictEqual(
            lns_pkg.lib.lns_utils.calc_opt_val_lexicographic(model), ref
        )

    def test_lexi_comparison(self):
        """
        Test comparison of lexicographic values.
        """
        val1 = {2: 10}
        val2 = {3: 1, 1: 1}
        self.assertTrue(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val1, val2))
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val2, val1))
        val1 = {3: 2}
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val1, val2))
        self.assertTrue(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val2, val1))
        val1 = {3: 1, 1: 2}
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val1, val2))
        self.assertTrue(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val2, val1))
        val1 = val2
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val1, val2))
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val2, val1))
        val1 = {}
        self.assertTrue(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val1, val2))
        self.assertFalse(lns_pkg.lib.lns_utils.check_smaller_lexicographic(val2, val1))

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
                    "_opt",
                    [
                        Function("", [Number(1), Number(2)], True),
                        Function("", [Number(1), Number(2)], True),
                    ],
                    True,
                ),
                Function(
                    "_opt",
                    [
                        Function("", [Number(3), Number(5)], True),
                        Function("", [Number(2), Number(1)], True),
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
                    "_opt",
                    [
                        Function("", [Number(1), Number(2)], True),
                        Function("", [Number(1), Number(2)], True),
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
                    "_opt",
                    [
                        Function("", [Number(1), Number(2)], True),
                        Function("", [Number(1), Number(2)], True),
                    ],
                    True,
                ),
                Function(
                    "_opt",
                    [
                        Function("", [Number(3), Number(5)], True),
                        Function("", [Number(1), Number(1)], True),
                    ],
                    True,
                ),
                Function(
                    "_opt",
                    [
                        Function("", [Number(4), Number(5)], True),
                        Function("", [Number(3), Number(1)], True),
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
                    "_opt",
                    [
                        Function("", [Number(1), Number(2)], True),
                        Function("", [Number(1), Number(1)], True),
                    ],
                    True,
                ),
                Function(
                    "_opt",
                    [
                        Function("", [Number(3), Number(5)], True),
                        Function("", [Number(1), Number(1)], True),
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
                    "_opt",
                    [
                        Function("", [Number(1), Number(2)], True),
                        Function("", [Number(1), Number(1)], True),
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
                    "_opt",
                    [
                        Function("", [Number(1), Number(2)], True),
                        Function("", [Number(1), Number(1)], True),
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

    def test_repair_clingo(self):
        """
        Test reparation of solution using clingo.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.set_params({"seed": 123})

        ctl = lns_pkg.lib.theory.setup_clingo(lns)[0]
        lns_pkg.lib.theory.ground_base(lns, ctl)
        self.assertTrue(
            lns_pkg.lib.theory.repair_clingo(lns, ctl, [], None).satisfiable
        )
        self.assertTrue(lns.models["new_model"])

        assumptions = lns_pkg.lib.search.relax_random(
            lns.models["new_model"], {"relax_rate": 0.2}
        )
        lns.models["new_model"] = {}
        self.assertTrue(
            lns_pkg.lib.theory.repair_clingo(lns, ctl, assumptions, None).satisfiable
        )
        self.assertTrue(lns.models["new_model"])

        assumptions_atoms = list(map(lambda x: x[0], assumptions))
        for atom in assumptions_atoms:
            self.assertIn(atom, lns.models["new_model"]["true"])

        lns = LNS(["./tests/ref/bad_encoding.lp"])
        lns.set_params({"seed": 123})
        ctl, thy = lns_pkg.lib.theory.setup_clingo(lns)
        lns_pkg.lib.theory.ground_base(lns, ctl)
        self.assertFalse(
            lns_pkg.lib.theory.repair_clingo(lns, ctl, [], thy).satisfiable
        )

    def test_repair_clingo_dl(self):
        """
        Test reparation of solution using clingo-dl.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.set_params({"seed": 123})

        ctl, thy = lns_pkg.lib.theory.setup_clingo_dl(lns)
        lns_pkg.lib.theory.ground_base(lns, ctl)
        self.assertTrue(
            lns_pkg.lib.theory.repair_clingo_dl(lns, ctl, [], thy).satisfiable
        )
        self.assertTrue(lns.models["new_model"])

        assumptions = lns_pkg.lib.search.relax_random(
            lns.models["new_model"], {"relax_rate": 0.2}
        )
        lns.models["new_model"] = {}
        self.assertTrue(
            lns_pkg.lib.theory.repair_clingo_dl(lns, ctl, assumptions, thy).satisfiable
        )
        self.assertTrue(lns.models["new_model"])

        assumptions_atoms = list(map(lambda x: x[0], assumptions))
        for atom in assumptions_atoms:
            self.assertIn(atom, lns.models["new_model"]["true"])

        lns = LNS(["./tests/ref/bad_encoding.lp"])
        lns.set_params({"seed": 123})
        ctl, thy = lns_pkg.lib.theory.setup_clingo_dl(lns)
        lns_pkg.lib.theory.ground_base(lns, ctl)
        self.assertFalse(
            lns_pkg.lib.theory.repair_clingo_dl(lns, ctl, [], thy).satisfiable
        )

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

    def test_main(self):
        """
        Test main method.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.main()

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

        lns = LNS(
            ["./tests/ref/golf.lp"],
            {"check_stop": lns_pkg.lib.boundary.check_stop_time},
        )
        lns.set_params({"seed": 123})
        lns.main()

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

        # faulty encoding
        lns = LNS(["./tests/ref/bad_encoding.lp"])
        lns.set_params({"seed": 123})
        lns.main()

        # clingo-dl
        lns = LNS(
            ["./tests/ref/golf.lp"],
            {
                "setup": lns_pkg.lib.theory.setup_clingo_dl,
                "repair": lns_pkg.lib.theory.repair_clingo_dl,
            },
        )
        lns.set_params({"seed": 123})
        lns.main()

        # stuck
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

        # timeout
        lns = LNS(
            ["./tests/ref/golf_big.lp"],
        )
        lns.set_params({"seed": 123, "time_limit": 1})
        with self.assertRaises(SystemExit):
            lns.main()

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

        # invalid params
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

"""
Test cases for main application functionality.
"""

# pylint: disable=protected-access, too-many-public-methods, duplicate-code
import logging
import random
from io import StringIO
from unittest import TestCase

import clingo
from clingo.symbol import Function, Number

from large_neighbourhood_search import LNS
from large_neighbourhood_search.lib import lns_functions as lns_f
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
            "relax_rates": [0.2],
            "current_relax_rate": 0.2,
            "bound": 2000,
            "switch_rr_after_no_improv": 3,
            "clingo_args": ["--rand-freq=0.8"],
        }

        ref_callables = {
            "on_model": lns_f.on_model,
            "relax": lns_f.relax_random,
            "repair": lns_f.repair,
            "calc_opt_value": lns_f.calculate_opt_val,
            "get_first_solution": lns_f.get_first_solution_hard_constraint,
            "check_accept": lns_f.check_accept_always,
            "check_better": lns_f.check_better_always,
            "better_solution_found": lns_f.better_solution_found_hard_constraint,
            "boundary_handling": lns_f.boundary_overall,
            "check_stop": lns_f.check_stop_steps,
        }

        lns = LNS(["./tests/ref/golf.lp"])
        self.assertDictEqual(lns.config_values, ref_config_values)
        self.assertDictEqual(lns.callables, ref_callables)

        ref_config_values = {
            **ref_config_values,
            **{
                "seed": 123,
                "relax_rates": [0.4],
                "current_relax_rate": 0.4,
                "clingo_args": ["--test"],
            },
        }
        ref_callables = {**ref_callables, **{"test": print, "on_model": print}}
        lns = LNS(
            ["./tests/ref/golf.lp"],
            {"test": print, "on_model": print},
            123,
            [0.4],
            ["--test"],
        )
        self.assertDictEqual(lns.config_values, ref_config_values)
        self.assertDictEqual(lns.callables, ref_callables)

    def test_get_set_params(self):
        """
        Test parameter getter and setter.
        """
        ref_config_values = {
            "files": ["./tests/ref/golf.lp"],
            "seed": None,
            "relax_rates": [0.2],
            "current_relax_rate": 0.2,
            "bound": 2000,
            "switch_rr_after_no_improv": 3,
            "clingo_args": ["--rand-freq=0.8"],
        }
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertDictEqual(lns.get_params(), ref_config_values)
        lns.set_params({"seed": 123, "new_param": "new"})
        self.assertDictEqual(
            lns.get_params(), {**ref_config_values, **{"seed": 123, "new_param": "new"}}
        )

    def test_lns_setup(self):
        """
        Test the clingo setup for LNS.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            seed=123,
        )
        test_ctl = lns.setup()
        self.assertListEqual(
            lns.config_values["clingo_args"], ["--rand-freq=0.8", "--seed=123"]
        )
        self.assertIsInstance(test_ctl, clingo.control.Control)

        lns = LNS(["./tests/ref/golf.lp"])
        test_ctl = lns.setup()
        self.assertEqual(lns.config_values["clingo_args"], ["--rand-freq=0.8"])
        self.assertIsInstance(test_ctl, clingo.control.Control)

    def test_variability(self):
        """
        Test variability calculation.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        l1 = [0, 1, 2, 3, 4, 5]
        l2 = [1, 3]
        self.assertEqual(lns.get_variability(l1, l2), 0)
        l2 = [0, 2, 6, 7]
        self.assertEqual(lns.get_variability(l1, l2), 0.5)
        self.assertEqual(lns.get_variability(l2, l1), 0.5)

    def test_stats(self):
        """
        Test stats getter. WIP
        """
        lns = lns = LNS(["./tests/ref/golf.lp"])
        test_ctl = lns.setup()
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
        self.assertListEqual(lns_f.relax_random(model, 0.2), ref)

        random.seed(seed)
        ref = [(Function("plays", [Number(2), Number(1), Number(3)], True), True)]
        self.assertListEqual(lns_f.relax_declarative(model, 0.2), ref)

    def test_calc_opt_val(self):
        """
        Test optimization value calculation.
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
                    "_minimize",
                    [Number(1), Function("", [Number(1), Number(2)], True)],
                    True,
                ),
                Function(
                    "_minimize",
                    [Number(1), Function("", [Number(3), Number(5)], True)],
                    True,
                ),
                Function(
                    "_minimize",
                    [Number(1), Function("", [Number(4), Number(5)], True)],
                    True,
                ),
                Function(
                    "_minimize",
                    [Number(1), Function("", [Number(7), Number(8)], True)],
                    True,
                ),
            ],
        }
        self.assertEqual(lns_f.calculate_opt_val(model), 4)

    def test_check_better(self):
        """
        Test check_better.
        """
        best_model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function(
                    "_minimize",
                    [Number(1), Function("", [Number(1), Number(2)], True)],
                    True,
                ),
                Function(
                    "_minimize",
                    [Number(1), Function("", [Number(3), Number(5)], True)],
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
                    "_minimize",
                    [Number(1), Function("", [Number(1), Number(2)], True)],
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
                    "_minimize",
                    [Number(1), Function("", [Number(1), Number(2)], True)],
                    True,
                ),
                Function(
                    "_minimize",
                    [Number(1), Function("", [Number(3), Number(5)], True)],
                    True,
                ),
                Function(
                    "_minimize",
                    [Number(1), Function("", [Number(4), Number(5)], True)],
                    True,
                ),
            ],
        }
        lns = LNS(["./tests/ref/golf.lp"])

        self.assertTrue(lns_f.check_better_classic(lns, better_model, best_model))
        self.assertFalse(lns_f.check_better_classic(lns, worse_model, best_model))

        self.assertTrue(lns_f.check_better_always(lns, better_model, best_model))
        self.assertTrue(lns_f.check_better_always(lns, worse_model, best_model))

    def test_check_acceptance(self):
        """
        Test check_accept.
        """
        best_model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function(
                    "_minimize",
                    [Number(1), Function("", [Number(1), Number(2)], True)],
                    True,
                ),
                Function(
                    "_minimize",
                    [Number(1), Function("", [Number(3), Number(5)], True)],
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
                    "_minimize",
                    [Number(1), Function("", [Number(1), Number(2)], True)],
                    True,
                ),
            ],
        }
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertTrue(lns_f.check_better_always(lns, new_model, best_model))

    def test_first_solution(self):
        """
        Test finding of first solution.
        """
        lns = LNS(["./tests/ref/golf.lp"], seed=123)
        ctl = lns.setup()
        self.assertEqual(lns_f.get_first_solution_hard_constraint(lns, ctl), True)
        self.assertIsNotNone(lns.models["new_model"])
        self.assertEqual(type(lns.models["new_model"]), dict)
        self.assertIsNotNone(lns.models["current_model"])
        self.assertEqual(type(lns.models["current_model"]), dict)
        self.assertIsNotNone(lns.models["best_model"])
        self.assertEqual(type(lns.models["best_model"]), dict)

        lns = LNS(["./tests/ref/bad_encoding.lp"], seed=123)
        ctl = lns.setup()
        self.assertEqual(lns_f.get_first_solution_hard_constraint(lns, ctl), False)

        lns = LNS(["./tests/ref/golf.lp"], seed=123)
        ctl = lns.setup()
        self.assertEqual(lns_f.get_first_solution_classic(lns, ctl), True)
        self.assertIsNotNone(lns.models["new_model"])
        self.assertEqual(type(lns.models["new_model"]), dict)
        self.assertIsNotNone(lns.models["current_model"])
        self.assertEqual(type(lns.models["current_model"]), dict)
        self.assertIsNotNone(lns.models["best_model"])
        self.assertEqual(type(lns.models["best_model"]), dict)

        lns = LNS(["./tests/ref/bad_encoding.lp"], seed=123)
        ctl = lns.setup()
        self.assertEqual(lns_f.get_first_solution_classic(lns, ctl), False)

    def test_repair(self):
        """
        Test reparation of solution.
        """
        lns = LNS(["./tests/ref/golf.lp"], seed=123)

        ctl = lns.setup()
        lns_f.get_first_solution_classic(lns, ctl)

        assumptions = lns_f.relax_random(
            lns.models["best_model"], lns.config_values["current_relax_rate"]
        )
        res = lns_f.repair(lns, ctl, assumptions)
        self.assertIsNotNone(res)
        self.assertEqual(type(res), clingo.solving.SolveResult)

        assumptions_atoms = list(map(lambda x: x[0], assumptions))
        for atom in assumptions_atoms:
            self.assertIn(atom, lns.models["new_model"]["true"])

    def test_boundary_overall_init(self):
        """
        Test "init" action of boundary_overall.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        boundary_dict = {}
        self.assertTrue(lns_f.boundary_overall(lns, boundary_dict, "init"))
        self.assertEqual(boundary_dict["bound"], lns.config_values["bound"])
        self.assertEqual(boundary_dict["step"], 0)
        s_time = boundary_dict["start_time"]
        self.assertEqual(type(s_time), float)
        self.assertEqual(boundary_dict["no_improvement"], 0)

    def test_boundary_overall_update(self):
        """
        Test "update" action of boundary_overall.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        boundary_dict = {}
        lns_f.boundary_overall(lns, boundary_dict, "init")
        s_time = boundary_dict["start_time"]
        self.assertTrue(lns_f.boundary_overall(lns, boundary_dict, "update"))
        self.assertEqual(boundary_dict["bound"], lns.config_values["bound"])
        self.assertEqual(boundary_dict["step"], 1)
        self.assertEqual(boundary_dict["start_time"], s_time)
        self.assertEqual(boundary_dict["no_improvement"], 0)

    def test_boundary_overall_improvement(self):
        """
        Test "improvement" action of boundary_overall.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        boundary_dict = {}
        lns_f.boundary_overall(lns, boundary_dict, "init")
        lns_f.boundary_overall(lns, boundary_dict, "update")
        s_time = boundary_dict["start_time"]
        self.assertTrue(lns_f.boundary_overall(lns, boundary_dict, "improvement"))
        self.assertEqual(boundary_dict["bound"], lns.config_values["bound"])
        self.assertEqual(boundary_dict["step"], 1)
        self.assertEqual(boundary_dict["start_time"], s_time)
        self.assertEqual(boundary_dict["no_improvement"], 0)

    def test_boundary_overall_no_improvement(self):
        """
        Test "no_improvement" action of boundary_overall.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.config_values["relax_rates"] = [0.2, 0.4]
        lns.config_values["current_relax_rate"] = 0.2
        lns.config_values["switch_rr_after_no_improv"] = 1
        boundary_dict = {}
        lns_f.boundary_overall(lns, boundary_dict, "init")
        s_time = boundary_dict["start_time"]
        self.assertTrue(lns_f.boundary_overall(lns, boundary_dict, "no_improvement"))
        self.assertEqual(boundary_dict["bound"], lns.config_values["bound"])
        self.assertEqual(boundary_dict["step"], 0)
        self.assertEqual(boundary_dict["start_time"], s_time)
        self.assertEqual(boundary_dict["no_improvement"], 1)
        self.assertEqual(lns.config_values["current_relax_rate"], 0.4)
        self.assertTrue(lns_f.boundary_overall(lns, boundary_dict, "no_improvement"))
        self.assertEqual(lns.config_values["current_relax_rate"], 0.2)

        self.assertFalse(lns_f.boundary_overall(lns, boundary_dict, "invalid_action"))

    def test_check_stop_steps(self):
        """
        Test check_stop_steps.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        boundary_dict = {}
        lns_f.boundary_overall(lns, boundary_dict, "init")
        boundary_dict["step"] = 1
        self.assertFalse(lns_f.check_stop_steps(lns, boundary_dict))
        boundary_dict["bound"] = 0
        self.assertTrue(lns_f.check_stop_steps(lns, boundary_dict))

    def test_check_stop_time(self):
        """
        Test check_stop_time.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        boundary_dict = {}
        lns_f.boundary_overall(lns, boundary_dict, "init")
        self.assertFalse(lns_f.check_stop_time(lns, boundary_dict))
        boundary_dict["bound"] = 0
        self.assertTrue(lns_f.check_stop_time(lns, boundary_dict))

    def test_main(self):
        """
        Test main method.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.main()

        lns = LNS(
            ["./tests/ref/golf.lp"],
            {
                "check_better": lns_f.check_better_classic,
                "better_solution_found": lns_f.better_solution_found_classic,
                "get_first_solution": lns_f.get_first_solution_classic,
            },
            122,
        )
        lns._search_mode = "classic"
        # lns.callables["check_better"] = lns_f.check_better_classic
        # lns.callables["better_solution_found"] = lns_f.better_solution_found_classic
        lns.main()

        lns = LNS(["./tests/ref/golf.lp"], {"check_stop": lns_f.check_stop_time}, 123)
        # lns.callables["check_stop"] = lns_f.check_stop_time
        lns.main()

        # faulty encoding
        lns = LNS(["./tests/ref/bad_encoding.lp"], seed=123)
        lns.main()

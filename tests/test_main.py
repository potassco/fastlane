"""
Test cases for main application functionality.
"""

# pylint: disable=protected-access, too-many-public-methods
import logging
import os
import random
from io import StringIO
from unittest import TestCase, mock

import clingo
from clingo.symbol import Function, Number

from large_neighbourhood_search import LNS
from large_neighbourhood_search.lib import lns_functions as lns_f
from large_neighbourhood_search.utils.logger import setup_logger
from large_neighbourhood_search.utils.parser import get_parser
from large_neighbourhood_search.utils.pf_handling import (
    create_param_file,
    gen_example_params,
    load_param_file,
    save_param_file,
)


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

    def test_load_param_file(self):
        """
        Test the loading of parameters from file.
        """
        ref_content = {
            "name": "example_params",
            "relaxation": {
                "mode": "declarative",
                "rates": [0.2, 0.4, 0.6],
                "threshold": 3,
            },
            "search": {
                "mode": "hard_constraint",
                "bound": {"mode": "overall", "type": "steps", "value": 2000},
            },
            "seed": None,
        }
        test_content = load_param_file("./tests/ref/example_params_ref.json")
        self.assertDictEqual(test_content, ref_content)

    def test_save_param_file(self):
        """
        Test the saving of parameters.
        """
        ref_content = {
            "name": "example_params",
            "relaxation": {
                "mode": "declarative",
                "rates": [0.2, 0.4, 0.6],
                "threshold": 3,
            },
            "search": {
                "mode": "hard_constraint",
                "bound": {"mode": "overall", "type": "steps", "value": 2000},
            },
            "seed": None,
        }
        save_param_file(ref_content, "./tests/test.json")
        test_content = load_param_file("./tests/test.json")
        os.remove("./tests/test.json")
        self.assertDictEqual(test_content, ref_content)

    def test_gen_example_param_file(self):
        """
        Test the generation of an example parameter file.
        """
        gen_example_params("./tests")
        test_content = load_param_file("./tests/example_params.json")
        os.remove("./tests/example_params.json")
        ref_content = load_param_file("./tests/ref/example_params_ref.json")
        self.assertDictEqual(test_content, ref_content)

    @mock.patch("large_neighbourhood_search.utils.pf_handling.input", create=True)
    def test_create_param_file(self, mocked_input):
        """
        Test the creation of a new parameter file.
        """
        mocked_input.side_effect = [
            "test",
            "bla",
            "1",
            "-2",
            "0.2",
            "x",
            "0.4",
            "0",
            "-3",
            "3",
            "3",
            "0",
            "-2",
            "1",
            "bla",
            "0",
            "-3",
            "1500",
            "bla",
            "None",
        ]
        create_param_file("./tests/")
        test_content = load_param_file("./tests/test.json")
        os.remove("./tests/test.json")
        ref_content = {
            "name": "test",
            "relaxation": {
                "mode": "declarative",
                "rates": [0.2, 0.4],
                "threshold": 3,
            },
            "search": {
                "mode": "hard_constraint",
                "bound": {"mode": "per_improvement", "type": "steps", "value": 1500},
            },
            "seed": None,
        }
        self.assertDictEqual(test_content, ref_content)

    def test_lns_load_params(self):
        """
        Test the loading of parameters for LNS.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            None,
            0.2,
            False,
            "./tests/ref/example_params_ref.json",
        )
        lns.load_params(lns.param_path)
        self.assertEqual(lns._relax_mode, "declarative")
        self.assertEqual(lns.config_values["relax_rates"], [0.2, 0.4, 0.6])
        self.assertEqual(lns.config_values["current_relax_rate"], 0.2)
        self.assertEqual(lns.config_values["switch_rr_after_unsat"], 3)
        self.assertEqual(lns._search_mode, "hard_constraint")
        self.assertEqual(lns._bound_mode, "overall")
        self.assertEqual(lns._bound_type, "steps")
        self.assertEqual(lns.config_values["bound"], 2000)
        self.assertEqual(lns.config_values["seed"], None)

    def test_lns_init(self):
        """
        Test LNS initialization.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertEqual(lns.config_values["files"], ["./tests/ref/golf.lp"])
        self.assertEqual(lns.config_values["clingo_args"], [])
        self.assertEqual(lns.config_values["seed"], None)
        self.assertEqual(lns.config_values["current_relax_rate"], 0.2)
        self.assertEqual(lns.config_values["relax_rates"], [0.2])
        self.assertEqual(lns._relax_mode, "random")
        self.assertEqual(lns.param_path, None)

        lns = LNS(
            ["./tests/ref/golf.lp"],
            ["--test"],
            123,
            0.4,
            True,
            "./tests/test.json",
        )
        self.assertEqual(lns.config_values["files"], ["./tests/ref/golf.lp"])
        self.assertEqual(lns.config_values["clingo_args"], ["--test"])
        self.assertEqual(lns.config_values["seed"], 123)
        self.assertEqual(lns.config_values["current_relax_rate"], 0.4)
        self.assertEqual(lns.config_values["relax_rates"], [0.4])
        self.assertEqual(lns._relax_mode, "declarative")
        self.assertEqual(lns.param_path, "./tests/test.json")

    def test_lns_setup(self):
        """
        Test the clingo setup for LNS.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            123,
            0.2,
            False,
            "./tests/test.json",
        )
        params = {
            "name": "example_params",
            "relaxation": {
                "mode": "declarative",
                "rates": [0.2, 0.4, 0.6],
                "threshold": 3,
            },
            "search": {
                "mode": "hard_constraint",
                "bound": {"mode": "overall", "type": "steps", "value": 2000},
            },
            "seed": 123,
        }
        save_param_file(params, "./tests/test.json")
        test_ctl = lns.setup()
        self.assertEqual(lns.config_values["clingo_args"], ["--seed=123"])
        self.assertIsInstance(test_ctl, clingo.control.Control)

        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            None,
            0.2,
            False,
            "./tests/test.json",
        )
        params["seed"] = None
        params["search"]["mode"] = "classic"
        save_param_file(params, "./tests/test.json")
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
        lns._search_mode = "hard_constraint"
        self.assertEqual(lns.get_first_solution(ctl), True)
        self.assertIsNotNone(lns.models["new_model"])
        self.assertEqual(type(lns.models["new_model"]), dict)
        self.assertIsNotNone(lns.models["current_model"])
        self.assertEqual(type(lns.models["current_model"]), dict)
        self.assertIsNotNone(lns.models["best_model"])
        self.assertEqual(type(lns.models["best_model"]), dict)

        lns = LNS(["./tests/ref/bad_encoding.lp"], seed=123)
        ctl = lns.setup()
        self.assertEqual(lns.get_first_solution(ctl), False)

    def test_repair(self):
        """
        Test reparation of solution.
        """
        lns = LNS(["./tests/ref/golf.lp"], seed=123)
        lns._search_mode = "classic"
        ctl = lns.setup()
        lns.get_first_solution(ctl)

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
        lns._bound_mode = "overall"
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
        lns.config_values["switch_rr_after_unsat"] = 1
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
        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            123,
            0.2,
            False,
            "./tests/ref/example_params_ref.json",
        )
        lns.main()

        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            122,
            0.2,
            False,
        )
        lns._search_mode = "classic"
        lns.callables["check_better"] = lns_f.check_better_classic
        lns.callables["better_solution_found"] = lns_f.better_solution_found_classic
        lns.main()

        lns = LNS(["./tests/ref/golf.lp"], seed=123)
        lns.callables["check_stop"] = lns_f.check_stop_time
        lns.main()

        # faulty encoding
        lns = LNS(["./tests/ref/bad_encoding.lp"], seed=123)
        lns.main()

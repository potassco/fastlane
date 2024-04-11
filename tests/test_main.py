"""
Test cases for main application functionality.
"""

# pylint: disable=protected-access, too-many-public-methods
import logging
import os
import random
import time
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
            False,
            "./tests/ref/example_params_ref.json",
        )
        lns.load_params(lns.param_path)
        self.assertEqual(lns._relax_mode, "declarative")
        self.assertEqual(lns._relax_rates, [0.2, 0.4, 0.6])
        self.assertEqual(lns._relax_rate, 0.2)
        self.assertEqual(lns._unsat_threshold, 3)
        self.assertEqual(lns._search_mode, "hard_constraint")
        self.assertEqual(lns._bound_mode, "overall")
        self.assertEqual(lns._bound_type, "steps")
        self.assertEqual(lns._bound, 2000)
        self.assertEqual(lns._seed, None)

    def test_lns_init(self):
        """
        Test LNS initialization.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertEqual(lns._files, ["./tests/ref/golf.lp"])
        self.assertEqual(lns._clingo_args, [])
        self.assertEqual(lns._seed, None)
        self.assertEqual(lns._relax_rate, 0.2)
        self.assertEqual(lns._relax_rates, [0.2])
        self.assertEqual(lns._bnb_search, False)
        self.assertEqual(lns._relax_mode, "random")
        self.assertEqual(lns.param_path, None)

        lns = LNS(
            ["./tests/ref/golf.lp"],
            ["--test"],
            123,
            0.4,
            True,
            True,
            "./tests/test.json",
        )
        self.assertEqual(lns._files, ["./tests/ref/golf.lp"])
        self.assertEqual(lns._clingo_args, ["--test"])
        self.assertEqual(lns._seed, 123)
        self.assertEqual(lns._relax_rate, 0.4)
        self.assertEqual(lns._relax_rates, [0.4])
        self.assertEqual(lns._bnb_search, True)
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
        self.assertEqual(lns._clingo_args, ["--seed=123"])
        self.assertIsInstance(test_ctl, clingo.control.Control)

        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            None,
            0.2,
            False,
            False,
            "./tests/test.json",
        )
        params["seed"] = None
        params["search"]["mode"] = "classic"
        save_param_file(params, "./tests/test.json")
        test_ctl = lns.setup()
        self.assertEqual(lns._clingo_args, ["--rand-freq=0.8"])
        self.assertIsInstance(test_ctl, clingo.control.Control)

        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            123,
            0.2,
            True,
            False,
            "./tests/test.json",
        )
        test_ctl = lns.setup()
        self.assertEqual(lns._relax_rate, 1)
        self.assertIsInstance(test_ctl, clingo.control.Control)
        os.remove("./tests/test.json")

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

    def test_acceptance(self):
        """
        Test acceptance check.
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
            ],
        }
        lns = LNS(["./tests/ref/golf.lp"], seed=123)
        lns._best_val = 4
        self.assertEqual(lns_f.check_acceptance_classic(lns, model), True)
        lns._best_val = 3
        self.assertEqual(lns_f.check_acceptance_classic(lns, model), False)
        self.assertEqual(lns_f.check_acceptance_always(lns, model), True)

    def test_first_solution(self):
        """
        Test finding of first solution.
        """
        lns = LNS(["./tests/ref/golf.lp"], seed=123)
        ctl = lns.setup()
        lns._search_mode = "hard_constraint"
        self.assertEqual(lns.get_first_solution(ctl), True)
        self.assertIsNotNone(lns._best_val)
        self.assertEqual(type(lns._best_val), int)
        self.assertIsNotNone(lns._model)
        self.assertEqual(type(lns._model), dict)
        self.assertIsNotNone(lns._best_model)
        self.assertEqual(type(lns._best_model), dict)

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

        assumptions = lns_f.relax_random(lns._best_model, lns._relax_rate)
        res = lns_f.repair(lns, ctl, assumptions)
        self.assertIsNotNone(res)
        self.assertEqual(type(res), clingo.solving.SolveResult)

        assumptions_atoms = list(map(lambda x: x[0], assumptions))
        for atom in assumptions_atoms:
            self.assertIn(atom, lns._model["true"])

    def test_print_step(self):
        """
        Test message output.
        """
        lns = LNS(["./tests/ref/golf.lp"], seed=123)
        lns.setup()
        lns._bound = 2
        lns._bound_type = "steps"
        self.assertEqual(lns.print_step(1, 1.23456), "1|2, relax rate 0.2:")
        lns._bound_type = "time"
        self.assertEqual(type(lns.print_step(1, 1.23456)), str)

    def test_handle_limit_init(self):
        """
        Test "init" action of handle_limit.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        limit = {}
        self.assertTrue(lns.handle_limit(limit, "init"))
        self.assertEqual(limit["bound"], lns._bound)
        self.assertEqual(limit["step"], 0)
        s_time = limit["start_time"]
        self.assertEqual(type(s_time), float)
        self.assertEqual(limit["step_for_improvement"], 0)
        self.assertEqual(limit["improvement_start_time"], s_time)
        self.assertEqual(limit["no_improvement"], 0)

    def test_handle_limit_update(self):
        """
        Test "update" action of handle_limit.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        limit = {}
        lns.handle_limit(limit, "init")
        s_time = limit["start_time"]
        self.assertTrue(lns.handle_limit(limit, "update"))
        self.assertEqual(limit["bound"], lns._bound)
        self.assertEqual(limit["step"], 1)
        self.assertEqual(limit["start_time"], s_time)
        self.assertEqual(limit["step_for_improvement"], 1)
        self.assertEqual(limit["improvement_start_time"], limit["start_time"])
        self.assertEqual(limit["no_improvement"], 0)

    def test_handle_limit_improvement(self):
        """
        Test "improvement" action of handle_limit.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        limit = {}
        lns.handle_limit(limit, "init")
        lns.handle_limit(limit, "update")
        s_time = limit["start_time"]
        lns._bound_mode = "overall"
        self.assertTrue(lns.handle_limit(limit, "improvement"))
        self.assertEqual(limit["bound"], lns._bound)
        self.assertEqual(limit["step"], 1)
        self.assertEqual(limit["start_time"], s_time)
        self.assertEqual(limit["step_for_improvement"], 1)
        self.assertEqual(limit["improvement_start_time"], limit["start_time"])
        self.assertEqual(limit["no_improvement"], 0)

        time.sleep(0.1)
        lns._bound_mode = "per_improvement"
        self.assertTrue(lns.handle_limit(limit, "improvement"))
        self.assertEqual(limit["bound"], lns._bound)
        self.assertEqual(limit["step"], 1)
        self.assertEqual(limit["start_time"], s_time)
        self.assertEqual(limit["step_for_improvement"], 0)
        self.assertNotEqual(limit["improvement_start_time"], limit["start_time"])
        self.assertEqual(limit["no_improvement"], 0)

    def test_handle_limit_no_improvement(self):
        """
        Test "no_improvement" action of handle_limit.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        limit = {}
        lns.handle_limit(limit, "init")
        s_time = limit["start_time"]
        self.assertTrue(lns.handle_limit(limit, "no_improvement"))
        self.assertEqual(limit["bound"], lns._bound)
        self.assertEqual(limit["step"], 0)
        self.assertEqual(limit["start_time"], s_time)
        self.assertEqual(limit["step_for_improvement"], 0)
        self.assertEqual(limit["improvement_start_time"], limit["start_time"])
        self.assertEqual(limit["no_improvement"], 1)

    def test_handle_limit_check_stop(self):
        """
        Test "check_stop" action of handle_limit.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        limit = {}
        lns.handle_limit(limit, "init")
        lns._bound_type = "steps"
        limit["step_for_improvement"] = 1
        self.assertFalse(lns.handle_limit(limit, "check_stop"))
        limit["bound"] = 0
        self.assertTrue(lns.handle_limit(limit, "check_stop"))
        lns._bound_type = "time"
        self.assertTrue(lns.handle_limit(limit, "check_stop"))
        limit["bound"] = 10
        self.assertFalse(lns.handle_limit(limit, "check_stop"))

        self.assertFalse(lns.handle_limit(limit, "invalid_action"))

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
            False,
            "./tests/ref/example_params_ref.json",
        )
        lns.main()

        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            123,
            0.2,
            False,
            False,
        )
        lns._bound_mode = "per_improvement"
        lns._search_mode = "classic"
        lns.callable_dict["check_acceptance"] = lns_f.check_acceptance_classic
        lns.callable_dict["better_solution_found"] = lns_f.better_solution_found_classic
        lns.main()

        lns = LNS(["./tests/ref/bad_encoding.lp"], seed=123)
        lns.main()

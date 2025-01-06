"""
Test cases for LNS class.
"""

import signal
from unittest import TestCase

from clingo.symbol import Function, Number

from mod_lns import LNS
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.hc_weighted_sum_rnd import HCWeightedSumRnd


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
            "relax_rate": 0.1,
            "max_steps": 2000,
            "clingo_args": {"rand-freq": 0.1},
            "solve_time_limit": 20,
            "overall_time_limit": 600,
            "stuck_after_no_improv": None,
            "start_sol": None,
            "vari_accept": 0,
            "pre_files": [],
            "pre_tl": 1800,
            "base_relax_rate": 0,
        }

        solver = ClingoSolver()
        strategy = HCWeightedSumRnd()

        lns = LNS(["./tests/ref/golf.lp"])
        self.assertDictEqual(lns.param_values, ref_config_values)
        self.assertIsInstance(lns.solver, ClingoSolver)
        self.assertIsInstance(lns.strategy, HCWeightedSumRnd)

        lns = LNS(
            ["./tests/ref/golf.lp"],
            solver,
            strategy,
            {"relax_rate": 0.4, "max_steps": 20},
        )
        self.assertDictEqual(
            lns.param_values,
            {**ref_config_values, **{"relax_rate": 0.4, "max_steps": 20}},
        )
        self.assertEqual(lns.solver, solver)
        self.assertEqual(lns.strategy, strategy)

        lns = LNS(["./tests/ref/golf.lp"], params={"max_steps": "20"})
        self.assertDictEqual(
            lns.param_values, {**ref_config_values, **{"max_steps": 20}}
        )

        lns = LNS(["./tests/ref/golf.lp"], params={"max_steps": "a"})
        self.assertDictEqual(
            lns.param_values, {**ref_config_values, **{"max_steps": None}}
        )

        lns = LNS(["./tests/ref/golf.lp"], params={"max_steps": None})
        self.assertDictEqual(
            lns.param_values, {**ref_config_values, **{"max_steps": None}}
        )

        lns = LNS(["./tests/ref/golf.lp"], params={"stuck_after_no_improv": "20"})
        self.assertDictEqual(
            lns.param_values, {**ref_config_values, **{"stuck_after_no_improv": 20}}
        )

        lns = LNS(["./tests/ref/golf.lp"], params={"stuck_after_no_improv": "a"})
        self.assertDictEqual(
            lns.param_values, {**ref_config_values, **{"stuck_after_no_improv": None}}
        )

        lns = LNS(["./tests/ref/golf.lp"], params={"stuck_after_no_improv": None})
        self.assertDictEqual(
            lns.param_values, {**ref_config_values, **{"stuck_after_no_improv": None}}
        )

    def test_set_params(self):
        """
        Test parameter getter and setter.
        """
        ref_config_values = {
            "files": ["./tests/ref/golf.lp"],
            "seed": None,
            "relax_rate": 0.1,
            "max_steps": 2000,
            "clingo_args": {"rand-freq": 0.1},
            "solve_time_limit": 20,
            "overall_time_limit": 600,
            "stuck_after_no_improv": None,
            "start_sol": None,
            "vari_accept": 0,
            "pre_files": [],
            "pre_tl": 1800,
            "base_relax_rate": 0,
        }
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertDictEqual(lns.get_params(), ref_config_values)
        lns.set_params({"max_steps": 20})
        self.assertDictEqual(
            lns.get_params(),
            {
                **ref_config_values,
                **{"max_steps": 20},
            },
        )
        lns.set_params({"max_steps": "20"})
        self.assertDictEqual(
            lns.get_params(),
            {
                **ref_config_values,
                **{"max_steps": 20},
            },
        )
        lns.set_params({"max_steps": "a"})
        self.assertDictEqual(
            lns.get_params(),
            {
                **ref_config_values,
                **{"max_steps": None},
            },
        )
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertDictEqual(lns.get_params(), ref_config_values)
        lns.set_params({"stuck_after_no_improv": 20})
        self.assertDictEqual(
            lns.get_params(),
            {
                **ref_config_values,
                **{"stuck_after_no_improv": 20},
            },
        )
        lns.set_params({"stuck_after_no_improv": "a"})
        self.assertDictEqual(
            lns.get_params(),
            {
                **ref_config_values,
                **{"stuck_after_no_improv": None},
            },
        )
        lns.set_params({"seed": 123, "new_param": "new", "stuck_after_no_improv": "20"})
        self.assertDictEqual(
            lns.get_params(),
            {
                **ref_config_values,
                **{
                    "seed": 123,
                    "new_param": "new",
                    "stuck_after_no_improv": 20,
                    "clingo_args": {**lns.param_values["clingo_args"], **{"seed": 123}},
                },
            },
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
            lns.param_values["clingo_args"], {"seed": 42, "rand-freq": 0.1}
        )

    def test_get_cost_str(self):
        """
        Test get cost str.
        """
        lns = LNS(["./tests/ref/golf_big.lp"])
        model = {"cost": 1}
        self.assertEqual(lns.get_cost_str(model), "1")
        model["cost"] = {3: 4, 2: 3, 1: 2}
        self.assertEqual(lns.get_cost_str(model), "4 3 2")
        model["cost"] = True
        self.assertEqual(lns.get_cost_str(model), "")

    def test_print_model(self):
        """
        Test print model.
        """
        lns = LNS(["./tests/ref/golf_big.lp"])
        model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
            ],
            "assignments": [
                "test=42",
            ],
            "cost": 2,
        }
        ref_str = "Answer\nplays(3,1,1)\nAssignments:\ntest=42\nCost: 2\n"
        self.assertEqual(lns.print_model(model), ref_str)

    def test_interrupt_handling(self):
        """
        Test interrupt handling.
        """
        model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
            ],
            "assignments": [
                "test=42",
            ],
            "cost": 2,
        }
        lns = LNS(["./tests/ref/golf_big.lp"])
        lns.models["best_model"] = model
        signal.signal(signal.SIGINT, lns.interrupt_handler)
        with self.assertRaises(SystemExit):
            signal.raise_signal(signal.SIGINT)

"""
Test cases for LNS class.
"""

import signal
from unittest import TestCase

from clingo.symbol import Function, Number

from mod_lns import LNS
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lns_config import LNSConfig


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
            "solve_time_limit": 20,
            "overall_time_limit": 600,
            "stuck_after_no_improv": None,
            "start_sol": None,
            "vari_accept": 0,
            "base_relax_rate": 0,
            "heuristics": False,
            "constrained": False,
            "declarative": False,
        }

        lns = LNS(["./tests/ref/golf.lp"])
        self.assertDictEqual(lns.param_values, ref_config_values)
        self.assertEqual(lns.clingo_options, ["--rand-freq=0.05"])
        self.assertIsInstance(lns.solver, ClingoSolver)
        self.assertIsInstance(lns.strategy, DefaultStrategy)

        solver = ClingoSolver()
        strategy = DefaultStrategy()
        config = LNSConfig(
            {"relax_rate": 0.4, "max_steps": 20}, ["--test"], solver, strategy
        )

        lns = LNS(["./tests/ref/golf.lp"], config)
        self.assertDictEqual(
            lns.param_values,
            {**ref_config_values, **{"relax_rate": 0.4, "max_steps": 20}},
        )
        self.assertCountEqual(lns.clingo_options, ["--rand-freq=0.05", "--test"])
        self.assertEqual(lns.solver, solver)
        self.assertEqual(lns.strategy, strategy)

        lns = LNS(["./tests/ref/golf.lp"], LNSConfig({"max_steps": "20"}))
        self.assertDictEqual(
            lns.param_values, {**ref_config_values, **{"max_steps": 20}}
        )

        lns = LNS(["./tests/ref/golf.lp"], LNSConfig({"max_steps": "a"}))
        self.assertDictEqual(
            lns.param_values, {**ref_config_values, **{"max_steps": None}}
        )

        lns = LNS(["./tests/ref/golf.lp"], LNSConfig({"max_steps": None}))
        self.assertDictEqual(
            lns.param_values, {**ref_config_values, **{"max_steps": None}}
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
            "solve_time_limit": 20,
            "overall_time_limit": 600,
            "stuck_after_no_improv": None,
            "start_sol": None,
            "vari_accept": 0,
            "base_relax_rate": 0,
            "heuristics": False,
            "constrained": False,
            "declarative": False,
        }
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertDictEqual(lns.get_parameters(), ref_config_values)
        lns.set_parameters({"max_steps": 20})
        self.assertDictEqual(
            lns.get_parameters(),
            {
                **ref_config_values,
                **{"max_steps": 20},
            },
        )
        lns.set_parameters({"max_steps": "20"})
        self.assertDictEqual(
            lns.get_parameters(),
            {
                **ref_config_values,
                **{"max_steps": 20},
            },
        )
        lns.set_parameters({"max_steps": "a"})
        self.assertDictEqual(
            lns.get_parameters(),
            {
                **ref_config_values,
                **{"max_steps": None},
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

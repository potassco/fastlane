"""
Test cases for LNSConfig class.
"""

from unittest import TestCase
from unittest.mock import patch

import clingo

from mod_lns import LNS
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lns_config import LNSConfig


# pylint: disable=protected-access
class TestLNSConfig(TestCase):
    """
    Test cases for LNSConfig class.
    """

    def test_init(self):
        """
        Test config initialization.
        """
        ref_lns_opt = {
            "heuristics": False,
            "constrained": True,
            "declarative": False,
            "relax_rate": 0.1,
            "max_steps": "2000",
            "solve_time_limit": 20,
            "overall_time_limit": 600,
        }
        ref_clingo_opt = []
        config = LNSConfig()
        self.assertDictEqual(config.lns_options, ref_lns_opt)
        self.assertCountEqual(config.clingo_options, ref_clingo_opt)
        self.assertIsInstance(config.solver, ClingoSolver)
        self.assertIsInstance(config.strategy, DefaultStrategy)

        ref_lns_opt = {
            "heuristics": False,
            "constrained": False,
            "declarative": False,
            "relax_rate": 0.1,
            "max_steps": "2000",
            "solve_time_limit": 20,
            "overall_time_limit": 600,
            "test_opt": "abc",
        }
        ref_clingo_opt = ["--rand-freq=0.05", "--test_opt=123"]
        ref_solver = ClingoSolver()
        ref_strat = DefaultStrategy()

        config = LNSConfig(
            {"test_opt": "abc", "constrained": False},
            ["--test_opt=123"],
            ref_solver,
            ref_strat,
        )
        self.assertDictEqual(config.lns_options, ref_lns_opt)
        self.assertCountEqual(config.clingo_options, ref_clingo_opt)
        self.assertIs(config.solver, ref_solver)
        self.assertIsInstance(config.strategy, type(ref_strat))

        with patch.object(
            LNSConfig, "_enable_heuristics", return_value=None
        ) as mock_method:
            config = LNSConfig({"heuristics": True})
        mock_method.assert_called_once()

        with patch.object(
            LNSConfig, "_enable_constrained_approach", return_value=None
        ) as mock_method:
            config = LNSConfig({"constrained": True})
        mock_method.assert_called_once()

        with patch.object(
            LNSConfig, "_enable_declarative", return_value=None
        ) as mock_method:
            config = LNSConfig({"declarative": True})
        mock_method.assert_called_once()

    def test_enable_heuristics(self):
        """
        Test _enable_heuristics method.
        """
        with (
            patch.object(ClingoSolver, "setup") as solver_setup,
            patch.object(
                ClingoSolver, "repair", return_value=clingo.solving.SolveResult
            ) as solver_repair,
        ):
            ref_solver = ClingoSolver()
            config = LNSConfig({"constrained": False}, solver=ref_solver)
            lns = LNS(["./tests/ref/golf.lp"], config)
            self.assertIsInstance(config.solver, type(ref_solver))
            self.assertIs(config.solver, ref_solver)

            config._enable_heuristics()
            self.assertIsInstance(config.solver, type(ref_solver))
            self.assertIsNot(config.solver, ref_solver)

            config.solver.control = clingo.Control()
            config.solver.setup(lns)
            solver_setup.assert_called_once_with(
                lns, None, ["--rand-freq=0.05", "--heuristic=Domain"]
            )

            config.solver.repair(lns, [])
            solver_repair.assert_called_once_with(lns, [])

        with patch.object(ClingoSolver, "setup") as solver_setup:
            ref_solver = ClingoSolver()
            config = LNSConfig(solver=ref_solver)
            lns = LNS(["./tests/ref/golf.lp"], config)
            self.assertIsInstance(config.solver, type(ref_solver))
            self.assertIs(config.solver, ref_solver)

            config._enable_heuristics()
            self.assertIsInstance(config.solver, type(ref_solver))
            self.assertIsNot(config.solver, ref_solver)

            config.solver.control = clingo.Control()
            config.solver.setup(lns, ["test"], ["--test_arg"])
            solver_setup.assert_called_once_with(
                lns, ["test"], ["--test_arg", "--heuristic=Domain"]
            )

    def test_enable_constrained(self):
        """
        Test _enable_constrained_approach method.
        """
        with (
            patch.object(
                DefaultStrategy, "post_first_solution"
            ) as strat_post_first_solution,
            patch.object(DefaultStrategy, "better") as strat_better,
        ):
            ref_strat = DefaultStrategy()
            config = LNSConfig({"constrained": False}, strategy=ref_strat)
            lns = LNS(["./tests/ref/golf.lp"], config)
            self.assertIsInstance(config.strategy, type(ref_strat))
            self.assertIs(config.strategy, ref_strat)

            config._enable_constrained_approach()
            self.assertIsInstance(config.strategy, type(ref_strat))
            self.assertIsNot(config.strategy, ref_strat)

            config.solver.control = clingo.Control()
            lns.models["new_model"]["cost"] = {1: 1}
            config.strategy.post_first_solution(lns)
            strat_post_first_solution.assert_called_once_with(lns)

            self.assertTrue(config.strategy.check_better(lns))

            lns.models["best_model"]["cost"] = {1: 1}
            config.strategy.better(lns)
            strat_better.assert_called_once_with(lns)

    def test_enable_declarative(self):
        """
        Test _enable_declarative method.
        """

        with patch(
            "mod_lns.lns_config.relax_declarative", return_value=["return"]
        ) as relax_decl:
            ref_strat = DefaultStrategy()
            config = LNSConfig({"constrained": False}, strategy=ref_strat)
            LNS(["./tests/ref/golf.lp"], config)
            self.assertIsInstance(config.strategy, type(ref_strat))
            self.assertIs(config.strategy, ref_strat)

            config._enable_declarative()
            self.assertIsInstance(config.strategy, type(ref_strat))
            self.assertIsNot(config.strategy, ref_strat)
            self.assertEqual(config.strategy.relax({"test": 2}, {"par": 1}), ["return"])
            relax_decl.assert_called_once_with({"test": 2}, {"par": 1})

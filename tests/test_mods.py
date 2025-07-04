"""
Test cases for solver and strategy modifications.
"""

from unittest import TestCase
from unittest.mock import patch

import clingo

from mod_lns.lib.mods.solver_mods import enable_heuristics
from mod_lns.lib.mods.strategy_mods import (
    enable_constrained_approach,
    enable_declarative,
)
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lns import LNS
from mod_lns.lns_config import LNSConfig


class TestSolverMods(TestCase):
    """
    Test cases for solver modifications.
    """

    def test_enable_heuristics(self):
        """
        Test enable_heuristics function.
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

            solver = enable_heuristics(ref_solver)
            self.assertIsInstance(solver, type(ref_solver))
            self.assertIsNot(solver, ref_solver)

            solver.control = clingo.Control()
            solver.setup(lns)
            solver_setup.assert_called_once_with(
                lns, None, ["--rand-freq=0.05", "--heuristic=Domain"]
            )

            solver.repair(lns, [])
            solver_repair.assert_called_once_with(lns, [], None, 1)

        with patch.object(ClingoSolver, "setup") as solver_setup:
            ref_solver = ClingoSolver()
            config = LNSConfig(solver=ref_solver)
            lns = LNS(["./tests/ref/golf.lp"], config)

            solver = enable_heuristics(ref_solver)
            self.assertIsInstance(solver, type(ref_solver))
            self.assertIsNot(solver, ref_solver)

            solver.control = clingo.Control()
            solver.setup(lns, ["test"], ["--test_arg"])
            solver_setup.assert_called_once_with(
                lns, ["test"], ["--test_arg", "--heuristic=Domain"]
            )


class TestStrategyMods(TestCase):
    """
    Test cases for strategy modifications.
    """

    def test_enable_constrained(self):
        """
        Test enable_constrained_approach function.
        """
        with patch.object(
            ClingoSolver, "repair", return_value=clingo.SolveResult(1)
        ) as solver_repair:
            ref_solver = ClingoSolver()
            ref_strat = DefaultStrategy()
            config = LNSConfig(
                {"constrained": False}, solver=ref_solver, strategy=ref_strat
            )
            lns = LNS(["./tests/ref/golf.lp"], config)

            solver, strategy = enable_constrained_approach(ref_solver, ref_strat)
            self.assertIsInstance(solver, type(ref_solver))
            self.assertIsNot(solver, ref_solver)
            self.assertIsInstance(strategy, type(ref_strat))
            self.assertIsNot(strategy, ref_strat)

            solver.control = clingo.Control()
            lns.new_model.cost = [1, 2]
            solver.repair(lns, [])
            solver_repair.assert_called_once_with(lns, [], None, 1)

            self.assertTrue(strategy.check_better(lns))

    def test_enable_declarative(self):
        """
        Test enable_declarative function.
        """

        with patch(
            "mod_lns.lib.mods.strategy_mods.relax_declarative", return_value=["return"]
        ) as relax_decl:
            ref_strat = DefaultStrategy()
            config = LNSConfig({"constrained": False}, strategy=ref_strat)
            LNS(["./tests/ref/golf.lp"], config)

            strategy = enable_declarative(ref_strat)
            self.assertIsInstance(strategy, type(ref_strat))
            self.assertIsNot(strategy, ref_strat)
            self.assertEqual(strategy.relax({"test": 2}, {"par": 1}), ["return"])
            relax_decl.assert_called_once_with({"test": 2}, {"par": 1})

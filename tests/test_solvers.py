"""
Test cases for solver classes.
"""

from typing import Type
from unittest import TestCase

import clingo
import clingodl

from mod_lns import Model
from mod_lns.interfaces.solver import SolverInterface
from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lns import LNS
from mod_lns.lns_config import LNSConfig


class TestSolverClingo(TestCase):
    """
    Test cases for ClingoSolver class.
    """

    def setUp(self) -> None:
        self.solver_type: Type[SolverInterface] = ClingoSolver
        self.solver: SolverInterface = self.solver_type()
        self.strategy = DefaultStrategy()
        config = LNSConfig(solver=self.solver, strategy=self.strategy)
        self.lns = LNS(["./tests/ref/golf.lp"], config)

    def test_setup(self):
        """
        Test clingo setup.
        """
        self.solver.setup(self.lns)
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsNone(self.solver.theory)

        self.lns.set_seed(123)
        self.solver.setup(self.lns)
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsNone(self.solver.theory)

        self.solver.setup(self.lns, ["./tests/ref/golf.lp"], ["--solve-limit=1000"])
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsNone(self.solver.theory)

    def test_repair(self):
        """
        Test repair method.
        """
        self.lns.set_seed(123)
        self.solver.setup(self.lns)
        self.solver.ground_base(self.lns)
        self.assertEqual(self.solver.control.configuration.solve.models, "-1")
        self.assertTrue(self.solver.repair(self.lns, []).satisfiable)
        self.assertEqual(self.solver.control.configuration.solve.models, "1")
        self.assertTrue(self.lns.new_model)

        assumptions = self.strategy.relax(self.lns.new_model, {"relax_rate": 0.2})
        self.lns.new_model = Model()
        self.assertTrue(self.solver.repair(self.lns, assumptions).satisfiable)
        self.assertTrue(self.lns.new_model)

        # flaky
        self.solver.setup(self.lns, ["./tests/ref/golf_big.lp"])
        self.solver.ground_base(self.lns)
        self.assertFalse(self.solver.repair(self.lns, assumptions, 0).satisfiable)

    def test_get_stats(self):
        """
        Test get_statistics method.
        """
        self.lns.set_seed(123)
        self.solver.setup(self.lns)
        self.solver.ground_base(self.lns)
        self.solver.control.solve(on_model=print)
        stats = self.solver.get_stats()
        self.assertIsNotNone(stats)
        self.assertIsInstance(stats["solving"]["solvers"]["choices"], float)

        self.solver.control = None
        self.assertDictEqual(self.solver.get_stats(), {})


class TestSolverClingoDL(TestSolverClingo):
    """
    Test cases for ClingoDLSolver class.

    Test cases for get_avail_solve_time() and solve_under_assumptions()
    inherited from TestSolverClingo.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoDLSolver()
        self.strategy = DefaultStrategy()
        config = LNSConfig(solver=self.solver, strategy=self.strategy)
        self.lns = LNS(["./tests/ref/golf.lp"], config)

    def test_setup(self):
        """
        Test clingoDL setup.
        """
        self.solver.setup(self.lns)
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsInstance(self.solver.theory, clingodl.ClingoDLTheory)

        self.lns.set_seed(123)
        self.solver.setup(self.lns)
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsInstance(self.solver.theory, clingodl.ClingoDLTheory)

        self.solver.setup(self.lns, ["./tests/ref/golf.lp"], ["--solve-limit=1000"])
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsInstance(self.solver.theory, clingodl.ClingoDLTheory)

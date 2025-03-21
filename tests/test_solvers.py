"""
Test cases for solver classes.
"""

from unittest import TestCase

import clingo
import clingodl

from mod_lns import LNS
from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lns_config import LNSConfig


class TestSolverClingo(TestCase):
    """
    Test cases for ClingoSolver class.
    """

    def setUp(self) -> None:
        self.solver = ClingoSolver()
        self.strategy = DefaultStrategy()
        config = LNSConfig(base_solver=self.solver, base_strategy=self.strategy)
        self.lns = LNS(["./tests/ref/golf.lp"], config)

    def test_setup(self):
        """
        Test clingo setup.
        """
        self.solver.setup(self.lns)
        self.assertEqual(self.lns.clingo_options, ["--rand-freq=0.05"])
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
        self.assertTrue(self.solver.repair(self.lns, []).satisfiable)
        self.assertTrue(self.lns.models["new_model"])

        assumptions = self.strategy.relax(
            self.lns.models["new_model"], {"relax_rate": 0.2}
        )
        self.lns.models["new_model"] = {}
        self.assertTrue(self.solver.repair(self.lns, assumptions).satisfiable)
        self.assertTrue(self.lns.models["new_model"])

        # flaky, covered by integration test instead
        # self.lns.set_params({"solve_time_limit": 0})
        # self.assertTrue(self.solver.repair(self.lns, assumptions).interrupted)

    def test_get_avail_solve_time(self):
        """
        Test calculation of available solve time.
        """
        self.lns.set_parameters({"overall_time_limit": 16, "solve_time_limit": 10})
        self.assertEqual(self.solver.get_available_solve_time(self.lns), 10)
        self.lns.avail_time = 6
        self.assertEqual(self.solver.get_available_solve_time(self.lns), 6)

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
        self.solver = ClingoDLSolver()
        self.strategy = DefaultStrategy()
        config = LNSConfig(base_solver=self.solver, base_strategy=self.strategy)
        self.lns = LNS(["./tests/ref/golf.lp"], config)

    def test_setup(self):
        """
        Test clingoDL setup.
        """
        self.solver.setup(self.lns)
        self.assertEqual(self.lns.clingo_options, ["--rand-freq=0.05"])
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsInstance(self.solver.theory, clingodl.ClingoDLTheory)

        self.lns.set_seed(123)
        self.solver.setup(self.lns)
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsInstance(self.solver.theory, clingodl.ClingoDLTheory)

        self.solver.setup(self.lns, ["./tests/ref/golf.lp"], ["--solve-limit=1000"])
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsInstance(self.solver.theory, clingodl.ClingoDLTheory)

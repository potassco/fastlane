"""
Test cases for solver classes.
"""

from unittest import TestCase

import clingo
import clingodl

from large_neighbourhood_search import LNS
from large_neighbourhood_search.interfaces.solver import SolverInterface
from large_neighbourhood_search.interfaces.strategy import StrategyInterface
from large_neighbourhood_search.lib.solvers.clingo_dl_heu_solver import (
    ClingoDLHeuSolver,
)
from large_neighbourhood_search.lib.solvers.clingo_dl_solver import ClingoDLSolver
from large_neighbourhood_search.lib.solvers.clingo_heu_solver import ClingoHeuSolver
from large_neighbourhood_search.lib.solvers.clingo_solver import ClingoSolver
from large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd import (
    ClassicWeightedSumRnd,
)


class TestSolverClingo(TestCase):
    """
    Test cases for ClingoSolver class.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoSolver()
        self.strategy: StrategyInterface = ClassicWeightedSumRnd()
        self.lns = LNS(["./tests/ref/golf.lp"], self.solver, self.strategy)

    def test_get_avail_solve_time(self):
        """
        Test calculation of available solve time.
        """
        self.lns.set_params({"overall_time_limit": 16, "solve_time_limit": 10})
        self.assertEqual(self.solver.get_avail_solve_time(self.lns), 10)
        self.lns.avail_time = 6
        self.assertEqual(self.solver.get_avail_solve_time(self.lns), 6)

    def test_setup(self):
        """
        Test clingo setup.
        """
        self.solver.setup(self.lns)
        self.assertDictEqual(self.lns.param_values["clingo_args"], {"rand-freq": 0.8})
        self.assertIsInstance(self.solver.ctl, clingo.control.Control)
        self.assertIsNone(self.solver.thy)

        self.lns.set_seed(123)
        self.solver.setup(self.lns)
        self.assertDictEqual(
            self.lns.param_values["clingo_args"], {"rand-freq": 0.8, "seed": 123}
        )
        self.assertIsInstance(self.solver.ctl, clingo.control.Control)
        self.assertIsNone(self.solver.thy)

    def test_solve_fixed(self):
        """
        Test clingo solving under assumptions.
        """
        self.lns.set_seed(123)
        self.solver.setup(self.lns)
        self.solver.ground_base(self.lns)
        self.assertTrue(self.solver.solve_fixed(self.lns, []).satisfiable)
        self.assertTrue(self.lns.models["new_model"])

        assumptions = self.strategy.relax(
            self.lns.models["new_model"], {"relax_rate": 0.2}
        )
        self.lns.models["new_model"] = {}
        self.assertTrue(self.solver.solve_fixed(self.lns, assumptions).satisfiable)
        self.assertTrue(self.lns.models["new_model"])

        # flaky, covered by integration test instead
        # self.lns.set_params({"solve_time_limit": 0})
        # self.assertTrue(self.solver.solve_fixed(self.lns, assumptions).interrupted)

    def test_get_stats(self):
        """
        Test get_statistics method.
        """
        self.lns.set_seed(123)
        self.solver.setup(self.lns)
        self.solver.ground_base(self.lns)
        self.solver.ctl.solve(on_model=print)
        stats = self.solver.get_stats()
        self.assertIsNotNone(stats)
        self.assertIsInstance(stats["solving"]["solvers"]["choices"], float)

        self.solver.ctl = None
        self.assertDictEqual(self.solver.get_stats(), {})


class TestSolverClingoHeu(TestSolverClingo):
    """
    Test cases for ClingoHeuSolver class.

    Test cases inherited from TestSolverClingo.
    """

    def setUp(self) -> None:
        self.solver = ClingoHeuSolver()
        self.strategy = ClassicWeightedSumRnd()
        self.lns = LNS(["./tests/ref/golf.lp"], self.solver, self.strategy)


class TestSolverClingoDL(TestSolverClingo):
    """
    Test cases for ClingoDLSolver class.

    Test cases for get_avail_solve_time() and solve_under_assumptions()
    inherited from TestSolverClingo.
    """

    def setUp(self) -> None:
        self.solver = ClingoDLSolver()
        self.strategy = ClassicWeightedSumRnd()
        self.lns = LNS(["./tests/ref/golf.lp"], self.solver, self.strategy)

    def test_setup(self):
        """
        Test clingoDL setup.
        """
        self.solver.setup(self.lns)
        self.assertDictEqual(self.lns.param_values["clingo_args"], {"rand-freq": 0.8})
        self.assertIsInstance(self.solver.ctl, clingo.control.Control)
        self.assertIsInstance(self.solver.thy, clingodl.ClingoDLTheory)

        self.lns.set_seed(123)
        self.solver.setup(self.lns)
        self.assertDictEqual(
            self.lns.param_values["clingo_args"], {"rand-freq": 0.8, "seed": 123}
        )
        self.assertIsInstance(self.solver.ctl, clingo.control.Control)
        self.assertIsInstance(self.solver.thy, clingodl.ClingoDLTheory)


class TestSolverClingoDLHeu(TestSolverClingoDL):
    """
    Test cases for ClingoDLHeuSolver class.

    Test cases inherited from TestSolverClingoDL.
    """

    def setUp(self) -> None:
        self.solver = ClingoDLHeuSolver()
        self.strategy = ClassicWeightedSumRnd()
        self.lns = LNS(["./tests/ref/golf.lp"], self.solver, self.strategy)

"""
Test cases for ClingconSolver class.
"""

import clingcon
import clingo

from fastlane.lib.solvers.clingcon_solver import ClingconSolver
from fastlane.lns import LNS
from tests.solver.test_clingo import TestSolverClingo


class TestClingconSolver(TestSolverClingo):
    """
    Test cases for ClingconSolver class.
    """

    def setUp(self) -> None:
        self.solver = ClingconSolver()
        self.stype = ClingconSolver
        self.name = "clingcon"
        self.lns = LNS(["./tests/ref/golf.lp"], {"log_level": 50})

    def test_setup(self):
        """
        Test clingcon setup.
        """
        self.solver.setup(self.lns)
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsInstance(self.solver.theory, clingcon.ClingconTheory)

        self.solver.setup(self.lns, ["--models=2"], ["./tests/ref/golf.lp"])
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsInstance(self.solver.theory, clingcon.ClingconTheory)
        self.assertEqual(self.solver.control.configuration.solve.models, "2")

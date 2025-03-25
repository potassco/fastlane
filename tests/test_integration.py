"""
Integration tests.
"""

from unittest import TestCase

from mod_lns import LNS
from mod_lns.interfaces.solver import SolverInterface
from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lns_config import LNSConfig


class TestIntegrationCommon(TestCase):
    """
    Common integration tests.
    """

    def test_start_sol(self):
        """
        Test execution with start sol.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            LNSConfig(
                {
                    "start_sol": "plays(3,1,1) plays(8,1,1) plays(9,1,1) "
                    "plays(1,2,1) plays(2,2,1) plays(9,2,1) plays(1,3,1)"
                }
            ),
        )
        lns.main()

    def test_faulty_encoding(self):
        """
        Test execution with faulty encoding.
        """
        lns = LNS(["./tests/ref/bad_encoding.lp"])
        with self.assertRaises(SystemExit):
            lns.main()


class TestIntegrationClingoClassic(TestCase):
    """
    Integration tests using clingo and classic LNS.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoSolver()
        self.params = {"max_steps": 100, "seed": 123}

    def test_rnd(self):
        """
        Test classic LNS with random relaxation and assumptions.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            LNSConfig(self.params, [], solver=self.solver),
        )
        lns.main()

    def test_decl(self):
        """
        Test classic LNS with declarative relaxation and assumptions.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            LNSConfig({**self.params, **{"declarative": True}}, [], solver=self.solver),
        )
        lns.main()


class TestIntegrationClingoClassicHeu(TestIntegrationClingoClassic):
    """
    Integration tests using clingo, classic LNS and heuristics.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoSolver()
        self.params = {
            "max_steps": 100,
            "seed": 123,
            "heuristics": True,
        }


class TestIntegrationClingoCons(TestIntegrationClingoClassic):
    """
    Integration tests using clingo, constrained LNSand constrained LNS.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoSolver()
        self.params = {"max_steps": 100, "seed": 123, "constrained": True}


class TestIntegrationClingoConsHeu(TestIntegrationClingoCons):
    """
    Integration tests using clingo, constrained LNS and heuristics.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoSolver()
        self.params = {
            "max_steps": 100,
            "seed": 123,
            "heuristics": True,
            "constrained": True,
        }


class TestIntegrationClingoDLClassic(TestCase):
    """
    Integration tests using clingo-dl and classic LNS.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoDLSolver()
        self.params = {"max_steps": 100, "seed": 123}

    def test_rnd(self):
        """
        Test classic LNS with random relaxation and assumptions.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            LNSConfig(self.params, [], solver=self.solver),
        )
        lns.main()

    def test_decl(self):
        """
        Test classic LNS with declarative relaxation and assumptions.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            LNSConfig({**self.params, **{"declarative": True}}, [], solver=self.solver),
        )
        lns.main()


class TestIntegrationClingoDLClassicHeu(TestIntegrationClingoClassic):
    """
    Integration tests using clingo, classic LNS and heuristics.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoDLSolver()
        self.params = {
            "max_steps": 100,
            "seed": 123,
            "heuristics": True,
        }


class TestIntegrationClingoDLCons(TestIntegrationClingoDLClassic):
    """
    Integration tests using clingo, constrained LNSand constrained LNS.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoDLSolver()
        self.params = {"max_steps": 100, "seed": 123, "constrained": True}


class TestIntegrationClingoDLConsHeu(TestIntegrationClingoCons):
    """
    Integration tests using clingo, constrained LNS and heuristics.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoDLSolver()
        self.params = {
            "max_steps": 100,
            "seed": 123,
            "heuristics": True,
            "constrained": True,
        }

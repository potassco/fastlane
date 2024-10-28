"""
Integration tests.
"""

from unittest import TestCase

from large_neighbourhood_search import LNS
from large_neighbourhood_search.interfaces.solver import SolverInterface
from large_neighbourhood_search.lib.solvers.clingo_dl_heu_solver import (
    ClingoDLHeuSolver,
)
from large_neighbourhood_search.lib.solvers.clingo_dl_solver import ClingoDLSolver
from large_neighbourhood_search.lib.solvers.clingo_heu_solver import ClingoHeuSolver
from large_neighbourhood_search.lib.solvers.clingo_solver import ClingoSolver
from large_neighbourhood_search.lib.strategies.classic_lexicographic_declarative import (
    ClassicLexiDecl,
)
from large_neighbourhood_search.lib.strategies.classic_lexicographic_rnd import (
    ClassicLexiRnd,
)
from large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd import (
    ClassicWeightedSumRnd,
)
from large_neighbourhood_search.lib.strategies.hc_lexicographic_declarative import (
    HCLexiDecl,
)
from large_neighbourhood_search.lib.strategies.hc_lexicographic_rnd import HCLexiRnd
from large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd import (
    HCWeightedSumRnd,
)


class TestIntegrationCommon(TestCase):
    """
    Common integration tests.
    """

    def test_default_run(self):
        """
        Test default execution.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.main()

    def test_faulty_encoding(self):
        """
        Test execution with faulty encoding.
        """
        lns = LNS(["./tests/ref/bad_encoding.lp"])
        with self.assertRaises(SystemExit):
            lns.main()


class TestIntegrationClingo(TestCase):
    """
    Integration tests using clingo.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoSolver()

    def test_classic_weighted_sum(self):
        """
        Test classic execution with weighted sum.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            self.solver,
            ClassicWeightedSumRnd(),
            {"max_steps": 500},
        )
        lns.set_seed(456)
        lns.main()

    def test_classic_weighted_sum_start_sol(self):
        """
        Test classic execution with weighted sum and starting solution.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            self.solver,
            ClassicWeightedSumRnd(),
            {
                "max_steps": 500,
                "start_sol": "plays(3,1,1) plays(8,1,1) plays(9,1,1) "
                "plays(1,2,1) plays(2,2,1) plays(9,2,1) plays(1,3,1)",
            },
        )
        lns.set_seed(456)
        lns.main()

    def test_classic_lexi_rnd(self):
        """
        Test classic execution with lexicographic optimization.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"], self.solver, ClassicLexiRnd(), {"max_steps": 500}
        )
        lns.set_seed(123)
        lns.main()

    def test_classic_lexi_decl(self):
        """
        Test classic execution with lexicographic optimization (declarative).
        """
        lns = LNS(
            ["./tests/ref/golf.lp"], self.solver, ClassicLexiDecl(), {"max_steps": 500}
        )
        lns.set_seed(123)
        lns.main()

    def test_hc_weighted_sum(self):
        """
        Test execution with hard constraints and weighted sum.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"], self.solver, HCWeightedSumRnd(), {"max_steps": 50}
        )
        lns.set_seed(123)
        lns.main()

    def test_hc_weighted_sum_start_sol(self):
        """
        Test execution with hard constraints, weighted sum and starting solution.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            self.solver,
            HCWeightedSumRnd(),
            {
                "max_steps": 50,
                "start_sol": "plays(3,1,1) plays(8,1,1) plays(9,1,1) "
                "plays(1,2,1) plays(2,2,1) plays(9,2,1) plays(1,3,1)",
            },
        )
        lns.set_seed(123)
        lns.main()

    def test_hc_lexi_rnd(self):
        """
        Test execution with hard constraints and lexicographic optimization.
        """
        lns = LNS(["./tests/ref/golf.lp"], self.solver, HCLexiRnd(), {"max_steps": 50})
        lns.set_seed(123)
        lns.main()

    def test_hc_lexi_rnd_start_sol(self):
        """
        Test execution with hard constraints, lexicographic optimization and starting solution.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            self.solver,
            HCLexiRnd(),
            {
                "max_steps": 50,
                "start_sol": "plays(3,1,1) plays(8,1,1) plays(9,1,1) "
                "plays(1,2,1) plays(2,2,1) plays(9,2,1) plays(1,3,1)",
            },
        )
        lns.set_seed(123)
        lns.main()

    def test_hc_lexi_decl(self):
        """
        Test execution with hard constraints and lexicographic optimization (declarative).
        """
        lns = LNS(["./tests/ref/golf.lp"], self.solver, HCLexiDecl(), {"max_steps": 50})
        lns.set_seed(123)
        lns.main()

    def test_stuck(self):
        """
        Test execution being stuck.
        """
        lns = LNS(
            ["./tests/ref/golf_big.lp"],
            self.solver,
            HCLexiDecl(),
            {"solve_time_limit": 1, "stuck_after_no_improv": 5},
        )
        lns.set_seed(123)
        lns.main()

    def test_pre_solve(self):
        """
        Test pre solving.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            self.solver,
            params={"pre_files": ["./tests/ref/golf_pre.lp"], "max_steps": 1},
        )
        lns.set_seed(123)
        lns.main()

        lns = LNS(
            ["./tests/ref/golf_big.lp"],
            self.solver,
            params={
                "pre_files": ["./tests/ref/golf_pre_big.lp"],
                "pre_tl": 1,
                "max_steps": 1,
            },
        )
        lns.set_seed(123)
        lns.main()

        lns = LNS(
            ["./tests/ref/golf.lp"],
            self.solver,
            params={"pre_files": ["./tests/ref/bad_encoding.lp"], "max_steps": 1},
        )
        with self.assertRaises(SystemExit):
            lns.main()

    def test_start_sol(self):
        """
        Test solving with pre-defined start solution.
        """
        s = (
            "plays(4,1,1) plays(6,1,1) plays(7,1,1) plays(1,2,1) plays(3,2,1) plays(6,2,1) plays(1,3,1) "
            "plays(2,3,1) plays(4,3,1) plays(2,1,2) plays(3,1,2) plays(8,1,2) plays(2,2,2) plays(5,2,2) "
            "plays(7,2,2) plays(3,3,2) plays(7,3,2) plays(9,3,2) plays(1,1,3) plays(5,1,3) plays(9,1,3) "
            "plays(4,2,3) plays(8,2,3) plays(9,2,3) plays(5,3,3) plays(6,3,3) plays(8,3,3)"
        )
        lns = LNS(
            ["./tests/ref/golf.lp"],
            self.solver,
            params={
                "start_sol": s,
            },
        )
        lns.set_seed(123)
        lns.main()


class TestIntegrationClingoHeu(TestIntegrationClingo):
    """
    Integration tests using heuristic clingo.
    """

    def setUp(self) -> None:
        self.solver = ClingoHeuSolver()


class TestIntegrationClingoDL(TestIntegrationClingo):
    """
    Integration tests using clingo-dl.
    """

    def setUp(self) -> None:
        self.solver = ClingoDLSolver()


class TestIntegrationClingoDLHeu(TestIntegrationClingo):
    """
    Integration tests using heuristic clingo-dl.
    """

    def setUp(self) -> None:
        self.solver = ClingoDLHeuSolver()

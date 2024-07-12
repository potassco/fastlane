"""
Integration tests.
"""

from unittest import TestCase

from large_neighbourhood_search import LNS
from large_neighbourhood_search.lib.solvers.clingo_dl_solver import ClingoDLSolver
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
        self.solver = ClingoSolver()

    def test_classic_weighted_sum(self):
        """
        Test classic execution with weighted sum.
        """
        lns = LNS(["./tests/ref/golf.lp"], self.solver, ClassicWeightedSumRnd())
        lns.set_seed(456)
        lns.main()

    def test_classic_lexi_rnd(self):
        """
        Test classic execution with lexicographic optimization.
        """
        lns = LNS(["./tests/ref/golf.lp"], self.solver, ClassicLexiRnd())
        lns.set_seed(123)
        lns.main()

    def test_classic_lexi_decl(self):
        """
        Test classic execution with lexicographic optimization (declarative).
        """
        lns = LNS(["./tests/ref/golf.lp"], self.solver, ClassicLexiDecl())
        lns.set_seed(123)
        lns.main()

    def test_hc_weighted_sum(self):
        """
        Test execution with hard constraints and weighted sum.
        """
        lns = LNS(["./tests/ref/golf.lp"], self.solver, HCWeightedSumRnd())
        lns.set_seed(123)
        lns.main()

    def test_hc_lexi_rnd(self):
        """
        Test execution with hard constraints and lexicographic optimization.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            self.solver,
            HCLexiRnd(),
        )
        lns.set_seed(123)
        lns.main()

    def test_hc_lexi_decl(self):
        """
        Test execution with hard constraints and lexicographic optimization (declarative).
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            self.solver,
            HCLexiDecl(),
        )
        lns.set_seed(123)
        lns.main()


class TestIntegrationClingoDL(TestIntegrationClingo):
    """
    Integration tests using clingoDL.
    """

    def setUp(self) -> None:
        self.solver = ClingoDLSolver()

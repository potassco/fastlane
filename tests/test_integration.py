"""
Integration tests.
"""

import io
from unittest import TestCase, mock

from mod_lns.lib.solvers.clingcon_solver import ClingconSolver
from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.default_strategy import DefaultStrategy, LNSConfig
from mod_lns.lib.strategies.heulingo import Heulingo, HeulingoConfig
from mod_lns.lns import LNS


class TestIntegrationDefaultClingo(TestCase):
    """
    Integration tests using clingo and default strategy.
    """

    def setUp(self):
        self.strat = DefaultStrategy()
        self.strat.config = LNSConfig(
            max_steps=20, seed=123, init_time_limit=3, lns_time_limit=3, time_limit=10
        )
        self.strat.solver = ClingoSolver()
        self.strat.log_level = 50

    def test_execution(self):
        """
        Test execution.
        """
        out = io.StringIO()
        with mock.patch("sys.stdout", new=out):
            lns = LNS(["./tests/ref/golf.lp"], strategy=self.strat)
            lns.main()

    def test_bigger_instance(self):
        """
        Test execution with a bigger instance.
        """
        out = io.StringIO()
        with mock.patch("sys.stdout", new=out):
            lns = LNS(["./tests/ref/golf_big.lp"], strategy=self.strat)
            lns.main()

    def test_faulty_encoding(self):
        """
        Test execution with faulty encoding.
        """
        lns = LNS(["./tests/ref/bad_encoding.lp"], strategy=self.strat)
        with self.assertRaises(SystemExit):
            lns.main()


class TestIntegrationDefaultClingoDL(TestIntegrationDefaultClingo):
    """
    Integration tests using clingo-dl and default strategy.
    """

    def setUp(self):
        super().setUp()
        self.strat.solver = ClingoDLSolver()


class TestIntegrationDefaultClingcon(TestIntegrationDefaultClingo):
    """
    Integration tests using clingcon and default strategy.
    """

    def setUp(self):
        super().setUp()
        self.strat.solver = ClingconSolver()


class TestIntegrationHeulingoClingo(TestIntegrationDefaultClingo):
    """
    Integration tests using clingo and Heulingo strategy.
    """

    def setUp(self):
        super().setUp()
        self.strat = Heulingo()
        self.strat.config = HeulingoConfig(
            max_steps=20, seed=123, init_time_limit=3, lns_time_limit=3, time_limit=10
        )
        self.strat.solver = ClingoSolver()
        self.strat.log_level = 50


class TestIntegrationHeulingoClingoDL(TestIntegrationHeulingoClingo):
    """
    Integration tests using clingo-dl and Heulingo strategy.
    """

    def setUp(self):
        super().setUp()
        self.strat.solver = ClingoDLSolver()


class TestIntegrationHeulingoClingcon(TestIntegrationHeulingoClingo):
    """
    Integration tests using clingcon and Heulingo strategy.
    """

    def setUp(self):
        super().setUp()
        self.strat.solver = ClingconSolver()

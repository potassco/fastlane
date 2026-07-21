"""
Integration tests.
"""

from io import StringIO
from unittest import TestCase, mock

from mod_lns.lib.auto_destruction_converters.average import AverageDestructionConverter
from mod_lns.lib.solvers.clingcon_solver import ClingconSolver
from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lns import LNS
from mod_lns.lns_options import LNSOptions


class TestIntegrationClingo(TestCase):
    """
    Integration tests using clingo solver.
    """

    def setUp(self):
        self.config = LNSOptions(
            max_steps=20,
            seed=42,
            init_time_limit=3,
            lns_time_limit=2,
            time_limit=10,
            log_level=50,
            solver=ClingoSolver(),
        )

    def _run_lns(self, files: list[str]) -> tuple[LNS, str]:
        """
        Execute LNS and capture stdout.
        """
        out = StringIO()
        with mock.patch("sys.stdout", new=out):
            lns = LNS(files, options=self.config)
            lns.main()
        return lns, out.getvalue()

    def _check_lns(self, lns: LNS, output: str):
        """
        Check integration results.
        """
        # final output
        self.assertIn("Result", output)
        self.assertIn("Optimum:", output)
        self.assertIn("Overall time:", output)

        # models should be obtained
        self.assertIsNotNone(lns.current_model)
        self.assertIsNotNone(lns.best_model)
        self.assertGreater(len(lns.best_model.shown), 0)

        # valid solver status
        self.assertIn(
            lns.solver.result,
            {"SATISFIABLE", "UNSATISFIABLE", "OPTIMUM FOUND", "UNKNOWN"},
        )

        # valid step count
        self.assertGreaterEqual(lns.step_c, 0)
        if self.config.max_steps is not None:
            self.assertLessEqual(lns.step_c, self.config.max_steps)

        # valid stats
        if lns.stats:
            last_stats = lns.stats[-1]
            self.assertIn("step", last_stats)
            self.assertIn("elapsed_time", last_stats)
            self.assertIn("no_improvement_cutoff_count", last_stats)
            self.assertEqual(last_stats["step"], lns.step_c)

    def _check_solver(self, lns: LNS):
        """
        Hook for solver-specific assertions.
        """

    def test_execution_basic(self):
        """
        Test basic execution.
        """
        self.config.relaxation = ("simple", 40)
        self.config.fix = "assumptions"
        self.config.default_adaptive_strategy_name = "static"
        lns, output = self._run_lns(["./tests/ref/golf.lp"])
        self._check_lns(lns, output)
        self._check_solver(lns)

    def test_execution_auto(self):
        """
        Test execution using auto relaxation and heuristics.
        """
        self.config.relaxation = ("simple", "auto")
        self.config.fix = "heuristics"
        self.config.default_adaptive_strategy_name = "static"
        lns, output = self._run_lns(["./tests/ref/golf.lp"])
        self._check_lns(lns, output)
        self._check_solver(lns)

    def test_execution_declarative(self):
        """
        Test execution using declarative relaxation and heuristics.
        """
        self.config.relaxation = ("declarative", 0)
        self.config.fix = "heuristics"
        self.config.default_adaptive_strategy_name = "roulette"
        lns, output = self._run_lns(["./tests/ref/golf.lp", "./tests/ref/golf_config.lp"])
        self._check_lns(lns, output)
        self._check_solver(lns)

    def test_bigger_instance(self):
        """
        Test execution with a bigger instance.
        """
        self.config.relaxation = ("simple", "auto")
        self.config.auto_converter = AverageDestructionConverter()
        self.config.fix = "heuristics"
        lns, output = self._run_lns(["./tests/ref/golf_big.lp"])
        self._check_lns(lns, output)
        self._check_solver(lns)


class TestIntegrationClingoDL(TestIntegrationClingo):
    """
    Integration tests using clingo-dl solver.
    """

    def setUp(self):
        super().setUp()
        self.config.solver = ClingoDLSolver()

    def _check_solver(self, lns: LNS):
        self.assertIsNotNone(lns.solver.theory)


class TestIntegrationClingcon(TestIntegrationClingo):
    """
    Integration tests using clingcon solver.
    """

    def setUp(self):
        super().setUp()
        self.config.solver = ClingconSolver()

    def _check_solver(self, lns: LNS):
        self.assertIsNotNone(lns.solver.theory)

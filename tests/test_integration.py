"""
Integration tests.
"""

import signal
import subprocess
import sys
import textwrap
import threading
from io import StringIO
from unittest import TestCase, mock

from fastlane.lib.auto_destruction_converters.average import AverageDestructionConverter
from fastlane.lib.solvers.clingcon_solver import ClingconSolver
from fastlane.lib.solvers.clingo_dl_solver import ClingoDLSolver
from fastlane.lib.solvers.clingo_solver import ClingoSolver
from fastlane.lns import LNS
from fastlane.lns_options import LNSOptions


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
        self.config.destruction = ("simple", 40)
        self.config.fix = "assumptions"
        self.config.default_adaptive_strategy_name = "static"
        lns, output = self._run_lns(["./tests/ref/golf.lp"])
        self._check_lns(lns, output)
        self._check_solver(lns)

    def test_execution_auto(self):
        """
        Test execution using auto relaxation and heuristics.
        """
        self.config.destruction = ("simple", "auto")
        self.config.fix = "heuristics"
        self.config.default_adaptive_strategy_name = "static"
        lns, output = self._run_lns(["./tests/ref/golf.lp"])
        self._check_lns(lns, output)
        self._check_solver(lns)

    def test_execution_declarative(self):
        """
        Test execution using declarative relaxation and heuristics.
        """
        self.config.destruction = ("declarative", 0)
        self.config.fix = "heuristics"
        self.config.default_adaptive_strategy_name = "roulette"
        lns, output = self._run_lns(["./tests/ref/golf.lp", "./tests/ref/golf_config.lp"])
        self._check_lns(lns, output)
        self._check_solver(lns)

    def test_bigger_instance(self):
        """
        Test execution with a bigger instance.
        """
        self.config.destruction = ("simple", "auto")
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


class TestSolveInterruptions(TestCase):
    """
    Exercise non-polling shutdown with real threads, alarms, signals, and clingo.
    """

    def test_external_stop(self):
        """
        Stop a background solve started without a time limit, via Control.interrupt().
        """
        solver = ClingoSolver()
        solver.control.configuration.solve.models = 0
        solver.add("base", [], "{ a(1..35) }.")
        solver.ground()
        started = threading.Event()
        solver._on_model = lambda _model: started.set()  # pylint: disable=protected-access
        errors = []

        def solve():
            try:
                solver.solve()
            except BaseException as error:  # pylint: disable=broad-exception-caught
                errors.append(error)

        worker = threading.Thread(target=solve)
        worker.start()
        try:
            self.assertTrue(started.wait(5), "Search did not start")
            solver.request_stop()
            worker.join(5)
            self.assertFalse(worker.is_alive(), "Stop request did not wake the solve")
        finally:
            solver.request_stop()
            worker.join(5)
        self.assertEqual(errors, [])
        self.assertIsNotNone(solver.last_model)

    def test_signals(self):
        """
        SIGINT and SIGTERM interrupt a blocked main-thread solve on Windows and Unix.
        """
        code = textwrap.dedent("""
            import os
            import signal
            import sys
            import threading
            import time
            from fastlane.lns import LNS
            from fastlane.lns_options import LNSOptions

            lns = LNS([], options=LNSOptions(log_level=50))
            solver = lns.solver
            solver.control.configuration.solve.models = 0
            solver.add("base", [], "{ a(1..35) }.")
            solver.ground()
            ready = threading.Event()
            solver._on_model = lambda model: ready.set()
            sent_at = []

            def interrupt():
                if not ready.wait(5):
                    raise RuntimeError("Search did not start")
                sent_at.append(time.monotonic())
                sig = int(sys.argv[1])
                if sys.platform == "win32":
                    signal.raise_signal(sig)
                else:
                    os.kill(os.getpid(), sig)

            previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
            with lns._preserve_signals():
                sender = threading.Thread(target=interrupt)
                sender.start()
                solver.solve()
                sender.join()
            assert sent_at and time.monotonic() - sent_at[0] < 2, "Unresponsive interruption"
            assert lns.interrupted and solver.finished
            assert solver.last_model is not None
            assert all(signal.getsignal(sig) == handler for sig, handler in previous.items())
            fd = signal.set_wakeup_fd(-1)
            assert fd == -1, "Signal wakeup fd was not restored"
            assert not solver.watcher.active
            """)
        for sig in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=sig):
                result = subprocess.run(
                    [sys.executable, "-c", code, str(int(sig))],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

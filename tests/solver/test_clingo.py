"""
Test cases for solver classes.
"""

import signal
from logging import Logger
from unittest import TestCase, mock

import clingo
from clingo.symbol import Function

from mod_lns import Model, Timer
from mod_lns.interfaces.solver import SolverConfig
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lns import LNS

# pylint: disable=protected-access, too-many-statements


class TestSolverConfig(TestCase):
    """
    Test cases for SolverConfig class.
    """

    def test_init(self):
        """
        Test initialization of SolverConfig.
        """
        config = SolverConfig()
        self.assertIsNone(config.configuration)
        self.assertIsNone(config.opt_strategy)
        self.assertIsNone(config.opt_heuristic)
        self.assertIsNone(config.restart_on_model)
        self.assertIsNone(config.heuristic)
        self.assertIsNone(config.opt_mode)
        self.assertIsNone(config.solve_limit)
        self.assertIsNone(config.time_limit)
        self.assertIsNone(config.cutoff)
        self.assertIsNone(config.seed)
        self.assertTrue(config.variability)


class TestSolverClingo(TestCase):
    """
    Test cases for ClingoSolver class.
    """

    def setUp(self) -> None:
        self.solver = ClingoSolver()
        self.stype = ClingoSolver
        self.name = "clingo"
        self.lns = LNS(["./tests/ref/golf.lp"], {"log_level": 50})

    def test_init(self):
        """
        Test initialization of ClingoSolver.
        """
        self.assertIsInstance(self.solver, self.stype)
        self.assertIsInstance(self.solver.control, clingo.Control)
        self.assertIsNone(self.solver.theory)
        self.assertFalse(self.solver.finished)
        self.assertEqual(self.solver.result, "UNKNOWN")
        self.assertEqual(self.solver.optimum, "unknown")
        self.assertIsNone(self.solver.minimize_variable)
        self.assertIsInstance(self.solver.logger, Logger)
        self.assertFalse(self.solver.stop)
        self.assertFalse(self.solver._assumptions_used)
        self.assertIsNone(self.solver.last_model)
        self.assertIsInstance(self.solver._solve_timer, Timer)
        self.assertIsInstance(self.solver._cutoff_timer, Timer)
        self.assertFalse(self.solver._interrupted)
        self.assertFalse(self.solver._variability)

    def test_ground(self):
        """
        Test ground method.
        """
        self.solver.setup(self.lns)
        with mock.patch.object(self.solver.control, "ground") as mock_ground:
            self.solver.ground()
            mock_ground.assert_called_once_with([("base", [])], None)

    def test_add(self):
        """
        Test add method.
        """
        self.solver.setup(self.lns)
        with mock.patch.object(self.solver.control, "add") as mock_add:
            self.solver.add("test", [], "a.")
            mock_add.assert_called_once_with("test", [], "a.")

    def test_assign_external(self):
        """
        Test assign_external method.
        """
        self.solver.setup(self.lns)
        with mock.patch.object(self.solver.control, "assign_external") as mock_assign:
            atom = clingo.Function("a")
            self.solver.assign_external(atom, True)
            mock_assign.assert_called_once_with(atom, True)

    def test_release_external(self):
        """
        Test release_external method.
        """
        self.solver.setup(self.lns)
        with mock.patch.object(self.solver.control, "release_external") as mock_release:
            atom = clingo.Function("a")
            self.solver.release_external(atom)
            mock_release.assert_called_once_with(atom)

    def test_get_stats(self):
        """
        Test get_stats method.
        """
        self.solver.setup(self.lns)
        self.solver.ground()
        self.solver.control.configuration.solve.models = 2
        self.solver.control.solve(on_model=lambda *args: None)
        stats = self.solver.get_stats()
        self.assertIsNotNone(stats)
        self.assertIsInstance(stats["solving"]["solvers"]["choices"], float)

    def test_get_name(self):
        """
        Test get_name method.
        """
        self.assertEqual(self.stype.get_name(), self.name)

    def test_interrupt_handler(self):
        """
        Test interrupt_handler method.
        """
        self.solver.setup_interrupt_handling(self.lns)
        self.assertFalse(self.solver.finished)
        self.assertFalse(self.solver.stop)
        with self.assertRaises(SystemExit), mock.patch.object(self.lns, "print_result") as print_result_mock:
            signal.raise_signal(signal.SIGINT)
            print_result_mock.assert_called_once_with(self.lns)
        self.assertTrue(self.solver.finished)
        self.assertTrue(self.solver.stop)

        self.solver.setup(self.lns)
        with (
            self.assertRaises(SystemExit),
            mock.patch.object(self.solver.control, "interrupt") as mock_interrupt,
            mock.patch.object(self.lns, "print_result") as print_result_mock,
        ):
            self.solver.finished = False
            self.solver.stop = False
            signal.raise_signal(signal.SIGTERM)
            mock_interrupt.assert_called_once()
            print_result_mock.assert_called_once_with(self.lns)
            self.assertTrue(self.solver.finished)
            self.assertTrue(self.solver.stop)

    def test_setup(self):
        """
        Test clingo setup.
        """
        self.solver.setup(self.lns)
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsNone(self.solver.theory)

        self.solver.setup(self.lns, ["--models=2"], ["./tests/ref/golf.lp"])
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsNone(self.solver.theory)
        self.assertEqual(self.solver.control.configuration.solve.models, "2")

    def test_on_model(self):
        """
        Test _on_model method.
        """
        self.solver.setup(self.lns)
        self.solver.ground()
        self.solver.control.configuration.solve.models = 1
        self.assertIsNone(self.solver.last_model)
        with (
            mock.patch.object(self.solver._cutoff_timer, "get_elapsed_time", return_value=1) as mock_elapsed_time,
            mock.patch.object(self.solver._cutoff_timer, "restart") as mock_restart,
        ):
            self.solver.control.solve(on_model=self.solver._on_model)
            mock_elapsed_time.assert_called_once()
            mock_restart.assert_called_once()
        self.assertEqual(self.solver.stats["time_to_last_model"], 1)
        self.assertIsInstance(self.solver.last_model, Model)

    def test_apply_config_to_control(self):
        """
        Test _apply_config_to_control method.
        """
        self.solver.setup(self.lns)
        config = SolverConfig(
            configuration="tweety",
            opt_strategy="bb,0",
            opt_heuristic="3",
            restart_on_model="1",
            heuristic="Domain",
            opt_mode="opt,10",
            solve_limit="1000",
        )
        self.solver._apply_config_to_control(config)
        self.assertEqual(self.solver.control.configuration.configuration, config.configuration)
        self.assertEqual(self.solver.control.configuration.solver.opt_strategy, "bb,lin")
        self.assertEqual(self.solver.control.configuration.solver.opt_heuristic, "sign,model")
        self.assertEqual(self.solver.control.configuration.solver.restart_on_model, config.restart_on_model)
        self.assertEqual(self.solver.control.configuration.solver.heuristic, "domain,0")
        self.assertEqual(self.solver.control.configuration.solve.opt_mode, config.opt_mode)
        self.assertEqual(self.solver.control.configuration.solve.solve_limit, "1000,umax")

    def test_control_config_debug(self):
        """
        Test control configuration debug output.
        """
        self.solver.setup(self.lns)
        self.test_apply_config_to_control()
        with mock.patch.object(self.solver.logger, "debug_extra") as mock_debug:
            self.solver._control_config_debug()
            self.assertEqual(mock_debug.call_count, 9)

    def test_solve(self):
        """
        Test solve method.
        """
        self.solver.setup(self.lns)

        def setup_mock_timers(solve_ringing: bool, cutoff_ringing: bool) -> None:
            self.solver._solve_timer = mock.MagicMock()
            self.solver._solve_timer.is_ringing = solve_ringing
            self.solver._solve_timer.get_elapsed_time.return_value = 1
            self.solver._cutoff_timer = mock.MagicMock()
            self.solver._cutoff_timer.is_ringing = cutoff_ringing
            self.solver._cutoff_timer.get_elapsed_time.return_value = 1

        def make_solve_context() -> tuple[mock.MagicMock, mock.MagicMock]:
            handle = mock.MagicMock()
            handle.wait.side_effect = [False, True]
            solve_context = mock.MagicMock()
            solve_context.__enter__.return_value = handle
            solve_context.__exit__.return_value = False
            return solve_context, handle

        # default -> cutoff cancels
        self.solver.last_model = None
        self.solver.finished = False
        self.solver._interrupted = False
        setup_mock_timers(solve_ringing=False, cutoff_ringing=True)
        solve_context, handle = make_solve_context()
        with mock.patch.object(self.solver.control, "solve", return_value=solve_context):
            self.solver.solve()
            handle.cancel.assert_called_once()

        # require_model=True -> cutoff does not cancel if no model exists yet
        self.solver.last_model = None
        self.solver.finished = False
        self.solver._interrupted = False
        setup_mock_timers(solve_ringing=False, cutoff_ringing=True)
        solve_context, handle = make_solve_context()
        with mock.patch.object(self.solver.control, "solve", return_value=solve_context):
            self.solver.solve(require_model=True)
            handle.cancel.assert_not_called()

        # model exists -> cutoff cancels even when require_model=True
        self.solver.last_model = Model()
        self.solver.finished = False
        self.solver._interrupted = False
        setup_mock_timers(solve_ringing=False, cutoff_ringing=True)
        solve_context, handle = make_solve_context()
        with mock.patch.object(self.solver.control, "solve", return_value=solve_context):
            self.solver.solve(require_model=True)
            handle.cancel.assert_called_once()

        # solve timer always cancels, independent of require_model
        self.solver.last_model = None
        self.solver.finished = False
        self.solver._interrupted = False
        setup_mock_timers(solve_ringing=True, cutoff_ringing=False)
        solve_context, handle = make_solve_context()
        with mock.patch.object(self.solver.control, "solve", return_value=solve_context):
            self.solver.solve(require_model=True)
            handle.cancel.assert_called_once()

        # assumptions are forwarded and config is applied
        assumptions = [(Function("a"), True)]
        config = SolverConfig(time_limit=10, cutoff=5)
        self.solver.last_model = None
        self.solver.finished = False
        self.solver._interrupted = False
        setup_mock_timers(solve_ringing=False, cutoff_ringing=False)
        solve_context, _ = make_solve_context()
        with (
            mock.patch.object(self.solver, "_apply_config_to_control") as mock_apply,
            mock.patch.object(self.solver.control, "solve", return_value=solve_context) as mock_solve,
        ):
            self.assertFalse(self.solver._assumptions_used)
            self.solver.solve(config=config, assumptions=assumptions)
            self.assertTrue(self.solver._assumptions_used)
            mock_apply.assert_called_once_with(config)
            self.assertEqual(mock_solve.call_args.kwargs["assumptions"], assumptions)

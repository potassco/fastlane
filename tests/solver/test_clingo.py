"""
Test cases for clingo solvers and their solve watcher.
"""

from unittest import TestCase, mock

import clingo
from clingo.symbol import Function

from fastlane import Model, Timer
from fastlane.interfaces.solver import Solver, SolverConfig
from fastlane.lib.solvers.clingo_solver import ClingoSolver, ClingoSolveWatcher

# pylint: disable=protected-access


class TestSolverConfig(TestCase):
    """
    Test cases for SolverConfig class.
    """

    def test_init(self):
        """Test default solver configuration."""
        config = SolverConfig()
        for name in (
            "configuration",
            "opt_strategy",
            "opt_heuristic",
            "restart_on_model",
            "heuristic",
            "opt_mode",
            "solve_limit",
            "time_limit",
            "cutoff",
            "seed",
        ):
            with self.subTest(name=name):
                self.assertIsNone(getattr(config, name))
        self.assertTrue(config.variability)


class TestSolverClingo(TestCase):  # pylint: disable=too-many-public-methods
    """
    Test cases for ClingoSolver class.
    """

    stype = ClingoSolver
    name = "clingo"

    def setUp(self) -> None:
        control_patch = mock.patch("fastlane.interfaces.solver.clingo.control.Control", autospec=True)
        self.control = control_patch.start().return_value
        self.addCleanup(control_patch.stop)
        self.solver = self.stype()
        self.solver.logger = mock.Mock()
        self.solver.logger.isEnabledFor.return_value = False
        self.control.configuration = mock.Mock()
        self.control.configuration.solver = mock.Mock(
            spec=clingo.Configuration,
            opt_strategy="bb,lin",
            opt_heuristic="no",
            restart_on_model="0",
            heuristic="vsids",
        )
        self.control.configuration.solve = mock.Mock(
            spec=clingo.Configuration, opt_mode="opt", solve_limit="umax,umax", parallel_mode="1"
        )
        self.lns = mock.Mock(files=["input.lp"])

    def test_init(self):
        """
        Test initialization of the current solver state.
        """
        self.assertIs(self.solver.control, self.control)
        self.assertIsNone(self.solver.theory)
        self.assertFalse(self.solver.finished)
        self.assertEqual(self.solver.result, "UNKNOWN")
        self.assertEqual(self.solver.optimum, "unknown")
        self.assertIsNone(self.solver.minimize_variable)
        self.assertFalse(self.solver.stop)
        self.assertFalse(self.solver._assumptions_used)
        self.assertIsNone(self.solver.last_model)
        self.assertIsNone(self.solver.watcher)
        self.assertFalse(self.solver.interrupted)
        self.assertFalse(self.solver._variability)

    def test_ground(self):
        """
        Test forwarding grounding arguments.
        """
        self.solver.ground()
        self.control.ground.assert_called_once_with([("base", [])], None)

    def test_add(self):
        """
        Test forwarding program additions.
        """
        self.solver.add("test", [], "a.")
        self.control.add.assert_called_once_with("test", [], "a.")

    def test_assign_external(self):
        """
        Test forwarding external assignments.
        """
        atom = Function("a")
        self.solver.assign_external(atom, True)
        self.control.assign_external.assert_called_once_with(atom, True)

    def test_release_external(self):
        """
        Test forwarding external releases.
        """
        atom = Function("a")
        self.solver.release_external(atom)
        self.control.release_external.assert_called_once_with(atom)

    def test_get_stats(self):
        """
        Test returning control statistics without solving.
        """
        self.control.statistics = {"solving": {"solvers": {"choices": 2}}}
        self.assertIs(self.solver.get_stats(), self.control.statistics)

    def test_get_name(self):
        """
        Test the registered solver name.
        """
        self.assertEqual(self.stype.get_name(), self.name)

    def test_request_stop(self):
        """
        Test shutdown requests with and without an active watcher, always interrupting.
        """
        self.assertFalse(self.solver.request_stop())
        self.control.interrupt.assert_called_once_with()
        self.assertTrue(self.solver.stop)
        self.assertTrue(self.solver.finished)
        self.assertTrue(self.solver.interrupted)

        watcher = mock.Mock()
        self.solver.watcher = watcher
        for active in (False, True):
            with self.subTest(active=active):
                self.solver.stop = self.solver.finished = False
                watcher.active = active
                self.assertEqual(self.solver.request_stop(), active)
                self.assertTrue(self.solver.stop)
                self.assertTrue(self.solver.finished)
        self.assertEqual(watcher.mock_calls, [])
        self.assertEqual(self.control.interrupt.call_count, 3)

    def test_setup(self):
        """
        Test default and explicit files without loading real programs.
        """
        for files in (None, ["other.lp"]):
            with self.subTest(files=files), mock.patch("fastlane.lib.solvers.clingo_solver.clingo.Control") as control:
                self.solver.setup(self.lns, ["--models=2"], files)
                self.assertEqual(control.call_args.args, (["--models=2"],))
                self.assertTrue(callable(control.call_args.kwargs["logger"]))
                control.return_value.load.assert_called_once_with((self.lns.files if files is None else files)[0])
                self.assertIs(self.solver.control, control.return_value)
                self.assertIsNone(self.solver.theory)

    def test_prepare_solve(self):
        """
        Test that plain clingo needs no additional preparation.
        """
        self.solver._prepare_solve()
        self.assertEqual(self.control.method_calls, [])

    def test_apply_config_to_control(self):
        """
        Test configuration forwarding without clingo's value normalization.
        """
        config = SolverConfig(
            configuration="tweety",
            opt_strategy="bb,0",
            opt_heuristic="3",
            restart_on_model="1",
            heuristic="Domain",
            opt_mode="opt,10",
            solve_limit="1000",
        )
        with mock.patch.object(self.solver, "_apply_opt_mode") as apply_opt_mode:
            self.solver._apply_config_to_control(config)
        self.assertEqual(self.control.configuration.configuration, config.configuration)
        for name in ("opt_strategy", "opt_heuristic", "restart_on_model", "heuristic"):
            self.assertEqual(getattr(self.control.configuration.solver, name), getattr(config, name))
        apply_opt_mode.assert_called_once_with(config.opt_mode)
        self.assertEqual(self.control.configuration.solve.solve_limit, config.solve_limit)

    def test_apply_opt_mode(self):
        """
        Test applying the optimization mode.
        """
        self.solver._apply_opt_mode("opt,10")
        self.assertEqual(self.control.configuration.solve.opt_mode, "opt,10")

    def test_control_config_debug(self):
        """
        Test logging all control configuration fields.
        """
        self.control.configuration.configuration = "tweety"
        solver_config = self.control.configuration.solver
        solve_config = self.control.configuration.solve
        self.solver._control_config_debug()
        self.solver.logger.debug_extra.assert_has_calls(
            [
                mock.call("clingo.Control configuration:"),
                mock.call("configuration: %s", "tweety"),
                mock.call("opt-strategy: %s", solver_config.opt_strategy),
                mock.call("opt-heuristic: %s", solver_config.opt_heuristic),
                mock.call("restart-on-model: %s", solver_config.restart_on_model),
                mock.call("heuristic: %s", solver_config.heuristic),
                mock.call("opt-mode: %s", solve_config.opt_mode),
                mock.call("solve-limit: %s", solve_config.solve_limit),
                mock.call("parallel-mode: %s", solve_config.parallel_mode),
            ]
        )

    def test_solve(self):
        """
        Test resetting state, applying configuration and delegating the solve pass.
        """
        assumptions = [(Function("a"), True)]
        config = SolverConfig(time_limit=10, cutoff=5, variability=True)
        model = Model()

        def run_watcher(*_args):
            self.assertIsNone(self.solver.last_model)
            self.solver.last_model = model

        with (
            mock.patch.object(self.solver, "_apply_config_to_control") as apply_config,
            mock.patch.object(self.solver, "_prepare_solve") as prepare,
            mock.patch.object(self.solver, "_run_watcher", side_effect=run_watcher) as run,
        ):
            self.assertIs(self.solver.solve(config, assumptions, True), model)
            self.assertTrue(self.solver._assumptions_used)
            self.assertTrue(self.solver._variability)
            apply_config.assert_called_once_with(config)
            prepare.assert_called_once_with()
            run.assert_called_once_with(assumptions, 10, 5, True)

            apply_config.reset_mock()
            run.reset_mock()
            self.assertIs(self.solver.solve(), model)
            self.assertFalse(self.solver._assumptions_used)
            apply_config.assert_not_called()
            run.assert_called_once_with([], None, None, False)

    def test_run_watcher(self):
        """
        Test delegating lifecycle ownership to the retained watcher.
        """
        assumptions = [(Function("a"), True)]
        with mock.patch("fastlane.lib.solvers.clingo_solver.ClingoSolveWatcher") as watcher_class:
            watcher = watcher_class.return_value
            self.solver._run_watcher(assumptions, 10, 5, True)
            watcher_class.assert_called_once_with(self.solver, assumptions)
            self.assertIs(self.solver.watcher, watcher)
            watcher.solve.assert_called_once_with(10, 5, True)

    def test_run_watcher_error(self):
        """
        Test propagating the lifecycle owner's error unchanged.
        """
        error = RuntimeError("solve failed")
        with mock.patch("fastlane.lib.solvers.clingo_solver.ClingoSolveWatcher") as watcher_class:
            watcher_class.return_value.solve.side_effect = error
            with self.assertRaises(RuntimeError) as raised:
                self.solver._run_watcher([], None)
            self.assertIs(raised.exception, error)

    def test_save_model(self):
        """
        Test copying shown atoms, true atoms and cost.
        """
        model = mock.Mock(cost=[3, 2])
        model.symbols.side_effect = [[Function("shown")], [Function("shown"), Function("hidden")]]
        self.solver._save_model(model)
        self.assertEqual(self.solver.last_model.shown, {Function("shown")})
        self.assertEqual(self.solver.last_model.true, {Function("shown"), Function("hidden")})
        self.assertEqual(self.solver.last_model.cost, [3, 2])
        model.symbols.assert_has_calls([mock.call(shown=True), mock.call(atoms=True)])

    def test_postprocess_solve(self):
        """
        Test saving models and recognizing exhausted SAT and UNSAT searches.
        """
        model = mock.Mock()
        sat = mock.Mock(satisfiable=True, unsatisfiable=False, exhausted=True)
        unsat = mock.Mock(satisfiable=False, unsatisfiable=True, exhausted=True)
        with mock.patch.object(self.solver, "_save_model") as save:
            self.solver.last_model = Model()
            self.solver._variability = True
            self.solver.postprocess_solve(model, sat)
            save.assert_called_once_with(model)
        self.assertEqual(self.solver.result, "OPTIMUM FOUND")
        self.assertEqual(self.solver.stats["result"], "OPTIMUM FOUND")
        self.assertEqual(self.solver.optimum, "yes")
        self.assertTrue(self.solver.finished)

        self.solver.finished = False
        self.solver.last_model = None
        self.solver.postprocess_solve(None, unsat)
        self.assertEqual(self.solver.result, "UNSATISFIABLE")
        self.assertEqual(self.solver.stats["result"], "UNSATISFIABLE")
        self.assertTrue(self.solver.finished)

        self.solver.finished = False
        self.solver.postprocess_solve(None, sat)
        self.assertEqual(self.solver.result, "SATISFIABLE")
        self.assertEqual(self.solver.stats["result"], "SATISFIABLE")
        self.assertTrue(self.solver.finished)

    def test_postprocess_solve_incomplete(self):
        """
        Test that assumptions and interruptions do not prove an optimum.
        """
        result = mock.Mock(satisfiable=True, unsatisfiable=False, exhausted=True)
        for attribute in ("_assumptions_used", "interrupted"):
            with self.subTest(attribute=attribute):
                self.solver.finished = False
                self.solver.last_model = Model()
                self.solver._variability = True
                setattr(self.solver, attribute, True)
                self.solver.postprocess_solve(None, result)
                self.assertEqual(self.solver.result, "SATISFIABLE")
                self.assertFalse(self.solver.finished)
                setattr(self.solver, attribute, False)

    def test_postprocess_solve_abstract(self):
        """
        Test that the abstract interface requires a concrete postprocessor.
        """
        with self.assertRaises(NotImplementedError):
            Solver.postprocess_solve(self.solver, None, mock.Mock())


class TestClingoSolveWatcher(TestCase):
    """
    Test watcher methods with mocked control and timers.
    """

    def setUp(self) -> None:
        self.solver = mock.Mock()
        self.watcher = ClingoSolveWatcher(self.solver, [(Function("a"), True)])

    def test_init(self):
        """
        Test watcher ownership, assumptions and initial state.
        """
        self.assertIs(self.watcher.solver, self.solver)
        self.assertIs(self.watcher.ctl, self.solver.control)
        self.assertEqual(self.watcher.assumptions, [(Function("a"), True)])
        self.assertIsInstance(self.watcher.solve_timer, Timer)
        self.assertIsInstance(self.watcher.cutoff_timer, Timer)
        self.assertFalse(self.watcher.active)
        self.assertIsNone(self.watcher._cutoff_seconds)
        self.assertIsNone(self.watcher._cutoff_alarm)

    def test_on_model(self):
        """
        Test model callback forwarding, cutoff rearming, and alarm rescheduling.
        """
        model = mock.Mock(cost=[4])
        self.solver.stats = {}
        self.watcher.solve_timer = mock.Mock(get_elapsed_time=mock.Mock(return_value=2))
        self.watcher.cutoff_timer = mock.Mock(get_elapsed_time=mock.Mock(return_value=1))
        old_alarm = mock.Mock()
        self.watcher._cutoff_alarm = old_alarm
        self.watcher._cutoff_seconds = 5
        with mock.patch.object(self.watcher, "_schedule", return_value="new-alarm") as schedule:
            self.watcher._on_model(model)
        self.solver._on_model.assert_called_once_with(model)
        self.solver.logger.info.assert_called_once_with("%.3f, %s", 2, [4])
        self.assertEqual(self.solver.stats["time_to_last_model"], 1)
        self.watcher.cutoff_timer.restart.assert_called_once_with()
        old_alarm.cancel.assert_called_once_with()
        old_alarm.join.assert_called_once_with()
        schedule.assert_called_once_with(5)
        self.assertEqual(self.watcher._cutoff_alarm, "new-alarm")

    def test_stop(self):
        """
        Test that stop interrupts the solve directly, without any indirection.
        """
        self.watcher.stop()
        self.assertTrue(self.solver.interrupted)
        self.solver.control.interrupt.assert_called_once_with()

    def test_schedule_none(self):
        """
        Test that no alarm is scheduled when there is no deadline.
        """
        self.assertIsNone(self.watcher._schedule(None))

    def test_schedule(self):
        """
        Test scheduling a daemonized one-shot alarm that calls stop() on expiry.
        """
        with mock.patch("fastlane.interfaces.solver.threading.Timer") as timer_class:
            alarm = timer_class.return_value
            result = self.watcher._schedule(5)
        timer_class.assert_called_once_with(5, self.watcher.stop)
        self.assertTrue(alarm.daemon)
        alarm.start.assert_called_once_with()
        self.assertIs(result, alarm)

    def test_cancel_none(self):
        """
        Test that cancelling a missing alarm is a no-op.
        """
        ClingoSolveWatcher._cancel(None)  # pylint: disable=protected-access

    def test_cancel(self):
        """
        Test cancelling and joining a scheduled alarm.
        """
        alarm = mock.Mock()
        ClingoSolveWatcher._cancel(alarm)  # pylint: disable=protected-access
        alarm.cancel.assert_called_once_with()
        alarm.join.assert_called_once_with()

    def test_solve(self):
        """
        Test the full solve pass: deadlines, the blocking wait, and result handling.
        """
        context = mock.MagicMock()
        handle = context.__enter__.return_value
        self.solver.control.solve.return_value = context
        solve_alarm, cutoff_alarm = mock.Mock(), mock.Mock()
        self.watcher.solve_timer = mock.Mock(is_ringing=True, get_elapsed_time=mock.Mock(return_value=10))
        self.watcher.cutoff_timer = mock.Mock(is_ringing=False)
        with mock.patch.object(self.watcher, "_schedule", side_effect=[solve_alarm, cutoff_alarm]) as schedule:
            self.watcher.solve(10, 5, False)
        self.watcher.solve_timer.start.assert_called_once_with(10)
        self.watcher.cutoff_timer.start.assert_called_once_with(5, armed=True)
        self.solver.control.solve.assert_called_once_with(
            assumptions=self.watcher.assumptions,
            on_model=self.watcher._on_model,
            on_statistics=self.solver._on_statistics,
            on_finish=self.solver._on_finish,
            async_=True,
        )
        handle.wait.assert_called_once_with()
        self.solver.postprocess_solve.assert_called_once_with(handle.last.return_value, handle.get.return_value)
        self.solver.logger.info.assert_called_once_with("%s timer ringing after %s seconds", "Solve", 10)
        schedule.assert_has_calls([mock.call(10), mock.call(5)])
        solve_alarm.cancel.assert_called_once_with()
        solve_alarm.join.assert_called_once_with()
        cutoff_alarm.cancel.assert_called_once_with()
        cutoff_alarm.join.assert_called_once_with()
        self.assertFalse(self.watcher.active)
        self.assertFalse(self.solver.interrupted)

    def test_solve_require_model_defers_cutoff(self):
        """
        Test that require_model defers scheduling the cutoff alarm until the first model.
        """
        self.solver.control.solve.return_value = mock.MagicMock()
        self.watcher.cutoff_timer = mock.Mock()
        with mock.patch.object(self.watcher, "_schedule", return_value=None) as schedule:
            self.watcher.solve(None, 5, True)
        self.watcher.cutoff_timer.start.assert_called_once_with(5, armed=False)
        schedule.assert_called_once_with(None)  # only the (disabled) overall deadline
        self.assertIsNone(self.watcher._cutoff_alarm)

    def test_solve_error_propagates(self):
        """
        Test that solve errors propagate directly to the caller, with state still reset.
        """
        error = RuntimeError("solve failed")
        self.solver.control.solve.side_effect = error
        with self.assertRaises(RuntimeError) as raised:
            self.watcher.solve(None)
        self.assertIs(raised.exception, error)
        self.assertFalse(self.watcher.active)
        self.assertFalse(self.solver.interrupted)

    def test_real_time_limit(self):
        """
        Test that a real one-shot alarm interrupts an otherwise much longer real solve.
        """
        solver = ClingoSolver()
        solver.logger = mock.Mock()
        solver.logger.isEnabledFor.return_value = False
        solver.control.configuration.solve.models = 0  # enumerate all answer sets
        solver.add("base", [], "{ a(1..24) }.")
        solver.ground()
        watcher = ClingoSolveWatcher(solver)

        watcher.solve(0.2)

        self.assertTrue(watcher.solve_timer.is_ringing)
        self.assertFalse(watcher.active)
        solver.logger.info.assert_any_call("%s timer ringing after %s seconds", "Solve", mock.ANY)

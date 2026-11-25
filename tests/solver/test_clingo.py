"""
Test cases for clingo solvers and their solve watcher.
"""

import threading
from unittest import TestCase, mock

import clingo
from clingo.symbol import Function

from fastlane import Model
from fastlane.interfaces.solver import Solver, SolverConfig, SolveWatcher
from fastlane.lib.solvers.clingo_solver import ClingoSolver

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
        self.assertFalse(self.solver._watcher_active)
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
        Test shutdown requests with and without an active watcher.
        """
        for active in (False, True):
            with self.subTest(active=active):
                self.solver.stop = self.solver.finished = False
                self.solver._watcher_active = active
                self.assertEqual(self.solver.request_stop(), active)
                self.assertTrue(self.solver.stop)
                self.assertTrue(self.solver.finished)
        self.control.interrupt.assert_not_called()

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
        Test watcher startup, joining and cleanup.
        """
        assumptions = [(Function("a"), True)]
        with mock.patch("fastlane.lib.solvers.clingo_solver.SolveWatcher") as watcher_class:
            watcher = watcher_class.return_value
            watcher.is_alive.side_effect = [True, False]
            watcher.exception = None
            self.solver.interrupted = True
            self.solver._run_watcher(assumptions, 10, 5, True)
            watcher_class.assert_called_once_with(self.solver, assumptions)
            watcher.solve_timer.start.assert_called_once_with(10)
            watcher.cutoff_timer.start.assert_called_once_with(5, armed=False)
            watcher.start.assert_called_once_with()
            watcher.join.assert_called_once_with(timeout=0.1)
            watcher.cleanup.assert_called_once_with()
            self.assertFalse(self.solver._watcher_active)
            self.assertFalse(self.solver.interrupted)

    def test_run_watcher_errors(self):
        """
        Test propagating startup, worker and cleanup failures after resetting state.
        """
        for failure in ("start", "worker", "cleanup"):
            with (
                self.subTest(failure=failure),
                mock.patch("fastlane.lib.solvers.clingo_solver.SolveWatcher") as watcher_class,
            ):
                error = RuntimeError(failure)
                watcher = watcher_class.return_value
                watcher.is_alive.return_value = False
                watcher.exception = error if failure == "worker" else None
                if failure != "worker":
                    getattr(watcher, failure).side_effect = error
                self.solver.interrupted = True
                with self.assertRaises(RuntimeError) as raised:
                    self.solver._run_watcher([], None)
                self.assertIs(raised.exception, error)
                watcher.cleanup.assert_called_once_with()
                self.assertFalse(self.solver._watcher_active)
                self.assertFalse(self.solver.interrupted)

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


class TestSolveWatcher(TestCase):
    """
    Test watcher methods with mocked control and timers.
    """

    def setUp(self) -> None:
        self.solver = mock.Mock()
        with mock.patch("fastlane.interfaces.solver.ThreadedTimer") as timer_class:
            self.watcher = SolveWatcher(self.solver, [(Function("a"), True)])
        self.assertEqual(timer_class.call_args_list, [mock.call(self.watcher.stop), mock.call(self.watcher.stop)])
        self.watcher.solve_timer = mock.Mock()
        self.watcher.cutoff_timer = mock.Mock()

    def test_init(self):
        """
        Test watcher ownership, assumptions and initial state.
        """
        self.assertIs(self.watcher.solver, self.solver)
        self.assertIs(self.watcher.ctl, self.solver.control)
        self.assertEqual(self.watcher.assumptions, [(Function("a"), True)])
        self.assertIsNone(self.watcher.exception)
        self.assertFalse(self.watcher._stop_event.is_set())

    def test_on_model(self):
        """
        Test model callback forwarding and cutoff rearming.
        """
        model = mock.Mock(cost=[4])
        self.solver.stats = {}
        self.watcher.solve_timer.get_elapsed_time.return_value = 2
        self.watcher.cutoff_timer.get_elapsed_time.return_value = 1
        self.watcher._on_model(model)
        self.solver._on_model.assert_called_once_with(model)
        self.solver.logger.info.assert_called_once_with("%.3f, %s", 2, [4])
        self.assertEqual(self.solver.stats["time_to_last_model"], 1)
        self.watcher.cutoff_timer.restart.assert_called_once_with()

    def test_on_finish(self):
        """
        Test finish callback forwarding and wakeup.
        """
        result = mock.Mock()
        self.watcher._on_finish(result)
        self.solver._on_finish.assert_called_once_with(result)
        self.assertTrue(self.watcher._stop_event.is_set())

    def test_run(self):
        """
        Test delegation to the solve worker and storage of worker exceptions.
        """
        with mock.patch.object(self.watcher, "_run_solve") as run:
            self.watcher.run()
            run.assert_called_once_with()
            self.assertIsNone(self.watcher.exception)
            error = RuntimeError("worker failed")
            run.side_effect = error
            self.watcher.run()
            self.assertIs(self.watcher.exception, error)

    def test_run_solve(self):
        """
        Test asynchronous solve arguments, cancellation and result forwarding.
        """
        context = mock.MagicMock()
        handle = context.__enter__.return_value
        self.solver.control.solve.return_value = context
        self.watcher._stop_event.set()
        self.watcher.solve_timer.is_ringing = True
        self.watcher.solve_timer.get_elapsed_time.return_value = 10
        self.watcher.cutoff_timer.is_ringing = False
        self.watcher._run_solve()
        self.solver.control.solve.assert_called_once_with(
            async_=True,
            on_model=self.watcher._on_model,
            on_statistics=self.solver._on_statistics,
            on_finish=self.watcher._on_finish,
            assumptions=self.watcher.assumptions,
        )
        handle.cancel.assert_called_once_with()
        self.solver.postprocess_solve.assert_called_once_with(handle.last.return_value, handle.get.return_value)
        self.solver.logger.info.assert_called_once_with("%s timer ringing after %s seconds", "Solve", 10)

    def test_stop(self):
        """
        Test nonblocking stop signalling without cancellation in the caller.
        """
        self.watcher.stop()
        self.assertTrue(self.solver.interrupted)
        self.assertTrue(self.watcher._stop_event.is_set())
        self.solver.control.interrupt.assert_not_called()

    def test_cleanup(self):
        """
        Test waiting for callbacks before shutting down timers.
        """
        calls = mock.Mock()
        calls.attach_mock(self.watcher.solve_timer, "solve_timer")
        calls.attach_mock(self.watcher.cutoff_timer, "cutoff_timer")
        with (
            mock.patch.object(self.watcher, "stop") as stop,
            mock.patch.object(self.watcher, "is_alive", side_effect=[True, False]),
            mock.patch.object(self.watcher, "join") as join,
        ):
            calls.attach_mock(stop, "stop")
            calls.attach_mock(join, "join")
            self.watcher.cleanup()
        self.assertEqual(
            calls.mock_calls,
            [
                mock.call.stop(),
                mock.call.join(timeout=0.1),
                mock.call.solve_timer.stop(),
                mock.call.cutoff_timer.stop(),
                mock.call.solve_timer.join(),
                mock.call.cutoff_timer.join(),
            ],
        )

    def test_thread_stop(self):
        """
        Test that stop wakes a real watcher thread blocked on its event.
        """
        started = threading.Event()
        context = mock.MagicMock()

        def enter_solve():
            started.set()
            return mock.Mock()

        context.__enter__.side_effect = enter_solve
        self.solver.control.solve.return_value = context
        self.watcher.solve_timer.is_ringing = False
        self.watcher.cutoff_timer.is_ringing = False
        self.watcher.start()
        try:
            self.assertTrue(started.wait(timeout=2), "Watcher did not start")
            self.watcher.stop()
            self.watcher.join(timeout=2)
            self.assertFalse(self.watcher.is_alive(), "Stop did not wake the watcher")
            self.assertIsNone(self.watcher.exception)
            self.solver.postprocess_solve.assert_called_once()
        finally:
            self.watcher.stop()
            self.watcher.join(timeout=2)

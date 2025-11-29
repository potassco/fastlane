"""
Test cases for solver classes.
"""

import signal
from unittest import TestCase, mock

import clingcon
import clingo
import clingodl
from clingo.symbol import Function, Number

from mod_lns import Model, Timer
from mod_lns.interfaces.solver import SolverConfig
from mod_lns.lib.solvers.clingcon_solver import ClingconSolver
from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lns import LNS

# pylint: disable=protected-access


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
        self.strategy = DefaultStrategy()
        self.strategy.config.log_level = 50
        self.lns = LNS(["./tests/ref/golf.lp"], self.strategy)

        # for solve tests
        self.ref_opt_mode = "opt,10"

    def test_init(self):
        """
        Test initialization of ClingoSolver.
        """
        self.assertIsInstance(self.solver, self.stype)
        self.assertIsNone(self.solver.control)
        self.assertIsNone(self.solver.theory)
        self.assertFalse(self.solver.finished)
        self.assertEqual(self.solver.result, "UNKNOWN")
        self.assertEqual(self.solver.optimum, "unknown")
        self.assertIsNone(self.solver.minimize_variable)
        self.assertFalse(self.solver.stop)
        self.assertFalse(self.solver._assumptions_used)
        self.assertIsInstance(self.solver._timer, Timer)
        self.assertFalse(self.solver._interrupted)
        self.assertIsNone(self.solver.last_model)
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

        self.solver.control = None
        self.assertDictEqual(self.solver.get_stats(), {})

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
        with self.assertRaises(SystemExit), mock.patch.object(self.lns.strategy, "print_result") as print_result_mock:
            signal.raise_signal(signal.SIGINT)
            print_result_mock.assert_called_once_with(self.lns)
        self.assertTrue(self.solver.finished)
        self.assertTrue(self.solver.stop)

        self.solver.setup(self.lns)
        with (
            self.assertRaises(SystemExit),
            mock.patch.object(self.solver.control, "interrupt") as mock_interrupt,
            mock.patch.object(self.lns.strategy, "print_result") as print_result_mock,
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
        self.solver.control.configuration.solve.models = 2
        self.assertIsNone(self.solver.last_model)
        self.solver.control.solve(on_model=self.solver._on_model)
        self.assertIsInstance(self.solver.last_model, Model)

    def test_find_first_solution(self):
        """
        Test _find_first_solution method.
        """
        self.solver.setup(self.lns)
        self.solver.ground()
        self.assertIsNone(self.solver.last_model)
        self.solver._find_first_solution()
        self.assertIsInstance(self.solver.last_model, Model)

    def test_solve(self):
        """
        Test solve method.
        """
        self.solver.setup(self.lns)
        self.solver.ground()
        # default run
        self.solver.control.configuration.solve.models = 2
        model = self.solver.solve()
        self.assertIsInstance(model, Model)
        self.assertIn(self.solver.result, ["SATISFIABLE", "OPTIMUM"])

        # test setting of parameters
        self.solver.setup(self.lns)
        self.solver.ground()
        config = SolverConfig(
            configuration="tweety",
            opt_strategy="bb,0",
            opt_heuristic="3",
            restart_on_model="1",
            heuristic="Domain",
            opt_mode="opt,10",
            solve_limit="1000",
            time_limit=2,
            seed=42,
            variability=True,
        )
        model = self.solver.solve(config)
        self.assertIsInstance(model, Model)
        self.assertEqual(self.solver._variability, config.variability)
        self.assertEqual(self.solver.control.configuration.configuration, config.configuration)
        self.assertEqual(self.solver.control.configuration.solver.opt_strategy, "bb,lin")
        self.assertEqual(self.solver.control.configuration.solver.opt_heuristic, "sign,model")
        self.assertEqual(
            self.solver.control.configuration.solver.restart_on_model,
            config.restart_on_model,
        )
        self.assertEqual(self.solver.control.configuration.solver.heuristic, "domain,0")
        self.assertEqual(self.solver.control.configuration.solve.opt_mode, self.ref_opt_mode)
        self.assertEqual(self.solver.control.configuration.solve.solve_limit, "1000,umax")

        def spy_decorator(method_to_decorate):
            mock_obj = mock.MagicMock()

            def wrapper(self, *args, **kwargs):
                mock_obj(*args, **kwargs)
                return method_to_decorate(self, *args, **kwargs)

            wrapper.mock_obj = mock_obj
            return wrapper

        # test interruption by timer and finding first solution call
        mock_cancel = spy_decorator(clingo.SolveHandle.cancel)
        self.solver.setup(self.lns, [], ["./tests/ref/golf_big.lp"])
        self.solver.ground()
        self.solver.last_model = None
        with (
            mock.patch("mod_lns.Timer.is_ringing", mock.PropertyMock(return_value=True)),
            mock.patch.object(clingo.SolveHandle, "cancel", mock_cancel),
            mock.patch.object(self.solver, "_find_first_solution") as mock_find_first,
        ):
            self.solver.finished = False
            self.solver.solve()
            mock_cancel.mock_obj.assert_called_once()
            mock_find_first.assert_called_once()

        # test assumptions being used
        self.solver.setup(self.lns)
        self.solver.last_model = Model()
        assumptions = [(Function("a"), True)]
        with mock.patch.object(self.solver.control, "solve") as mock_solve:
            self.assertFalse(self.solver._assumptions_used)
            self.solver.solve(assumptions=assumptions)
            self.assertTrue(self.solver._assumptions_used)
            self.assertEqual(mock_solve.call_args.kwargs["assumptions"], assumptions)


class TestClingoDLSolver(TestSolverClingo):
    """
    Test cases for ClingoDLSolver class.
    """

    def setUp(self) -> None:
        self.solver = ClingoDLSolver()
        self.stype = ClingoDLSolver
        self.name = "clingo-dl"
        self.strategy = DefaultStrategy()
        self.strategy.config.log_level = 50
        self.lns = LNS(["./tests/ref/golf.lp"], self.strategy)
        # for solve tests, default
        self.ref_opt_mode = "opt,10"

    def test_setup(self):
        """
        Test clingo-dl setup.
        """
        self.solver.setup(self.lns)
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsInstance(self.solver.theory, clingodl.ClingoDLTheory)

        self.solver.setup(self.lns, ["--models=2"], ["./tests/ref/golf.lp"])
        self.assertIsInstance(self.solver.control, clingo.control.Control)
        self.assertIsInstance(self.solver.theory, clingodl.ClingoDLTheory)
        self.assertEqual(self.solver.control.configuration.solve.models, "2")

        self.solver.minimize_variable = Function("x")
        with mock.patch.object(clingo.ast, "parse_string") as mock_parse:
            self.solver.setup(self.lns)
            mock_parse.assert_called_once()

    def test_release_bound(self):
        """
        Test _release_bound method.
        """
        bound = 10
        self.solver.setup(self.lns)
        with mock.patch.object(self.solver.control, "release_external") as mock_release:
            self.solver._release_bound(bound)
            mock_release.assert_called_once_with(Function("__b", [Number(bound), Number(0)]))

    def test_add_bound(self):
        """
        Test _add_bound method.
        """
        bound = 10
        search_num = 1
        self.solver.setup(self.lns)
        self.solver._search_num = search_num
        with (
            mock.patch.object(self.solver.control, "add") as mock_add,
            mock.patch.object(self.solver.control, "ground") as mock_ground,
            mock.patch.object(self.solver.control, "assign_external") as mock_assign,
        ):
            self.solver._add_bound(bound)
            mock_add.assert_called_once_with("bound", ["t"], f"#external __b({bound},{search_num}).")
            mock_ground.assert_called_once_with([("bound", [Number(search_num)])])
            mock_assign.assert_called_once_with(Function("__b", [Number(bound), Number(search_num)]), True)

    def test_minimize_variable(self):
        """
        Test _minimize_variable method.
        """
        self.solver.setup(self.lns)
        self.solver.ground()
        self.solver.minimize_variable = Function("x")
        self.solver.control.configuration.solve.solve_limit = "1000,1000"
        self.solver.control.statistics["solving"]["solvers"]["conflicts"] = 5
        self.solver.control.statistics["solving"]["solvers"]["restarts"] = 10
        self.solver.last_model = Model()
        self.solver.last_model.cost = [42]

        # optimization finishes and timer rings
        # pylint: disable=unused-argument
        def mock_solve(on_model, on_statistics, on_finish, async_):
            setattr(self.solver._timer, "_time_limit", 5)
            setattr(self.solver._timer, "_ringing", True)
            setattr(self.solver, "result", "UNSATISFIABLE")
            handle = mock.MagicMock(name="handle", spec=clingo.SolveHandle)
            handle.__enter__.return_value.wait = lambda timeout: False
            handle.__enter__.return_value.cancel = lambda *args: (
                setattr(self.solver, "finished", True),
                setattr(handle.__enter__.return_value, "wait", lambda timeout: True),
            )
            return handle

        with (
            mock.patch.object(self.solver.control, "solve", mock_solve),
            mock.patch.object(self.solver, "_release_bound") as mock_release,
            mock.patch.object(self.solver, "_add_bound") as mock_add,
        ):
            self.solver._minimize_variable(prev_bound=43)
            mock_release.assert_called_once_with(43)
            mock_add.assert_called_once_with(41)
            self.assertEqual(self.solver.control.configuration.solve.solve_limit, "995,990")
            self.assertEqual(self.solver.result, "OPTIMUM FOUND")
            self.assertEqual(self.solver.optimum, "yes")

        # optimization does not finish, timer rings
        self.solver.control.configuration.solve.solve_limit = "1000,1000"
        self.solver._timer._ringing = False
        self.solver.finished = False

        with (
            mock.patch.object(self.solver.control, "solve"),
            mock.patch.object(self.solver, "_release_bound") as mock_release,
            mock.patch.object(
                self.solver,
                "_add_bound",
                side_effect=lambda prev_bound: setattr(self.solver._timer, "_ringing", True),
            ) as mock_add,
        ):
            self.solver._minimize_variable(prev_bound=43)
            mock_release.assert_has_calls([mock.call(43), mock.call(41)])
            mock_add.assert_called_once_with(41)
            self.assertEqual(self.solver.control.configuration.solve.solve_limit, "1000,1000")

        # conflict and restart limit reached
        self.solver._timer._ringing = False
        self.solver.finished = False

        with mock.patch.object(self.solver, "_add_bound") as mock_add:
            self.solver.control.configuration.solve.solve_limit = "1,1000"
            self.solver._minimize_variable(prev_bound=43)
            mock_add.assert_not_called()
            self.solver.control.configuration.solve.solve_limit = "1000,1"
            self.solver._minimize_variable(prev_bound=43)
            mock_add.assert_not_called()

    def test_solve(self):
        """
        Test solve method.
        """
        # no minimize variable set
        super().test_solve()

        self.setUp()
        # minimize variable set
        self.solver.minimize_variable = Function("x")
        self.ref_opt_mode = "opt"
        with (
            mock.patch.object(self.solver, "_minimize_variable") as mock_minimize,
            mock.patch.object(self.solver, "_add_bound") as mock_add,
        ):
            super().test_solve()
            mock_add.assert_called_once_with(10)
            # default run, setting of parameters, interruption by timer
            mock_minimize.assert_has_calls([mock.call(None), mock.call(10), mock.call(None)])


class TestClingconSolver(TestSolverClingo):
    """
    Test cases for ClingconSolver class.
    """

    def setUp(self) -> None:
        self.solver = ClingconSolver()
        self.stype = ClingconSolver
        self.name = "clingcon"
        self.strategy = DefaultStrategy()
        self.strategy.config.log_level = 50
        self.lns = LNS(["./tests/ref/golf.lp"], self.strategy)
        # for solve tests
        self.ref_opt_mode = "opt,10"

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

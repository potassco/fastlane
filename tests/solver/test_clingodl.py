"""
Test cases for ClingoDLSolver class.
"""

from unittest import mock

import clingo
import clingodl
from clingo.symbol import Function, Number

from mod_lns import Model
from mod_lns.interfaces.solver import SolverConfig
from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver
from mod_lns.lns import LNS
from tests.solver.test_clingo import TestSolverClingo


class TestClingoDLSolver(TestSolverClingo):
    """
    Test cases for ClingoDLSolver class.
    """

    def setUp(self) -> None:
        self.solver = ClingoDLSolver()
        self.stype = ClingoDLSolver
        self.name = "clingo-dl"
        self.lns = LNS(["./tests/ref/golf.lp"], {"log_level": 50})

    def test_init(self):
        """
        Test initialization of ClingoDLSolver.
        """
        super().test_init()
        self.assertEqual(self.solver._search_num, 0)
        self.assertFalse(self.solver._exhausted)
        self.assertIsNone(self.solver.bound)

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
            setattr(self.solver._solve_timer, "_time_limit", 5)
            setattr(self.solver._solve_timer, "_ringing", True)
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
        self.solver._solve_timer._ringing = False
        self.solver.finished = False

        with (
            mock.patch.object(self.solver.control, "solve"),
            mock.patch.object(self.solver, "_release_bound") as mock_release,
            mock.patch.object(
                self.solver,
                "_add_bound",
                side_effect=lambda prev_bound: setattr(self.solver._solve_timer, "_ringing", True),
            ) as mock_add,
        ):
            self.solver._minimize_variable(prev_bound=43)
            mock_release.assert_has_calls([mock.call(43), mock.call(41)])
            mock_add.assert_called_once_with(41)
            self.assertEqual(self.solver.control.configuration.solve.solve_limit, "1000,1000")

        # conflict and restart limit reached
        self.solver._solve_timer._ringing = False
        self.solver.finished = False

        with mock.patch.object(self.solver, "_add_bound") as mock_add:
            self.solver.control.configuration.solve.solve_limit = "1,1000"
            self.solver._minimize_variable(prev_bound=43)
            mock_add.assert_not_called()
            self.solver.control.configuration.solve.solve_limit = "1000,1"
            self.solver._minimize_variable(prev_bound=43)
            mock_add.assert_not_called()

    def test_apply_config_to_control(self):
        super().test_apply_config_to_control()
        self.solver.minimize_variable = Function("x")
        config = SolverConfig(
            opt_mode="opt,10",
        )
        with mock.patch.object(self.solver, "_add_bound") as mock_add:
            self.solver._apply_config_to_control(config)
            mock_add.assert_called_once_with(10)
        self.assertEqual(self.solver.bound, 10)

    def test_solve(self):
        """
        Test solve method.
        """
        # no minimize variable set
        super().test_solve()

        self.setUp()
        self.solver.setup(self.lns)
        self.solver.ground()
        self.solver.control.configuration.solve.models = 2
        # minimize variable set
        self.solver.minimize_variable = Function("x")
        with (
            mock.patch("mod_lns.Timer.is_ringing", mock.PropertyMock(return_value=True)),
            mock.patch.object(self.solver, "_minimize_variable") as mock_minimize,
        ):
            self.solver.solve(SolverConfig(opt_mode="opt,10"))
            mock_minimize.assert_has_calls([mock.call(10)])

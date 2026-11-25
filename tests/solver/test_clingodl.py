"""
Test cases for ClingoDLSolver class.
"""

from unittest import mock

import clingodl
from clingo.symbol import Function, Number

from fastlane import Model
from fastlane.interfaces.solver import SolverConfig
from fastlane.lib.solvers.clingo_dl_solver import ClingoDLSolver
from fastlane.lib.solvers.clingo_solver import ClingoSolver
from tests.solver import test_clingo

# pylint: disable=protected-access


class TestClingoDLSolver(test_clingo.TestSolverClingo):
    """
    Test cases for ClingoDLSolver class.
    """

    stype = ClingoDLSolver
    name = "clingo-dl"

    def test_init(self):
        """
        Test initialization of the DL search state.
        """
        super().test_init()
        self.assertEqual(self.solver._search_num, 0)
        self.assertIsNone(self.solver.bound)

    def test_setup(self):
        """
        Test theory registration, file rewriting and optional bound program.
        """
        for files, variable in ((None, None), (["other.lp"], Function("x"))):
            with (
                self.subTest(files=files, variable=variable),
                mock.patch("fastlane.lib.solvers.clingo_dl_solver.ClingoDLTheory") as theory,
                mock.patch("fastlane.lib.solvers.clingo_dl_solver.clingo.Control") as control,
                mock.patch("fastlane.lib.solvers.clingo_dl_solver.ast.ProgramBuilder") as builder,
                mock.patch("fastlane.lib.solvers.clingo_dl_solver.ast.parse_files") as parse_files,
                mock.patch("fastlane.lib.solvers.clingo_dl_solver.ast.parse_string") as parse_string,
            ):
                self.solver.minimize_variable = variable
                self.solver.setup(self.lns, ["--models=2"], files)
                theory.assert_called_once_with()
                self.assertEqual(control.call_args.args, (["--models=2"],))
                self.assertTrue(callable(control.call_args.kwargs["logger"]))
                theory.return_value.register.assert_called_once_with(control.return_value)
                builder.assert_called_once_with(control.return_value)
                self.assertEqual(parse_files.call_args.args[0], self.lns.files if files is None else files)
                node = mock.Mock()
                parse_files.call_args.args[1](node)
                theory.return_value.rewrite_ast.assert_called_once_with(
                    node, builder.return_value.__enter__.return_value.add
                )
                if variable is None:
                    parse_string.assert_not_called()
                else:
                    self.assertEqual(
                        parse_string.call_args.args[0],
                        "#program bound(t). &diff { x - 0 } <= B :- __b(B,t).",
                    )
                    theory.return_value.rewrite_ast.reset_mock()
                    parse_string.call_args.args[1](node)
                    theory.return_value.rewrite_ast.assert_called_once_with(
                        node, builder.return_value.__enter__.return_value.add
                    )
                self.assertIs(self.solver.control, control.return_value)
                self.assertIs(self.solver.theory, theory.return_value)

    def test_prepare_solve(self):
        """
        Test theory preparation.
        """
        self.solver.theory = mock.Mock(spec=clingodl.ClingoDLTheory)
        self.solver._prepare_solve()
        self.solver.theory.prepare.assert_called_once_with(self.control)

    def test_on_model(self):
        """
        Test forwarding models to the theory.
        """
        self.solver.theory = mock.Mock(spec=clingodl.ClingoDLTheory)
        model = mock.Mock()
        self.solver._on_model(model)
        self.solver.theory.on_model.assert_called_once_with(model=model)

    def test_on_statistics(self):
        """
        Test forwarding both statistics maps to the theory.
        """
        self.solver.theory = mock.Mock(spec=clingodl.ClingoDLTheory)
        step, accu = mock.Mock(), mock.Mock()
        self.solver._on_statistics(step, accu)
        self.solver.theory.on_statistics.assert_called_once_with(step, accu)

    def test_release_bound(self):
        """
        Test releasing the bound for the current search.
        """
        self.solver._search_num = 2
        self.solver._release_bound(10)
        self.control.release_external.assert_called_once_with(Function("__b", [Number(10), Number(2)]))

    def test_add_bound(self):
        """
        Test adding, grounding and enabling the bound for the current search.
        """
        self.solver._search_num = 2
        self.solver._add_bound(10)
        self.control.add.assert_called_once_with("bound", ["t"], "#external __b(10,2).")
        self.control.ground.assert_called_once_with([("bound", [Number(2)])])
        self.control.assign_external.assert_called_once_with(Function("__b", [Number(10), Number(2)]), True)

    def test_minimize_variable(self):
        """
        Test tightening successive bounds with remaining conflict, restart and time budgets.
        """
        self.solver.watcher = mock.Mock()
        self.solver.watcher.solve_timer.get_elapsed_time.side_effect = [1, 2, 3, 4]
        self.control.configuration.solve.solve_limit = "1000,1000"
        self.control.statistics = {"solving": {"solvers": {"conflicts": 5, "restarts": 10}}}
        self.solver.last_model = mock.Mock(spec=Model, cost=[42])
        self.solver.bound = 43
        assumptions = [(Function("a"), True)]
        limits = []

        def run_watcher(*_args):
            limits.append(self.control.configuration.solve.solve_limit)
            if len(limits) == 1:
                self.solver.last_model = mock.Mock(spec=Model, cost=[40])

        with (
            mock.patch.object(self.solver, "_release_bound") as release,
            mock.patch.object(self.solver, "_add_bound") as add,
            mock.patch.object(self.solver, "_prepare_solve") as prepare,
            mock.patch.object(self.solver, "_run_watcher", side_effect=run_watcher) as run,
        ):
            self.solver._minimize_variable(assumptions, 10)
            release.assert_has_calls([mock.call(43), mock.call(41)])
            add.assert_has_calls([mock.call(41), mock.call(39)])
            self.assertEqual(prepare.call_count, 2)
            self.assertEqual(run.call_args_list, [mock.call(assumptions, 8), mock.call(assumptions, 6)])
        self.assertEqual(limits, ["995,990", "990,980"])
        self.assertEqual(self.control.configuration.solve.solve_limit, "1000,1000")
        self.assertEqual(self.solver.last_model.cost, [40])
        self.assertEqual(self.solver.bound, 39)

    def test_minimize_variable_limits(self):
        """
        Test stopping before a pass when the time, conflict or restart budget runs out.
        """
        self.solver.watcher = mock.Mock()
        self.solver.last_model = mock.Mock(spec=Model, cost=[42])
        self.control.statistics = {"solving": {"solvers": {"conflicts": 5, "restarts": 10}}}
        for limit, elapsed, time_limit in (
            ("umax,umax", [10], 10),
            ("5,umax", [0], 10),
            ("umax,10", [0], 10),
            ("umax,umax", [0, 10], 10),
        ):
            with (
                self.subTest(limit=limit, elapsed=elapsed),
                mock.patch.object(self.solver, "_add_bound"),
                mock.patch.object(self.solver, "_release_bound"),
                mock.patch.object(self.solver, "_prepare_solve"),
                mock.patch.object(self.solver, "_run_watcher") as run,
            ):
                self.control.configuration.solve.solve_limit = limit
                self.solver.watcher.solve_timer.get_elapsed_time.side_effect = elapsed
                self.solver._minimize_variable([], time_limit)
                run.assert_not_called()
                self.assertEqual(self.control.configuration.solve.solve_limit, limit)

    def test_minimize_variable_error(self):
        """
        Test unlimited budgets and restoration of solve limits after worker errors.
        """
        self.solver.watcher = mock.Mock()
        self.solver.last_model = mock.Mock(spec=Model, cost=[42])
        self.control.configuration.solve.solve_limit = "umax,umax"
        self.control.statistics = {"solving": {"solvers": {"conflicts": 5, "restarts": 10}}}
        error = RuntimeError("worker failed")
        with (
            mock.patch.object(self.solver, "_add_bound") as add,
            mock.patch.object(self.solver, "_prepare_solve"),
            mock.patch.object(self.solver, "_run_watcher", side_effect=error) as run,
        ):
            with self.assertRaises(RuntimeError) as raised:
                self.solver._minimize_variable([], None)
            self.assertIs(raised.exception, error)
            add.assert_called_once_with(41)
            run.assert_called_once_with([], None)
        self.assertEqual(self.control.configuration.solve.solve_limit, "umax,umax")
        self.solver.watcher.solve_timer.get_elapsed_time.assert_not_called()

    def test_apply_opt_mode(self):
        """
        Test delegating ordinary optimization and adding a DL bound.
        """
        with mock.patch.object(ClingoSolver, "_apply_opt_mode") as apply:
            self.solver._apply_opt_mode("opt")
            apply.assert_called_once_with("opt")
        self.solver.minimize_variable = Function("x")
        with mock.patch.object(self.solver, "_add_bound") as add:
            self.solver._apply_opt_mode("opt,10")
            self.assertEqual(self.solver.bound, 10)
            add.assert_called_once_with(10)

    def test_solve(self):
        """
        Test search numbering, parent delegation, minimization and bound cleanup.
        """
        assumptions = [(Function("a"), True)]
        config = SolverConfig(time_limit=10)
        self.solver.last_model = mock.Mock(spec=Model, cost=[42])
        with (
            mock.patch.object(ClingoSolver, "solve", return_value=self.solver.last_model) as solve,
            mock.patch.object(self.solver, "_minimize_variable") as minimize,
            mock.patch.object(self.solver, "_release_bound") as release,
        ):
            self.assertIs(self.solver.solve(config, assumptions, True), self.solver.last_model)
            solve.assert_called_once_with(config, assumptions, True)
            minimize.assert_not_called()
            self.assertEqual(self.solver._search_num, 1)

            self.solver.minimize_variable = Function("x")
            self.solver.bound = 43
            self.assertIs(self.solver.solve(config, assumptions), self.solver.last_model)
            minimize.assert_called_once_with(assumptions, 10)
            release.assert_called_once_with(43)
            self.assertIsNone(self.solver.bound)
            self.assertEqual(self.solver._search_num, 2)

            minimize.reset_mock()
            self.solver.solve()
            minimize.assert_called_once_with([], None)

    def test_solve_error(self):
        """
        Test releasing the bound even if the parent solve fails.
        """
        self.solver.bound = 10
        error = RuntimeError("startup failed")
        with (
            mock.patch.object(ClingoSolver, "solve", side_effect=error),
            mock.patch.object(self.solver, "_release_bound") as release,
        ):
            with self.assertRaises(RuntimeError) as raised:
                self.solver.solve()
            self.assertIs(raised.exception, error)
            release.assert_called_once_with(10)
        self.assertIsNone(self.solver.bound)

    def test_postprocess_solve(self):
        """
        Test parent postprocessing and extraction of DL assignments.
        """
        self.solver.last_model = Model()
        model = mock.Mock()
        model.symbols.return_value = [Function("other"), Function("dl", [Function("x"), Number(7)])]
        result = mock.Mock()
        with mock.patch.object(ClingoSolver, "postprocess_solve") as postprocess:
            self.solver.postprocess_solve(model, result)
            postprocess.assert_called_once_with(model, result)
        model.symbols.assert_called_once_with(theory=True)
        self.assertEqual(self.solver.last_model.assignments, ["x=7"])

    def test_postprocess_solve_minimize(self):
        """
        Test saving DL assignments and the objective value.
        """
        self.solver.minimize_variable = Function("x")
        self.solver.last_model = Model()
        model = mock.Mock()
        model.symbols.return_value = [
            Function("dl", [Function("y"), Number(1)]),
            Function("dl", [Function("x"), Number(7)]),
        ]
        result = mock.Mock(satisfiable=True, unsatisfiable=False, exhausted=False)
        with mock.patch.object(self.solver, "_save_model") as save, mock.patch("builtins.print") as output:
            self.solver.postprocess_solve(model, result)
            save.assert_called_once_with(model)
            output.assert_called_once_with("Optimization:", 7)
        self.assertEqual(self.solver.last_model.assignments, ["y=1", "x=7"])
        self.assertEqual(self.solver.last_model.cost, [7])
        self.assertEqual(self.solver.result, "SATISFIABLE")
        self.assertEqual(self.solver.stats["result"], "SATISFIABLE")
        self.assertFalse(self.solver.finished)

    def test_postprocess_solve_exhausted(self):
        """
        Test infeasible objectives, optimal incumbents and SAT without a model.
        """
        self.solver.minimize_variable = Function("x")
        self.solver._variability = True
        unsat = mock.Mock(satisfiable=False, unsatisfiable=True, exhausted=True)
        for incumbent, expected in ((None, "UNSATISFIABLE"), (mock.Mock(spec=Model, cost=[7]), "OPTIMUM FOUND")):
            with self.subTest(expected=expected):
                self.solver.finished = False
                self.solver.last_model = incumbent
                self.solver.postprocess_solve(None, unsat)
                self.assertEqual(self.solver.result, expected)
                self.assertEqual(self.solver.stats["result"], expected)
                self.assertTrue(self.solver.finished)
        self.assertEqual(self.solver.optimum, "yes")

        self.solver.finished = False
        self.solver.last_model = None
        self.solver.postprocess_solve(None, mock.Mock(satisfiable=True))
        self.assertEqual(self.solver.result, "SATISFIABLE")
        self.assertTrue(self.solver.finished)

    def test_postprocess_solve_missing_assignment(self):
        """
        Test reporting a missing minimize variable instead of inventing a cost.
        """
        self.solver.minimize_variable = Function("x")
        self.solver.last_model = Model()
        model = mock.Mock()
        model.symbols.return_value = [Function("dl", [Function("y"), Number(1)])]
        result = mock.Mock(satisfiable=False, unsatisfiable=False)
        with mock.patch.object(self.solver, "_save_model"):
            with self.assertRaisesRegex(ValueError, "No DL assignment for minimize variable x"):
                self.solver.postprocess_solve(model, result)

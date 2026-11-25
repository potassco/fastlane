"""
Test cases for ClingconSolver class.
"""

from unittest import mock

import clingcon
from clingo.symbol import Function, String

from fastlane import Model
from fastlane.lib.solvers.clingcon_solver import ClingconSolver
from fastlane.lib.solvers.clingo_solver import ClingoSolver
from tests.solver import test_clingo

# pylint: disable=protected-access


class TestClingconSolver(test_clingo.TestSolverClingo):
    """
    Test cases for ClingconSolver class.
    """

    stype = ClingconSolver
    name = "clingcon"

    def test_setup(self):
        """
        Test theory registration and AST rewriting without parsing real files.
        """
        for files in (None, ["other.lp"]):
            with (
                self.subTest(files=files),
                mock.patch("fastlane.lib.solvers.clingcon_solver.ClingconTheory") as theory,
                mock.patch("fastlane.lib.solvers.clingcon_solver.clingo.Control") as control,
                mock.patch("fastlane.lib.solvers.clingcon_solver.ast.ProgramBuilder") as builder,
                mock.patch("fastlane.lib.solvers.clingcon_solver.ast.parse_files") as parse_files,
            ):
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
                self.assertIs(self.solver.control, control.return_value)
                self.assertIs(self.solver.theory, theory.return_value)

    def test_prepare_solve(self):
        """
        Test theory preparation.
        """
        self.solver.theory = mock.Mock(spec=clingcon.ClingconTheory)
        self.solver._prepare_solve()
        self.solver.theory.prepare.assert_called_once_with(self.control)

    def test_on_model(self):
        """
        Test forwarding models to the theory.
        """
        self.solver.theory = mock.Mock(spec=clingcon.ClingconTheory)
        model = mock.Mock()
        self.solver._on_model(model)
        self.solver.theory.on_model.assert_called_once_with(model=model)

    def test_on_statistics(self):
        """
        Test forwarding both statistics maps to the theory.
        """
        self.solver.theory = mock.Mock(spec=clingcon.ClingconTheory)
        step, accu = mock.Mock(), mock.Mock()
        self.solver._on_statistics(step, accu)
        self.solver.theory.on_statistics.assert_called_once_with(step, accu)

    def test_save_model(self):
        """
        Test theory assignments and cost fallback independently of base model copying.
        """
        self.solver.theory = mock.Mock(spec=clingcon.ClingconTheory)
        self.solver.theory.assignment.return_value = [(Function("x"), 7)]
        self.solver.last_model = Model()
        model = mock.Mock(thread_id=2)
        model.symbols.return_value = [Function("other"), Function("__csp_cost", [String("7")])]
        with mock.patch.object(ClingoSolver, "_save_model") as save, mock.patch("builtins.print") as output:
            self.solver._save_model(model)
            save.assert_called_once_with(model)
            self.solver.theory.assignment.assert_called_once_with(2)
            self.assertEqual(self.solver.last_model.assignments, ["x=7"])
            self.assertEqual(self.solver.last_model.cost, [7])
            model.symbols.assert_called_once_with(theory=True)
            output.assert_called_once_with("Optimization:", 7)

            model.symbols.reset_mock()
            output.reset_mock()
            self.solver._save_model(model)
            model.symbols.assert_not_called()
            output.assert_not_called()

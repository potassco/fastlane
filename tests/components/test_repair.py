"""
Test cases for repair components of the LNS framework.
"""

from unittest import TestCase, mock

from clingo.symbol import Function, Number

from fastlane.interfaces.solver import Solver, SolverConfig
from fastlane.lib.components.repair import repair_assumptions, repair_heuristics


class TestRepairComponents(TestCase):
    """
    Test cases for repair components of the LNS framework.
    """

    def test_repair_assumptions(self):
        """
        Test repair_assumptions function.
        """
        mock_solver = mock.Mock(spec=Solver)
        mock_solver_config = mock.Mock(spec=SolverConfig)

        fixed_atoms = {mock.Mock(), mock.Mock()}

        repair_assumptions(mock_solver, mock_solver_config, fixed_atoms)

        mock_solver.solve.assert_called_once_with(mock_solver_config, list(map(lambda x: (x, True), fixed_atoms)))

    def test_repair_heuristics(self):
        """
        Test repair_heuristics function.
        """
        mock_solver = mock.Mock(spec=Solver)
        mock_solver_config = mock.Mock(spec=SolverConfig)
        mock_logger = mock.Mock()

        fixed_atoms_heuristics = {
            Function(
                "__heuristic",
                [
                    Function("plays", [Number(1), Number(2), Number(3)], True),
                    Number(1),
                    Function("true", [], True),
                    Number(2),
                ],
                True,
            ),
            Function(
                "__heuristic",
                [
                    Function("plays", [Number(4), Number(5), Number(6)], True),
                    Number(1),
                    Function("true", [], True),
                    Number(2),
                ],
                True,
            ),
        }
        prev_fixed_atoms_heuristics = {
            Function(
                "__heuristic",
                [
                    Function("plays", [Number(1), Number(2), Number(3)], True),
                    Number(1),
                    Function("true", [], True),
                    Number(1),
                ],
                True,
            )
        }

        repair_heuristics(
            solver=mock_solver,
            solver_config=mock_solver_config,
            fixed_atoms_heuristics=fixed_atoms_heuristics,
            prev_fixed_atoms_heuristics=prev_fixed_atoms_heuristics,
            step=2,
            logger=mock_logger,
        )

        self.assertEqual(mock_solver.release_external.call_count, len(prev_fixed_atoms_heuristics))
        mock_solver.add.assert_called_once()
        add_name, add_parameters, add_program = mock_solver.add.call_args.args
        self.assertEqual(add_name, "external")
        self.assertEqual(add_parameters, ["t"])
        self.assertSetEqual(
            {statement for statement in add_program.split(".") if statement},
            {
                "#external __heuristic(plays(1,2,3),1,true,2)",
                "#external __heuristic(plays(4,5,6),1,true,2)",
            },
        )
        # ground external and heuristic subprograms
        self.assertEqual(mock_solver.ground.call_count, 2)
        self.assertEqual(mock_solver.assign_external.call_count, len(fixed_atoms_heuristics))

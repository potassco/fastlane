"""
Test cases for the destruction component.
"""

from unittest import TestCase, mock

from clingo.symbol import Function, Number, Tuple_

from mod_lns import Model
from mod_lns.lib.components.destruction import (
    _destroy,
    _destroy_atoms_if_all_args_selected,
    _destroy_atoms_if_term_selected,
    _project,
    destroy_config,
    destroy_random,
    format_atoms,
)
from mod_lns.utils.types import ActiveConfig, DestroyOperator, ProjectOperator


class TestDestructionComponents(TestCase):
    """
    Test cases for the destruction component.
    """

    def test_destroy_random(self):
        """
        Test destroy_random function.
        """
        model = Model()
        model.shown = {Function("a", [Number(1)]), Function("b", [Number(2), Number(3)])}
        model.true = {Function("a", [Number(1)]), Function("b", [Number(2), Number(3)]), Function("c")}
        destruction_rate = 50
        fixed_atoms = destroy_random(model, destruction_rate)
        self.assertEqual(len(fixed_atoms), 1)

    def test_format_atoms(self):
        """
        Test format_atoms function.
        """
        atoms = {Function("a", [Number(1)]), Function("b", [Number(2), Number(3)]), Function("c")}
        formatted = format_atoms(atoms)
        self.assertEqual(formatted, "c a(1) b(2,3)")

    def test_project(self):
        """
        Test _project function.
        """
        model = mock.Mock(spec=Model)
        projected_atoms = {
            Function("plays", [Number(1), Number(2), Number(3)], True),
            Function("plays", [Number(4), Number(5), Number(6)], True),
        }

        with mock.patch(
            "mod_lns.lib.components.destruction.ConfigParser.get_projected_atoms", return_value=projected_atoms
        ) as mock_get_projected_atoms:
            project_operators = [ProjectOperator(name="plays_3")]
            self.assertSetEqual(_project(model, project_operators, mock.Mock()), projected_atoms)
            mock_get_projected_atoms.assert_called_once_with(model, "plays_3")

    def test_destroy_atoms_if_term_selected(self):
        """
        Test _destroy_atoms_if_term_selected function.
        """
        atom_term_pairs = [
            {"atom": Function("a", [Number(1)]), "term": Number(1)},
            {"atom": Function("b", [Number(2), Number(3)]), "term": Number(2)},
        ]
        percent_or_number = {"type": "p", "value": 50}
        destroyed_atoms = _destroy_atoms_if_term_selected(atom_term_pairs, percent_or_number)
        self.assertEqual(len(destroyed_atoms), 1)
        percent_or_number = {"type": "n", "value": 0}
        destroyed_atoms = _destroy_atoms_if_term_selected(atom_term_pairs, percent_or_number)
        self.assertEqual(len(destroyed_atoms), 0)

    def test_destroy_atoms_if_all_args_selected(self):
        """
        Test _destroy_atoms_if_all_args_selected function.
        """
        atom_term_pairs = [
            {"atom": Function("a", [Number(1), Number(2)]), "term": Tuple_([Number(1), Number(2)])},
            {"atom": Function("b", [Number(3), Number(2)]), "term": Tuple_([Number(3), Number(2)])},
        ]
        percents_or_numbers = [{"type": "p", "value": 50}, {"type": "n", "value": 1}]
        destroyed_atoms = _destroy_atoms_if_all_args_selected(atom_term_pairs, percents_or_numbers)
        self.assertEqual(len(destroyed_atoms), 1)
        percents_or_numbers = [{"type": "p", "value": 50}, {"type": "n", "value": 0}]
        destroyed_atoms = _destroy_atoms_if_all_args_selected(atom_term_pairs, percents_or_numbers)
        self.assertEqual(len(destroyed_atoms), 0)

    def test_destroy(self):
        """
        Test _destroy function.
        """
        # single destroy argument
        model = mock.Mock(spec=Model)
        projected_atoms = {
            Function("plays", [Number(1), Number(2), Number(3)], True),
            Function("plays", [Number(4), Number(5), Number(6)], True),
            Function("plays", [Number(7), Number(8), Number(9)], True),
        }
        destroy_operators = [DestroyOperator.from_specs("random_n", [{"type": "p", "value": 50}])]
        atom_term_pairs = [
            {"atom": Function("plays", [Number(1), Number(2), Number(3)], True), "term": Number(1)},
            {"atom": Function("plays", [Number(4), Number(5), Number(6)], True), "term": Number(4)},
        ]
        with mock.patch(
            "mod_lns.lib.components.destruction.ConfigParser.get_atom_term_pairs", return_value=atom_term_pairs
        ) as mock_get_atom_term_pairs:
            # 3 projected atoms, 2 with destroy operators, 1 destroyed -> 2 remaining
            self.assertEqual(len(_destroy(model, destroy_operators, projected_atoms, mock.Mock())), 2)
            mock_get_atom_term_pairs.assert_called_once_with(model, projected_atoms, "random_n")

        # multiple destroy arguments
        model = mock.Mock(spec=Model)
        projected_atoms = {
            Function("plays", [Number(1), Number(2), Number(3)], True),
            Function("plays", [Number(4), Number(5), Number(6)], True),
            Function("plays", [Number(7), Number(8), Number(9)], True),
        }
        destroy_operators = [
            DestroyOperator.from_specs("random_n", [{"type": "p", "value": 50}, {"type": "n", "value": 1}])
        ]
        atom_term_pairs = [
            {
                "atom": Function("plays", [Number(1), Number(2), Number(3)], True),
                "term": Tuple_([Number(1), Number(2)]),
            },
            {
                "atom": Function("plays", [Number(4), Number(5), Number(6)], True),
                "term": Tuple_([Number(4), Number(2)]),
            },
        ]
        with mock.patch(
            "mod_lns.lib.components.destruction.ConfigParser.get_atom_term_pairs", return_value=atom_term_pairs
        ) as mock_get_atom_term_pairs:
            # 3 projected atoms, 2 with destroy operators, 1 destroyed -> 2 remaining
            self.assertEqual(len(_destroy(model, destroy_operators, projected_atoms, mock.Mock())), 2)
            mock_get_atom_term_pairs.assert_called_once_with(model, projected_atoms, "random_n")

    def test_destroy_config(self):
        """
        Test destroy_config function.
        """
        model = mock.Mock(spec=Model)
        config: ActiveConfig = {
            "prioritize_operators": [{"name": "test_op", "value": 1, "modifier": "true"}],
            "destroy_operators": [DestroyOperator.from_specs("test_op", [{"type": "p", "value": 50}])],
            "project_operators": [ProjectOperator.from_signatures(name="test_op", signatures={("test_op", 1)})],
        }
        logger = mock.Mock()
        projected = {Function("test_atom", [Number(1)])}
        with (
            mock.patch("mod_lns.lib.components.destruction._project", return_value=projected) as mock_project,
            mock.patch("mod_lns.lib.components.destruction._destroy") as mock_destroy,
        ):
            destroy_config(model, config, logger)
            mock_project.assert_called_once_with(model, config["project_operators"], logger)
            mock_destroy.assert_called_once_with(model, config["destroy_operators"], projected, logger)

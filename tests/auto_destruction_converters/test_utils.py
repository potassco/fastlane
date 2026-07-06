"""
Test cases for auto-destruction converter utilities.
"""

from unittest import TestCase, mock

from clingo.symbol import Function

from mod_lns import Model
from mod_lns.lib.auto_destruction_converters.utils import calculate_actual_destruction_percent, is_new_model_better


class TestAutoDestructionConverterUtils(TestCase):
    """
    Test cases for utility functions in auto-destruction converters.
    """

    def test_calculate_actual_destruction_percent(self):
        """
        Test the calculate_actual_destruction_percent function.
        """
        self.assertEqual(calculate_actual_destruction_percent(set(), mock.Mock()), 0.0)

        destruction_candidate_atoms = {Function("a"), Function("b")}
        model = Model()
        model.shown = {Function("a")}
        expected_percent = (len(destruction_candidate_atoms - model.shown) / len(destruction_candidate_atoms)) * 100
        self.assertEqual(calculate_actual_destruction_percent(destruction_candidate_atoms, model), expected_percent)

    def test_is_new_model_better(self):
        """
        Test the is_new_model_better function.
        """
        current_model = Model()
        current_model.cost = 10
        new_model_better = Model()
        new_model_better.cost = 5
        new_model_worse = Model()
        new_model_worse.cost = 15

        self.assertTrue(is_new_model_better(new_model_better, current_model))
        self.assertFalse(is_new_model_better(new_model_worse, current_model))
        self.assertFalse(is_new_model_better(None, current_model))

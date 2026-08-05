"""
Test cases for the heuristics components of the LNS framework.
"""

from unittest import TestCase, mock

from clingo.symbol import Function, Number

from fastlane.lib.components.heuristics import (
    generate_heuristic_subprogram,
    get_fixed_atoms_heuristics,
)
from fastlane.parsers.config_parser import ConfigParser
from fastlane.utils.types import ActiveConfig, ConfigCatalog, PrioritizeOperator


class TestHeuristicsComponents(TestCase):
    """
    Test cases for the heuristics components of the LNS framework.
    """

    def test_generate_heuristic_subprogram(self):
        """
        Test generate_heuristic_subprogram function.
        """
        config_catalog: ConfigCatalog = {
            "project_operators": {
                "op1": {("a", 2), ("b", 1)},
                "op2": {("c", 3)},
            }
        }
        expected_components = [
            (
                "#heuristic a(X0,X1) : __heuristic(a(X0,X1),W,M,t), W != inf. [W,M]"
                ":- not a(X0,X1), __heuristic(a(X0,X1),inf,true,t)."
                ":- a(X0,X1), __heuristic(a(X0,X1),inf,false,t)."
            ),
            (
                "#heuristic b(X0) : __heuristic(b(X0),W,M,t), W != inf. [W,M]"
                ":- not b(X0), __heuristic(b(X0),inf,true,t)."
                ":- b(X0), __heuristic(b(X0),inf,false,t)."
            ),
            (
                "#heuristic c(X0,X1,X2) : __heuristic(c(X0,X1,X2),W,M,t), W != inf. [W,M]"
                ":- not c(X0,X1,X2), __heuristic(c(X0,X1,X2),inf,true,t)."
                ":- c(X0,X1,X2), __heuristic(c(X0,X1,X2),inf,false,t)."
            ),
        ]

        heuristic_subprogram = generate_heuristic_subprogram(config_catalog)

        for expected_component in expected_components:
            self.assertIn(expected_component, heuristic_subprogram)
        self.assertEqual(heuristic_subprogram.count("#heuristic "), len(expected_components))

    def test_get_fixed_atoms_heuristics(self):
        """
        Test get_fixed_atoms_heuristics function.
        """
        active_config: ActiveConfig = {
            "prioritize_operators": [
                PrioritizeOperator.from_spec("1_true", {"value": "inf", "modifier": "true"}),
                PrioritizeOperator.from_spec("5_sign", {"value": 5, "modifier": "sign"}),
            ]
        }
        model = mock.Mock()
        fixed_atoms = {
            Function("plays", [Number(1), Number(2), Number(3)], True),
            Function("plays", [Number(4), Number(5), Number(6)], True),
            Function("plays", [Number(7), Number(8), Number(9)], True),
        }
        heuristic_targets = [
            {Function("plays", [Number(1), Number(2), Number(3)], True)},
            {Function("plays", [Number(4), Number(5), Number(6)], True)},
        ]
        expected_fixed_atoms_heuristics = {
            Function(
                "__heuristic",
                [
                    Function("plays", [Number(1), Number(2), Number(3)], True),
                    Function("inf", [], True),
                    Function("true", [], True),
                    Number(1),
                ],
                True,
            ),
            Function(
                "__heuristic",
                [
                    Function("plays", [Number(4), Number(5), Number(6)], True),
                    Number(5),
                    Function("sign", [], True),
                    Number(1),
                ],
                True,
            ),
            Function(
                "__heuristic",
                [
                    Function("plays", [Number(7), Number(8), Number(9)], True),
                    Number(1),
                    Function("true", [], True),
                    Number(1),
                ],
                True,
            ),
        }

        with mock.patch.object(
            ConfigParser, "get_heuristic_targets", side_effect=heuristic_targets
        ) as mock_get_heuristic_targets:
            fixed_atoms_heuristics = get_fixed_atoms_heuristics(active_config, model, fixed_atoms, step=1)
            mock_get_heuristic_targets.assert_any_call(model, fixed_atoms, "1_true")
            mock_get_heuristic_targets.assert_any_call(model, fixed_atoms, "5_sign")
        self.assertSetEqual(fixed_atoms_heuristics, expected_fixed_atoms_heuristics)

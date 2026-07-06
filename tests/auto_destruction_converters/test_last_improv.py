"""
Test cases for the last improvement auto-destruction converter.
"""

from unittest import TestCase, mock

from clingo.symbol import Function, Number, String

from mod_lns import Model
from mod_lns.lib.auto_destruction_converters.last_improv import LastImprovementDestructionConverter

# pylint: disable=protected-access


class TestLastImprovementDestructionConverter(TestCase):
    """
    Test cases for the last improvement auto-destruction converter.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        self.converter = LastImprovementDestructionConverter(auto_init_percent=10)

    def test_init(self):
        """
        Test the initialization of the converter.
        """
        self.assertEqual(LastImprovementDestructionConverter()._auto_init_percent, 0)
        self.assertEqual(self.converter._auto_init_percent, 10)
        self.assertIsNone(self.converter._last_improvement_models)
        self.assertIsNone(self.converter._last_improvement_specs)
        self.assertDictEqual(self.converter._projected_atoms_cache, {})
        self.assertDictEqual(self.converter._actual_destruction_percent_cache, {})

    def test_reset_caches(self):
        """
        Test the reset of caches.
        """
        self.converter._projected_atoms_cache = {
            "proj_op": {
                Function("plays", [Number(1), Number(2), Number(3)], True),
                Function("plays", [Number(4), Number(5), Number(6)], True),
            }
        }
        self.converter._actual_destruction_percent_cache = {("config", "dest_op"): 20.0}
        self.converter._reset_caches()
        self.assertDictEqual(self.converter._projected_atoms_cache, {})
        self.assertDictEqual(self.converter._actual_destruction_percent_cache, {})

    def test_get_projected_atoms(self):
        """
        Test the get_projected_atoms method.
        """
        model = mock.Mock(spec=Model)
        op_specs = {
            "_project": {
                Function(
                    "_project", [String("plays_3"), Function("plays", [Number(1), Number(2), Number(3)], True)], True
                ),
                Function(
                    "_project", [String("plays_3"), Function("plays", [Number(4), Number(5), Number(6)], True)], True
                ),
                Function("_project", [String("day_1"), Function("day", [Number(1)], True)], True),
                Function(
                    "_project", [String("other"), Function("plays", [Number(7), Number(8), Number(9)], True)], True
                ),
            }
        }
        project_operators = [
            {"name": "plays_3", "signatures": {("plays", 3)}},
            {"name": "day_1", "signatures": {("day", 1)}},
        ]
        projected_atoms = [
            {
                Function("plays", [Number(1), Number(2), Number(3)], True),
                Function("plays", [Number(4), Number(5), Number(6)], True),
            },
            {
                Function("day", [Number(1)], True),
            },
        ]

        with mock.patch(
            "mod_lns.lib.auto_destruction_converters.last_improv.ConfigParser.get_projected_atoms",
            side_effect=projected_atoms,
        ) as mock_get_projected_atoms:
            self.assertSetEqual(
                self.converter._get_projected_atoms(model, op_specs, project_operators),
                {
                    Function("plays", [Number(1), Number(2), Number(3)], True),
                    Function("plays", [Number(4), Number(5), Number(6)], True),
                    Function("day", [Number(1)], True),
                },
            )
            mock_get_projected_atoms.assert_any_call(model, op_specs, "plays_3")
            mock_get_projected_atoms.assert_any_call(model, op_specs, "day_1")

    def test_update_last_improvement_stats(self):
        """
        Test _update_last_improvement_stats method.
        """
        new_model = mock.Mock(spec=Model)
        current_model = mock.Mock(spec=Model)
        with (
            mock.patch(
                "mod_lns.lib.auto_destruction_converters.last_improv.ConfigParser.get_op_specs",
                return_value={"test": {Function("test", [Number(1)], True)}},
            ) as mock_get_op_specs,
            mock.patch.object(self.converter, "_reset_caches") as mock_reset_caches,
        ):
            with mock.patch(
                "mod_lns.lib.auto_destruction_converters.last_improv.is_new_model_better", return_value=False
            ):
                self.converter._update_last_improvement_stats(new_model, current_model)
                mock_get_op_specs.assert_not_called()
                mock_reset_caches.assert_not_called()
            with mock.patch(
                "mod_lns.lib.auto_destruction_converters.last_improv.is_new_model_better", return_value=True
            ):
                self.converter._update_last_improvement_stats(new_model, current_model)
                mock_get_op_specs.assert_called_once_with(current_model)
                mock_reset_caches.assert_called_once()
                self.assertEqual(self.converter._last_improvement_models, (current_model, new_model))
                self.assertEqual(
                    self.converter._last_improvement_specs, {"test": {Function("test", [Number(1)], True)}}
                )

    def test_convert_auto_in_config(self):
        """
        Test convert_auto_in_config method.
        Includes test of interface method.
        """
        config = {
            "name": "test",
            "project_operators": [
                {"name": "proj", "signatures": {("t", 1)}},
            ],
            "destroy_operators": [{"name": "dest_op", "percents_or_numbers": [{"type": "auto", "value": 0}]}],
        }
        lns_object = mock.Mock()
        lns_object.new_model = mock.Mock(spec=Model)
        lns_object.current_model = mock.Mock(spec=Model)

        with (
            mock.patch.object(self.converter, "_update_last_improvement_stats") as mock_update_last_improvement_stats,
            mock.patch.object(
                LastImprovementDestructionConverter, "compute_auto_destruction_percent", return_value=20
            ) as mock_compute_auto_destruction_percent,
        ):
            new_config = self.converter.convert_auto_in_config(config, lns_object)
            mock_update_last_improvement_stats.assert_called_once_with(lns_object.new_model, lns_object.current_model)
            mock_compute_auto_destruction_percent.assert_called_once_with(
                "test", [{"name": "proj", "signatures": {("t", 1)}}], "dest_op"
            )
            self.assertEqual(new_config["destroy_operators"][0]["percents_or_numbers"], [{"type": "p", "value": 20}])

        with (
            mock.patch.object(self.converter, "_update_last_improvement_stats") as mock_update_last_improvement_stats,
            mock.patch(
                "mod_lns.lib.auto_destruction_converters.last_improv.AutoDestructionConverter.convert_auto_in_config"
            ) as mock_super_convert,
        ):
            lns_object.new_model = None
            self.converter.convert_auto_in_config(config, None)
            mock_update_last_improvement_stats.assert_not_called()

            self.converter.convert_auto_in_config(config, lns_object)
            mock_update_last_improvement_stats.assert_not_called()

            self.assertEqual(mock_super_convert.call_count, 2)

    def test_compute_auto_destruction_percent(self):
        """
        Test compute_auto_destruction_percent method.
        """
        config_name = "test"
        project_operators = [
            {"name": "proj", "signatures": {("t", 1)}},
        ]
        destroy_operator_name = "dest_op"

        # key in cache
        self.converter._actual_destruction_percent_cache[(config_name, destroy_operator_name)] = 30.0
        self.assertEqual(
            self.converter.compute_auto_destruction_percent(config_name, project_operators, destroy_operator_name), 30.0
        )

        # last improvement models are None
        self.converter._reset_caches()
        self.converter._last_improvement_models = None
        self.converter._last_improvement_specs = None
        self.assertEqual(
            self.converter.compute_auto_destruction_percent(config_name, project_operators, destroy_operator_name),
            float(self.converter._auto_init_percent),
        )

        # default case
        current_model = mock.Mock(spec=Model)
        new_model = mock.Mock(spec=Model)
        project_operators = [
            {"name": "plays_3", "signatures": {("plays", 3)}},
        ]
        projected_atoms = [
            {
                Function("plays", [Number(1), Number(2), Number(3)], True),
            }
        ]
        destruction_candidate_atoms = {
            Function("plays", [Number(2), Number(3), Number(4)], True),
        }
        self.converter._last_improvement_models = (current_model, new_model)
        self.converter._last_improvement_specs = mock.Mock()

        with (
            mock.patch.object(
                self.converter, "_get_projected_atoms", return_value=projected_atoms
            ) as mock_get_projected_atoms,
            mock.patch(
                "mod_lns.lib.auto_destruction_converters.last_improv.ConfigParser.get_destruction_candidate_atoms",
                return_value=destruction_candidate_atoms,
            ) as mock_get_destructuon_candidate_atoms,
            mock.patch(
                "mod_lns.lib.auto_destruction_converters.last_improv.calculate_actual_destruction_percent",
                return_value=40.0,
            ) as mock_calculate_actual_destruction_percent,
        ):
            self.assertEqual(
                self.converter.compute_auto_destruction_percent(config_name, project_operators, destroy_operator_name),
                40.0,
            )

            mock_get_projected_atoms.assert_called_once_with(
                current_model, self.converter._last_improvement_specs, project_operators
            )
            mock_get_destructuon_candidate_atoms.assert_called_once_with(
                self.converter._last_improvement_specs, projected_atoms, destroy_operator_name
            )
            mock_calculate_actual_destruction_percent.assert_called_once_with(destruction_candidate_atoms, new_model)
            self.assertEqual(
                self.converter._actual_destruction_percent_cache[(config_name, destroy_operator_name)], 40.0
            )

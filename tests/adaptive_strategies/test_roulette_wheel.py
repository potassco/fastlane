"""
Test cases for the roulette wheel adaptive strategy.
"""

from unittest import TestCase, mock

from mod_lns import Model
from mod_lns.lib.adaptive_strategies.roulette_wheel import RouletteWheelStrategy
from mod_lns.lib.auto_destruction_converters.last_improv import LastImprovementDestructionConverter
from mod_lns.utils.types import ConfigCatalog, DestroyOperator, ProjectOperator

# pylint: disable=protected-access


class TestRouletteWheelStrategy(TestCase):
    """
    Test cases for the RouletteWheelStrategy class.
    """

    def setUp(self) -> None:
        """
        Set up the test case.
        """
        self.strategy = RouletteWheelStrategy(mock.Mock())
        self.config_catalog: ConfigCatalog = {
            "project_operators": {
                "default": ProjectOperator.from_signatures(name="default", signatures={("plays", 3)})
            },
            "destroy_operators": {"default": DestroyOperator.from_specs("default", [{"type": "p", "value": 20}])},
            "prioritize_operators": {"default": {"value": 1, "modifier": "true"}},
            "configs": {
                "default": {
                    "project_operators": ["default"],
                    "destroy_operators": ["default"],
                    "prioritize_operators": ["default"],
                }
            },
            "strategy": "static",
        }

    def test_init(self):
        """
        Test initialization of RouletteWheelStrategy.
        """
        self.assertEqual(self.strategy._learning_rate, 0.5)
        self.assertEqual(self.strategy._lex_weight, 1000)
        self.assertIsInstance(self.strategy._converter, LastImprovementDestructionConverter)
        self.assertEqual(self.strategy._min_weight, 0.001)
        self.assertDictEqual(self.strategy._weights, {})

    def test_compute_lex_weighted_sum(self):
        """
        Test the _compute_lex_weighted_sum method.
        """
        lex_costs = [1, 2, 3]
        expected_sum = 1 * (1000**2) + 2 * (1000**1) + 3 * (1000**0)
        self.assertEqual(self.strategy._compute_lex_weighted_sum(lex_costs), expected_sum)

    def test_initialize_weights(self):
        """
        Test the _initialize_weights method.
        """
        model = Model()
        model.cost = [1, 2, 3]

        with self.assertRaises(RuntimeError):
            self.strategy._initialize_weights({"configs": {}}, model)

        with mock.patch.object(self.strategy, "_compute_lex_weighted_sum", return_value=6) as mock_compute:
            self.strategy._initialize_weights(self.config_catalog, model)
            mock_compute.assert_called_once_with(model.cost)
            self.assertDictEqual(self.strategy._weights, {"default": 6})

        model.cost = [10]
        self.strategy._initialize_weights(self.config_catalog, model)
        self.assertDictEqual(self.strategy._weights, {"default": 10})

    def test_select_config(self):
        """
        Test the _select_config method.
        """
        self.strategy._weights = {"default": 1.0}
        with mock.patch.object(
            self.strategy, "_get_config", return_value={"test": "config", "config_repr": "default"}
        ) as mock_get_config:
            self.assertDictEqual(
                self.strategy._select_config(self.config_catalog), {"test": "config", "config_repr": "default"}
            )
            mock_get_config.assert_called_once_with("default", self.config_catalog)

    def test_get_initial_config(self):
        """
        Test the get_initial_config method.
        """
        model = Model()
        model.cost = [1, 2, 3]
        with (
            mock.patch.object(self.strategy, "_initialize_weights") as mock_initialize,
            mock.patch.object(self.strategy, "_select_config", return_value={"test": "config"}) as mock_select,
            mock.patch.object(
                self.strategy._converter, "convert_auto_in_config", return_value={"test": "config_converted"}
            ) as mock_convert,
        ):
            self.assertDictEqual(
                self.strategy.get_initial_config(self.config_catalog, model), {"test": "config_converted"}
            )
            mock_initialize.assert_called_once_with(self.config_catalog, model)
            mock_select.assert_called_once_with(self.config_catalog)
            mock_convert.assert_called_once_with({"test": "config"})

    def test_compute_effectiveness_score(self):
        """
        Test the _compute_effectiveness_score method.
        """
        current_model = Model()
        current_model.cost = [1, 2, 3]
        new_model = Model()
        new_model.cost = [1, 2, 2]

        self.assertEqual(self.strategy._compute_effectiveness_score(current_model, None, 5), 0)

        with mock.patch.object(self.strategy, "_compute_lex_weighted_sum", side_effect=[6, 5]) as mock_compute:
            score = self.strategy._compute_effectiveness_score(current_model, new_model, 2)
            mock_compute.assert_any_call(current_model.cost)
            mock_compute.assert_any_call(new_model.cost)
            self.assertEqual(mock_compute.call_count, 2)
            self.assertEqual(score, 0.5)  # (6 - 5) / 2 = 0.5

            current_model.cost = [10]
            score = self.strategy._compute_effectiveness_score(current_model, new_model, 0)
            self.assertEqual(mock_compute.call_count, 2)
            self.assertEqual(score, (10 - 1) / 0.001)

    def test_update_weights(self):
        """
        Test the _update_weights method.
        """
        self.strategy._weights = {"default": 5.0}
        self.strategy._update_weights("default", 3.0)
        expected_weight = (1 - 0.5) * 5.0 + 0.5 * 3.0
        self.assertAlmostEqual(self.strategy._weights["default"], expected_weight)

        self.strategy._update_weights("default", -100.0)
        expected_weight = (1 - 0.5) * expected_weight + 0.5 * (-100.0)
        self.assertAlmostEqual(self.strategy._weights["default"], self.strategy._min_weight)

    def test_update_config(self):
        """
        Test the update_config method.
        """
        current_model = Model()
        current_model.cost = [1, 2, 3]
        new_model = Model()
        new_model.cost = [1, 2, 2]

        self.strategy._weights = {"config": 1.0}
        active_config = {"name": "config", "config_repr": "default"}
        stats = [{"time_to_last_model": 4}, {"time_to_last_model": 2}]
        lns_object = mock.Mock()
        lns_object.current_model = current_model
        lns_object.new_model = new_model

        with (
            mock.patch.object(self.strategy, "_compute_effectiveness_score", return_value=0.5) as mock_compute,
            mock.patch.object(self.strategy, "_update_weights") as mock_update,
            mock.patch.object(
                self.strategy, "_select_config", return_value={"name": "new_config", "config_repr": "default"}
            ) as mock_select,
            mock.patch.object(
                self.strategy._converter,
                "convert_auto_in_config",
                return_value={"name": "new_config_converted", "config_repr": "default"},
            ) as mock_convert,
        ):
            self.assertDictEqual(
                self.strategy.update_config(active_config, self.config_catalog, stats, lns_object),
                {"name": "new_config_converted", "config_repr": "default"},
            )
            mock_compute.assert_called_once_with(current_model, new_model, 2)
            mock_update.assert_called_once_with("config", 0.5)
            mock_select.assert_called_once_with(self.config_catalog)
            mock_convert.assert_called_once_with({"name": "new_config", "config_repr": "default"}, lns_object)

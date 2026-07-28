"""
Test cases for adaptive strategy interface and static adaptive strategy.
"""

from unittest import TestCase, mock

from mod_lns.lib.adaptive_strategies.static import StaticStrategy
from mod_lns.utils.types import ActiveConfig, ConfigCatalog, ProjectOperator

# pylint: disable=protected-access


class TestStaticStrategy(TestCase):
    """
    Test cases for the StaticStrategy class.
    """

    def setUp(self) -> None:
        """
        Set up the test case.
        """
        self.strategy = StaticStrategy()
        self.config_catalog: ConfigCatalog = {
            "project_operators": {
                "default": ProjectOperator.from_signatures(name="default", signatures={("plays", 3)})
            },
            "destroy_operators": {"default": [{"type": "p", "value": 20}]},
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

    # test interface methods
    def test_get_config(self):
        """
        Test _get_config and _format_config methods of AdaptiveStrategy interface.
        """
        ref_config: ActiveConfig = {
            "name": "default",
            "project_operators": [ProjectOperator.from_signatures(name="default", signatures={("plays", 3)})],
            "destroy_operators": [{"name": "default", "percents_or_numbers": [{"type": "p", "value": 20}]}],
            "prioritize_operators": [{"name": "default", "value": 1, "modifier": "true"}],
            "config_repr": (
                "default[project_operators={default[(plays,3)]},"
                "destroy_operators={default[p(20)]},"
                "prioritize_operators={default[1,true]}]"
            ),
        }
        self.assertDictEqual(self.strategy._get_config("default", self.config_catalog), ref_config)

    def test_select_config(self):
        """
        Test _select_config method.
        """
        self.config_catalog["configs"]["2nd"] = {}
        with mock.patch.object(self.strategy, "_get_config", return_value={"test": "config"}) as mock_get_config:
            self.assertDictEqual(self.strategy._select_config(self.config_catalog), {"test": "config"})
            mock_get_config.assert_called_once_with("default", self.config_catalog)

    def test_get_initial_config(self):
        """
        Test get_initial_config method.
        """
        with (
            mock.patch.object(self.strategy, "_select_config", return_value={"test": "config"}) as mock_select_config,
            mock.patch.object(
                self.strategy._converter, "convert_auto_in_config", return_value={"test": "config_converted"}
            ) as mock_convert,
        ):
            self.assertDictEqual(
                self.strategy.get_initial_config(self.config_catalog, mock.Mock()), {"test": "config_converted"}
            )
            mock_select_config.assert_called_once_with(self.config_catalog)
            mock_convert.assert_called_once_with({"test": "config"})

    def test_update_config(self):
        """
        Test update_config method.
        """
        lns_object = mock.Mock()
        with (
            mock.patch.object(self.strategy, "_select_config", return_value={"test": "config"}) as mock_select_config,
            mock.patch.object(
                self.strategy._converter, "convert_auto_in_config", return_value={"test": "config_converted"}
            ) as mock_convert,
        ):
            self.assertDictEqual(
                self.strategy.update_config({"test": "config"}, self.config_catalog, [], lns_object),
                {"test": "config_converted"},
            )
            mock_select_config.assert_called_once_with(self.config_catalog)
            mock_convert.assert_called_once_with({"test": "config"}, lns_object)

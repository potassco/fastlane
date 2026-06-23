"""
Static strategy for adaptive LNS configuration selection.
"""

from typing import TYPE_CHECKING, Any

from mod_lns import Model
from mod_lns.interfaces.adaptive_strategy import AdaptiveStrategy
from mod_lns.interfaces.auto_destruction_converter import AutoDestructionConverter
from mod_lns.lib.auto_destruction_converters.last_improv import LastImprovementDestructionConverter

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class StaticStrategy(AdaptiveStrategy):
    """
    Static strategy that always selects the same LNPS configuration.

    :param converter: Converter for computing destruction percentages of auto-mode destroy operators.
    :type converter: AutoDestructionConverter
    """

    def __init__(self, converter: AutoDestructionConverter = LastImprovementDestructionConverter()):
        self._converter = converter

    def _select_config(self, config_catalog: dict[str, Any]) -> dict[str, Any]:
        """
        Select first LNS configuration.

        :param config_catalog: Configuration catalog.
        :type config_catalog: dict[str, Any]
        :return: Selected LNS configuration.
        :rtype: dict[str, Any]
        """
        selected_config = list(config_catalog["configs"].keys())[0]
        active_config = self._get_config(selected_config, config_catalog)
        return active_config

    def get_initial_config(self, config_catalog: dict[str, Any], initial_model: Model) -> dict[str, Any]:
        """
        Get initial LNS configuration.

        :param config_catalog: Config catalog.
        :type config_catalog: dict[str, Any]
        :param initial_model: Initial model.
        :type initial_model: Model
        :return: LNS configuration dictionary.

            The returned dictionary contains these keys:
            - "name" (str): Name of LNS configuration.
            - "project_operators" (list[str]):
                List of project operator names.
            - "destroy_operators" (list[dict[str, Any]]):
                List of names and percentages or numbers of destroy operators.
            - "prioritize_operators" (list[dict[str, Any]]):
                List of names, heuristic modifiers, and their values of prioritize operators.
            - "config_repr" (str):
                String representation of LNS configuration.
        :rtype: dict[str, Any]
        """
        return self._converter.convert_auto_in_config(self._select_config(config_catalog))

    def update_config(
        self,
        active_config: dict[str, Any],
        config_catalog: dict[str, Any],
        stats: list[dict[str, Any]],
        lns_object: "LNS",
    ) -> dict[str, Any]:
        """
        Return the same LNS configuration without updating.

        :param active_config: Current active LNS configuration.
        :type active_config: dict[str, Any]
        :param config_catalog: Full LNS configuration catalog.
        :type config_catalog: dict[str, Any]
        :param stats: Statistics.
        :type stats: list[dict[str, Any]]
        :return: New LNS configuration.
        :rtype: dict[str, Any]
        """
        return self._converter.convert_auto_in_config(self._select_config(config_catalog), lns_object)

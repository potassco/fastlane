"""
Static strategy for adaptive LNS configuration selection.
"""

from typing import TYPE_CHECKING, Any

from mod_lns import Model
from mod_lns.interfaces.adaptive_strategy import AdaptiveStrategy
from mod_lns.interfaces.auto_destruction_converter import AutoDestructionConverter
from mod_lns.lib.auto_destruction_converters.last_improv import LastImprovementDestructionConverter
from mod_lns.utils.types import ActiveConfig, ConfigCatalog

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class StaticStrategy(AdaptiveStrategy):
    """
    Static strategy that always selects the same LNPS configuration.

    :param converter: Converter for computing destruction percentages of auto-mode destroy operators.
    """

    def __init__(self, converter: AutoDestructionConverter = LastImprovementDestructionConverter()):
        self._converter = converter

    def _select_config(self, config_catalog: ConfigCatalog) -> ActiveConfig:
        """
        Select first LNS configuration.

        :param config_catalog: Configuration catalog.
        :return: Selected LNS configuration.
        """
        selected_config = list(config_catalog["configs"].keys())[0]
        active_config = self._get_config(selected_config, config_catalog)
        return active_config

    def get_initial_config(self, config_catalog: ConfigCatalog, initial_model: Model) -> ActiveConfig:
        """
        Get initial LNS configuration.

        :param config_catalog: Config catalog.
        :param initial_model: Initial model.
        :return: Selected active LNS configuration.
        """
        return self._converter.convert_auto_in_config(self._select_config(config_catalog))

    def update_config(
        self,
        active_config: ActiveConfig,
        config_catalog: ConfigCatalog,
        stats: list[dict[str, Any]],
        lns_object: "LNS",
    ) -> ActiveConfig:
        """
        Return the same LNS configuration without updating.

        :param active_config: Current active LNS configuration.
        :param config_catalog: Full LNS configuration catalog.
        :param stats: Statistics.
        :return: New active LNS configuration.
        """
        return self._converter.convert_auto_in_config(self._select_config(config_catalog), lns_object)

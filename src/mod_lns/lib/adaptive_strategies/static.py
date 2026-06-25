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
    :type converter: AutoDestructionConverter
    """

    def __init__(self, converter: AutoDestructionConverter = LastImprovementDestructionConverter()):
        self._converter = converter

    def _select_config(self, config_catalog: ConfigCatalog) -> ActiveConfig:
        """
        Select first LNS configuration.

        :param config_catalog: Configuration catalog.
        :type config_catalog: ConfigCatalog
        :return: Selected LNS configuration.
        :rtype: ActiveConfig
        """
        selected_config = list(config_catalog["configs"].keys())[0]
        active_config = self._get_config(selected_config, config_catalog)
        return active_config

    def get_initial_config(self, config_catalog: ConfigCatalog, initial_model: Model) -> ActiveConfig:
        """
        Get initial LNS configuration.

        :param config_catalog: Config catalog.
        :type config_catalog: ConfigCatalog
        :param initial_model: Initial model.
        :type initial_model: Model
        :return: Selected active LNS configuration.
        :rtype: ActiveConfig
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
        :type active_config: ActiveConfig
        :param config_catalog: Full LNS configuration catalog.
        :type config_catalog: ConfigCatalog
        :param stats: Statistics.
        :type stats: list[dict[str, Any]]
        :return: New active LNS configuration.
        :rtype: ActiveConfig
        """
        return self._converter.convert_auto_in_config(self._select_config(config_catalog), lns_object)

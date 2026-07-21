"""
Roulette-wheel strategy for adaptive LNS configuration selection.
"""

import random
from logging import Logger
from typing import TYPE_CHECKING, Any

from mod_lns import Model
from mod_lns.interfaces.adaptive_strategy import AdaptiveStrategy
from mod_lns.interfaces.auto_destruction_converter import AutoDestructionConverter
from mod_lns.lib.auto_destruction_converters.last_improv import LastImprovementDestructionConverter
from mod_lns.utils.types import ActiveConfig, ConfigCatalog

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class RouletteWheelStrategy(AdaptiveStrategy):
    """
    Roulette-wheel strategy.

    :param logger: Logger for logging messages.
    :param learning_rate: Learning rate used to update weights, 0 < learning_rate < 1.
    :param lex_weight: Weight used to convert lexicographic cost into integer cost.
    :param converter: Converter for computing destruction percentages of auto-mode destroy operators.
    :param min_weight: Minimum value of weight. Defaults to 0.001.
    """

    def __init__(
        self,
        logger: Logger,
        learning_rate: float = 0.5,
        lex_weight: int = 1000,
        converter: AutoDestructionConverter = LastImprovementDestructionConverter(),
        min_weight: float = 0.001,
    ):
        self.logger = logger
        self._learning_rate = learning_rate
        self._lex_weight = lex_weight
        self._converter = converter
        self._min_weight = min_weight
        self._weights: dict[str, float] = {}

    def _compute_lex_weighted_sum(self, lex_costs: list[int]) -> int:
        """
        Convert lexicographic cost into integer cost by computing weighted sum.

        :param lex_costs: Lexicographic cost.
        :return: Integer cost.
        """
        num_lex_costs = len(lex_costs)
        last_lex_cost_idx = num_lex_costs - 1
        cost = 0
        for i in range(num_lex_costs):
            cost += lex_costs[i] * (self._lex_weight ** (last_lex_cost_idx - i))
        return cost

    def _initialize_weights(self, config_catalog: ConfigCatalog, initial_model: Model) -> None:
        """
        Initialize weights for all possible LNS configurations using initial model's cost.

        :param config_catalog: Config catalog.
        :param initial_model: Initial model.
        """
        if len(initial_model.cost) > 1:
            initial_weight = abs(self._compute_lex_weighted_sum(initial_model.cost))
        else:
            initial_weight = abs(initial_model.cost[0])

        configs = config_catalog["configs"]
        if not isinstance(configs, dict) or configs == {}:
            raise RuntimeError("Received invalid config catalog. Expected non-empty dictionary under 'configs' key.")
        config_names = configs.keys()
        for config in config_names:
            self._weights[config] = initial_weight

        self.logger.debug("Initial weight: %s", initial_weight)

    def _select_config(self, config_catalog: ConfigCatalog) -> ActiveConfig:
        """
        Select LNS configuration using roulette wheel selection based on normalized weights.

        :param config_catalog: Config catalog.
        :return: Selected LNS configuration.
        """
        weights = self._weights.values()
        normalized_weights = [w / max(weights) for w in weights]
        selected_config = random.choices(list(self._weights.keys()), weights=normalized_weights, k=1)[0]
        active_config = self._get_config(selected_config, config_catalog)
        self.logger.debug("Selected LNPS configuration: %s", active_config["config_repr"])
        return active_config

    def get_initial_config(self, config_catalog: ConfigCatalog, initial_model: Model) -> ActiveConfig:
        """
        Get initial LNS configuration using roulette wheel selection after initializing weights.

        :param config_catalog: Config catalog.
        :param initial_model: Initial model.
        :return: Active LNS configuration.
        """
        self._initialize_weights(config_catalog, initial_model)
        return self._converter.convert_auto_in_config(self._select_config(config_catalog))

    def _compute_effectiveness_score(
        self, current_model: Model, new_model: Model | None, time_to_last_model: float
    ) -> float:
        """
        Compute effectiveness score of current LNPS configuration.

        :param current_model: Current model.
        :param new_model: New model found by using current LNPS configuration.
        :param time_to_last_model: Elapsed time to new model found.
        :return: Effectiveness score.
        """
        if new_model is None:
            return 0.0

        if len(current_model.cost) > 1:
            current_cost = self._compute_lex_weighted_sum(current_model.cost)
            new_cost = self._compute_lex_weighted_sum(new_model.cost)
        else:
            current_cost = current_model.cost[0]
            new_cost = new_model.cost[0]

        # Guard against zero/negative elapsed time
        if time_to_last_model <= 0:
            self.logger.warning("time_to_last_model <= 0; treated as 0.001")
            time_to_last_model = 0.001

        return (current_cost - new_cost) / time_to_last_model

    def _update_weights(self, spec_name: str, effectiveness_score: float) -> None:
        """
        Update weight of LNS specification based on effectiveness score.

        :param spec_name: Name of LNS specification.
        :param effectiveness_score: Effectiveness score.
        """
        weight = self._weights[spec_name]
        new_weight = (1 - self._learning_rate) * weight + self._learning_rate * effectiveness_score
        self._weights[spec_name] = max(new_weight, self._min_weight)

    def update_config(
        self,
        active_config: ActiveConfig,
        config_catalog: ConfigCatalog,
        stats: list[dict[str, Any]],
        lns_object: "LNS",
    ) -> ActiveConfig:
        """
        Update weight of current LNS configuration and select new LNS configuration using roulette wheel selection.

        :param active_config: Current active LNS configuration.
        :param config_catalog: Full LNS configuration catalog.
        :param stats: Statistics.
        :return: New LNS configuration.
        """
        effectiveness_score = self._compute_effectiveness_score(
            lns_object.current_model, lns_object.new_model, stats[-1]["time_to_last_model"]
        )
        config_name = active_config["name"]
        weight = self._weights[config_name]
        self._update_weights(config_name, effectiveness_score)
        new_weight = self._weights[config_name]
        self.logger.debug("%s weight: %s -> %s", active_config["config_repr"], weight, new_weight)
        return self._converter.convert_auto_in_config(self._select_config(config_catalog), lns_object)

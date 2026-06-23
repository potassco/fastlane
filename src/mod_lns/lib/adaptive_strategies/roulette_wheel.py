"""
Roulette-wheel strategy for adaptive LNS configuration selection.
"""

import random
from logging import Logger
from typing import TYPE_CHECKING, Any

from mod_lns import Model
from mod_lns.interfaces.adaptive_strategy import AdaptiveStrategy
from mod_lns.interfaces.auto_destruction_converter import AutoDestructionConverter

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class RouletteWheelStrategy(AdaptiveStrategy):
    """
    Roulette-wheel strategy.

    :param logger: Logger for logging messages.
    :type logger: Logger
    :param learning_rate: Learning rate used to update weights.
    :type learning_rate: float
    :param lex_weight: Weight used to convert lexicographic cost into integer cost.
    :type lex_weight: int
    :param converter: Converter for computing destruction percentages of auto-mode destroy operators.
    :type converter: AutoDestructionConverter
    :param min_weight: Minimum value of weight. Defaults to 0.001.
    :type min_weight: float, optional
    :default min_weight: 0.001
    """

    def __init__(
        self,
        logger: Logger,
        learning_rate: float,
        lex_weight: int,
        converter: AutoDestructionConverter,
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
        :type lex_costs: list[int]
        :return: Integer cost.
        :rtype: int
        """
        num_lex_costs = len(lex_costs)
        last_lex_cost_idx = num_lex_costs - 1
        cost = 0
        for i in range(num_lex_costs):
            cost += lex_costs[i] * (self._lex_weight ** (last_lex_cost_idx - i))
        return cost

    def _initialize_weights(self, config_catalog: dict[str, Any], initial_model: Model) -> None:
        """
        Initialize weights for all possible LNS configurations using initial model's cost.

        :param config_catalog: Config catalog.
        :type config_catalog: dict[str, Any]
        :param initial_model: Initial model.
        :type initial_model: Model
        """
        if len(initial_model.cost) > 1:
            initial_weight = abs(self._compute_lex_weighted_sum(initial_model.cost))
        else:
            initial_weight = abs(initial_model.cost[0])

        catalog: dict[str, Any] = config_catalog["configs"]
        if not isinstance(catalog, dict) or catalog == {}:
            raise RuntimeError("Received invalid config catalog. Expected non-empty dictionary under 'configs' key.")
        configs = catalog.keys()
        for config in configs:
            self._weights[config] = initial_weight

        self.logger.debug("Initial weight: %s", initial_weight)

    def _select_config(self, config_catalog: dict[str, Any]) -> dict[str, Any]:
        """
        Select LNS configuration using roulette wheel selection based on normalized weights.

        :param config_catalog: Config catalog.
        :type config_catalog: dict[str, Any]
        :return: Selected LNS configuration.
        :rtype: dict[str, Any]
        """
        weights = self._weights.values()
        normalized_weights = [w / max(weights) for w in weights]
        selected_config = random.choices(list(self._weights.keys()), weights=normalized_weights, k=1)[0]
        active_config = self._get_config(selected_config, config_catalog)
        self.logger.debug("Selected LNPS configuration: %s", active_config["config_repr"])
        return active_config

    def get_initial_config(self, config_catalog: dict[str, Any], initial_model: Model) -> dict[str, Any]:
        """
        Get initial LNS configuration using roulette wheel selection after initializing weights.

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
        self._initialize_weights(config_catalog, initial_model)
        return self._converter.convert_auto_in_config(self._select_config(config_catalog))

    def _compute_effectiveness_score(
        self, current_soluion: Model, new_model: Model | None, time_to_last_model: float
    ) -> float:
        """
        Compute effectiveness score of current LNPS configuration.

        :param current_soluion: Current model.
        :type current_soluion: Model
        :param new_model: New model found by using current LNPS configuration.
        :type new_model: Model | None
        :param time_to_last_model: Elapsed time to new model found.
        :type time_to_last_model: float
        :return: Effectiveness score.
        :rtype: float
        """
        if new_model is None:
            return 0.0

        if len(current_soluion.cost) > 1:
            current_cost = self._compute_lex_weighted_sum(current_soluion.cost)
            new_cost = self._compute_lex_weighted_sum(new_model.cost)
        else:
            current_cost = current_soluion.cost[0]
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
        :type spec_name: str
        :param effectiveness_score: Effectiveness score.
        :type effectiveness_score: float
        """
        weight = self._weights[spec_name]
        new_weight = (1 - self._learning_rate) * weight + self._learning_rate * effectiveness_score
        self._weights[spec_name] = max(new_weight, self._min_weight)

    def update_config(
        self,
        active_config: dict[str, Any],
        config_catalog: dict[str, Any],
        stats: list[dict[str, Any]],
        lns_object: "LNS",
    ) -> dict[str, Any]:
        """
        Update weight of current LNS configuration and select new LNS configuration using roulette wheel selection.

        :param active_config: Current active LNS configuration.
        :type active_config: dict[str, Any]
        :param config_catalog: Full LNS configuration catalog.
        :type config_catalog: dict[str, Any]
        :param stats: Statistics.
        :type stats: list[dict[str, Any]]
        :return: New LNS configuration.
        :rtype: dict[str, Any]
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

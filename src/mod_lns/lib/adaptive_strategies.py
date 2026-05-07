import itertools

# from .logger import logger
import logging
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from mod_lns import Model

from .converter import AutoDestructionConverter

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class AdaptiveStrategy(ABC):
    """
    Strategy to select LNPS configuration from ALNPS configuration.
    """

    @abstractmethod
    def get_initial_config(self, alnps_config: dict[str, Any], initial_model: Model) -> dict[str, Any]:
        """
        Abstract method to get initial LNPS configuration.

        :param alnps_config: ALNPS configuration.
        :type alnps_config: dict[str, Any]
        :param initial_model: Initial model.
        :type initial_model: Model
        :return: LNPS configuration dictionary with the following keys:
            - "name" (str): Name of LNPS configuration.
            - "project_operators" (list[str]): List of project operator names.
            - "destroy_operators" (list[dict[str, Any]]): List of dictionaries with the following keys:
                - "name" (str): Name of destroy operator.
                - "percents_or_numbers" (list[dict[str, Any]]): List of dictionaries with the following keys:
                    - "type" (str): Type of percentage or number ("p" or "n").
                    - "value" (int | float): Value of percentage or number.
            - "prioritize_operators" (list[dict[str, Any]]): List of dictionaries with the following keys:
                - "name" (str): Name of prioritize operator.
                - "value" (int | str): Value of heuristic modifier (integer or "inf").
                - "modifier" (str): Heuristic modifier ("sign", "level", "true", "false", "init", or "factor").
            - "key" (tuple[Any, ...]): Key of LNPS configuration.
        :rtype: dict[str, Any]
        """

    @abstractmethod
    def update_config(
        self, lnps_config: dict[str, Any], alnps_config: dict[str, Any], stats: list[dict[str, Any]], lns_object: "LNS"
    ) -> dict[str, Any]:
        """
        Abstract method to update LNPS configuration.

        :param lnps_config: Current LNPS configuration.
        :type lnps_config: dict[str, Any]
        :param alnps_config: ALNPS configuration.
        :type alnps_config: dict[str, Any]
        :param stats: Statistics.
        :type stats: list[dict[str, Any]]
        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: New LNPS configuration.
        :rtype: dict[str, Any]
        """


class RouletteWheelStrategy(AdaptiveStrategy):
    """
    Roulette-wheel strategy.

    :param learning_rate: Learning rate used to update weights.
    :type learning_rate: float
    :param lex_weight: Weight used to convert lexicographic cost into integer cost.
    :type lex_weight: int
    :param converter: Converter for computing destruction percentages of auto-mode destroy operators.
    :type converter: AutoDestructionConverter
    :param min_weight: Minimum value of weight. Defaults to 0.001.
    :type min_weight: float, optional
    """

    def __init__(
        self,
        learning_rate: float,
        lex_weight: int,
        converter: AutoDestructionConverter,
        min_weight: float = 0.001,
    ):
        self._learning_rate = learning_rate
        self._lex_weight = lex_weight
        self._converter = converter
        self._min_weight = min_weight
        self._weights = {}

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

    def _initialize_weights(self, alnps_config: dict[str, Any], initial_model: Model) -> None:
        """
        Initialize weights for all possible LNPS configurations using initial model's cost.

        :param alnps_config: ALNPS configuration.
        :type alnps_config: dict[str, Any]
        :param initial_model: Initial model.
        :type initial_model: Model
        """
        if len(initial_model.cost) > 1:
            initial_weight = abs(self._compute_lex_weighted_sum(initial_model.cost))
        else:
            initial_weight = abs(initial_model.cost[0])

        configs = alnps_config["configs"].keys()  # self._generate_keys(alnps_config)
        for config in configs:
            # TODO check typing
            self._weights[config] = initial_weight

        # if logger.isEnabledFor(logging.DEBUG):
        #     logger.debug("Initial weight:", initial_weight)

    def _get_operator_values(self, config_name: str, alnps_config: dict[str, Any]) -> dict[str, Any]:
        """
        Convert key into corresponding LNPS configuration.

        :param config_name: Name of LNPS configuration.
        :type config_name: str
        :param alnps_config: ALNPS configuration.
        :type alnps_config: dict[str, Any]
        :return: LNPS configuration corresponding to key.
        :rtype: dict[str, Any]
        """
        config = {
            "name": config_name,
            "project_operators": [],
            "destroy_operators": [],
            "prioritize_operators": [],
        }

        # project
        for operator_name in alnps_config["configs"][config_name]["project_operators"]:
            config["project_operators"].append(
                {"name": operator_name, "signatures": alnps_config["project_operators"][operator_name]}
            )
        # destroy
        for operator_name in alnps_config["configs"][config_name]["destroy_operators"]:
            config["destroy_operators"].append(
                {"name": operator_name, "percents_or_numbers": alnps_config["destroy_operators"][operator_name]}
            )

        # prioritize
        for operator_name in alnps_config["configs"][config_name]["prioritize_operators"]:
            heuristic_modifier = alnps_config["prioritize_operators"][operator_name]
            config["prioritize_operators"].append(
                {
                    "name": operator_name,
                    "value": heuristic_modifier["value"],
                    "modifier": heuristic_modifier["modifier"],
                }
            )

        config["config_repr"] = self._format_lnps_config(config)

        return config

    def _select_config(self, alnps_config: dict[str, Any]) -> dict[str, Any]:
        """
        Select LNPS configuration using roulette wheel selection based on normalized weights.

        :param alnps_config: ALNPS configuration.
        :type alnps_config: dict[str, Any]
        :return: Selected LNPS configuration.
        :rtype: dict[str, Any]
        """
        weights = self._weights.values()
        normalized_weights = [w / max(weights) for w in weights]
        selected_config = random.choices(list(self._weights.keys()), weights=normalized_weights, k=1)[0]
        # print("weights:", self._weights)
        # logger.info("Selected LNPS configuration:", lnps_config["config_repr"])
        lnps_config = self._get_operator_values(selected_config, alnps_config)
        return lnps_config

    def get_initial_config(self, alnps_config: dict[str, Any], initial_model: Model) -> dict[str, Any]:
        """
        Get initial LNPS configuration using roulette wheel selection after initializing weights.

        :param alnps_config: ALNPS configuration.
        :type alnps_config: dict[str, Any]
        :param initial_model: Initial model.
        :type initial_model: Model
        :return: LNPS configuration dictionary with the following keys:
            - "name" (str): Name of LNPS configuration.
            - "project_operators" (list[str]): List of project operator names.
            - "destroy_operators" (list[dict[str, Any]]): List of names and percentages or numbers of destroy operators.
            - "prioritize_operators" (list[dict[str, Any]]): List of names, heuristic modifiers, and their values of prioritize operators.
            - "key" (tuple[Any, ...]): Key of LNPS configuration.
            - "config_repr" (str): String representation of LNPS configuration.
        :rtype: dict[str, Any]
        """
        self._initialize_weights(alnps_config, initial_model)
        return self._converter.convert_config(self._select_config(alnps_config))

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
            logging.warning("time_to_last_model <= 0; treated as 0.001")
            time_to_last_model = 0.001

        return (current_cost - new_cost) / time_to_last_model

    def _update_weights(self, config_name: str, effectiveness_score: float) -> None:
        """
        Update weight of LNPS configuration based on effectiveness score.

        :param config_name: Name of LNPS configuration.
        :type config_name: str
        :param effectiveness_score: Effectiveness score.
        :type effectiveness_score: float
        """
        weight = self._weights[config_name]
        new_weight = (1 - self._learning_rate) * weight + self._learning_rate * effectiveness_score
        if new_weight < self._min_weight:
            new_weight = self._min_weight
        self._weights[config_name] = new_weight

    def update_config(
        self, lnps_config: dict[str, Any], alnps_config: dict[str, Any], stats: list[dict[str, Any]], lns_object: "LNS"
    ) -> dict[str, Any]:
        """
        Update weight of current LNPS configuration and select new LNPS configuration using roulette wheel selection.

        :param lnps_config: Current LNPS configuration.
        :type lnps_config: dict[str, Any]
        :param alnps_config: ALNPS configuration.
        :type alnps_config: dict[str, Any]
        :param stats: Statistics.
        :type stats: list[dict[str, Any]]
        :return: New LNPS configuration.
        :rtype: dict[str, Any]
        """
        effectiveness_score = self._compute_effectiveness_score(
            lns_object.current_model, lns_object.new_model, stats[-1]["time_to_last_model"]
        )
        config_name = lnps_config["name"]
        self._weights[config_name]
        self._update_weights(config_name, effectiveness_score)
        self._weights[config_name]
        # if logger.isEnabledFor(logging.DEBUG):
        #     logger.debug(lnps_config["config_repr"], "weight:", weight, "->", new_weight)
        return self._converter.convert_config(self._select_config(alnps_config), lns_object)

    def _format_lnps_config(self, lnps_config: dict[str, Any]) -> str:
        """
        Convert LNPS configuration into string.

        :param lnps_config: LNPS configuration.
        :type lnps_config: dict[str, Any]
        :return: String representing LNPS configuration.
        :rtype: str
        """
        project_operators = ",".join(
            project_operator["name"]
            + "["
            + ",".join(f"({signature[0]},{signature[1]})" for signature in project_operator["signatures"])
            + "]"
            for project_operator in lnps_config["project_operators"]
        )

        destroy_operators = ",".join(
            destroy_operator["name"]
            + "["
            + ",".join(
                (
                    f"{percent_or_number['type']}({percent_or_number['value']})"
                    if percent_or_number["value"] is not None
                    else percent_or_number["type"]
                )
                for percent_or_number in destroy_operator["percents_or_numbers"]
            )
            + "]"
            for destroy_operator in lnps_config["destroy_operators"]
        )

        prioritize_operators = ",".join(
            f"{prioritize_operator['name']}[{prioritize_operator['value']},{prioritize_operator['modifier']}]"
            for prioritize_operator in lnps_config["prioritize_operators"]
        )

        return f"{lnps_config['name']}[project_operators={{{project_operators}}},destroy_operators={{{destroy_operators}}},prioritize_operators={{{prioritize_operators}}}]"

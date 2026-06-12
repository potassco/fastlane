"""
Interface for adaptive strategies to select declarative LNS configuration.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from mod_lns import Model

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class AdaptiveStrategy(ABC):
    """
    Adaptive strategy interface to select declarative LNS configuration.
    """

    @classmethod
    def __subclasshook__(cls, subclass: type) -> bool:  # nocoverage
        return (
            hasattr(subclass, "get_initial_config")
            and callable(subclass.get_initial_config)
            and hasattr(subclass, "update_config")
            and callable(subclass.update_config)
            or NotImplemented
        )

    @abstractmethod
    def get_initial_config(self, config_catalog: dict[str, Any], initial_model: Model) -> dict[str, Any]:
        """
        Abstract method to get initial LNS configuration.

        :param config_catalog: Full declarative LNS catalog.
        :type config_catalog: dict[str, Any]
        :param initial_model: Initial model.
        :type initial_model: Model
        :return: LNS configuration dictionary with the following keys:
            - "name" (str): Name of LNS configuration.
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
            - "key" (tuple[Any, ...]): Key of LNS configuration.
        :rtype: dict[str, Any]
        """
        raise NotImplementedError

    @abstractmethod
    def update_config(
        self,
        active_config: dict[str, Any],
        config_catalog: dict[str, Any],
        stats: list[dict[str, Any]],
        lns_object: "LNS",
    ) -> dict[str, Any]:
        """
        Abstract method to update LNS configuration.

        :param active_config: Active LNS configuration.
        :type active_config: dict[str, Any]
        :param config_catalog: Full LNS configuration catalog.
        :type config_catalog: dict[str, Any]
        :param stats: Statistics.
        :type stats: list[dict[str, Any]]
        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: New LNS configuration.
        :rtype: dict[str, Any]
        """
        raise NotImplementedError

    def _get_config(self, config_name: str, config_catalog: dict[str, Any]) -> dict[str, Any]:
        """
        Convert key into corresponding configuration.

        :param config_name: Name of LNS configuration.
        :type config_name: str
        :param config_catalog: Full LNS configuration catalog.
        :type config_catalog: dict[str, Any]
        :return: LNS configuration corresponding to key.
        :rtype: dict[str, Any]
        """
        config = {
            "name": config_name,
            "project_operators": [],
            "destroy_operators": [],
            "prioritize_operators": [],
        }

        # project
        for operator_name in config_catalog["configs"][config_name]["project_operators"]:
            config["project_operators"].append(
                {"name": operator_name, "signatures": config_catalog["project_operators"][operator_name]}
            )
        # destroy
        for operator_name in config_catalog["configs"][config_name]["destroy_operators"]:
            config["destroy_operators"].append(
                {"name": operator_name, "percents_or_numbers": config_catalog["destroy_operators"][operator_name]}
            )

        # prioritize
        for operator_name in config_catalog["configs"][config_name]["prioritize_operators"]:
            heuristic_modifier = config_catalog["prioritize_operators"][operator_name]
            config["prioritize_operators"].append(
                {
                    "name": operator_name,
                    "value": heuristic_modifier["value"],
                    "modifier": heuristic_modifier["modifier"],
                }
            )

        config["config_repr"] = self._format_config(config)

        return config

    def _format_config(self, config: dict[str, Any]) -> str:
        """
        Convert LNS configuration into string.

        :param config: LNS configuration.
        :type config: dict[str, Any]
        :return: String representing LNS configuration.
        :rtype: str
        """
        project_operators = ",".join(
            project_operator["name"]
            + "["
            + ",".join(f"({signature[0]},{signature[1]})" for signature in project_operator["signatures"])
            + "]"
            for project_operator in config["project_operators"]
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
            for destroy_operator in config["destroy_operators"]
        )

        prioritize_operators = ",".join(
            f"{prioritize_operator['name']}[{prioritize_operator['value']},{prioritize_operator['modifier']}]"
            for prioritize_operator in config["prioritize_operators"]
        )

        return f"{config['name']}[project_operators={{{project_operators}}},destroy_operators={{{destroy_operators}}},prioritize_operators={{{prioritize_operators}}}]"

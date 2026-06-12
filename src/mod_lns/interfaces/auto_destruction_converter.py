"""
Interface for computing destruction percentages of auto-mode destroy operators.
"""

import copy
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class AutoDestructionConverter(ABC):
    """
    Converter interface for computing destruction percentages of auto-mode destroy operators.
    """

    @classmethod
    def __subclasshook__(cls, subclass: type) -> bool:  # nocoverage
        return (
            hasattr(subclass, "_compute_auto_destruction_percent")
            and callable(subclass._compute_auto_destruction_percent)
            or NotImplemented
        )

    def convert_auto_in_config(self, config: dict[str, Any], lns_object: Optional["LNS"] = None) -> dict[str, Any]:
        """
        Convert automatic values in LNS configuration into concrete percentages.

        :param config: LNS configuration containing automatic values.
        :type config: dict[str, Any]
        :param lns_object: LNS object.
        :type lns_object: Optional["LNS"]
        :return: LNS configuration with all automatic values replaced by concrete percentages.
        :rtype: dict[str, Any]
        """
        resolved_config = copy.deepcopy(config)
        for destroy_operator in resolved_config["destroy_operators"]:
            destroy_operator_name = destroy_operator["name"]
            for percent_or_number in destroy_operator["percents_or_numbers"]:
                if percent_or_number["type"] == "auto":
                    percent_or_number["type"] = "p"
                    destruction_percent = self._compute_auto_destruction_percent(
                        config["name"], config["project_operators"], destroy_operator_name
                    )
                    if lns_object is not None:
                        lns_object.logger.debug(
                            f"Auto destruction percent: {destruction_percent} (destroy operator: {destroy_operator_name})"
                        )
                    percent_or_number["value"] = destruction_percent
        return resolved_config

    @abstractmethod
    def _compute_auto_destruction_percent(
        self, config_name: str, project_operators: list[dict[str, Any]], destroy_operator_name: str
    ) -> float:
        """
        Compute destruction percentage of auto-mode destroy operator.

        :param config_name: Config name.
        :type config_name: str
        :param project_operators: Project operators.
        :type project_operators: list[dict[str, Any]]
        :param destroy_operator_name: Destroy operator name.
        :type destroy_operator_name: str
        :return: Destruction percentage of auto-mode destroy operator.
        :rtype: float
        """
        raise NotImplementedError

"""
Interface for computing destruction percentages of auto-mode destroy operators.
"""

import copy
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from mod_lns.utils.types import ActiveConfig, ProjectOperator

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class AutoDestructionConverter(ABC):
    """
    Converter interface for computing destruction percentages of auto-mode destroy operators.
    """

    @classmethod
    def __subclasshook__(cls, subclass: type) -> bool:  # nocoverage
        return (
            hasattr(subclass, "compute_auto_destruction_percent")
            and callable(subclass.compute_auto_destruction_percent)
            or NotImplemented
        )

    def convert_auto_in_config(self, config: ActiveConfig, lns_object: Optional["LNS"] = None) -> ActiveConfig:
        """
        Convert automatic values in LNS configuration into concrete percentages.

        :param config: Active LNS configuration containing automatic values.
        :param lns_object: LNS object.
        :return: LNS configuration with all automatic values replaced by concrete percentages.
        """
        resolved_config: ActiveConfig = copy.deepcopy(config)
        for destroy_operator in resolved_config["destroy_operators"]:
            destroy_operator_name = destroy_operator.name
            for i, destruction_spec in enumerate(destroy_operator):
                if destruction_spec["type"] == "auto":

                    destruction_percent = self.compute_auto_destruction_percent(
                        config["name"], config["project_operators"], destroy_operator_name
                    )
                    if lns_object is not None:
                        lns_object.logger.debug(
                            f"Auto destruction percent: {destruction_percent} "
                            f"(destroy operator: {destroy_operator_name})"
                        )
                    destroy_operator[i] = {"type": "p", "value": destruction_percent}
        return resolved_config

    @abstractmethod
    def compute_auto_destruction_percent(
        self, config_name: str, project_operators: list[ProjectOperator], destroy_operator_name: str
    ) -> float:  # nocoverage
        """
        Compute destruction percentage of auto-mode destroy operator.

        :param config_name: Config name.
        :param project_operators: Project operators.
        :param destroy_operator_name: Destroy operator name.
        :return: Destruction percentage of auto-mode destroy operator.
        """
        raise NotImplementedError

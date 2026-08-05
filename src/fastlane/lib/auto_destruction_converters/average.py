"""
Average destruction converter for adaptive LNS configuration selection.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from clingo import Symbol

from fastlane import Model
from fastlane.interfaces.auto_destruction_converter import AutoDestructionConverter
from fastlane.lib.auto_destruction_converters.utils import calculate_actual_destruction_percent, is_new_model_better
from fastlane.parsers.config_parser import ConfigParser
from fastlane.utils.types import ActiveConfig, ProjectOperator

if TYPE_CHECKING:
    from fastlane.lns import LNS  # nocoverage


@dataclass
class _RunningAverage:
    """
    State container for incremental average computation.

    :param total: Running total of values.
    :param count: Count of values added.
    """

    total: float = 0.0
    count: int = 0

    def add(self, value: float) -> None:
        """
        Add a value to the running total and increment the count.

        :param value: Value to add.
        """
        self.total += value
        self.count += 1

    def mean(self, default: float) -> float:
        """
        Compute the mean of the values added.

        :param default: Default value to return if no values have been added.
        :return: Mean of the values added or the default value.
        """
        if self.count == 0:
            return default
        return self.total / self.count


class AverageDestructionConverter(AutoDestructionConverter):
    """
    Converter using the average of observed destruction percentages.

    :param auto_init_percent: Initial destruction percentage. Defaults to 0.
    """

    def __init__(self, auto_init_percent: int = 0):
        self._auto_init_percent = auto_init_percent

        # Remove backfill for better memory efficiency
        # Required for lazy key initialization and optional backfill.
        self._improvement_models: list[tuple[Model, Model]] = []

        # Per-key metadata and running aggregates.
        self._project_operator_names: dict[tuple[str, str], list[str]] = {}
        self._running_averages: dict[tuple[str, str], _RunningAverage] = {}

    def _compute_actual_destruction_percent(
        self,
        project_operator_names: list[str],
        destroy_operator_name: str,
        current_model: Model,
        new_model: Model,
    ) -> float:
        """
        Compute actual destruction percentage for one stats entry.

        :param project_operator_names: Project operator names.
        :param destroy_operator_name: Destroy operator name.
        :param current_model: Current model.
        :param new_model: New model.
        :return: Actual destruction percentage.
        """
        projected_atoms: set[Symbol] = set()
        for project_operator_name in project_operator_names:
            projected_atoms.update(ConfigParser.get_projected_atoms(current_model, project_operator_name))

        destruction_candidate_atoms = ConfigParser.get_destruction_candidate_atoms(
            current_model,
            projected_atoms,
            destroy_operator_name,
        )

        return calculate_actual_destruction_percent(destruction_candidate_atoms, new_model)

    def _update_running_averages(self, current_model: Model, new_model: Model) -> None:
        """
        Update running average for all registered keys with one new improvement stat.

        :param current_model: Current model in last improving iteration.
        :param new_model: New model in last improving iteration.
        """
        for key, running in self._running_averages.items():
            project_operator_names = self._project_operator_names[key]
            value = self._compute_actual_destruction_percent(
                project_operator_names,
                key[1],
                current_model,
                new_model,
            )
            running.add(value)

    def _register_key(self, key: tuple[str, str], project_operator_names: list[str]) -> None:
        """
        Register a key and backfill its running average from past improvements.

        :param key: Tuple of config name and destroy operator name.
        :param project_operator_names: Project operator names.
        """
        self._project_operator_names[key] = project_operator_names
        running = _RunningAverage()
        for current_model, new_model in self._improvement_models:
            running.add(
                self._compute_actual_destruction_percent(
                    project_operator_names,
                    key[1],
                    current_model,
                    new_model,
                )
            )
        self._running_averages[key] = running

    def convert_auto_in_config(
        self,
        config: ActiveConfig,
        lns_object: Optional["LNS"] = None,
    ) -> ActiveConfig:
        """
        Convert auto values and update running averages on improving iterations.

        :param config: LNPS configuration containing automatic values.
        :param lns_object: LNS object.
        :return: LNPS configuration with all automatic values replaced.
        """

        if (
            lns_object is not None
            and lns_object.new_model is not None
            and is_new_model_better(lns_object.new_model, lns_object.current_model)
        ):
            self._improvement_models.append((lns_object.current_model, lns_object.new_model))
            self._update_running_averages(lns_object.current_model, lns_object.new_model)
        return super().convert_auto_in_config(config, lns_object)

    def compute_auto_destruction_percent(
        self,
        config_name: str,
        project_operators: list[ProjectOperator],
        destroy_operator_name: str,
    ) -> float:
        """
        Compute auto destruction percentage from running average.

        :param config_name: Config name.
        :param project_operators: Project operators.
        :param destroy_operator_name: Destroy operator name.
        :return: Destruction percentage of auto-mode destroy operator.
        """
        operator_names = [operator.name for operator in project_operators]
        key = (config_name, destroy_operator_name)
        if key not in self._running_averages:
            self._register_key(key, operator_names)

        return self._running_averages[key].mean(float(self._auto_init_percent))

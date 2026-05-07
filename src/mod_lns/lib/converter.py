import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from clingo import Symbol, SymbolicAtoms

from mod_lns import Model

# from .logger import logger
from mod_lns.lib.parser.config_parser import ConfigParser

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


def calculate_actual_destruction_percent(destruction_candidate_atoms: set[Symbol], model: Model) -> float:
    """
    Return percentage of atoms subject to destruction actually destroyed in given model.

    :param destruction_candidate_atoms: Atoms subject to destruction
    :type destruction_candidate_atoms: set[Symbol]
    :param model: Model used to determine destruction percentage.
    :type model: Model
    :return: Percentage of atoms subject to destruction that were destroyed.
    :rtype: float
    """
    if not destruction_candidate_atoms:
        return 0.0
    actual_destroyed_atoms = destruction_candidate_atoms - model.shown
    actual_destruction_percent = (len(actual_destroyed_atoms) / len(destruction_candidate_atoms)) * 100
    return actual_destruction_percent


def is_new_model_better(new_model: Optional[Model], current_model: Model) -> bool:
    """
    Check whether new model is better than current model.

    :param new_model: New model.
    :type new_model: Optional[Model]
    :param current_model: Current model.
    :type current_model: Model
    :return: True if new model is better than current model, otherwise False.
    :rtype: bool
    """
    return new_model is not None and new_model.cost < current_model.cost


class AutoDestructionConverter(ABC):
    """
    Converter for computing destruction percentages of auto-mode destroy operators.
    """

    def convert_config(self, lnps_config: dict[str, Any], lns_object: Optional["LNS"] = None) -> dict[str, Any]:
        """
        Convert automatic values in LNPS configuration into concrete percentages.

        :param lnps_config: LNPS configuration containing automatic values.
        :type lnps_config: dict[str, Any]
        :param lns_object: LNS object.
        :type lns_object: Optional["LNS"]
        :return: LNPS configuration with all automatic values replaced by concrete percentages.
        :rtype: dict[str, Any]
        """
        resolved_config = copy.deepcopy(lnps_config)
        for destroy_operator in resolved_config["destroy_operators"]:
            destroy_operator_name = destroy_operator["name"]
            for percent_or_number in destroy_operator["percents_or_numbers"]:
                if percent_or_number["type"] == "auto":
                    percent_or_number["type"] = "p"
                    destruction_percent = self._compute_auto_destruction_percent(
                        lnps_config["name"], lnps_config["project_operators"], destroy_operator_name
                    )
                    # logger.info(f"Auto destruction percent: {destruction_percent} (destroy operator: {destroy_operator_name})")
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


class LastImprovementDestructionConverter(AutoDestructionConverter):
    """
    Simplest algorithm for computing destruction percentages.

    :param auto_init_percent: Initial destruction percentage. Defaults to 0.
    :type auto_init_percent: int, optional
    """

    def __init__(self, auto_init_percent: int = 0):
        self._auto_init_percent = auto_init_percent
        self._last_improvement_models: Optional[tuple[Model, Model]] = None
        self._last_improvement_specs: Optional[dict[str, set[Symbol]]] = None
        self._projected_atoms_cache: dict[str, set[Symbol]] = {}
        self._actual_destruction_percent_cache: dict[tuple[str, str], float] = {}

    def _reset_caches(self) -> None:
        """
        Clear cached projected atoms and percentages after an improvement update.
        """
        self._projected_atoms_cache.clear()
        self._actual_destruction_percent_cache.clear()

    def _get_projected_atoms(
        self,
        current_model: Model,
        op_specs: dict[str, set[Symbol]],
        project_operators: list[dict[str, Any]],
    ) -> set[Symbol]:
        """
        Collect projected atoms for all project operators with per-operator caching.

        :param current_model: Current model.
        :type current_model: Model
        :param op_specs: Operator specifications.
        :type op_specs: dict[str, set[Symbol]]
        :param project_operators: Project operators.
        :type project_operators: list[dict[str, Any]]
        :return: Set of projected atoms.
        :rtype: set[Symbol]
        """
        projected_atoms: set[Symbol] = set()
        for project_operator in project_operators:
            project_operator_name = project_operator["name"]
            if project_operator_name not in self._projected_atoms_cache:
                self._projected_atoms_cache[project_operator_name] = ConfigParser.get_projected_atoms(
                    current_model,
                    op_specs,
                    project_operator_name,
                )
            projected_atoms.update(self._projected_atoms_cache[project_operator_name])
        return projected_atoms

    def _update_last_improvement_stats(self, lns_object: "LNS") -> None:
        """
        Update statistics of last iteration where new model was better than current model.

        :param lns_object: LNS object.
        :type lns_object: "LNS"
        """
        if is_new_model_better(lns_object.new_model, lns_object.current_model):
            self._last_improvement_models = (lns_object.current_model, lns_object.new_model)
            self._last_improvement_specs = ConfigParser.get_op_specs(lns_object.current_model)
            self._reset_caches()

    def convert_config(self, lnps_config: dict[str, Any], lns_object: Optional["LNS"] = None) -> dict[str, Any]:
        """
        Convert automatic values in LNPS configuration into concrete percentages
        based on last iteration’s statistics where new model was better than current model.

        :param lnps_config: LNPS configuration containing automatic values.
        :type lnps_config: dict[str, Any]
        :param lns_object: LNS object.
        :type lns_object: Optional["LNS"]
        :return: LNPS configuration with all automatic values replaced by concrete percentages.
        :rtype: dict[str, Any]
        """
        if lns_object is not None:
            self._update_last_improvement_stats(lns_object)
        return super().convert_config(lnps_config, lns_object)

    def _compute_auto_destruction_percent(
        self, config_name: str, project_operators: list[dict[str, Any]], destroy_operator_name: str
    ) -> float:
        """
        Compute destruction percentage of auto-mode destroy operator based on actual destruction percentage.

        :param config_name: Config name.
        :type config_name: str
        :param project_operators: Project operators.
        :type project_operators: list[dict[str, Any]]
        :param destroy_operator_name: Destroy operator name.
        :type destroy_operator_name: str
        :return: Destruction percentage of auto-mode destroy operator.
        :rtype: float
        """
        key = (config_name, destroy_operator_name)
        if key in self._actual_destruction_percent_cache:
            return self._actual_destruction_percent_cache[key]

        if self._last_improvement_models is None or self._last_improvement_specs is None:
            return float(self._auto_init_percent)

        current_model = self._last_improvement_models[0]
        op_specs = self._last_improvement_specs
        new_model = self._last_improvement_models[1]

        projected_atoms = self._get_projected_atoms(current_model, op_specs, project_operators)

        destruction_candidate_atoms = ConfigParser.get_destruction_candidate_atoms(
            current_model, op_specs, projected_atoms, destroy_operator_name
        )
        actual_destruction_percent = calculate_actual_destruction_percent(destruction_candidate_atoms, new_model)
        self._actual_destruction_percent_cache[key] = actual_destruction_percent
        return actual_destruction_percent


@dataclass
class _RunningAverage:
    """State container for incremental average computation."""

    total: float = 0.0
    count: int = 0

    def add(self, value: float) -> None:
        self.total += value
        self.count += 1

    def mean(self, default: float) -> float:
        if self.count == 0:
            return default
        return self.total / self.count


class AverageDestructionConverter(AutoDestructionConverter):
    """
    Converter using the average of observed destruction percentages.

    Compared to the original implementation, this version keeps compact running
    aggregates (sum/count) per (config, destroy-operator) key and avoids storing
    full per-key histories.

    :param auto_init_percent: Initial destruction percentage. Defaults to 0.
    :type auto_init_percent: int, optional
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
        :type project_operator_names: list[str]
        :param destroy_operator_name: Destroy operator name.
        :type destroy_operator_name: str
        :param current_model: Current model.
        :type current_model: Model
        :param new_model: New model.
        :type new_model: Model
        :return: Actual destruction percentage.
        :rtype: float
        """
        op_specs = ConfigParser.get_op_specs(current_model)

        projected_atoms: set[Symbol] = set()
        for project_operator_name in project_operator_names:
            projected_atoms.update(ConfigParser.get_projected_atoms(current_model, op_specs, project_operator_name))

        destruction_candidate_atoms = ConfigParser.get_destruction_candidate_atoms(
            current_model,
            op_specs,
            projected_atoms,
            destroy_operator_name,
        )

        return calculate_actual_destruction_percent(destruction_candidate_atoms, new_model)

    def _update_running_averages(self, current_model: Model, new_model: Model) -> None:
        """
        Update running average for all registered keys with one new improvement stat.

        :param current_model: Current model in last improving iteration.
        :type current_model: Model
        :param new_model: New model in last improving iteration.
        :type new_model: Model
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
        :type key: tuple[str, str]
        :param project_operator_names: Project operator names.
        :type project_operator_names: list[str]
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

    def convert_config(
        self,
        lnps_config: dict[str, Any],
        lns_object: Optional["LNS"] = None,
    ) -> dict[str, Any]:
        """
        Convert auto values and update running averages on improving iterations.

        :param lnps_config: LNPS configuration containing automatic values.
        :type lnps_config: dict[str, Any]
        :param lns_object: LNS object.
        :type lns_object: Optional["LNS"]
        :return: LNPS configuration with all automatic values replaced.
        :rtype: dict[str, Any]
        """

        if lns_object is not None and is_new_model_better(lns_object.new_model, lns_object.current_model):
            self._improvement_models.append((lns_object.current_model, lns_object.new_model))
            self._update_running_averages(lns_object.current_model, lns_object.new_model)
        return super().convert_config(lnps_config, lns_object)

    def _compute_auto_destruction_percent(
        self,
        config_name: str,
        project_operator_names: list[dict[str, Any]],
        destroy_operator_name: str,
    ) -> float:
        """
        Compute auto destruction percentage from running average.

        :param config_name: Config name.
        :type config_name: str
        :param project_operator_names: Project operators.
        :type project_operator_names: list[dict[str, Any]]
        :param destroy_operator_name: Destroy operator name.
        :type destroy_operator_name: str
        :return: Destruction percentage of auto-mode destroy operator.
        :rtype: float
        """
        operator_names = [operator["name"] for operator in project_operator_names]
        key = (config_name, destroy_operator_name)
        if key not in self._running_averages:
            self._register_key(key, operator_names)

        return self._running_averages[key].mean(float(self._auto_init_percent))

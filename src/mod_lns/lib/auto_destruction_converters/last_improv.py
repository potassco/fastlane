"""
Last improvement destruction converter for adaptive LNS configuration selection.
"""

from typing import TYPE_CHECKING, Optional

from clingo import Symbol

from mod_lns import Model
from mod_lns.interfaces.auto_destruction_converter import AutoDestructionConverter
from mod_lns.lib.auto_destruction_converters.utils import calculate_actual_destruction_percent, is_new_model_better
from mod_lns.parsers.config_parser import ConfigParser
from mod_lns.utils.types import ActiveConfig, ProjectOperator

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class LastImprovementDestructionConverter(AutoDestructionConverter):
    """
    Simplest algorithm for computing destruction percentages.

    :param auto_init_percent: Initial destruction percentage. Defaults to 0.
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
        project_operators: list[ProjectOperator],
    ) -> set[Symbol]:
        """
        Collect projected atoms for all project operators with per-operator caching.

        :param current_model: Current model.
        :param op_specs: Operator specifications.
        :param project_operators: Project operators.
        :return: Set of projected atoms.
        """
        projected_atoms: set[Symbol] = set()
        for project_operator in project_operators:
            project_operator_name = project_operator.name
            if project_operator_name not in self._projected_atoms_cache:
                self._projected_atoms_cache[project_operator_name] = ConfigParser.get_projected_atoms(
                    current_model,
                    op_specs,
                    project_operator_name,
                )
            projected_atoms.update(self._projected_atoms_cache[project_operator_name])
        return projected_atoms

    def _update_last_improvement_stats(self, new_model: Model, current_model: Model) -> None:
        """
        Update statistics of last iteration where new model was better than current model.

        :param new_model: New model.
        :param current_model: Current model.
        """
        if is_new_model_better(new_model, current_model):
            self._last_improvement_models = (current_model, new_model)
            self._last_improvement_specs = ConfigParser.get_op_specs(current_model)
            self._reset_caches()

    def convert_auto_in_config(self, config: ActiveConfig, lns_object: Optional["LNS"] = None) -> ActiveConfig:
        """
        Convert automatic values in LNPS configuration into concrete percentages
        based on last iteration’s statistics where new model was better than current model.

        :param config: LNPS configuration containing automatic values.
        :param lns_object: LNS object.
        :return: LNPS configuration with all automatic values replaced by concrete percentages.
        """
        if lns_object is not None and lns_object.new_model is not None:
            self._update_last_improvement_stats(lns_object.new_model, lns_object.current_model)
        return super().convert_auto_in_config(config, lns_object)

    def compute_auto_destruction_percent(
        self, config_name: str, project_operators: list[ProjectOperator], destroy_operator_name: str
    ) -> float:
        """
        Compute destruction percentage of auto-mode destroy operator based on actual destruction percentage.

        :param config_name: Config name.
        :param project_operators: Project operators.
        :param destroy_operator_name: Destroy operator name.
        :return: Destruction percentage of auto-mode destroy operator.
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
            op_specs, projected_atoms, destroy_operator_name
        )
        actual_destruction_percent = calculate_actual_destruction_percent(destruction_candidate_atoms, new_model)
        self._actual_destruction_percent_cache[key] = actual_destruction_percent
        return actual_destruction_percent

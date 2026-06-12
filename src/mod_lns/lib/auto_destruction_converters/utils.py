"""
Utility functions for auto destruction converters.
"""

from typing import Optional

from clingo import Symbol

from mod_lns import Model


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

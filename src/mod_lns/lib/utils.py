"""
Collection of utility functions used for LNS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence, TypeVar

import clingo

if TYPE_CHECKING:
    from mod_lns.interfaces.solver import SolverConfig  # nocoverage
    from mod_lns.new_lns import LNS  # nocoverage


def calculate_variability(list1: Sequence[Any], list2: Sequence[Any]) -> float:
    """
    Calculate variability of two lists in percent.

    0 - no variability (same lists or bigger one contains smaller one)

    100 - completely different

    :param list1: First list.
    :type list1: Sequence[Any]
    :param list2: Second list.
    :type list2: Sequence[Any]
    :return: Variability of both lists.
    :rtype: float
    """
    len1 = len(list1)
    len2 = len(list2)
    if len1 < len2:
        return (1 - len(set(list1).intersection(list2)) / len1) * 100
    return (1 - len(set(list2).intersection(list1)) / len2) * 100


def fix_symbols(
    symbols: list[clingo.symbol.Symbol],
) -> list[tuple[clingo.symbol.Symbol, bool]]:
    """
    Prepare symbols to be used as assumptions (being fixed).

    :param symbols: Symbols to be used.
    :type symbols: list[clingo.symbol.Symbol]
    :return: Fixed symbols/atoms.
    :rtype:  list[tuple[clingo.symbol.Symbol, bool]]
    """
    fixed = []
    for symbol in symbols:
        fixed.append((symbol, True))
    return fixed


def get_unique_list(seq: Sequence[Any]) -> list[Any]:
    """
    Get unique elements from a list while preserving the order.

    :param seq: Input sequence.
    :type seq: Sequence[Any]
    :return: List of unique elements.
    :rtype: list[Any]
    """
    seen = []
    return [x for x in seq if x not in seen and not seen.append(x)]  # type: ignore


T = TypeVar("T", float, int)


def clamp(value: T, min_value: int, max_value: int) -> T:
    """
    Clamp a value between a minimum and maximum value.

    :param value: Value to clamp.
    :type value: T
    :param min_value: Minimum value.
    :type min_value: int
    :param max_value: Maximum value.
    :type max_value: int
    :return: Clamped value.
    :rtype: T
    """
    return max(min_value, min(max_value, value))


def update_time_limit(lns_object: "LNS", solver_config: "SolverConfig") -> None:
    """
    Update solve time-limit.

    :param solver_config: Solver configuration to update.
    :type solver_config: SolverConfig
    """
    if lns_object.config.time_limit is not None:
        solver_tl = solver_config.time_limit
        remaining_time = lns_object.timer.remaining_time()  # return float, cast to int (maybe in solver)
        if solver_tl is None:
            solver_config.time_limit = remaining_time
        elif remaining_time > 0 and remaining_time < solver_tl:
            solver_config.time_limit = remaining_time
            lns_object.logger.debug("elapsed time: %d seconds", lns_object.timer.get_elapsed_time())
            lns_object.logger.debug(
                "Time limit for solver reduced to %d seconds to fit into overall time limit.",
                solver_config.time_limit,
            )

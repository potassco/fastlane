"""
Collection of utility functions used for LNS.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Optional, Sequence, TypeVar

import clingo
from clingo import Symbol

from mod_lns import Timer

if TYPE_CHECKING:
    from mod_lns.interfaces.solver import SolverConfig  # nocoverage
    from mod_lns.lns import LNS  # nocoverage

UINT_MAX = 4294967295


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
    if lns_object.options.time_limit is not None:
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


def format_atoms(atoms: set[Symbol]) -> str:
    """
    Format set of atoms into sorted space-separated string.

    :param atoms: Set of atoms.
    :type atoms: set[Symbol]
    :return: Formatted atom string.
    :rtype: str
    """
    return " ".join([str(atom) for atom in sorted(atoms)])


def increase_solve_limit(current_solve_limit: str, increase_rate: float) -> str:
    """
    Increase solve limit by a percentage.

    :param current_solve_limit: Current solve limit as string (e.g., "1000ms", "10s").
    :type current_solve_limit: str
    :param increase_rate: Percentage to increase the solve limit (e.g., 20 for 20%).
    :type increase_rate: float
    :return: New solve limit as string.
    :rtype: str
    """
    if increase_rate == 0:
        return current_solve_limit
    increased_solve_limit = []
    for n in current_solve_limit.split(","):
        if n == "umax":
            increased_solve_limit.append(n)
        else:
            new_n = math.ceil(int(n) * increase_rate / 100 + int(n))
            if new_n <= UINT_MAX:
                increased_solve_limit.append(str(new_n))
            else:
                increased_solve_limit.append("umax")

    return ",".join(increased_solve_limit)


def increase_time_limit(timer: Timer, time_limit: Optional[int], solver_time_limit: int, increase_rate: float) -> int:
    """
    Increase time limit by a percentage.

    :param current_time_limit: Current time limit in seconds (or None for unlimited).
    :type current_time_limit: int | None
    :param increase_rate: Percentage to increase the time limit (e.g., 20 for 20%).
    :type increase_rate: float
    :return: New time limit in seconds (or None for unlimited).
    :rtype: int
    """
    if increase_rate == 0:
        return solver_time_limit
    # dont increase time limit past overall time limit
    if time_limit is not None:
        if timer.remaining_time() < solver_time_limit:
            return solver_time_limit
    current_time_limit = solver_time_limit
    return math.ceil(current_time_limit * increase_rate / 100 + current_time_limit)


def increase_cutoff(
    current_cutoff: int,
    cutoff_threshold: int,
    increase_rate: int,
    timer: Timer,
    time_limit: Optional[int],
    latest_stats: dict[str, Any],
) -> int:
    """
    Update the solver's cutoff for the next iteration.

    :param solver_config: Solver configuration
    :type solver_config: SolverConfig
    :return: int
    """
    if increase_rate == 0:
        return current_cutoff
    # dont increase time limit past overall time limit
    if time_limit is not None:
        if timer.remaining_time() < current_cutoff:
            return current_cutoff
    if (
        latest_stats.get("no_improvement_cutoff_count", 0) != 0
        and latest_stats.get("no_improvement_cutoff_count", 0) % cutoff_threshold == 0
    ):
        return math.ceil(current_cutoff * increase_rate / 100 + current_cutoff)

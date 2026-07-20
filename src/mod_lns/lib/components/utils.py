"""
Collection of utility functions used for LNS.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Optional, Sequence

from mod_lns import Timer

if TYPE_CHECKING:
    from mod_lns.interfaces.solver import SolverConfig  # nocoverage
    from mod_lns.lns import LNS  # nocoverage

UINT_MAX = 4294967295


def calculate_variability(list1: set[Any], list2: set[Any]) -> float:
    """
    Calculate variability of two sets in percent.

    0 - no variability (same sets or bigger one contains smaller one)

    100 - completely different

    :param list1: First set.
    :param list2: Second set.
    :return: Variability of both sets.
    """
    len1 = len(list1)
    len2 = len(list2)
    if len1 < len2:
        return (1 - len(list1.intersection(list2)) / len1) * 100
    return (1 - len(list2.intersection(list1)) / len2) * 100


def get_unique_list(seq: Sequence[Any]) -> list[Any]:
    """
    Get unique elements from a list while preserving the order.

    :param seq: Input sequence.
    :return: List of unique elements.
    """
    seen = []
    return [x for x in seq if x not in seen and not seen.append(x)]  # type: ignore


def update_time_limit(lns_object: "LNS", solver_config: "SolverConfig") -> None:
    """
    Update solve time-limit.

    :param lns_object: LNS object.
    :param solver_config: Solver configuration to update.
    """
    if lns_object.options.time_limit is not None:
        solver_tl = solver_config.time_limit
        remaining_time = lns_object.timer.remaining_time()  # return float, cast to int (maybe in solver)
        if solver_tl is None:
            solver_config.time_limit = remaining_time
        elif 0 < remaining_time < solver_tl:
            solver_config.time_limit = remaining_time
            lns_object.logger.debug("elapsed time: %d seconds", lns_object.timer.get_elapsed_time())
            lns_object.logger.debug(
                "Time limit for solver reduced to %d seconds to fit into overall time limit.",
                solver_config.time_limit,
            )


def increase_solve_limit(current_solve_limit: str, increase_rate: float) -> str:
    """
    Increase solve limit by a percentage.

    :param current_solve_limit: Current solve limit as string (e.g., "1000,1000", "1000,umax").
    :param increase_rate: Percentage to increase the solve limit (e.g., 20 for 20%).
    :return: New solve limit as string.
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

    :param timer: Timer object.
    :param time_limit: Overall time limit in seconds (or None for unlimited).
    :param solver_time_limit: Current solver time limit in seconds.
    :param increase_rate: Percentage to increase the time limit (e.g., 20 for 20%).
    :return: New time limit in seconds (or None for unlimited).
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
    *,
    current_cutoff: int,
    cutoff_threshold: Optional[int],
    increase_rate: int,
    timer: Timer,
    time_limit: Optional[int],
    latest_stats: dict[str, Any],
) -> int:
    """
    Update the solver's cutoff for the next iteration.

    :param current_cutoff: Current cutoff value.
    :param cutoff_threshold: Threshold for increasing the cutoff.
    :param increase_rate: Percentage to increase the cutoff (e.g., 20 for 20%).
    :param timer: Timer object.
    :param time_limit: Overall time limit in seconds (or None for unlimited).
    :param latest_stats: Latest statistics dictionary containing "no_improvement_cutoff_count".
    :return: New cutoff value.
    """
    if increase_rate == 0:
        return current_cutoff
    # dont increase time limit past overall time limit
    if time_limit is not None:
        if timer.remaining_time() < current_cutoff:
            return current_cutoff
    if (
        cutoff_threshold is not None
        and latest_stats.get("no_improvement_cutoff_count", 0) != 0
        and latest_stats.get("no_improvement_cutoff_count", 0) % cutoff_threshold == 0
    ):
        return math.ceil(current_cutoff * increase_rate / 100 + current_cutoff)
    return current_cutoff

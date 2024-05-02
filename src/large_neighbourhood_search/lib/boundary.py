"""
Collection of functions regarding the boundary of a LNS.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


def boundary_overall(lns_object: LNS, values: Dict[str, Any], action: str) -> bool:
    """
    Handle LNS boundary.
    Has to support the following actions:

    - "init"
    - "update"
    - "improvement"
    - "no_improvement"

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param values: Dictionary containing all values used for keeping track of the LNS.
    :type values: Dict[str, Any]
    :return: Whether action succeeded or not.
    :rtype: bool
    """
    # dict call-by-reference
    if action == "init":
        values.clear()
        values["bound"] = lns_object.config_values["bound"]
        values["step"] = 0
        values["start_time"] = time.time()
        values["no_improvement"] = 0
        return True
    if action == "update":
        values["step"] += 1
        return True
    if action == "improvement":
        print(f"{values['step']}|{values['bound']}")
        if lns_object.models["best_model"] != {}:
            print(
                f"New opt_val: {lns_object.callables['calc_opt_value'](lns_object.models['best_model'])}"
            )
        return True
    if action == "no_improvement":
        values["no_improvement"] += 1
        # change relax rate
        if lns_object.config_values["switch_rr_after_no_improv"] > 0:
            lns_object.config_values["current_relax_rate"] = lns_object.config_values[
                "relax_rates"
            ][
                values["no_improvement"]
                // lns_object.config_values["switch_rr_after_no_improv"]
                % len(lns_object.config_values["relax_rates"])
            ]
        return True
    return False


def check_stop_steps(lns_object: LNS, boundary_dict: Dict[str, Any]) -> bool:
    """
    Check whether to stop LNS depending on steps made.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param boundary_dict: Dictionary containing all values used for keeping track of the LNS.
    :type boundary_dict: Dict[str, Any]
    :return: Whether to stop LNS or not.
    :rtype: bool
    """
    if lns_object.models["best_model"] != {}:
        return (
            boundary_dict["step"] >= boundary_dict["bound"]
            or lns_object.callables["calc_opt_value"](lns_object.models["best_model"])
            == 0
        )
    return boundary_dict["step"] >= boundary_dict["bound"]


def check_stop_time(lns_object: LNS, boundary_dict: Dict[str, Any]) -> bool:
    """
    Check whether to stop LNS depending on passed time.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param boundary_dict: Dictionary containing all values used for keeping track of the LNS.
    :type boundary_dict: Dict[str, Any]
    :return: Whether to stop LNS or not.
    :rtype: bool
    """
    if lns_object.models["best_model"] != {}:
        return (
            time.time() - boundary_dict["start_time"] >= boundary_dict["bound"]
            or lns_object.callables["calc_opt_value"](lns_object.models["best_model"])
            == 0
        )
    return time.time() - boundary_dict["start_time"] >= boundary_dict["bound"]

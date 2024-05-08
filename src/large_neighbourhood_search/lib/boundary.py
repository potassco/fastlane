"""
Collection of functions regarding the boundary of a LNS.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


def boundary_overall(lns_object: LNS, action: str) -> bool:
    """
    Handle LNS boundary.
    Has to support the following actions:

    - "init"
    - "update"
    - "improvement"
    - "no_improvement"

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :return: Whether action succeeded or not.
    :rtype: bool
    """
    values = lns_object.boundary_dict
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
        if values["step"] % 50 == 0:
            print(f"{values['step']}|{values['bound']}")
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


def check_stop_steps(lns_object: LNS) -> bool:
    """
    Check whether to stop LNS depending on steps made.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :return: Whether to stop LNS or not.
    :rtype: bool
    """
    if lns_object.models["best_model"] != {}:
        return (
            lns_object.boundary_dict["step"] >= lns_object.boundary_dict["bound"]
            or lns_object.callables["calc_opt_value"](lns_object.models["best_model"])
            == 0
        )
    return lns_object.boundary_dict["step"] >= lns_object.boundary_dict["bound"]


def check_stop_time(lns_object: LNS) -> bool:
    """
    Check whether to stop LNS depending on passed time.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :return: Whether to stop LNS or not.
    :rtype: bool
    """
    if lns_object.models["best_model"] != {}:
        return (
            time.time() - lns_object.boundary_dict["start_time"]
            >= lns_object.boundary_dict["bound"]
            or lns_object.callables["calc_opt_value"](lns_object.models["best_model"])
            == 0
        )
    return (
        time.time() - lns_object.boundary_dict["start_time"]
        >= lns_object.boundary_dict["bound"]
    )


def finish(lns_object) -> None:
    """
    Print results on finished search.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    """
    end_time = time.time()
    answer_string = " ".join(
        [str(atom) for atom in lns_object.models["best_model"]["shown"]]
    )
    if "assignments" in lns_object.models["best_model"]:
        answer_string += "\n".join(lns_object.models["best_model"]["assignments"])
    print("==================")
    print(
        (
            "Answer\n"
            f"{answer_string}\n"
            f"Final opt_val: {lns_object.callables['calc_opt_value'](lns_object.models['best_model'])}\n"
            f"Overall steps: {lns_object.boundary_dict['step']}\n"
            f"Overall time: {end_time - lns_object.boundary_dict['start_time']:.3f}s"
        )
    )

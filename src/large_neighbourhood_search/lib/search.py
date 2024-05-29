"""
Collection of functions used during LNS.
"""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Any, Dict, List, Sequence, Tuple

import clingo
from clingo.symbol import Number

from large_neighbourhood_search.lib.lns_utils import (
    calculate_variability,
    check_smaller_lexicographic,
)
from large_neighbourhood_search.lib.theory import ground_base

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


def relax_declarative(
    model: Dict[str, Sequence[clingo.symbol.Symbol]], relax_parameters: Dict[str, Any]
) -> List[Tuple[clingo.symbol.Symbol, bool]]:
    """
    Relax portion of selected atoms given by the relax_rate.
    ASP encoding has to contain `_lns_select/1` and `_lns_fix/2` predicates.

    :param model: Dictionary containing list of shown and true atoms.
    :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param relax_parameters: Parameters used to determine relaxed atoms.
    :type relax_parameters: Dict[str, Any]
    :return: Fixed (not relaxed) atoms.
    :rtype: List[Tuple[clingo.symbol.Symbol, bool]]
    """
    fixed_atoms = []
    selected_atoms = []
    declared_fixed_atoms: dict[
        clingo.symbol.Symbol, list[tuple[clingo.symbol.Symbol, bool]]
    ] = {}
    for atom in model["true"]:
        if atom.match("_lns_select", 1):
            selected_atoms.append(atom.arguments[0])
            declared_fixed_atoms[atom.arguments[0]] = []
        elif atom.match("_lns_fix", 2):
            declared_fixed_atoms[atom.arguments[1]].append((atom.arguments[0], True))
    for symbol in selected_atoms:
        if random.randint(0, 100) >= relax_parameters["relax_rate"] * 100:
            fixed_atoms += declared_fixed_atoms[symbol]
    return fixed_atoms


def relax_random(
    model: Dict[str, Sequence[clingo.symbol.Symbol]], relax_parameters: Dict[str, Any]
) -> List[Tuple[clingo.symbol.Symbol, bool]]:
    """
    Relax random number of shown atoms given by the relax_rate.

    :param model: Dictionary containing list of shown and true atoms.
    :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param relax_parameters: Parameters used to determine relaxed atoms.
    :type relax_parameters: Dict[str, Any]
    :return: Fixed (not relaxed) atoms.
    :rtype: List[Tuple[clingo.symbol.Symbol, bool]]
    """
    fixed_atoms = []
    for atom in model["shown"]:
        if random.randint(0, 100) >= relax_parameters["relax_rate"] * 100:
            fixed_atoms.append((atom, True))
    return fixed_atoms


# pylint: disable=unused-argument
def check_accept_always(
    lns_object: LNS,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    current_model: Dict[str, Sequence[clingo.symbol.Symbol]],
) -> bool:
    """
    Check whether new model is accepted.
    Always accept.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param new_model: New model checked for acceptance.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param current_model: Current model used for comparison.
    :type current_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was accepted or not.
    :rtype: bool
    """
    return True


# pylint: disable=unused-argument
def check_accept_variability(
    lns_object: LNS,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    current_model: Dict[str, Sequence[clingo.symbol.Symbol]],
) -> bool:
    """
    Check whether new model is accepted.
    Accept if variability of new and current model >= 0.5.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param new_model: New model checked for acceptance.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param current_model: Current model used for comparison.
    :type current_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was accepted or not.
    :rtype: bool
    """
    return calculate_variability(new_model["true"], current_model["true"]) >= 0.5


def check_better_weighted_sum(
    lns_object: LNS,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    current_model: Dict[str, Sequence[clingo.symbol.Symbol]],
) -> bool:
    """
    Check whether new model is better.
    Compare optimization values of new and old model.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param new_model: New model being checked.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param current_model: Current model used for comparison.
    :type current_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was better or not.
    :rtype: bool
    """
    new_opt_val = lns_object.callables["calc_opt_value"](new_model)
    return new_opt_val < lns_object.callables["calc_opt_value"](current_model)


def check_better_lexicographic(
    lns_object: LNS,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    current_model: Dict[str, Sequence[clingo.symbol.Symbol]],
) -> bool:
    """
    Check whether new model is better.
    Compare optimization values of new and old model.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param new_model: New model being checked.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param current_model: Current model used for comparison.
    :type current_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was better or not.
    :rtype: bool
    """
    return check_smaller_lexicographic(
        lns_object.callables["calc_opt_value"](new_model),
        lns_object.callables["calc_opt_value"](current_model),
    )


# pylint: disable=unused-argument
def check_better_always(
    lns_object: LNS,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    current_model: Dict[str, Sequence[clingo.symbol.Symbol]],
) -> bool:
    """
    Check whether new model is better.
    Always better due to added hard constraint during grounding.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param new_model: New model being checked.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param current_model: Current model used for comparison.
    :type current_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was better or not.
    :rtype: bool
    """
    return True


def better_solution_found_classic(lns_object: LNS, ctl: clingo.control.Control) -> None:
    """
    What to do if better solution was found.
    Assign new best model.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Clingo control object used for solving.
    :type ctl: clingo.control.Control
    """
    lns_object.models["best_model"] = lns_object.models["new_model"].copy()


def better_solution_found_hc(lns_object: LNS, ctl: clingo.control.Control) -> None:
    """
    What to do if better solution was found.
    Assign new best model and ground new hard constraint.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Clingo control object used for solving.
    :type ctl: clingo.control.Control
    """
    lns_object.models["best_model"] = lns_object.models["new_model"].copy()

    # update boundary
    opt_val = lns_object.callables["calc_opt_value"](lns_object.models["best_model"])
    ctl.ground([("opt_val", [Number(opt_val)])])


def get_first_solution_hc_weighted_sum(lns_object: LNS, ctl, thy: Any) -> bool:
    """
    Find initial solution.
    Ground found optimization value as hard constraint.
    Use weighted sum as optimization criteria.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Control object used for search.
    :type ctl: clingo.control.Control
    :param thy: Theory object used for search.
    :type thy: Any
    :return: Whether a solution was found or not
    :rtype: bool
    """
    # add constraint to force better solution with each iteration
    # encoding has to contain  _opt(I,(P,V)) predicates as optimization criteria
    # where I: identifier, P: Priority, V: Value
    ctl.add("opt_val", ["o"], ":- #sum{V,I: _opt(I,(P,V))} >= o.")
    ground_base(lns_object, ctl)

    # get first solution
    if lns_object.callables["repair"](lns_object, ctl, [], thy).satisfiable:
        new_opt_val = lns_object.callables["calc_opt_value"](
            lns_object.models["new_model"]
        )
        print(f"Initial solution found with opt_val: {new_opt_val}")
        ctl.ground([("opt_val", [Number(new_opt_val)])])
        lns_object.models["current_model"] = lns_object.models["new_model"].copy()
        lns_object.models["best_model"] = lns_object.models["new_model"].copy()
        return True
    print("No first solution found.")
    return False


def get_first_solution_classic(lns_object: LNS, ctl, thy: Any) -> bool:
    """
    Find initial solution.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Control object used for search.
    :type ctl: clingo.control.Control
    :param thy: Theory object used for search.
    :type thy: Any
    :return: Whether a solution was found or not
    :rtype: bool
    """
    ctl.ground([("base", [])], context=lns_object)

    # get first solution
    if lns_object.callables["repair"](lns_object, ctl, [], thy).satisfiable:
        new_opt_val = lns_object.callables["calc_opt_value"](
            lns_object.models["new_model"]
        )
        print(f"Initial solution found with opt_val: {new_opt_val}")
        lns_object.models["current_model"] = lns_object.models["new_model"].copy()
        lns_object.models["best_model"] = lns_object.models["new_model"].copy()
        return True
    print("No first solution found.")
    return False


def check_stuck_never(lns_object: LNS) -> bool:
    """
    Search is never stuck.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :return: False.
    :rtype: bool
    """
    return False


def check_stuck(lns_object: LNS) -> bool:
    """
    Determine if search is stuck.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :return: Whether search is stuck or not.
    :rtype: bool
    """
    if lns_object.boundary_dict["no_improvement"] >= 1000:
        return True
    return False


def is_stuck(lns_object: LNS) -> None:
    """
    What to do if search is stuck.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    """
    print("Search stuck. Stopping...")
    lns_object.callables["finish"](lns_object)


def time_out(lns_object: LNS) -> None:
    """
    Time out handling.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    """
    if "timeout" not in lns_object.boundary_dict:
        lns_object.boundary_dict["timeout"] = 0
    timelimit = lns_object.param_values["time_limit"]
    print(
        f"{time.time() - lns_object.boundary_dict['start_time']:.3f}s: "
        f"Unable to repair model during time limit ({timelimit}s)."
    )
    lns_object.boundary_dict["timeout"] += 1
    if lns_object.boundary_dict["timeout"] >= 5:
        lns_object.callables["is_stuck"](lns_object)
        raise SystemExit

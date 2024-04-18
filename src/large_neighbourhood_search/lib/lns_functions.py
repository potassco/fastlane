"""
Library of functions used for LNS.
"""

# pylint: disable=protected-access
import random
import time
from typing import Any, Dict, List, Sequence, Tuple

import clingo
from clingo.symbol import Number, SymbolType


def on_model(lns_object, model: clingo.solving.Model) -> None:
    """
    Saves shown and true atoms of model and aggregates optimization values.

    :param model: Model found during solving.
    :type model: clingo.solving.Model
    """
    lns_object.models["new_model"] = {}
    lns_object.models["new_model"]["shown"] = model.symbols(shown=True)
    lns_object.models["new_model"]["true"] = model.symbols(atoms=True)

    # if lns_object.models["best_model"]:
    #    print(
    #        lns_object.get_variability(
    #            lns_object.models["new_model"]["shown"],
    #            lns_object.models["best_model"]["shown"],
    #        )
    #    )


def relax_declarative(
    model: Dict[str, Sequence[clingo.symbol.Symbol]], relax_rate: float
) -> List[Tuple[clingo.symbol.Symbol, bool]]:
    """
    Relax portion of selected atoms given by the relax_rate.
    ASP encoding has to contain `_lns_select/1` and `_lns_fix/2` predicates.

    :param model: Dictionary containing list of shown and true atoms.
    :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param relax_rate: Percentage of atoms to be relaxed.
    :type relax_rate: float
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
        if random.randint(0, 100) >= relax_rate * 100:
            fixed_atoms += declared_fixed_atoms[symbol]
    return fixed_atoms


def relax_random(
    model: Dict[str, Sequence[clingo.symbol.Symbol]], relax_rate: float
) -> List[Tuple[clingo.symbol.Symbol, bool]]:
    """
    Relax random number of shown atoms given by the relax_rate.

    :param model: Dictionary containing list of shown and true atoms.
    :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param relax_rate: Percentage of atoms to be relaxed.
    :type relax_rate: float
    :return: Fixed (not relaxed) atoms.
    :rtype: List[Tuple[clingo.symbol.Symbol, bool]]
    """
    fixed_atoms = []
    for atom in model["shown"]:
        if random.randint(0, 100) >= relax_rate * 100:
            fixed_atoms.append((atom, True))
    return fixed_atoms


def repair(
    lns_object,
    ctl: clingo.control.Control,
    assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
) -> clingo.solving.SolveResult:
    """
    Solve under given assumptions.

    :param ctl: Clingo Control object used for solving.
    :type ctl: clingo..control.Control
    :param assumptions: Assumptions for solving (fixed atoms).
    :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
    :return: Result of solving call.
    :rtype: clingo.solving.SolveResult
    """
    x = ctl.solve(assumptions=assumptions, on_model=lns_object._on_model)
    return x


def calculate_opt_val(model: Dict[str, Sequence[clingo.symbol.Symbol]]) -> int:
    """
    Get optimization value of given model.

    :param model: Model.
    :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Opt value of given model.
    :rtype: int
    """
    opt_val = 0
    for atom in model["true"]:
        if atom.match("_minimize", 2) and atom.arguments[0].type is SymbolType.Number:
            opt_val += atom.arguments[0].number
    return opt_val


# pylint: disable=unused-argument
def check_accept_always(
    lns_object,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    current_model: Dict[str, Sequence[clingo.symbol.Symbol]],
) -> bool:
    """
    Check whether new model is accepted.
    Always accept.

    :param new_model: New model checked for acceptance.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param old_model: Current model used for comparison.
    :type old_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was accepted or not.
    :rtype: bool
    """
    return True


def check_better_classic(
    lns_object,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    best_model: Dict[str, Sequence[clingo.symbol.Symbol]],
) -> bool:
    """
    Check whether new model is better.
    Compare optimization values of new and old model.

    :param new_model: New model being checked.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param old_model: Best model used for comparison.
    :type old_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was better or not.
    :rtype: bool
    """
    new_opt_val = lns_object.callables["calc_opt_value"](new_model)
    if new_opt_val < lns_object.callables["calc_opt_value"](best_model):
        return True
    return False


# pylint: disable=dangerous-default-value, unused-argument
def check_better_always(
    lns_object,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    best_model: Dict[str, Sequence[clingo.symbol.Symbol]],
) -> bool:
    """
    Check whether new model is better.
    Always better due to added hard constraint during grounding.

    :param new_model: New model being checked.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param old_model: Best model used for comparison.
    :type old_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was better or not.
    :rtype: bool
    """
    return True


def better_solution_found_classic(lns_object, ctl: clingo.control.Control) -> None:
    """
    What to do if better solution was found.
    Assign new best model.

    :param ctl: Clingo control object used for solving.
    :type ctl: clingo.control.Control
    """
    lns_object.models["best_model"] = lns_object.models["new_model"].copy()


def better_solution_found_hard_constraint(
    lns_object, ctl: clingo.control.Control
) -> None:
    """
    What to do if better solution was found.
    Assign new best model and ground new hard constraint.

    :param ctl: Clingo control object used for solving.
    :type ctl: clingo.control.Control
    """
    lns_object.models["best_model"] = lns_object.models["new_model"].copy()

    # update boundary
    opt_val = lns_object.callables["calc_opt_value"](lns_object.models["best_model"])
    ctl.ground([("opt_val", [Number(opt_val)])])


def get_first_solution_hard_constraint(lns_object, ctl) -> bool:
    """
    Find initial solution.
    And ground found optimization value as hard constraint.

    :param ctl: Control object used for search.
    :type ctl: clingo.control.Control
    :return: Whether a solution was found or not
    :rtype: bool
    """
    # add constraint to force better solution with each iteration
    # encoding has to contain _minimize(V,I) predicates as minimization criteria
    # where V: value, I: identifier
    ctl.add("opt_val", ["o"], ":- #sum{V,I: _minimize(V,I)} >= o.")
    ctl.ground([("base", [])], context=lns_object)

    # get first solution
    if ctl.solve(on_model=lns_object._on_model).satisfiable:
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


def get_first_solution_classic(lns_object, ctl) -> bool:
    """
    Find initial solution.

    :param ctl: Control object used for search.
    :type ctl: clingo.control.Control
    :return: Whether a solution was found or not
    :rtype: bool
    """
    ctl.ground([("base", [])], context=lns_object)

    # get first solution
    if ctl.solve(on_model=lns_object._on_model).satisfiable:
        new_opt_val = lns_object.callables["calc_opt_value"](
            lns_object.models["new_model"]
        )
        print(f"Initial solution found with opt_val: {new_opt_val}")
        lns_object.models["current_model"] = lns_object.models["new_model"].copy()
        lns_object.models["best_model"] = lns_object.models["new_model"].copy()
        return True
    print("No first solution found.")
    return False


def boundary_overall(lns_object, values: Dict[str, Any], action: str) -> bool:
    """
    Handle LNS boundary.
    Has to support the following actions:

    - "init"
    - "update"
    - "improvement"
    - "no_improvement"

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


def check_stop_steps(lns_object, boundary_dict: Dict[str, Any]) -> bool:
    """
    Check whether to stop LNS depending on steps made.

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


def check_stop_time(lns_object, boundary_dict: Dict[str, Any]) -> bool:
    """
    Check whether to stop LNS depending on passed time.

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

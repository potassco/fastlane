"""
Library of functions used for LNS.
"""

# pylint: disable=protected-access
from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Any, Dict, List, Sequence, Tuple

import clingo
from clingo import ast
from clingo.symbol import Number, SymbolType
from clingodl import ClingoDLTheory

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


def setup_clingo(lns_object: LNS) -> Tuple[clingo.control.Control, None]:
    """
    Initialize clingo.Control object using clingo.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :return: Control and theory object used for LNS
    :rytpe: Tuple[clingo.control.Control, clingodl.ClingoDlTheory]
    """
    ctl = clingo.Control(lns_object.config_values["clingo_args"])
    # no input files not supported
    # if not lns_object._files:
    #    lns_object._files = ["-"]
    for path in lns_object.config_values["files"]:
        ctl.load(path)

    # set seed if given
    if lns_object.config_values["seed"] is not None:
        random.seed(lns_object.config_values["seed"])
        lns_object.config_values["clingo_args"].append(
            f"--seed={lns_object.config_values['seed']}"
        )
    return (ctl, None)


def setup_clingo_dl(lns_object: LNS) -> Tuple[clingo.control.Control, ClingoDLTheory]:
    """
    Initialize clingo.Control object using clingo-dl.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :return: Control and theory object used for LNS
    :rytpe: Tuple[clingo.control.Control, clingodl.ClingoDlTheory]
    """
    thy = ClingoDLTheory()
    ctl = clingo.Control(lns_object.config_values["clingo_args"])
    thy.register(ctl)
    # no input files not supported
    # if not lns_object._files:
    #    lns_object._files = ["-"]
    # for path in lns_object.config_values["files"]:
    with ast.ProgramBuilder(ctl) as builder:
        ast.parse_files(
            lns_object.config_values["files"],
            lambda ast: thy.rewrite_ast(ast, builder.add),
        )

    # set seed if given
    if lns_object.config_values["seed"] is not None:
        random.seed(lns_object.config_values["seed"])
        lns_object.config_values["clingo_args"].append(
            f"--seed={lns_object.config_values['seed']}"
        )
    return ctl, thy


def ground_base(lns_object: LNS, ctl: clingo.Control) -> None:
    """
    Ground base using control object.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Clingo Control object used for solving.
    :type ctl: clingo.control.Control
    """
    ctl.ground([("base", [])], context=lns_object)


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


# pylint: disable=unused-argument
def repair_clingo(
    lns_object: LNS,
    ctl: clingo.control.Control,
    assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
    thy: Any,
) -> bool:
    """
    Solve under given assumptions using clingo.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Clingo Control object used for solving.
    :type ctl: clingo.control.Control
    :param assumptions: Assumptions for solving (fixed atoms).
    :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
    :param thy: Theory object.
    :type thy: Any
    :return: Whether model was found.
    :rtype: bool
    """
    with ctl.solve(assumptions=assumptions, yield_=True) as handle:
        for model in handle:
            lns_object.models["new_model"] = {}
            lns_object.models["new_model"]["shown"] = model.symbols(shown=True)
            lns_object.models["new_model"]["true"] = model.symbols(atoms=True)
            if model:
                return True
    return False


def repair_clingo_dl(
    lns_object: LNS,
    ctl: clingo.control.Control,
    assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
    thy: ClingoDLTheory,
) -> bool:
    """
    Solve under given assumptions using clingo.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Clingo Control object used for solving.
    :type ctl: clingo.control.Control
    :param assumptions: Assumptions for solving (fixed atoms).
    :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
    :param thy: clingo-dl theory object.
    :type thy: clingodl.ClingoDlTheory
    :return: Whether model was found.
    :rtype: bool
    """
    thy.prepare(ctl)
    with ctl.solve(
        assumptions=assumptions, yield_=True, on_model=thy.on_model
    ) as handle:
        for model in handle:
            lns_object.models["new_model"] = {}
            lns_object.models["new_model"]["shown"] = model.symbols(shown=True)
            lns_object.models["new_model"]["true"] = model.symbols(atoms=True)
            lns_object.models["new_model"]["assignments"] = [
                f"{key}={val}" for key, val in thy.assignment(model.thread_id)
            ]
            if model:
                return True
    return False


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
    :param old_model: Current model used for comparison.
    :type old_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was accepted or not.
    :rtype: bool
    """
    return True


def check_better_classic(
    lns_object: LNS,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    best_model: Dict[str, Sequence[clingo.symbol.Symbol]],
) -> bool:
    """
    Check whether new model is better.
    Compare optimization values of new and old model.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
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


# pylint: disable=unused-argument
def check_better_always(
    lns_object: LNS,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    best_model: Dict[str, Sequence[clingo.symbol.Symbol]],
) -> bool:
    """
    Check whether new model is better.
    Always better due to added hard constraint during grounding.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param new_model: New model being checked.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param old_model: Best model used for comparison.
    :type old_model: Dict[str, Sequence[clingo.symbol.Symbol]]
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


def better_solution_found_hard_constraint(
    lns_object: LNS, ctl: clingo.control.Control
) -> None:
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


def get_first_solution_hard_constraint(lns_object: LNS, ctl, thy: Any) -> bool:
    """
    Find initial solution.
    And ground found optimization value as hard constraint.

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
    # encoding has to contain _minimize(V,I) predicates as minimization criteria
    # where V: value, I: identifier
    ctl.add("opt_val", ["o"], ":- #sum{V,I: _minimize(V,I)} >= o.")
    ground_base(lns_object, ctl)

    # get first solution
    if lns_object.callables["repair"](lns_object, ctl, [], thy):
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
    if lns_object.callables["repair"](lns_object, ctl, [], thy):
        new_opt_val = lns_object.callables["calc_opt_value"](
            lns_object.models["new_model"]
        )
        print(f"Initial solution found with opt_val: {new_opt_val}")
        lns_object.models["current_model"] = lns_object.models["new_model"].copy()
        lns_object.models["best_model"] = lns_object.models["new_model"].copy()
        return True
    print("No first solution found.")
    return False


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

"""
Library of functions used for LNS.
"""

# pylint: disable=protected-access
import random
from typing import Dict, List, Sequence, Tuple

import clingo
from clingo.symbol import Number, SymbolType


def on_model(lns_object, model: clingo.solving.Model) -> None:
    """
    Saves shown and true atoms of model and aggregates optimization values.

    :param model: Model found during solving.
    :type model: clingo.solving.Model
    """
    lns_object._model = {}
    lns_object._model["shown"] = model.symbols(shown=True)
    lns_object._model["true"] = model.symbols(atoms=True)

    if lns_object._best_model:
        print(
            lns_object.get_variability(
                lns_object._model["shown"], lns_object._best_model["shown"]
            )
        )


def relax_declarative(
    model: Dict[str, Sequence[clingo.symbol.Symbol]], relax_rate: float
) -> List[Tuple[clingo.symbol.Symbol, bool]]:
    """
    Relax selected atoms given by the relax_rate.

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
    Get opt value of given model.

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


# pylint: disable=dangerous-default-value, unused-argument
def check_acceptance_classic(
    lns_object,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    old_model: Dict[str, Sequence[clingo.symbol.Symbol]] = {},
) -> bool:
    """
    Check whether new model is accepted.

    :param new_model: New model checked for acceptance.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param old_model: Old model optionally used for comparison.
    :type old_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was accepted or not.
    :rtype: bool
    """
    new_opt_val = lns_object.callable_dict["calc_opt_value"](new_model)
    if new_opt_val < lns_object._best_val:
        return True
    return False


# pylint: disable=dangerous-default-value, unused-argument
def check_acceptance_always(
    lns_object,
    new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    old_model: Dict[str, Sequence[clingo.symbol.Symbol]] = {},
) -> bool:
    """
    Check whether new model is accepted.

    :param new_model: New model checked for acceptance.
    :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :param old_model: Old model optionally used for comparison.
    :type old_model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Whether new model was accepted or not.
    :rtype: bool
    """
    return True


def better_solution_found_classic(lns_object, ctl: clingo.control.Control) -> None:
    """
    What to do if better solution was found.

    :param ctl: Clingo control object used for solving.
    :type ctl: clingo.control.Control
    """
    lns_object._best_val = lns_object.callable_dict["calc_opt_value"](lns_object._model)
    lns_object._best_model = lns_object._model.copy()
    print(f"New opt_val: {lns_object._best_val}")


def better_solution_found_hard_constraint(
    lns_object, ctl: clingo.control.Control
) -> None:
    """
    What to do if better solution was found.

    :param ctl: Clingo control object used for solving.
    :type ctl: clingo.control.Control
    """
    lns_object._best_val = lns_object.callable_dict["calc_opt_value"](lns_object._model)
    lns_object._best_model = lns_object._model.copy()
    print(f"New opt_val: {lns_object._best_val}")

    # update boundary
    ctl.ground([("opt_val", [Number(lns_object._best_val)])])

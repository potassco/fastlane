"""
Different relaxation methods for LNS.
"""

import random
from typing import Any

import clingo

from mod_lns import Model


def relax_declarative(
    model: Model,
    relax_parameters: dict[str, Any],
) -> list[tuple[clingo.symbol.Symbol, bool]]:
    """
    Relax portion of selected atoms given by the relax_rate.
    ASP encoding has to contain `_lns_select/1` and `_lns_fix/2` predicates.

    :param model: model.
    :type model: Model
    :param relax_parameters: Parameters used to determine relaxed atoms.
    :type relax_parameters: dict[str, Any]
    :return: Fixed (not relaxed) atoms.
    :rtype: list[tuple[clingo.symbol.Symbol, bool]]
    """
    fixed_atoms = []
    selected_atoms = []
    declared_fixed_atoms: dict[
        clingo.symbol.Symbol, list[tuple[clingo.symbol.Symbol, bool]]
    ] = {}
    for atom in model.true:
        if atom.match("_lns_select", 1):
            if atom.arguments[0] not in selected_atoms:
                selected_atoms.append(atom.arguments[0])
                declared_fixed_atoms[atom.arguments[0]] = []
        elif atom.match("_lns_fix", 2):
            if atom.arguments[1] in declared_fixed_atoms:
                declared_fixed_atoms[atom.arguments[1]].append(
                    (atom.arguments[0], True)
                )
    if len(selected_atoms) == 1:
        symbols = selected_atoms.copy()
    else:
        symbols = random.sample(
            selected_atoms,
            int(len(selected_atoms) * (1 - relax_parameters["relax_rate"])),
        )
    for s in symbols:
        fixed_atoms += random.sample(
            declared_fixed_atoms[s],
            int(
                len(declared_fixed_atoms[s]) * (1 - relax_parameters["base_relax_rate"])
            ),
        )
    return fixed_atoms


def relax_random(
    model: Model,
    relax_parameters: dict[str, Any],
) -> list[tuple[clingo.symbol.Symbol, bool]]:
    """
    Relax random number of shown atoms given by the relax_rate.

    :param model: model.
    :type model: Model
    :param relax_parameters: Parameters used to determine relaxed atoms.
    :type relax_parameters: dict[str, Any]
    :return: Fixed (not relaxed) atoms.
    :rtype: list[tuple[clingo.symbol.Symbol, bool]]
    """
    fixed_atoms = []
    sample = random.sample(
        model.shown, int(len(model.shown) * (1 - relax_parameters["relax_rate"]))
    )
    for atom in sample:
        fixed_atoms.append((atom, True))
    return fixed_atoms

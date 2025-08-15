"""
Different relaxation methods for LNS.
"""

import random

import clingo
from clingo import Symbol

from mod_lns import Model


def relax_declarative(
    model: Model,
    relax_rate: int,
) -> list[tuple[clingo.symbol.Symbol, bool]]:
    """
    Relax portion of selected atoms given by the relax_rate.
    ASP encoding has to contain `_lns_select/1` and `_lns_fix/2` predicates.

    :param model: model.
    :type model: Model
    :param relax_rate: Percentage of atoms to relax.
    :type relax_rate: int
    :return: Fixed (not relaxed) atoms.
    :rtype: list[Symbol]
    """
    fixed_atoms: list[Symbol] = []
    selected_atoms: list[Symbol] = []
    declared_fixed_atoms: dict[clingo.symbol.Symbol, list[Symbol]] = {}
    # !inefficient
    for atom in model.true:
        # get possible selection
        if atom.match("_lns_select", 1):
            if atom.arguments[0] not in selected_atoms:
                selected_atoms.append(atom.arguments[0])
                declared_fixed_atoms[atom.arguments[0]] = []
        # associate selecttion with fixed atoms
        elif atom.match("_lns_fix", 2):
            if atom.arguments[1] in declared_fixed_atoms:
                declared_fixed_atoms[atom.arguments[1]].append(atom.arguments[0])
    # sample selection atoms
    if len(selected_atoms) == 1:
        symbols = selected_atoms.copy()
    else:
        symbols = random.sample(
            selected_atoms,
            round(len(selected_atoms) * (1 - relax_rate / 100)),
        )
    # fix corresponding atoms
    for s in symbols:
        fixed_atoms += declared_fixed_atoms[s]
    return fixed_atoms


def relax_random(
    model: Model,
    relax_rate: int,
) -> list[Symbol]:
    """
    Relax random number of shown atoms given by the relax_rate.

    :param model: model.
    :type model: Model
    :param relax_rate: Percentage of atoms to relax.
    :type relax_rate: int
    :return: Fixed (not relaxed) atoms.
    :rtype: list[Symbol]
    """
    fixed_atoms = random.sample(
        model.shown, round(len(model.shown) * (1 - relax_rate / 100))
    )
    return fixed_atoms

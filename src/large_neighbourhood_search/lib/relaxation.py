"""
Different relaxation methods for LNS.
"""

import random
from typing import Any, Dict, List, Sequence, Tuple, Union

import clingo


def relax_declarative(
    model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]],
    relax_parameters: Dict[str, Any],
) -> List[Tuple[clingo.symbol.Symbol, bool]]:
    """
    Relax portion of selected atoms given by the relax_rate.
    ASP encoding has to contain `_lns_select/1` and `_lns_fix/2` predicates.

    :param model: Dictionary containing list of shown and true atoms.
    :type model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
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
    symbols = random.sample(
        selected_atoms, int(len(selected_atoms) * (1 - relax_parameters["relax_rate"]))
    )
    for s in symbols:
        fixed_atoms += declared_fixed_atoms[s]
    return fixed_atoms


def relax_random(
    model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]],
    relax_parameters: Dict[str, Any],
) -> List[Tuple[clingo.symbol.Symbol, bool]]:
    """
    Relax random number of shown atoms given by the relax_rate.

    :param model: Dictionary containing list of shown and true atoms.
    :type model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
    :param relax_parameters: Parameters used to determine relaxed atoms.
    :type relax_parameters: Dict[str, Any]
    :return: Fixed (not relaxed) atoms.
    :rtype: List[Tuple[clingo.symbol.Symbol, bool]]
    """
    fixed_atoms = []
    sample = random.sample(
        model["shown"], int(len(model["shown"]) * (1 - relax_parameters["relax_rate"]))
    )
    for atom in sample:
        fixed_atoms.append((atom, True))
    return fixed_atoms

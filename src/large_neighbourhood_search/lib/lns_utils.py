"""
Collection of utility functions used for LNS.
"""

from typing import Dict, Sequence

import clingo
from clingo.symbol import SymbolType


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
        if atom.match("_opt", 2):
            opt = atom.arguments[1].arguments
            if opt[0].type is SymbolType.Number and opt[1].type is SymbolType.Number:
                opt_val += opt[0].number * opt[1].number
    return opt_val


def calculate_variability(list1: Sequence, list2: Sequence) -> float:
    """
    Calculate variability of two lists.

    0 - no variability (same lists or bigger one contains smaller one)

    1 - completely different

    :param list1: First list.
    :type list1: Sequence
    :param list2: Second list.
    :type list2: Sequence
    :return: Variability of both lists.
    :rtype: float
    """
    len1 = len(list1)
    len2 = len(list2)
    if len1 < len2:
        return 1 - len(set(list1).intersection(list2)) / len1
    return 1 - len(set(list2).intersection(list1)) / len2

"""
Collection of utility functions used for LNS.
"""

from typing import Dict, Sequence

import clingo
from clingo.symbol import SymbolType


def calc_opt_val_weighted_sum(model: Dict[str, Sequence[clingo.symbol.Symbol]]) -> int:
    """
    Get optimization value of given model using weighted sum.

    :param model: Model.
    :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Opt value of given model.
    :rtype: int
    """
    opt_val = 0
    for atom in model["true"]:
        if atom.match("_lns_penalty", 3):
            if atom.arguments[2].type is SymbolType.Number:
                opt_val += atom.arguments[2].number
    return opt_val


def calc_opt_val_lexicographic(
    model: Dict[str, Sequence[clingo.symbol.Symbol]]
) -> Dict[int, int]:
    """
    Get optimization value of given model using lexicographic ordering.

    :param model: Model.
    :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
    :return: Opt value of given model.
    :rtype: Dict[int, int]
    """
    priorities: Dict[str, int] = {}
    temp_val: Dict[str, int] = {}
    opt_val: Dict[int, int] = {}
    for atom in model["true"]:
        if atom.match("_lns_priority", 2):
            if (
                atom.arguments[0].type is SymbolType.String
                and atom.arguments[1].type is SymbolType.Number
            ):
                priorities[atom.arguments[0].string] = atom.arguments[1].number
        elif atom.match("_lns_penalty", 3):
            if (
                atom.arguments[0].type is SymbolType.String
                and atom.arguments[2].type is SymbolType.Number
            ):
                temp_val[atom.arguments[0].string] = (
                    temp_val.get(atom.arguments[0].string, 0) + atom.arguments[2].number
                )

    for item in priorities.items():
        opt_val[item[1]] = opt_val.get(item[1], 0) + temp_val.get(item[0], 0)
    return opt_val


def check_smaller_lexicographic(
    opt_val1: Dict[int, int], opt_val2: Dict[int, int]
) -> bool:
    """
    Check whether opt_val1 is smaller than opt_val2.

    :param opt_val1: Optimization dictionary.
    :type opt_val1: Dict[int, int]
    :param opt_val2: Optimization dictionary.
    :type opt_val2: Dict[int, int]
    :return: whether opt_val1 is smaller than opt_val2.
    :rtype: bool
    """
    for i in sorted(list(set(opt_val1.keys()) | set(opt_val2.keys())), reverse=True):
        if opt_val1.get(i, 0) != opt_val2.get(i, 0):
            return opt_val1.get(i, 0) < opt_val2.get(i, 0)
    return False


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

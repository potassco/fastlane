"""
Collection of utility functions used for LNS.
"""

from typing import Dict, List, Sequence, Tuple

import clingo


def check_smaller_lexicographic(cost1: Dict[int, int], cost2: Dict[int, int]) -> bool:
    """
    Check whether cost1 is smaller than cost2.

    :param cost1: Optimization dictionary.
    :type cost1: Dict[int, int]
    :param cost2: Optimization dictionary.
    :type cost2: Dict[int, int]
    :return: whether cost1 is smaller than cost2.
    :rtype: bool
    """
    for i in sorted(list(set(cost1.keys()) | set(cost2.keys())), reverse=True):
        if cost1.get(i, 0) != cost2.get(i, 0):
            return cost1.get(i, 0) < cost2.get(i, 0)
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


def fix_symbols(
    symbols: List[clingo.symbol.Symbol],
) -> List[Tuple[clingo.symbol.Symbol, bool]]:
    """
    Prepare symbols to be used as assumptions (being fixed).

    :param symbols: Symbols to be used.
    :type symbols: List[clingo.symbol.Symbol]
    :return: Fixed symbols/atoms.
    :rtype:  List[Tuple[clingo.symbol.Symbol, bool]]
    """
    fixed = []
    for symbol in symbols:
        fixed.append((symbol, True))
    return fixed

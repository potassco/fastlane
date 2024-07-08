"""
Collection of utility functions used for LNS.
"""

from typing import Dict

import clingo
from clingo.symbol import SymbolType


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

"""
Components related to constrained optimization in the context of LNS.
"""

import math


def get_opt_bound(cost: list[int], opt_mode: str, opt_modifier: str, opt_nf: int | float) -> str:
    """
    Calculate bound for next step.

    :param cost: Current cost list
    :type cost: list[int]
    :return: String representing the bound for the next step.
    :rtype: str
    """
    if opt_modifier == "static":
        return opt_mode + "," + str(opt_nf)
    elif opt_modifier == "dynamic":
        bound = cost[:-1]
        bound.append(math.ceil(cost[-1] + abs(cost[-1]) * float(opt_nf) / 100) - 1)
        return opt_mode + "," + (",".join([str(i) for i in bound]))
    return opt_mode

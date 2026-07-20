"""
Components related to constrained optimization in the context of LNS.
"""

import math


def get_opt_bound(cost: list[int], opt_mode: str, opt_modifier: str = "dynamic", opt_nf: str = "0") -> str:
    """
    Calculate bound for next step.

    :param cost: Current cost list
    :param opt_mode: Optimization mode
    :param opt_modifier: Optimization modifier
    :default opt_modifier: "dynamic"
    :param opt_nf: Optimization factor
    :default opt_nf: "0"
    :return: String representing the bound for the next step.
    """
    if opt_modifier == "static":
        return opt_mode + "," + opt_nf
    if opt_modifier == "dynamic":
        bound = cost[:-1]
        bound.append(math.ceil(cost[-1] + abs(cost[-1]) * float(opt_nf) / 100) - 1)
        return opt_mode + "," + (",".join([str(i) for i in bound]))
    return opt_mode

"""
Utility functions.
"""

from typing import Any, Dict


# pylint: disable=unidiomatic-typecheck
def get_cost_str(model: Dict[str, Any]) -> str:
    """
    Get cost of given model as string.
    :param model: Model.
    :type model: Dict[str, Any]
    :return: Cost as string.
    :rtype: str
    """
    cost = model["cost"]
    if type(cost) is int:
        return str(cost)
    if type(cost) is dict:
        return " ".join(list(map(str, cost.values())))
    return ""


def print_model(model: Dict[str, Any]) -> str:
    """
    Print given model.

    :param model: Model.
    :type model: Dict[str, Any]
    :return: Printed string.
    :rtype: str
    """
    answer_string = " ".join([str(atom) for atom in model["shown"]])
    if "assignments" in model:
        answer_string += "\nAssignments:\n" + " ".join(model["assignments"])
    s = "Answer\n" f"{answer_string}\n" f"Cost: {get_cost_str(model)}\n"
    print(s)
    return s

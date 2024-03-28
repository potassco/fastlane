"""
The parameter file handling.
"""

import json
import re
from typing import Any, Dict, List, Union


def save_param_file(params: Dict, json_file: str) -> None:
    """
    Save parameters to .json file.

    :param param: Parameters to be saved.
    :type param: Dict
    :param json_file: Parameter file to be saved.
    :type json_file: str
    """
    with open(json_file, "w", encoding="utf-8") as file:
        json.dump(params, file, ensure_ascii=False, indent=4)
        file.close()


def gen_example_params(path: str) -> None:
    """
    Generate example parameter file.

    :param path: Directory of the example parameter file.
    :type path: str
    """
    # name of parameter file
    name = "example_params"

    # relaxation mode: declarative, random
    r_mode = "declarative"
    # relax rates
    rates = [0.2, 0.4, 0.6]
    # switch relax rates after threshold
    threshold = 3

    # search mode: hard_constraint, classic
    s_mode = "hard_constraint"

    # bound mode: overall, per_improvement
    b_mode = "overall"
    # bound type: steps, time
    b_type = "steps"
    # bound value (steps or seconds)
    b_value = 2000

    seed = None

    parameters: Dict[
        str,
        Union[
            str,
            int,
            None,
            Dict[str, Union[str, int, List[float], Dict[str, Union[str, int]]]],
        ],
    ] = {
        "name": name,
        "relaxation": {"mode": r_mode, "rates": rates, "threshold": threshold},
        "search": {
            "mode": s_mode,
            "bound": {"mode": b_mode, "type": b_type, "value": b_value},
        },
        "seed": seed,
    }
    save_param_file(parameters, path + "/example_params.json")


def parse_pos_int(string: str) -> bool:
    """
    Check if input string is positive integer.

    :param string: String to be checked.
    :type string: str
    :return: Whether input string was a positive integer or not.
    :rtype: bool
    """
    m = re.match(r"\+?\d+", string)
    if m is None:
        return False
    return True


def parse_rate(string: str) -> bool:
    """
    Check if input string is valid relax rate.

    :param string: String to be checked.
    :type string: str
    :return: Whether input string was a valid relax rate or not.
    :rtype: bool
    """
    m = re.match(r"\+?0.\d+", string)
    if m is None:
        return False
    return True


def selection_input(values: List, description: str) -> Any:
    """
    Offer a selection for user input.

    :param values: Offered values for selection.
    :type values: List
    :param description: Description presented to the user.
    :type description: str
    :return: Selected value.
    :rtype: Any
    """
    while True:
        selection = input(f"{description}\n")
        if selection in [str(i) for i in range(len(values))]:
            return values[int(selection)]
        print("Please select a valid option.")


def pos_int_input(description: str, none_allowed: bool = False) -> Union[int, None]:
    """
    Positive integer user input.

    :param description: Description presented to the user.
    :type description: str
    :param none_allowed: Whether None is a valid input or not.
    :type none_allowed: bool
    :default none_allowed: False
    :return: Positive integer.
    :rtype: Union[int, None]
    """
    while True:
        pos_int = input(f"{description}\n")
        if none_allowed and pos_int in ["None", "none"]:
            return None
        if parse_pos_int(pos_int):
            return int(pos_int)
        if none_allowed:
            print("Please enter a valid positive integer or None.")
        else:
            print("Please enter a valid positive integer.")


def create_param_file(path: str) -> None:
    """
    Create new parameter file.

    :param path: Directory of the new parameter file.
    :type path: str
    """
    f = True
    # name of parameter file
    print(f"Creating new parameter file at {path}")
    name = input("Name of the new parameter file:\n")

    # relaxation mode: random, declarative
    r_mode = selection_input(
        ["random", "declarative"], "Relax mode: 0: random, 1: declarative"
    )

    # relax rates
    print(
        "All possible relax rates used during LNS.\nTo stop adding new rates, please type 0."
    )
    rate = None
    rates: List[float] = []
    while rate != "0":
        f = True
        while f:
            rate = input(
                (
                    f"Current rates: {rates}\n"
                    "Add additional relax rate: 0 < relax rate < 1\n"
                )
            )
            if rate == "0":
                break
            if parse_rate(rate):
                rates.append(float(rate))
                f = False
            else:
                print("Please enter a valid relax rate between 0 and 1")
    f = True

    # switch relax rates after threshold
    threshold = pos_int_input(
        "Number of solutions without improvement before switching relax rates:"
    )

    # search mode: hard_const, classic
    s_mode = selection_input(
        ["hard_constraint", "classic"], "Search mode: 0: hard constraint, 1: classic"
    )

    # bound mode: overall, per_improv
    b_mode = selection_input(
        ["overall", "per_improvement"], "Bound mode: 0: overall, 1: per improvement"
    )

    # bound type: steps, time
    b_type = selection_input(
        ["steps", "time"], "Bound type: 0: number of steps, 1: time"
    )

    # bound value (steps or seconds)
    b_value = pos_int_input("Value of the bound:")

    # seed
    seed = pos_int_input("Seed, 'None' for no seed:", True)

    parameters: Dict[
        str,
        Union[
            str,
            int,
            None,
            Dict[
                str,
                Union[str, int, List[float], Dict[str, Union[str, int, None]], None],
            ],
        ],
    ] = {
        "name": name,
        "relaxation": {"mode": r_mode, "rates": rates, "threshold": threshold},
        "search": {
            "mode": s_mode,
            "bound": {"mode": b_mode, "type": b_type, "value": b_value},
        },
        "seed": seed,
    }
    save_param_file(parameters, path + name + ".json")


def load_param_file(json_file: str) -> Dict:
    """
    Load parameters from json file, overwriting all other options.

    :param json_file: Parameter file to be loaded.
    :type json_file: str
    :return: parameters from parameter file
    :rtype: Dict
    """
    with open(json_file, encoding="utf-8") as json_data:
        parameters = json.load(json_data)
        json_data.close()
    return parameters

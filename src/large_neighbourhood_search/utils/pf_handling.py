"""
The parameter file handling.
"""

import json
import re

def gen_example_params(path: str):
    """
    Generate example parameter file.

    :param path: Directory of the example parameter file.
    :type path: str
    """
    params = {}
    # name of parameter file
    params["name"] = "example_params"
    params["relaxation"] = {}
    # relaxation mode: declarative, random
    params["relaxation"]["mode"] = "declarative"
    # relax rates
    params["relaxation"]["rates"] = [0.2, 0.4, 0.6]
    # switch relax rates after threshold
    params["relaxation"]["threshold"] = 3

    params["search"] = {}
    # search mode: hard_constraint, classic
    params["search"]["mode"] = "hard_constraint"

    params["search"]["bound"] = {}
    # bound mode: overall, per_improvement
    params["search"]["bound"]["mode"] = "overall"
    # bound type: steps, time
    params["search"]["bound"]["type"] = "steps"
    # bound value (steps or seconds)
    params["search"]["bound"]["value"] = 2000

    params["seed"] = None

    with open(path + "/example_params.json", "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=4)
        f.close()


def parse_pos_int(string: str):
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


def parse_rate(string: str):
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


def selection_input(values: list, description: str):
    """
    Offer a selection for user input.

    :param values: Offered values for selection.
    :type values: list
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


def pos_int_input(description: str, none_allowed: bool = False):
    """
    Positive integer user input.

    :param description: Description presented to the user.
    :type description: str
    :param none_allowed: Whether None is a valid input or not.
    :type none_allowed: bool
    :default none_allowed: False
    :return: Positive integer.
    :rtype: Optional[int]
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


def create_param_file(path: str):
    """
    Create new parameter file.

    :param path: Directory of the new parameter file.
    :type path: str
    """
    f = True
    parameters = {}
    # name of parameter file
    print(f"Creating new parameter file at {path}")
    name = input("Name of the new parameter file:\n")
    parameters["name"] = name
    parameters["relaxation"] = {}

    # relaxation mode: random, declarative
    parameters["relaxation"]["mode"] = selection_input(
        ["random", "declarative"], "Relax mode: 0: random, 1: declarative"
    )

    # relax rates
    print(
        "All possible relax rates used during LNS.\nTo stop adding new rates, please type 0."
    )
    rate = None
    parameters["relaxation"]["rates"] = []
    while rate != "0":
        f = True
        while f:
            rates = parameters["relaxation"]["rates"]
            rate = input(
                (
                    f"Current rates: {rates}\n"
                    "Add additional relax rate: 0 < relax rate < 1\n"
                )
            )
            if rate == "0":
                break
            if parse_rate(rate):
                parameters["relaxation"]["rates"].append(float(rate))
                f = False
            else:
                print("Please enter a valid relax rate between 0 and 1")
    f = True

    # switch relax rates after threshold
    parameters["relaxation"]["threshold"] = pos_int_input(
        "Number of solutions without improvement before switching relax rates:"
    )

    parameters["search"] = {}
    # search mode: hard_const, classic
    parameters["search"]["mode"] = selection_input(
        ["hard_constraint", "classic"], "Search mode: 0: hard constraint, 1: classic"
    )

    parameters["search"]["bound"] = {}
    # bound mode: overall, per_improv
    parameters["search"]["bound"]["mode"] = selection_input(
        ["overall", "per_improvement"], "Bound mode: 0: overall, 1: per improvement"
    )

    # bound type: steps, time
    parameters["search"]["bound"]["type"] = selection_input(
        ["steps", "time"], "Bound type: 0: number of steps, 1: time"
    )

    # bound value (steps or seconds)
    parameters["search"]["bound"]["value"] = pos_int_input("Value of the bound:")

    # seed
    parameters["seed"] = pos_int_input("Seed, 'None' for no seed:", True)

    with open(path + name + ".json", "w", encoding="utf-8") as f:
        json.dump(parameters, f, ensure_ascii=False, indent=4)
        f.close()


def load_param_file(json_file: str):
    """
    Load parameters from json file, overwriting all other options.

    :param json_file: Parameter file to be loaded.
    :type json_file: str
    """
    with open(json_file, encoding="utf-8") as json_data:
        parameters = json.load(json_data)
        json_data.close()
    return parameters

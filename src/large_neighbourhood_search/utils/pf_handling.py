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
    # mode: decl, rndm
    params["relaxation"]["mode"] = "decl"
     # relax rates
    params["relaxation"]["rates"] = [0.2, 0.4, 0.6]
    # switch relax rates after threshold
    params["relaxation"]["threshold"] = 3

    params["search"] = {}
    # mode: hard_const, classic
    params["search"]["mode"] = "hard_const"
        
    params["search"]["bound"] = {}
    # mode: overall, per_improv
    params["search"]["bound"]["mode"] = "overall"
    # type: steps, time
    params["search"]["bound"]["type"] = "steps"
    # value (steps or seconds)
    params["search"]["bound"]["value"] = 2000

    params["seed"] = None

    with open(path+"/example_params.json", 'w', encoding='utf-8') as f:
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
    m = re.match(rf'\+?\d+', string)
    if m is None:
        return False
    else:
        return True

def parse_rate(string: str):
    """
    Check if input string is valid relax rate.

    :param string: String to be checked.
    :type string: str
    :return: Whether input string was a valid relax rate or not.
    :rtype: bool
    """
    m = re.match(rf'\+?0.\d+', string)
    if m is None:
        return False
    else:
        return True

def create_param_file(path: str):
    """
    Create new parameter file.

    :param path: Directory of the new parameter file.
    :type path: str
    """
    f = True
    params = {}
    # name of parameter file
    print("Creating new parameter file at {}".format(path))
    name = input("Name of the new parameter file:\n")
    params["name"] = name
    params["relaxation"] = {}

    # mode: decl, rndm
    while f:
        mode = input("Relax mode: 0: declarative, 1: random\n")
        if mode == "0":
            params["relaxation"]["mode"] = "decl"
            f = False
        elif mode == "1":
            params["relaxation"]["mode"] = "rndm"
            f = False
        else:
            print("Please select a valid mode.")
    f = True

    # relax rates
    print("All possible relax rates used during LNS.\nTo stop adding new rates, please type 0.")
    rate = None
    params["relaxation"]["rates"] = []
    while rate != "0":
        f = True
        while f:
            rate = input("Current rates: {}\nAdd additional relax rate: 0 < relax rate < 1\n".format( params["relaxation"]["rates"]))
            if rate == "0":
                break
            elif parse_rate(rate):
                params["relaxation"]["rates"].append(float(rate))
                f = False
            else:
                print("Please enter a valid relax rate between 0 and 1")
    f = True

    # switch relax rates after threshold
    while f:
        thresh = input("Number of solutions without improvement before switching relax rates:\n")
        if parse_pos_int(thresh):
            params["relaxation"]["threshold"] = int(thresh)
            f = False
        else:
            print("Please enter a valid positive integer.")
    f = True

    params["search"] = {}
    # mode: hard_const, classic
    while f:
        mode = input("Search mode: 0: hard constraints, 1: classic\n")
        if mode == "0":
            params["search"]["mode"] = "hard_const"
            f = False
        elif mode == "1":
            params["search"]["mode"] = "classic"
            f = False
        else:
            print("Please select a valid mode.")
    f = True
        
    params["search"]["bound"] = {}
    # mode: overall, per_improv
    while f:
        mode = input("Bound mode: 0: overall, 1: per improvement\n")
        if mode == "0":
            params["search"]["bound"]["mode"] = "overall"
            f = False
        elif mode == "1":
            params["search"]["bound"]["mode"] = "per_improv"
            f = False
        else:
            print("Please select a valid mode.")
    f = True
    
    # type: steps, time
    while f:
        mode = input("Bound type: 0: number of steps, 1: time\n")
        if mode == "0":
            params["search"]["bound"]["type"] = "steps"
            f = False
        elif mode == "1":
            params["search"]["bound"]["type"] = "time"
            f = False
        else:
            print("Please select a valid mode.")
    f = True
    
    # value (steps or seconds)
    while f:
        bound = input("Value of the bound:\n")
        if parse_pos_int(bound):
            params["search"]["bound"]["value"] = int(bound)
            f = False
        else:
            print("Please enter a valid positive integer.")
    f = True
    
    while f:
        seed = input("Seed, 'None' for no seed:\n")
        if seed in ["None","none"]:
            params["seed"] = None
            f = False
        elif parse_pos_int(seed):
            params["seed"] = int(seed)
            f = False
        else:
            print("Please enter a valid positive integer or 'None'.")
    f = True
    
    with open(path+name+".json", 'w', encoding='utf-8') as f:
        json.dump(params, f, ensure_ascii=False, indent=4)
        f.close()
      
def load_param_file(json_file: str):
    """
    Load parameters from json file, overwriting all other options.

    :param json_file: Parameter file to be loaded.
    :type json_file: str
    """
    with open(json_file) as json_data:
        params = json.load(json_data)
        json_data.close()
    return params

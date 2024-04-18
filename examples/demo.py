"""
Example on how to use the LNS api.
"""
from typing import Any, Callable, Dict

import large_neighbourhood_search

import large_neighbourhood_search.lib.lns_functions as lns_f


# callables for classic LNS with random relaxation limited by the number of stops
random_classic: Dict[str, Callable] = {
            "on_model": lns_f.on_model,
            "relax": lns_f.relax_random,
            "repair": lns_f.repair,
            "calc_opt_value": lns_f.calculate_opt_val,
            "get_first_solution": lns_f.get_first_solution_classic,
            "check_accept": lns_f.check_accept_always,
            "check_better": lns_f.check_better_classic,
            "better_solution_found": lns_f.better_solution_found_classic,
            "boundary_handling": lns_f.boundary_overall,
            "check_stop": lns_f.check_stop_steps,
        }

# set boundary to 3000 (in this case steps)
# switch to the next relax rate after new models did not improve the solution 3 times
config: Dict[str, Any] = {
            "bound": 3000,
            "switch_rr_after_no_improv": 3,
        }

def main():
    lns = large_neighbourhood_search.LNS(["./examples/golf.lp"], random_classic, 42, [0.2, 0.4, 0.6])
    lns.set_params(config)
    lns.main()

if __name__ == "__main__":
    main()
"""
Example on how to use the LNS api.
"""
from typing import Any, Callable, Dict

from large_neighbourhood_search import LNS
from large_neighbourhood_search.lib import boundary, lns_utils, search, theory

# callables for classic LNS with random relaxation limited by the number of stops
random_classic: Dict[str, Callable] = {
            "setup": theory.setup_clingo,
            "relax": search.relax_random,
            "repair": theory.repair_clingo,
            "calc_opt_value": lns_utils.calculate_opt_val,
            "get_first_solution": search.get_first_solution_hard_constraint,
            "check_accept": search.check_accept_always,
            "check_better": search.check_better_always,
            "better_solution_found": search.better_solution_found_hard_constraint,
            "boundary_handling": boundary.boundary_overall,
            "check_stop": boundary.check_stop_steps,
            "finish": boundary.finish,
        }

# set boundary to 3000 (in this case steps)
# switch to the next relax rate after new models did not improve the solution 3 times
config: Dict[str, Any] = {
            "seed": None,
            "relax_rates": [0.2, 0.4, 0.6],
            "bound": 3000,
            "switch_rr_after_no_improv": 3,
        }

def main():
    lns = LNS(["./examples/golf.lp"], random_classic)
    lns.set_params(config)
    lns.main()

if __name__ == "__main__":
    main()
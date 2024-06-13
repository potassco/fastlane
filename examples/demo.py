"""
Example on how to use the LNS framework.
"""
from typing import Any, Callable, Dict

from large_neighbourhood_search import LNS
from large_neighbourhood_search.lib import boundary, lns_utils, search, theory

# callables for classic LNS with random relaxation limited by the number of steps
clingo_classic_rndm_ws: Dict[str, Callable] = {
            "setup": theory.setup_clingo,
            "get_first_solution": search.get_first_solution_classic,
            "relax": search.relax_random,
            "repair": theory.repair_clingo,
            "check_accept": search.check_accept_always,
            "check_better": search.check_better_weighted_sum,
            "check_stop": boundary.check_stop_steps,
            "calc_opt_value": lns_utils.calc_opt_val_weighted_sum,
            "better_solution_found": search.better_solution_found_classic,
            "boundary_handling": boundary.boundary_overall,
            "finish": boundary.finish,
            "check_stuck": search.check_stuck_never,
            "is_stuck": search.is_stuck,
            "timeout": search.timeout,
        }

# callables for LNS using clingo-dl and hard constraints with random declarative relaxation limited by the number of steps
clingodl_hc_decl_lex: Dict[str, Callable] = {
            "setup": theory.setup_clingo_dl,
            "get_first_solution": search.get_first_solution_hc_lexicographic,
            "relax": search.relax_declarative,
            "repair": theory.repair_clingo_dl,
            "check_accept": search.check_accept_always,
            "check_better": search.check_better_always,
            "check_stop": boundary.check_stop_steps,
            "calc_opt_value": lns_utils.calc_opt_val_lexicographic,
            "better_solution_found": search.better_solution_found_hc_lexicographic,
            "boundary_handling": boundary.boundary_overall,
            "finish": boundary.finish,
            "check_stuck": search.check_stuck,
            "is_stuck": search.is_stuck,
            "timeout": search.timeout,
        }

# callables for LNS using hard constraints with random relaxation limited by the number of steps
clingo_hc_rndm_ws: Dict[str, Callable] = {
            "setup": theory.setup_clingo,
            "get_first_solution": search.get_first_solution_hc_weighted_sum,
            "relax": search.relax_random,
            "repair": theory.repair_clingo,
            "check_accept": search.check_accept_always,
            "check_better": search.check_better_always,
            "check_stop": boundary.check_stop_steps,
            "calc_opt_value": lns_utils.calc_opt_val_weighted_sum,
            "better_solution_found": search.better_solution_found_hc_weighted_sum,
            "boundary_handling": boundary.boundary_overall,
            "finish": boundary.finish,
            "check_stuck": search.check_stuck_never,
            "is_stuck": search.is_stuck,
            "timeout": search.timeout,
}

# set parameters
config: Dict[str, Any] = {
            "seed": 456,
            "relax_rates": [0.2, 0.4, 0.6],
            "max_steps": 2000,
            "switch_rr_after_no_improv": 3,
            "clingo_args": {"rand-freq": 0.8},
            "time_limit": 2,
            "overall_time_limit": 600,
        }

def main():
    lns = LNS(["./examples/golf.lp"], clingo_classic_rndm_ws)
    lns.set_params(config)
    lns.main()

if __name__ == "__main__":
    main()
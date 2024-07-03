from typing import Any, Dict, Sequence

import clingo


# replace LNS class in __init__
class LNS:
    def __init__(self, files, solver, strategy, params):
        self._solver = solver
        self._strategy = strategy

        new_model: Dict[str, Sequence[clingo.symbol.Symbol]] = {}
        current_model: Dict[str, Sequence[clingo.symbol.Symbol]] = {}
        best_model: Dict[str, Sequence[clingo.symbol.Symbol]] = {}
        self.models: Dict[str, Any] = {
            "new_model": new_model,
            "current_model": current_model,
            "best_model": best_model,
        }

        self.costs: Dict[str, Any] = {
            "new_cost": None,
            "current_cost": None,
            "best_cost": None,
        }

    def main(self):
        self._solver.setup()
        # c, b, n: current, best, new model
        # c = first sol
        # while check_stop
        #   n = repair(relax(c))
        #   check accept(n)
        #       c = n
        #   check better
        #       b = n

        # s     "setup": theory.setup_clingo,
        # st    "get_first_solution": search.get_first_solution_hc_weighted_sum,
        # st u   "relax": search.relax_random,
        # s st  "repair": theory.repair_clingo,
        # st    "check_accept": search.check_accept_always,
        # st    "check_better": search.check_better_always,
        # st    "check_stop": boundary.check_stop_steps,
        # st    "calc_opt_value": lns_utils.calc_opt_val_weighted_sum,
        #       "better_solution_found": search.better_solution_found_hc_weighted_sum,
        # --    "boundary_handling": boundary.boundary_overall,
        # --    "finish": boundary.finish,
        #       "check_stuck": search.check_stuck_never,
        #       "is_stuck": search.is_stuck,
        # --    "timeout": search.timeout,

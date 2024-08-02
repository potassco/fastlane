"""
Example on how to use the LNS framework.
"""
from typing import Any, Dict

from large_neighbourhood_search import LNS
from large_neighbourhood_search.lib.solvers.clingo_solver import ClingoSolver
from large_neighbourhood_search.lib.solvers.clingo_dl_solver import ClingoDLSolver
from large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd import (
    ClassicWeightedSumRnd
)
from large_neighbourhood_search.lib.solvers.clingo_heu_solver import ClingoHeuSolver
from large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd import HCWeightedSumRnd
from large_neighbourhood_search.lib.strategies.classic_lexicographic_declarative import (
    ClassicLexiDecl
)

# classic LNS with random relaxation using clingo and weighted sum
def config1():
    solver = ClingoSolver()
    strategy = ClassicWeightedSumRnd()
    return solver, strategy

# LNS using clingo-dl and hard constraints with random relaxation and weighted sum
def config2():
    solver = ClingoDLSolver()
    strategy = HCWeightedSumRnd()
    return solver, strategy

# classic LNS with random declarative relaxation using clingo and lexicographic optimization
def config3():
    solver = ClingoSolver()
    strategy = ClassicLexiDecl()
    return solver, strategy

# LNS using heuristic clingo and hard constraints with random relaxation and weighted sum
def config4():
    solver = ClingoHeuSolver()
    strategy = HCWeightedSumRnd()
    return solver, strategy

# additional parameters
params: Dict[str, Any] = {
            "seed": 456,
            "relax_rate": 0.2,
            "max_steps": 2000,
            "clingo_args": {"rand-freq": 0.8},
            "solve_time_limit": 2,
            "overall_time_limit": 600,
        }

def main():
    solver, strategy = config4()
    lns = LNS(["./examples/golf.lp"], solver, strategy, params)
    lns.main()

if __name__ == "__main__":
    main()
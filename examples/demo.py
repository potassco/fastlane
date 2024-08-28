"""
Examples on how to use the LNS framework.

Check out the Guide section in the documentation for
a step by step introduction.
"""
from typing import Any, Dict

from large_neighbourhood_search import LNS
from large_neighbourhood_search.lib.solvers.clingo_solver import ClingoSolver
from large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd import (
    ClassicWeightedSumRnd
)
from large_neighbourhood_search.lib.solvers.clingo_heu_solver import ClingoHeuSolver
from large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd import HCWeightedSumRnd
from large_neighbourhood_search.lib.relaxation import relax_declarative
from large_neighbourhood_search.lib.utils import symbol_to_str

# classic LNS with random relaxation using clingo with assumptions and weighted sum
def config1():
    solver = ClingoSolver()
    strategy = ClassicWeightedSumRnd()
    params: Dict[str, Any] = {
        "seed": 123,
        "relax_rate": 0.2,
    }
    return solver, strategy, params

def config1_1():
    solver = ClingoSolver()
    strategy = ClassicWeightedSumRnd()
    params: Dict[str, Any] = {
        "seed": 123,
        "relax_rate": 0.4,
    }
    return solver, strategy, params

# LNS using clingo with assumptions and hard constraints with random relaxation and weighted sum
def config2():
    solver = ClingoSolver()
    strategy = HCWeightedSumRnd()
    params: Dict[str, Any] = {
            "seed": 123,
            "solve_time_limit": 10,
        }
    return solver, strategy, params

# classic LNS with random relaxation using clingo with heuristics and weighted sum
def config3():
    solver = ClingoHeuSolver()
    strategy = ClassicWeightedSumRnd()
    params: Dict[str, Any] = {
        "seed": 123,
        "stuck_after_no_improv": 300,
    }
    return solver, strategy, params

# LNS using clingo with heuristics and hard constraints with random relaxation and weighted sum
def config3_1():
    solver = ClingoHeuSolver()
    strategy = HCWeightedSumRnd()
    params: Dict[str, Any] = {
        "seed": 123,
        "solve_time_limit": 10,
        "stuck_after_no_improv": 300,
    }
    return solver, strategy, params

# Implementation of classic LNS with declarative relaxation and weighted sum
class ClassicWeightedSumDecl(ClassicWeightedSumRnd):
    def relax(self, model, relax_parameters):
        r = relax_declarative(model, relax_parameters)
        #for s in r:
        #    print(symbol_to_str(s[0]))
        #print("--")
        return r

# classic LNS with declarative relaxation using clingo with assumptions and weighted sum
def config4():
    solver = ClingoSolver()
    strategy = ClassicWeightedSumDecl()
    params: Dict[str, Any] = {
        "seed": 123,
    }
    return solver, strategy, params

def config4_1():
    solver = ClingoSolver()
    strategy = ClassicWeightedSumDecl()
    params: Dict[str, Any] = {
        "seed": 123,
        "max_steps": 8,
    }
    return solver, strategy, params

def main():
    solver, strategy, params = config1()
    lns = LNS(["examples/golf_demo.lp"], solver, strategy, params)
    lns.main()

if __name__ == "__main__":
    main()
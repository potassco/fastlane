"""
Examples on how to use the LNS framework.

Check out the Guide section in the documentation for
a step by step introduction.
"""
from typing import Any, Dict

from mod_lns import LNS
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.relaxation import relax_declarative
from mod_lns.utils.conversions import symbol_to_str

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


from mod_lns.lns_config import LNSConfig

def main():
    #solver, strategy, params = config1()
    #lns = LNS(["examples/golf_demo.lp"], solver, strategy, params)
    #lns.main()
    config = LNSConfig(lns_options={"hc":True,"decl":False, "heu":False})
    lns = LNS(["examples/golf_demo.lp"], config)
    lns.main()

if __name__ == "__main__":
    main()
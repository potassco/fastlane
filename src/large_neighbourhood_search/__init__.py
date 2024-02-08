"""
The large_neighbourhood_search project.
"""

import random
import clingo
from clingo.symbol import Number, SymbolType

class LNS(clingo.Application):
    
    def __init__(self, seed, bnb_search):
        """
        Initialize application.
        """
        self.program_name = "lns"
        self.version = "0.1"

        self._model = None
        self._best_model = None
        self._opt_val = None
        self._bnb_search = bnb_search
        self._seed = seed
    
    def _on_model(self, model):
        """
        Saves shown atoms of model and aggregates optimization values.  
        """
        self._model = model.symbols(shown=True)
        self._opt_val = 0

        for atom in model.symbols(atoms=True):
            if (atom.match("_minimize", 2) and 
                atom.arguments[0].type is SymbolType.Number):
                    self._opt_val += atom.arguments[0].number

    def relax(self, atoms: list[clingo.Symbol], relax_rate: float = 0.2):
        """
        Relax random number of atoms given by the relax_rate.

        Returns remaining atoms.
        """
        fixed_atoms = []
        for atom in atoms:
                if random.randint(0,1) > relax_rate:
                    fixed_atoms.append((atom, True))
        return fixed_atoms
    
    def repair(self, ctl: clingo.Control, assumptions: list):
        """
        Solve under given assumptions.
        """
        return ctl.solve(assumptions=assumptions, on_model=self._on_model)
    
    def main(self, ctl, files):
        """
        Run Large-Neighbourhood Search.
        """
        # set seed if given
        if self._seed is not None:
             random.seed(self._seed)
        
        relax_rate = 0.2
        if self._bnb_search:
             relax_rate = 1
        
        if not files: files = ["-"]
        for path in files: ctl.load(path)
        
        # add constraint to force better solution with each iteration
        # encoding has to contain _minimize(V,I) predicates as minimization criteria
        # where V: value, I: identifier
        ctl.add("opt_val", ["o"], 
                ":- #sum{V,I: _minimize(V,I)} >= o.")
        ctl.ground([("base", [])], context=self)

        # get first solution
        if ctl.solve(on_model=self._on_model).satisfiable:
                print("New opt_val: {}".format(self._opt_val))
                ctl.ground([("opt_val", [Number(self._opt_val)])])
                self._best_model = self._model
        else:
            print("No first solution found.")
            return

        # perform LNS
        s = 0
        while True:
            s += 1
            #print(s)
            
            # relax model
            assumptions = self.relax(self._best_model, relax_rate)
            # reconstruct model, if new solution is satisfiable: better solution has been found
            if self.repair(ctl, assumptions).satisfiable:
                print("New opt_val: {}".format(self._opt_val))
                self._best_model = self._model
                # update boundary
                ctl.ground([("opt_val", [Number(self._opt_val)])])
            # stop criterion, WIP
            if s == 200 or self._opt_val == 0:
                print("Answer:\n{}\nopt_val: {}".format(" ".join([str(atom) for atom in self._best_model]), self._opt_val))
                break
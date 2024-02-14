"""
The large_neighbourhood_search project.
"""

import random
import clingo
from clingo.symbol import Number, SymbolType

class LNS(clingo.Application):
    
    def __init__(self, files: list[str], clingo_args: list[str] = [], seed: float = 0.2, bnb_search: bool = False, declarative: bool = False):
        """
        Initialize application.
        """
        self.program_name = "lns"
        self.version = "0.1"

        self._files = files
        self._clingo_args = clingo_args
        self._seed = seed
        self._bnb_search = bnb_search
        self._decl = declarative

        self._model = None
        self._best_model = None
        
        self._select = None
        self._fix = None

        self._opt_val = None
    
    def _on_model(self, model):
        """
        Saves shown atoms of model and aggregates optimization values.

        Extracts selected and fixed atoms from model if declarative mode is selected.
        """
        self._model = model.symbols(shown=True)
        self._opt_val = 0

        self._select = []
        self._fix = {}

        for atom in model.symbols(atoms=True):
            if (atom.match("_minimize", 2) and 
                atom.arguments[0].type is SymbolType.Number):
                    self._opt_val += atom.arguments[0].number
            if self._decl:
                if (atom.match("_lns_select", 1)):
                    self._select.append(atom.arguments[0])
                    self._fix[atom.arguments[0]] = []
                elif (atom.match("_lns_fix", 2)):
                    self._fix[atom.arguments[1]].append((atom.arguments[0], True))

    def relax(self, atoms: list[clingo.Symbol], relax_rate: float = 0.2):
        """
        Relax random number of shown atoms given by the relax_rate.

        Returns non-relaxed (fixed) atoms.
        """
        fixed_atoms = []
        for atom in atoms:
                if random.randint(0,1) > relax_rate:
                    fixed_atoms.append((atom, True))
        return fixed_atoms
    
    def decl_relax(self, select: list[clingo.Symbol], fix_dict: dict[clingo.Symbol, list[clingo.Symbol]], relax_rate: float = 0.2):
        """
        Fix random number of selected atoms, relax the rest.

        Arguments:
        select -- List of Symbols S corresponding to _lns_select(S)
        fix_dict -- Dictionary of lists of symbols S' with symbols S as key, corresponding to _lns_fix(S',S)
        relax_rate -- Percentage of selected atoms to be relaxed (not fixed)

        Returns fixed atoms.
        """
        fixed_atoms = []
        for sym in select:
            if random.randint(0,1) > relax_rate:
                fixed_atoms += fix_dict[sym]
        return fixed_atoms


    def repair(self, ctl: clingo.Control, assumptions: list):
        """
        Solve under given assumptions.
        """
        return ctl.solve(assumptions=assumptions, on_model=self._on_model)
    
    def main(self):
        """
        Run Large-Neighbourhood Search.
        """
        ctl = clingo.Control(self._clingo_args)
        if not self._files: self._files = ["-"]
        for path in self._files: ctl.load(path)
        
        # set seed if given
        if self._seed is not None:
            random.seed(self._seed)
        
        relax_rate = 0.2
        if self._bnb_search:
            print("Running branch-and-bound search.")
            relax_rate = 1       
        elif self._decl:
            print("Running with declarative relaxation with a rate of {}.".format(relax_rate))
        else:
            print("Running with random relaxation of shown atoms with a rate of {}.".format(relax_rate))
        
        # add constraint to force better solution with each iteration
        # encoding has to contain _minimize(V,I) predicates as minimization criteria
        # where V: value, I: identifier
        ctl.add("opt_val", ["o"], 
                ":- #sum{V,I: _minimize(V,I)} >= o.")
        ctl.ground([("base", [])], context=self)

        # get first solution
        if ctl.solve(on_model=self._on_model).satisfiable:
                print("Initial solution found with opt_val: {}".format(self._opt_val))
                ctl.ground([("opt_val", [Number(self._opt_val)])])
                self._best_model = self._model
        else:
            print("No first solution found.")
            return
        
        # perform LNS
        s = 0
        while True:
            s += 1
            print("{}:".format(s))
            
            # relax model
            if self._decl:
                assumptions = self.decl_relax(self._select, self._fix, relax_rate)
            else:
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
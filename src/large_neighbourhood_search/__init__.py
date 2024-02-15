"""
The large_neighbourhood_search project.
"""

import random
import json
import clingo
from clingo.symbol import Number, SymbolType

class LNS(clingo.Application):
    
    def __init__(self, 
                 files: list[str], 
                 clingo_args: list[str] = [], 
                 seed: int = None,
                 relax_rate: float = 0.2, 
                 bnb_search: bool = False, 
                 declarative: bool = False):
        """
        Initialize application.
        """
        self.program_name = "lns"
        self.version = "0.1"

        self._files = files
        self._clingo_args = clingo_args
        self._seed = seed
        self._relax_rates = [relax_rate]
        self._relax_rate = relax_rate
        self._unsat_treshold = 3

        self._bnb_search = bnb_search
        self._decl = declarative

        # 0: hard const, 1: classic
        self._search_mode = 0
        self._bound = 200


        self._model = None
        self._best_model = None
        
        self._select = None
        self._fix = None

        self._opt_val = None

    def load_param_file(self, json_file: str):
        """
        Load parameters from json file, overwriting all other options.
        """
        with open(json_file) as json_data:
            params = json.load(json_data)
            json_data.close()

        self._relax_rates = params["relaxation"]["rates"]
        self._relax_rate = self._relax_rates[0]
        if params["relaxation"]["mode"] in ["decl", "rndm"]:
            if params["relaxation"]["mode"] == "decl":
                self._decl = True
            else:
                self._decl = False
        else:
            pass
            # TODO throw invalid input error
        
        if params["search"]["mode"] == "hard_const":
            self._search_mode = 0
        else:
            pass
            # TODO throw invalid input error
        
        self._bound = params["search"]["bound"]
        return


    def _on_model(self, model):
        """
        Saves shown atoms of model and aggregates optimization values.

        Extracts selected and fixed atoms from model if declarative mode is selected.
        """
        self._model = model.symbols(shown=True)
        self._opt_val = 0

        self._select = []
        self._fix = {}

        if self._best_model:
            print(self.get_varibility(self._model, self._best_model))

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
        x = ctl.solve(assumptions=assumptions, on_model=self._on_model)
        return x
    
    def get_varibility(self, list1: list, list2:list):
        """
        Calculate varibility of two lists.

        0 - no variability (same lists or bigger one contains smaller one)
        1 - completely different
        """
        len1 = len(list1)
        len2 = len(list2)
        if len1 < len2:
            return 1 - len(set(list1).intersection(list2))/len1
        else:
            return 1 - len(set(list2).intersection(list1))/len2

    def get_stats(self, ctl: clingo.Control):
        """
        Method to obtain different stats from the last solver call.
        """
        conflicts = ctl.statistics["solvers"]["conflicts"]
        return conflicts

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
        
        if self._bnb_search:
            print("Running branch-and-bound search.")
            self._relax_rate = 1       
        elif self._decl:
            print("Running with declarative relaxation with a rate of {}.".format(self._relax_rate))
        else:
            print("Running with random relaxation of shown atoms with a rate of {}.".format(self._relax_rate))
        
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
        unsat_c = 0
        while True:
            s += 1
            print("step {} with rate {}:".format(s,self._relax_rate))
            
            # relax model
            if self._decl:
                assumptions = self.decl_relax(self._select, self._fix, self._relax_rate)
            else:
                assumptions = self.relax(self._best_model, self._relax_rate)
            # reconstruct model, if new solution is satisfiable: better solution has been found
            if self.repair(ctl, assumptions).satisfiable:
                print("New opt_val: {}".format(self._opt_val))
                
                self._best_model = self._model                
                # update boundary
                ctl.ground([("opt_val", [Number(self._opt_val)])])
            else:
                unsat_c += 1
            # change relax_rate after unsat_treshold amount of unsat solutions
            self._relax_rate = self._relax_rates[unsat_c//self._unsat_treshold%len(self._relax_rates)]
            # stop criterion, WIP
            if s == self._bound or self._opt_val == 0:
                print("Answer:\n{}\nopt_val: {}".format(" ".join([str(atom) for atom in self._best_model]), self._opt_val))
                break
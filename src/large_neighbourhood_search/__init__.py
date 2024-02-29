"""
The large_neighbourhood_search project.
"""

import random
import json
import clingo
from clingo.symbol import Number, SymbolType

class LNS(clingo.Application):
    """
    Clingo application performing LNS.

    :param files: Problem encoding.
    :type files: str
    :param clingo_args: Additional clingo arguments.
    :type clingo_args: list[str]
    :default clingo_args: []
    :param seed: Seed used for random relaxation.
    :type seed: int
    :default seed: None
    :param relax_rate: Singular relax rate used for LNS (1>RR>0).
    :type relax_rate: float
    :default relax_rate: 0.2
    :param bnb_search: Enables branch-and-bound search instead of LNS (RR=1).
    :type bnb_search: bool
    :default bnb_search: False
    :param declarative: Enables declarative relaxation mode. Otherwise random relaxation is used.
    :type declarative: bool
    :default declarative: False
    """
    
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
        self._unsat_threshold = 3

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
        self._best_val = None

    def load_params(self, json_file: str):
        """
        Load parameters from json file, overwriting all other options.

        :param json_file: Parameter file to be loaded.
        :type json_file: str
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

        :param model: Model found during solving.
        :type model: clingo.solving.Model
        """
        self._model = model.symbols(shown=True)
        self._opt_val = 0

        self._select = []
        self._fix = {}

        if self._best_model:
            print(self.get_variability(self._model, self._best_model))

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

    def relax(self, atoms: list[clingo.Symbol], relax_rate: float):
        """
        Relax random number of shown atoms given by the relax_rate.

        :param atoms: Symbols to choose from for relaxation.
        :type atoms: list[clingo.Symbol]
        :param relax_rate: Percentage of atoms to be relaxed.
        :type relax_rate: float
        :return: Fixed (not relaxed) atoms.
        :rtype: list[clingo.Symbol]
        """
        fixed_atoms = []
        for atom in atoms:
                if random.randint(0,1) > relax_rate:
                    fixed_atoms.append((atom, True))
        return fixed_atoms
    
    def decl_relax(self, select: list[clingo.Symbol], fix_dict: dict[clingo.Symbol, list[clingo.Symbol]], relax_rate: float):
        """
        Fix random number of selected atoms, relax the rest.

        :param select: List of Symbols S corresponding to _lns_select(S).
        :type select: list[clingo.Symbol]
        :param fix_dict: Dictionary of lists of symbols S' with symbols S as key, corresponding to _lns_fix(S',S).
        :type fix_dict: dict[clingo.Symbol, list[clingo.Symbol]]
        :param relax_rate: Percentage of selected atoms to be relaxed (not fixed).
        :type relax_rate: float
        :return: Fixed (not relaxed) atoms.
        :rtype: list[clingo.Symbol]
        """
        fixed_atoms = []
        for sym in select:
            if random.randint(0,1) > relax_rate:
                fixed_atoms += fix_dict[sym]
        return fixed_atoms


    def repair(self, ctl: clingo.Control, assumptions: list):
        """
        Solve under given assumptions.

        :param ctl: Clingo Control object used for solving.
        :type ctl: clingo.Control
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple(clingo.Symbol, True)]
        :return: Result of solving call.
        :rtype: clingo.solving.SolveResult
        """
        x = ctl.solve(assumptions=assumptions, on_model=self._on_model)
        return x
    
    def LNS_hard_cons(self, ctl: clingo.Control):
        """
        Run LNS using hard constraints.

        :param ctl: Clingo Control Object used for solving.
        :type ctl: clingo.Control
        """
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
            self._relax_rate = self._relax_rates[unsat_c//self._unsat_threshold%len(self._relax_rates)]
            # stop criterion, WIP
            if s == self._bound or self._opt_val == 0:
                print("Answer:\n{}\nopt_val: {}".format(" ".join([str(atom) for atom in self._best_model]), self._opt_val))
                return
    
    def LNS_classic(self, ctl: clingo.Control):
        """
        Run classic LNS.

        :param ctl: Clingo Control Object used for solving.
        :type ctl: clingo.Control
        """
        ctl.ground([("base", [])], context=self)
        # get first solution
        if ctl.solve(on_model=self._on_model).satisfiable:               
                print("Initial solution found with opt_val: {}".format(self._opt_val))
                self._best_val = self._opt_val            
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
            if self.repair(ctl, assumptions).satisfiable and self._opt_val < self._best_val:
                print("New opt_val: {}".format(self._opt_val))
                
                self._best_val = self._opt_val
                self._best_model = self._model                
            else:
                unsat_c += 1
            # change relax_rate after unsat_treshold amount of unsat solutions
            self._relax_rate = self._relax_rates[unsat_c//self._unsat_threshold%len(self._relax_rates)]
            # stop criterion, WIP
            if s == self._bound or self._opt_val == 0:
                print("Answer:\n{}\nopt_val: {}".format(" ".join([str(atom) for atom in self._best_model]), self._best_val))
                return

    def get_variability(self, list1: list, list2:list):
        """
        Calculate variability of two lists.

        0 - no variability (same lists or bigger one contains smaller one)

        1 - completely different

        :param list1: First list.
        :type list1: list
        :param list2: Second list.
        :type list2: list
        :return: Variability of both lists.
        :rtype: float
        """
        len1 = len(list1)
        len2 = len(list2)
        if len1 < len2:
            return 1 - len(set(list1).intersection(list2))/len1
        else:
            return 1 - len(set(list2).intersection(list1))/len2

    def get_stats(self, ctl: clingo.Control):
        """
        WIP Method to obtain different stats from the last solver call.

        :param ctl: Clingo Control object used for solving.
        :type ctl: clingo.Control
        :return: Conflict statistics
        """
        conflicts = ctl.statistics["solvers"]["conflicts"]
        return conflicts

    def main(self):
        """
        Run Large-Neighbourhood Search according to set parameters.
        """
        if self._search_mode==1:
            self._clingo_args.append("--rand-freq=0.5")

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
        
        match self._search_mode:
            case 0:
                self.LNS_hard_cons(ctl)
            case 1:
                self.LNS_classic(ctl)
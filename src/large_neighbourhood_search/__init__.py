"""
The large_neighbourhood_search project.
"""

import random
import clingo
import time
from clingo.symbol import Number, SymbolType
from .utils.pf_handling import load_param_file

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
    :param param_path: Location of parameter file.
    :type param_path: str
    :default param_path: None
    """
    
    def __init__(self, 
                 files: list[str], 
                 clingo_args: list[str] = [], 
                 seed: int = None,
                 relax_rate: float = 0.2, 
                 bnb_search: bool = False, 
                 declarative: bool = False,
                 param_path: str = None):
        """
        Initialize application.
        """
        self.program_name = "lns"
        self.version = "0.2"

        self._files = files
        self._clingo_args = clingo_args
        self._seed = seed
        self._relax_rates = [relax_rate]
        self._relax_rate = relax_rate
        self._unsat_threshold = 3

        self._bnb_search = bnb_search
        self._decl = declarative

        self.param_path = param_path

        # 0: hard const, 1: classic
        self._search_mode = 1
        # 0: overall, 1: per_improv
        self._bound_mode = 0
        # 0: steps, 1: time
        self._bound_type = 0
        self._bound = 2000


        self._model = None
        self._best_model = None

        self._opt_val = None
        self._best_val = None

    def load_params(self, json_file: str):
        """
        Load parameters from json file, overwriting all other options.

        :param json_file: Parameter file to be loaded.
        :type json_file: str
        """
        params = load_param_file(json_file)
        r_params = params["relaxation"]
        s_params = params["search"]
        b_params = s_params["bound"]
        # relaxation
        if r_params["mode"] in ["decl", "rndm"]:
            if r_params["mode"] == "decl":
                self._decl = True
            else:
                self._decl = False
        else:
            pass
            # TODO throw invalid input error
        
        self._relax_rates = r_params["rates"]
        self._relax_rate = self._relax_rates[0]
        self._unsat_threshold = r_params["threshold"]
        
        # search
        # 0: hard_cons 1: classic
        if s_params["mode"] == "hard_const":
            self._search_mode = 0
        elif s_params["mode"] == "classic":
            self._search_mode = 1
        else:
            pass
            # TODO throw invalid input error
        
        # bound
        # 0: overall, 1: per_improv
        if b_params["mode"] == "overall":
            self._bound_mode = 0
        elif b_params["mode"] == "per_step":
            self._bound_mode = 1
        else:
            pass
            # TODO throw invalid input error
        # 0: steps, 1: time
        if b_params["type"] == "steps":
            self._bound_type = 0
        elif b_params["type"] == "time":
            self._bound_type = 1
        else:
            pass
            # TODO throw invalid input error
        self._bound = b_params["value"]

        self._seed = params["seed"]
        return


    def _on_model(self, model):
        """
        Saves shown and true atoms of model and aggregates optimization values.

        :param model: Model found during solving.
        :type model: clingo.solving.Model
        """
        self._model = {}
        self._model["shown"] = model.symbols(shown=True)
        self._model["true"] = model.symbols(atoms=True)
        self._opt_val = 0

        if self._best_model:
            print(self.get_variability(self._model["shown"], self._best_model["shown"]))

        for atom in model.symbols(atoms=True):
            if (atom.match("_minimize", 2) and atom.arguments[0].type is SymbolType.Number):
                    self._opt_val += atom.arguments[0].number
    

    def relax(self, model: dict, relax_rate: float):
        """
        Relax random number of shown or selected (declarative mode) atoms given by the relax_rate.

        :param model: Dictionary containing list of shown and true atoms.
        :type model: dict{str: list[clingo.Symbol]}
        :param relax_rate: Percentage of atoms to be relaxed.
        :type relax_rate: float
        :return: Fixed (not relaxed) atoms.
        :rtype: list[clingo.Symbol]
        """
        fixed_atoms = []
        if self._decl:
            select = []
            fix = {}
            for atom in model["true"]:
                if (atom.match("_lns_select", 1)):
                    select.append(atom.arguments[0])
                    fix[atom.arguments[0]] = []
                elif (atom.match("_lns_fix", 2)):
                    fix[atom.arguments[1]].append((atom.arguments[0], True))
            for sym in select:
                if random.randint(0,1) > relax_rate:
                    fixed_atoms += fix[sym]
        else:
            for atom in model["shown"]:
                if random.randint(0,1) > relax_rate:
                    fixed_atoms.append((atom, True))
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
        # load parameters if needed
        if self.param_path:
            self.load_params(self.param_path)
            
        # classic mode
        if self._search_mode == 1:
            self._clingo_args.append("--rand-freq=0.8")

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
        
        # hard_cons mode
        if self._search_mode == 0:
            # add constraint to force better solution with each iteration
            # encoding has to contain _minimize(V,I) predicates as minimization criteria
            # where V: value, I: identifier
            ctl.add("opt_val", ["o"], 
                    ":- #sum{V,I: _minimize(V,I)} >= o.")
        ctl.ground([("base", [])], context=self)

        # get first solution
        if ctl.solve(on_model=self._on_model).satisfiable:               
                print("Initial solution found with opt_val: {}".format(self._opt_val))
                if self._search_mode == 0:
                    ctl.ground([("opt_val", [Number(self._opt_val)])])
                self._best_val = self._opt_val              
                self._best_model = self._model.copy()
        else:
            print("No first solution found.")
            return
        
        ## perform LNS 
        # overall step counter and time
        s = 0
        start_time = time.time()
        # step counter and time per improvement
        sc = 0
        improv_start_time = start_time
        # unsat counter
        unsat_c = 0
        while True:
            s += 1
            sc += 1
            if self._bound_type == 0:
                print("{}|{}, relax rate {}:".format(sc, self._bound, self._relax_rate))
            if self._bound_type == 1:
                print("{:.3f}s, relax rate {}:".format(time.time()-improv_start_time, self._relax_rate))
                
            # relax model
            assumptions = self.relax(self._best_model, self._relax_rate)

            # reconstruct model
            # hard_cons mode: if new solution is satisfiable -> better solution
            # classic mode: check if opt value better
            if self.repair(ctl, assumptions).satisfiable:
                if self._search_mode == 0 or (self._search_mode == 1 and self._opt_val < self._best_val):
                    print("New opt_val: {}".format(self._opt_val))
                
                    if self._bound_mode == 1:
                        sc = 0
                        improv_start_time = time.time()
                    self._best_val = self._opt_val
                    self._best_model = self._model.copy()
                    if self._search_mode == 0:              
                        # update boundary
                        ctl.ground([("opt_val", [Number(self._opt_val)])])
            else:
                unsat_c += 1
            # change relax_rate after unsat_threshold amount of unsat solutions
            self._relax_rate = self._relax_rates[unsat_c//self._unsat_threshold%len(self._relax_rates)]
            # stop criterion, WIP
            if (self._bound_type == 0 and (sc >= self._bound or self._best_val == 0)) or (self._bound_type == 1 and (time.time()-improv_start_time >= self._bound or self._best_val == 0)):
                end_time = time.time()
                print("Answer:\n{}\nFinal opt_val: {}\nOverall steps: {}\nOverall time: {:.3f}s".format(" ".join([str(atom) for atom in self._best_model["shown"]]), self._best_val, s, end_time-start_time))
                break

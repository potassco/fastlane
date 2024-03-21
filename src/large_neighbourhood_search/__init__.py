"""
The large_neighbourhood_search project.
"""

import random
import time
from typing import Dict, List, Sequence, Tuple, Union

import clingo
from clingo.symbol import Number, SymbolType

from .utils.pf_handling import load_param_file


class LNS:  # pylint: disable=too-many-instance-attributes
    """
    Clingo application performing LNS.

    :param files: Problem encoding.
    :type files: List[str]
    :param clingo_args: Additional clingo arguments.
    :type clingo_args: Union[List[str], None]
    :default clingo_args: None
    :param seed: Seed used for random relaxation.
    :type seed: Union[int, None]
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
    :type param_path: Union[str, None]
    :default param_path: None
    """

    def __init__(
        self,
        files: List[str],
        clingo_args: Union[List[str], None] = None,
        seed: Union[int, None] = None,
        relax_rate: float = 0.2,
        bnb_search: bool = False,
        declarative: bool = False,
        param_path: Union[str, None] = None,
    ) -> None:
        """
        Initialize application.
        """
        self.program_name = "lns"
        self.version = "0.2"

        self._files = files
        if clingo_args is None:
            clingo_args = []
        self._clingo_args = clingo_args
        self._seed = seed
        self._relax_rates = [relax_rate]
        self._relax_rate = relax_rate
        self._unsat_threshold = 3

        self._bnb_search = bnb_search
        self._relax_mode = "random"
        if declarative:
            self._relax_mode = "declarative"

        self.param_path = param_path

        self._search_mode = "hard_constraint"
        self._bound_mode = "overall"
        self._bound_type = "steps"
        self._bound = 2000

        self._model: Dict[str, Sequence[clingo.symbol.Symbol]] = {}
        self._best_model: Dict[str, Sequence[clingo.symbol.Symbol]] = {}

        self._opt_val: int = -1
        self._best_val: int = -1

    def load_params(self, json_file: str) -> None:
        """
        Load parameters from json file, overwriting all other options.
        Invalid parameters are ignored.

        :param json_file: Parameter file to be loaded.
        :type json_file: str
        """
        parameters = load_param_file(json_file)
        relaxation_parameters = parameters["relaxation"]
        search_parameters = parameters["search"]
        bound_parameters = search_parameters["bound"]
        # relaxation
        if relaxation_parameters["mode"] in ["declarative", "random"]:
            self._relax_mode = relaxation_parameters["mode"]

        self._relax_rates = relaxation_parameters["rates"]
        self._relax_rate = self._relax_rates[0]
        self._unsat_threshold = relaxation_parameters["threshold"]

        # search mode
        if search_parameters["mode"] in ["hard_constraint", "classic"]:
            self._search_mode = search_parameters["mode"]

        # bound mode
        if bound_parameters["mode"] in ["overall", "per_improvement"]:
            self._bound_mode = bound_parameters["mode"]

        # bound type
        if bound_parameters["type"] in ["steps", "time"]:
            self._bound_type = bound_parameters["type"]

        self._bound = bound_parameters["value"]

        self._seed = parameters["seed"]

    def _on_model(self, model: clingo.solving.Model) -> None:
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
            if (
                atom.match("_minimize", 2)
                and atom.arguments[0].type is SymbolType.Number
            ):
                self._opt_val += atom.arguments[0].number

    def relax(
        self, model: Dict[str, Sequence[clingo.symbol.Symbol]], relax_rate: float
    ) -> List[Tuple[clingo.symbol.Symbol, bool]]:
        """
        Relax random number of shown or selected (declarative mode) atoms given by the relax_rate.

        :param model: Dictionary containing list of shown and true atoms.
        :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
        :param relax_rate: Percentage of atoms to be relaxed.
        :type relax_rate: float
        :return: Fixed (not relaxed) atoms.
        :rtype: List[Tuple[clingo.symbol.Symbol, bool]]
        """
        fixed_atoms = []
        if self._relax_mode == "declarative":
            selected_atoms = []
            declared_fixed_atoms: dict[
                clingo.symbol.Symbol, list[tuple[clingo.symbol.Symbol, bool]]
            ] = {}
            for atom in model["true"]:
                if atom.match("_lns_select", 1):
                    selected_atoms.append(atom.arguments[0])
                    declared_fixed_atoms[atom.arguments[0]] = []
                elif atom.match("_lns_fix", 2):
                    declared_fixed_atoms[atom.arguments[1]].append(
                        (atom.arguments[0], True)
                    )
            for symbol in selected_atoms:
                if random.randint(0, 100) >= relax_rate * 100:
                    fixed_atoms += declared_fixed_atoms[symbol]
        elif self._relax_mode == "random":
            for atom in model["shown"]:
                if random.randint(0, 100) >= relax_rate * 100:
                    fixed_atoms.append((atom, True))
        return fixed_atoms

    def repair(
        self,
        ctl: clingo.control.Control,
        assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
    ) -> clingo.solving.SolveResult:
        """
        Solve under given assumptions.

        :param ctl: Clingo Control object used for solving.
        :type ctl: clingo..control.Control
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
        :return: Result of solving call.
        :rtype: clingo.solving.SolveResult
        """
        x = ctl.solve(assumptions=assumptions, on_model=self._on_model)
        return x

    def get_variability(self, list1: Sequence, list2: Sequence) -> float:
        """
        Calculate variability of two lists.

        0 - no variability (same lists or bigger one contains smaller one)

        1 - completely different

        :param list1: First list.
        :type list1: Sequence
        :param list2: Second list.
        :type list2: Sequence
        :return: Variability of both lists.
        :rtype: float
        """
        len1 = len(list1)
        len2 = len(list2)
        if len1 < len2:
            return 1 - len(set(list1).intersection(list2)) / len1
        return 1 - len(set(list2).intersection(list1)) / len2

    def get_stats(self, ctl: clingo.control.Control) -> Dict:
        """
        WIP Method to obtain different stats from the last solver call.

        :param ctl: Clingo Control object used for solving.
        :type ctl: clingo.control.Control
        :return: Conflict statistics
        :rtype: Dict
        """
        # conflicts = ctl.statistics["solvers"]["conflicts"]
        return ctl.statistics

    def setup(self) -> clingo.control.Control:
        """
        Initialize Control object and prepare LNS.

        :return: Control object used for LNS
        :rytpe: clingo.control.Control
        """
        # load parameters if needed
        if self.param_path:
            self.load_params(self.param_path)

        # classic mode
        if self._search_mode == "classic":
            self._clingo_args.append("--rand-freq=0.8")

        ctl = clingo.Control(self._clingo_args)
        if not self._files:
            self._files = ["-"]
        for path in self._files:
            ctl.load(path)

        # set seed if given
        if self._seed is not None:
            random.seed(self._seed)
            self._clingo_args.append(f"--seed={self._seed}")

        if self._bnb_search:
            print("Running branch-and-bound search.")
            self._relax_rates = [1]
            self._relax_rate = 1
        elif self._relax_mode == "declarative":
            print(
                f"Running with declarative relaxation with a rate of {self._relax_rate}."
            )
        elif self._relax_mode == "random":
            print(
                f"Running with random relaxation of shown atoms with a rate of {self._relax_rate}."
            )
        return ctl

    def get_first_solution(self, ctl) -> bool:
        """
        Find initial solution.

        :param ctl: Control object used for search.
        :type ctl: clingo.control.Control
        :return: Whether a solution was found or not
        :rtype: bool
        """
        # hard_cons mode
        if self._search_mode == "hard_constraint":
            # add constraint to force better solution with each iteration
            # encoding has to contain _minimize(V,I) predicates as minimization criteria
            # where V: value, I: identifier
            ctl.add("opt_val", ["o"], ":- #sum{V,I: _minimize(V,I)} >= o.")
        ctl.ground([("base", [])], context=self)

        # get first solution
        if ctl.solve(on_model=self._on_model).satisfiable:
            print(f"Initial solution found with opt_val: {self._opt_val}")
            if self._search_mode == "hard_constraint":
                ctl.ground([("opt_val", [Number(self._opt_val)])])
            self._best_val = self._opt_val
            self._best_model = self._model.copy()
            return True
        print("No first solution found.")
        return False

    def print_step(self, step_for_improvement, improvement_start_time) -> None:
        """
        Print current step statistics.

        :param step_for_improvement: Step of current improvement.
        :type step_for_improvement: int
        :param improvement_start_time: Start time of current improvement
        :type improvement_start_time: float
        """
        if self._bound_type == "steps":
            print(
                f"{step_for_improvement}|{self._bound}, relax rate {self._relax_rate}:"
            )
        if self._bound_type == "time":
            print(
                f"{time.time() - improvement_start_time:.3f}s, relax rate {self._relax_rate}:"
            )

    def main(self) -> None:
        """
        Run Large-Neighbourhood Search according to set parameters.
        """
        # prepare clingo control
        ctl = self.setup()

        # get first solution
        if not self.get_first_solution(ctl):
            return

        # perform LNS
        # overall step counter and time
        step = 0
        start_time = time.time()
        # step counter and time per improvement
        step_for_improvement = 0
        improvement_start_time = start_time
        # unsat counter
        unsat_counter = 0
        while True:
            step += 1
            step_for_improvement += 1
            self.print_step(step_for_improvement, improvement_start_time)

            # relax model
            assumptions = self.relax(self._best_model, self._relax_rate)

            # reconstruct model
            if self.repair(ctl, assumptions).satisfiable:
                # hard_cons mode: if new solution is satisfiable -> better solution
                # classic mode: check if opt value better
                if self._search_mode == "hard_constraint" or (
                    self._search_mode == "classic" and self._opt_val < self._best_val
                ):
                    print(f"New opt_val: {self._opt_val}")

                    if self._bound_mode == "per_improvement":
                        step_for_improvement = 0
                        improvement_start_time = time.time()
                    self._best_val = self._opt_val
                    self._best_model = self._model.copy()
                    if self._search_mode == "hard_constraint":
                        # update boundary
                        ctl.ground([("opt_val", [Number(self._opt_val)])])
            else:
                unsat_counter += 1
            # change relax_rate after unsat_threshold amount of unsat solutions
            self._relax_rate = self._relax_rates[
                unsat_counter // self._unsat_threshold % len(self._relax_rates)
            ]
            # stop criterion, WIP
            if (
                (self._bound_type == "steps" and step_for_improvement >= self._bound)
                or (
                    self._bound_type == "time"
                    and time.time() - improvement_start_time >= self._bound
                )
                or self._best_val == 0
            ):
                end_time = time.time()
                answer_string = " ".join(
                    [str(atom) for atom in self._best_model["shown"]]
                )
                print(
                    (
                        "Answer\n"
                        f"{answer_string}\n"
                        f"Final opt_val: { self._best_val}\n"
                        f"Overall steps: {step}\n"
                        f"Overall time: {end_time - start_time:.3f}s"
                    )
                )
                break

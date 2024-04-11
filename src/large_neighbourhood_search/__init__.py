"""
The large_neighbourhood_search project.
"""

import random
import time
from typing import Any, Callable, Dict, List, Sequence, Union

import clingo
from clingo.symbol import Number

from .lib import lns_functions as lns_f
from .utils.pf_handling import load_param_file


# pylint: disable=too-many-instance-attributes
class LNS:
    """
    Class handling and  performing LNS.

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
        declarative: bool = False,
        param_path: Union[str, None] = None,
    ) -> None:
        """
        Initialize application.
        """
        self.program_name = "lns"
        self.version = "0.2"

        self._unsat_threshold = 3

        self._relax_mode = "random"

        self.param_path = param_path

        self._search_mode = "hard_constraint"
        self._bound_mode = "overall"
        self._bound_type = "steps"

        self.config_values: Dict[str, Any] = {
            "files": files,
            "seed": seed,
            "relax_rates": [relax_rate],
            "current_relax_rate": relax_rate,
            "bound": 2000,
            "switch_rr_after_unsat": 3,
        }
        if clingo_args is None:
            clingo_args = []
        self.config_values["clingo_args"] = clingo_args

        model: Dict[str, Sequence[clingo.symbol.Symbol]] = {}
        best_model: Dict[str, Sequence[clingo.symbol.Symbol]] = {}
        self.lns_values: Dict[str, Any] = {
            "model": model,
            "best_model": best_model,
            "best_opt_val": -1,
        }

        self.callable_dict: Dict[str, Callable] = {
            "on_model": lns_f.on_model,
            "relax": lns_f.relax_random,
            "repair": lns_f.repair,
            "calc_opt_value": lns_f.calculate_opt_val,
            "check_acceptance": lns_f.check_acceptance_always,
            "better_solution_found": lns_f.better_solution_found_hard_constraint,
            "boundary_handling": lns_f.boundary_overall,
            "check_stop": lns_f.check_stop_steps,
        }
        if declarative:
            self._relax_mode = "declarative"
            self.callable_dict["relax"] = lns_f.relax_declarative

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
            if self._relax_mode == "declarative":
                self.callable_dict["relax"] = lns_f.relax_declarative

        self.config_values["relax_rates"] = relaxation_parameters["rates"]
        self.config_values["current_relax_rate"] = self.config_values["relax_rates"][0]
        self.config_values["switch_rr_after_unsat"] = relaxation_parameters["threshold"]

        # search mode
        if search_parameters["mode"] in ["hard_constraint", "classic"]:
            self._search_mode = search_parameters["mode"]
            if self._search_mode == "classic":
                self.callable_dict["check_acceptance"] = lns_f.check_acceptance_classic
                self.callable_dict["better_solution_found"] = (
                    lns_f.better_solution_found_classic
                )

        # bound mode
        if bound_parameters["mode"] in ["overall", "per_improvement"]:
            self._bound_mode = bound_parameters["mode"]

        # bound type
        if bound_parameters["type"] in ["steps", "time"]:
            self._bound_type = bound_parameters["type"]

        self.config_values["bound"] = bound_parameters["value"]

        self.config_values["seed"] = parameters["seed"]

    def _on_model(self, model: clingo.solving.Model) -> None:
        """
        Call on_model method.

        :param model: Model found during solving.
        :type model: clingo.solving.Model
        """
        return self.callable_dict["on_model"](self, model)

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
            self.config_values["clingo_args"].append("--rand-freq=0.8")

        ctl = clingo.Control(self.config_values["clingo_args"])
        # no input files not supported
        # if not self._files:
        #    self._files = ["-"]
        for path in self.config_values["files"]:
            ctl.load(path)

        # set seed if given
        if self.config_values["seed"] is not None:
            random.seed(self.config_values["seed"])
            self.config_values["clingo_args"].append(
                f"--seed={self.config_values['seed']}"
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
            new_opt_val = self.callable_dict["calc_opt_value"](self.lns_values["model"])
            print(f"Initial solution found with opt_val: {new_opt_val}")
            if self._search_mode == "hard_constraint":
                ctl.ground([("opt_val", [Number(new_opt_val)])])
            self.lns_values["best_opt_val"] = new_opt_val
            self.lns_values["best_model"] = self.lns_values["model"].copy()
            return True
        print("No first solution found.")
        return False

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
        boundary_dict: Dict[str, Any] = {}
        self.callable_dict["boundary_handling"](self, boundary_dict, "init")
        while True:
            self.callable_dict["boundary_handling"](self, boundary_dict, "update")
            # self.print_step(
            #    limit_dict["step_for_improvement"], limit_dict["improvement_start_time"]
            # )

            # relax model
            assumptions = self.callable_dict["relax"](
                self.lns_values["best_model"], self.config_values["current_relax_rate"]
            )

            # reconstruct model
            if self.callable_dict["repair"](self, ctl, assumptions).satisfiable:
                # check acceptance
                if self.callable_dict["check_acceptance"](
                    self, self.lns_values["model"]
                ):

                    self.callable_dict["better_solution_found"](self, ctl)

                    self.callable_dict["boundary_handling"](
                        self, boundary_dict, "improvement"
                    )
                else:
                    self.callable_dict["boundary_handling"](
                        self, boundary_dict, "no_improvement"
                    )
            else:
                self.callable_dict["boundary_handling"](
                    self, boundary_dict, "no_improvement"
                )
            # change relax_rate after unsat_threshold amount of unsat solutions
            self.config_values["current_relax_rate"] = self.config_values[
                "relax_rates"
            ][
                boundary_dict["no_improvement"]
                // self.config_values["switch_rr_after_unsat"]
                % len(self.config_values["relax_rates"])
            ]
            # stop criterion, WIP
            if self.callable_dict["check_stop"](self, boundary_dict):
                end_time = time.time()
                answer_string = " ".join(
                    [str(atom) for atom in self.lns_values["best_model"]["shown"]]
                )
                print(
                    (
                        "Answer\n"
                        f"{answer_string}\n"
                        f"Final opt_val: { self.lns_values['best_opt_val']}\n"
                        f"Overall steps: {boundary_dict['step']}\n"
                        f"Overall time: {end_time - boundary_dict['start_time']:.3f}s"
                    )
                )
                break

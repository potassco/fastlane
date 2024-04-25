"""
The large_neighbourhood_search project.
"""

import time
from typing import Any, Callable, Dict, List, Sequence, Union

import clingo

from .lib import lns_functions as lns_f


# pylint: disable=dangerous-default-value
class LNS:
    """
    Class handling and  performing LNS.

    :param files: Problem encodings.
    :type files: List[str]
    :param callables: Functions used during LNS.
    :type callables: Dict[str, Callables]
    :default callables: {}
    :param seed: Seed used for random relaxation.
    :type seed: Union[int, None]
    :default seed: None
    :param relax_rates: Relax rates used during LNS (1>RR>0).
    :type relax_rate: List[float]
    :default relax_rate: [0.2]
    :param clingo_args: Additional clingo arguments.
    :type clingo_args: Union[List[str], None]
    :default clingo_args: None
    """

    def __init__(
        self,
        files: List[str],
        callables: Dict[str, Callable] = {},
        seed: Union[int, None] = None,
        relax_rates: List[float] = [0.2],
        clingo_args: Union[List[str], None] = None,
    ) -> None:
        """
        Initialize application.
        """
        self.program_name = "lns"
        self.version = "1.0"

        self.config_values: Dict[str, Any] = {
            "files": files,
            "seed": seed,
            "relax_rates": relax_rates,
            "current_relax_rate": relax_rates[0],
            "bound": 2000,
            "switch_rr_after_no_improv": 3,
        }
        if clingo_args is None:
            # arbitrary value atm
            clingo_args = ["--rand-freq=0.8"]
        self.config_values["clingo_args"] = clingo_args

        new_model: Dict[str, Sequence[clingo.symbol.Symbol]] = {}
        current_model: Dict[str, Sequence[clingo.symbol.Symbol]] = {}
        best_model: Dict[str, Sequence[clingo.symbol.Symbol]] = {}
        self.models: Dict[str, Any] = {
            "new_model": new_model,
            "current_model": current_model,
            "best_model": best_model,
        }

        self.callables: Dict[str, Callable] = {
            "setup": lns_f.setup_clingo,
            "relax": lns_f.relax_random,
            "repair": lns_f.repair_clingo,
            "calc_opt_value": lns_f.calculate_opt_val,
            "get_first_solution": lns_f.get_first_solution_hard_constraint,
            "check_accept": lns_f.check_accept_always,
            "check_better": lns_f.check_better_always,
            "better_solution_found": lns_f.better_solution_found_hard_constraint,
            "boundary_handling": lns_f.boundary_overall,
            "check_stop": lns_f.check_stop_steps,
        }
        if callables:
            self.callables = {**self.callables, **callables}

    def get_params(self) -> Dict[str, Any]:
        """
        Get LNS parameters.

        :return: LNS parameters.
        :rtype: Dict[str, Any]
        """
        return self.config_values

    def set_params(self, params: Dict[str, Any]) -> None:
        """
        Set LNS parameters.

        :param params: LNS parameters.
        :type params: Dict[str, Any]
        """
        self.config_values = {**self.config_values, **params}

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

    def main(self) -> None:
        """
        Run Large-Neighbourhood Search according to set parameters.
        """
        # prepare clingo control
        ctl, thy = self.callables["setup"](self)

        # ctl, thy = lns_f.setup_clingo_dl(self)
        # lns_f.ground_base(self, ctl)
        # print(lns_f.repair_clingo_dl(self, ctl, [], thy))

        # get first solution
        if not self.callables["get_first_solution"](self, ctl, thy):
            return

        # perform LNS
        boundary_dict: Dict[str, Any] = {}
        self.callables["boundary_handling"](self, boundary_dict, "init")
        while True:
            self.callables["boundary_handling"](self, boundary_dict, "update")

            # relax model
            assumptions = self.callables["relax"](
                self.models["current_model"],
                self.config_values["current_relax_rate"],
            )

            # reconstruct model
            if self.callables["repair"](self, ctl, assumptions, thy):
                # check if new model is accepted
                if self.callables["check_accept"](
                    self, self.models["new_model"], self.models["current_model"]
                ):
                    # print(self.callable_dict["calc_opt_value"](self.lns_values["new_model"]))
                    self.models["current_model"] = self.models["new_model"].copy()

                    # check if new model is better
                    if self.callables["check_better"](
                        self,
                        self.models["new_model"],
                        self.models["best_model"],
                    ):
                        self.callables["better_solution_found"](self, ctl)

                        self.callables["boundary_handling"](
                            self, boundary_dict, "improvement"
                        )
                    else:
                        self.callables["boundary_handling"](
                            self, boundary_dict, "no_improvement"
                        )
                # else:
                #    self.callable_dict["boundary_handling"](
                #        self, boundary_dict, "no_improvement"
                #    )
            else:
                self.callables["boundary_handling"](
                    self, boundary_dict, "no_improvement"
                )
            # stop criterion, WIP
            if self.callables["check_stop"](self, boundary_dict):
                end_time = time.time()
                answer_string = " ".join(
                    [str(atom) for atom in self.models["best_model"]["shown"]]
                )
                print(
                    (
                        "Answer\n"
                        f"{answer_string}\n"
                        f"Final opt_val: { self.callables['calc_opt_value'](self.models['best_model'])}\n"
                        f"Overall steps: {boundary_dict['step']}\n"
                        f"Overall time: {end_time - boundary_dict['start_time']:.3f}s"
                    )
                )
                break

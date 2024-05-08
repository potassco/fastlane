"""
The large_neighbourhood_search project.
"""

import signal
import sys
from types import FrameType
from typing import Any, Callable, Dict, List, Sequence, Union

import clingo

from .lib import boundary, lns_utils, search, theory


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
            "setup": theory.setup_clingo,
            "relax": search.relax_random,
            "repair": theory.repair_clingo,
            "calc_opt_value": lns_utils.calculate_opt_val,
            "get_first_solution": search.get_first_solution_hard_constraint,
            "check_accept": search.check_accept_always,
            "check_better": search.check_better_always,
            "better_solution_found": search.better_solution_found_hard_constraint,
            "boundary_handling": boundary.boundary_overall,
            "check_stop": boundary.check_stop_steps,
            "finish": boundary.finish,
        }
        if callables:
            self.callables = {**self.callables, **callables}

        self.boundary_dict: Dict[str, Any] = {}

    # pylint: disable=unused-argument
    def interrupt_handler(
        self, sig: int, frame: Union[None, FrameType]
    ) -> None:  # nocoverage
        """
        Signal handler for interrupts (SIGINT)

        :param sig: Signal number.
        :type sig: int
        :param frame: Current stack frame.
        :type frame: Frame
        :rtype: Dict[str, Any]
        """
        print("==================")
        print("INTERRUPTED:")
        boundary.finish(self)
        raise SystemExit

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
        signal.signal(signal.SIGINT, self.interrupt_handler)
        # prepare clingo control
        ctl, thy = self.callables["setup"](self)

        # ctl, thy = lns_f.setup_clingo_dl(self)
        # lns_f.ground_base(self, ctl)
        # print(lns_f.repair_clingo_dl(self, ctl, [], thy))

        # get first solution
        if not self.callables["get_first_solution"](self, ctl, thy):
            return

        # perform LNS
        self.callables["boundary_handling"](self, "init")
        while True:
            self.callables["boundary_handling"](self, "update")

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

                        self.callables["boundary_handling"](self, "improvement")
                    else:
                        self.callables["boundary_handling"](self, "no_improvement")
                # else:
                #    self.callable_dict["boundary_handling"](
                #        self, boundary_dict, "no_improvement"
                #    )
            else:
                self.callables["boundary_handling"](self, "no_improvement")
            # stop criterion, WIP
            if self.callables["check_stop"](self):
                self.callables["finish"](self)
                break

"""
The large_neighbourhood_search project.
"""

import random
import signal
from types import FrameType
from typing import Any, Callable, Dict, List, Sequence, Union

import clingo
from clingodl import ClingoDLTheory

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
    """

    def __init__(self, files: List[str], callables: Dict[str, Callable] = {}) -> None:
        """
        Initialize application.
        """
        self.program_name = "lns"
        self.version = "2.0"

        self.theory: Union[ClingoDLTheory, None] = None
        self.param_values: Dict[str, Any] = {
            "files": files,
            "seed": None,
            "relax_rates": [0.2, 0.4, 0.6],
            "bound": 2000,
            "switch_rr_after_no_improv": 3,
            "clingo_args": {"rand-freq": 0.8},
            "time_limit": 20,
            "overall_time_limit": 600,
        }

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
            "check_stuck": search.check_stuck_never,
            "is_stuck": search.is_stuck,
            "time_out": search.time_out,
        }
        if callables:
            self.callables = {**self.callables, **callables}

        self.boundary_dict: Dict[str, Any] = {}

    def on_model(self, model: clingo.solving.Model) -> None:  # nocoverage
        """
        Saves model for later use.

        :param model: Model found during solving.
        :type model: clingo.solving.Model
        """
        # dl
        if self.theory:
            self.theory.on_model(model=model)
            self.models["new_model"]["assignments"] = [
                f"{key}={val}" for key, val in self.theory.assignment(model.thread_id)
            ]

        self.models["new_model"] = {}
        self.models["new_model"]["shown"] = model.symbols(shown=True)
        self.models["new_model"]["true"] = model.symbols(atoms=True)

    # pylint: disable=unused-argument
    def interrupt_handler(self, sig: int, frame: Union[None, FrameType]) -> None:
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
        self.callables["finish"](self)
        raise SystemExit

    def get_params(self) -> Dict[str, Any]:
        """
        Get LNS parameters.

        :return: LNS parameters.
        :rtype: Dict[str, Any]
        """
        return self.param_values

    def set_params(self, params: Dict[str, Any]) -> None:
        """
        Set LNS parameters.

        :param params: LNS parameters.
        :type params: Dict[str, Any]
        """
        self.param_values = {**self.param_values, **params}

    def set_seed(self, seed: int) -> None:
        """
        Set seed.

        :param seed: Seed to be set.
        :type seed: int
        """
        random.seed(self.param_values["seed"])
        self.param_values["seed"] = seed
        self.param_values["clingo_args"] = {
            **self.param_values["clingo_args"],
            **{"seed": seed},
        }

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

    # pylint: disable=too-many-branches
    def main(self) -> None:
        """
        Run Large-Neighbourhood Search according to set parameters.
        """

        def init_fail():
            print("Failed to init relax rate.")
            raise SystemExit

        if "relax_rates" in self.param_values:
            if (
                isinstance(self.param_values["relax_rates"], list)
                and self.param_values["relax_rates"]
            ):
                self.param_values["current_relax_rate"] = self.param_values[
                    "relax_rates"
                ][0]
            else:
                init_fail()
        else:
            init_fail()
        signal.signal(signal.SIGINT, self.interrupt_handler)
        # prepare clingo control
        ctl, thy = self.callables["setup"](self)

        # get first solution
        if not self.callables["get_first_solution"](self, ctl, thy):
            return

        # perform LNS
        self.callables["boundary_handling"](self, "init")
        while True:
            self.callables["boundary_handling"](self, "update")
            improvement_found: bool = False

            # relax model
            assumptions = self.callables["relax"](
                self.models["current_model"],
                {"relax_rate": self.param_values["current_relax_rate"]},
            )

            # reconstruct model
            if self.callables["repair"](self, ctl, assumptions, thy).satisfiable:
                if "timeout" not in self.boundary_dict:
                    self.boundary_dict["timeout"] = 0
                # check if new model is accepted
                if self.callables["check_accept"](
                    self, self.models["new_model"], self.models["current_model"]
                ):
                    self.models["current_model"] = self.models["new_model"].copy()

                    # check if new model is better
                    if self.callables["check_better"](
                        self,
                        self.models["new_model"],
                        self.models["best_model"],
                    ):
                        self.callables["better_solution_found"](self, ctl)

                        self.callables["boundary_handling"](self, "improvement")
                        improvement_found = True
            if not improvement_found:
                self.callables["boundary_handling"](self, "no_improvement")
                if self.callables["check_stuck"](self):
                    self.callables["is_stuck"](self)
                    break
            if self.callables["check_stop"](self):
                self.callables["finish"](self)
                break

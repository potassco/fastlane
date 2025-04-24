"""
A modifiable large neighborhood search framework.
"""

import random
import signal
import time
from types import FrameType
from typing import Any, Union

import clingo

from mod_lns import Model
from mod_lns.interfaces.solver import SolverInterface
from mod_lns.interfaces.strategy import StrategyInterface
from mod_lns.lns_config import LNSConfig
from mod_lns.utils.conversions import str_to_symbols


# pylint: disable=too-many-instance-attributes
class LNS:
    """
    Class handling and  performing LNS.

    :param files: Problem encodings.
    :type files: list[str]
    :param lns_config: LNSConfig object.
    :type lns_config: mod_lns.lns_config.LNSConfig
    :default lns_config: LNSConfig()
    """

    def __init__(
        self,
        files: list[str],
        lns_config: LNSConfig = LNSConfig(),
    ):
        """
        Initialization of the lns object.
        """
        self.clingo_options = lns_config.clingo_options
        self.solver: SolverInterface = lns_config.solver
        self.strategy: StrategyInterface = lns_config.strategy
        self.start_time: float = 0
        self.step_c: int = 0
        self.stopped = False

        self.new_model: Model = Model()
        self.current_model: Model = Model()
        self.best_model: Model = Model()

        # to be reworked
        self.param_values: dict[str, Any] = {
            "files": files,
            "seed": None,
            "relax_rate": 0.2,
            "max_steps": "2000",
            # move to clingo opts
            "solve_time_limit": 20,
            "overall_time_limit": 600,
            "stuck_after_no_improv": None,
            "start_sol": None,
            "vari_accept": 0,
            "base_relax_rate": 0,
            "fs_time_limit": 60,
            "fs_model_limit": 1,
        }
        self.set_parameters(lns_config.lns_options)

        self.avail_time = self.param_values["overall_time_limit"]

    def set_seed(self, seed: int) -> None:
        """
        Set seed.

        :param seed: Seed to be set.
        :type seed: int
        """
        self.param_values["seed"] = seed
        random.seed(self.param_values["seed"])

    def get_parameters(self) -> dict[str, Any]:
        """
        Get LNS parameters.
        """
        return self.param_values

    def set_parameters(self, params: dict[str, Any]) -> None:
        """
        Set LNS parameters.

        :param params: LNS parameters.
        :type params: dict[str, Any]
        """
        self.param_values = {**self.param_values, **params}
        self.set_seed(self.param_values["seed"])
        if isinstance(self.param_values["max_steps"], str):
            if self.param_values["max_steps"].isdigit():
                self.param_values["max_steps"] = int(self.param_values["max_steps"])
            else:
                self.param_values["max_steps"] = None
        elif isinstance(self.param_values["max_steps"], int):
            pass
        else:
            self.param_values["max_steps"] = None

    # pylint: disable=unused-argument
    def interrupt_handler(self, sig: int, frame: Union[None, FrameType]) -> None:
        """
        Signal handler for interrupts (SIGINT, SIGTERM)

        :param sig: Signal number.
        :type sig: int
        :param frame: Current stack frame.
        :type frame: Frame
        :rtype: dict[str, Any]
        """
        print("==================")
        print("INTERRUPTED:")
        self.best_model.print_model()
        print(f"Overall steps: {self.step_c}")
        print(f"Overall time: {time.time() - self.start_time:.3f}s")
        raise SystemExit

    def on_model(self, model: clingo.solving.Model) -> None:  # nocoverage
        """
        Saves model for later use.

        :param model: Model found during solving.
        :type model: clingo.solving.Model
        """
        self.new_model = Model()
        self.new_model.shown = model.symbols(shown=True)
        self.new_model.true = model.symbols(atoms=True)
        self.new_model.cost = model.cost

        # dl - to be improved
        if self.solver.theory:
            self.solver.theory.on_model(model=model)
            self.new_model.assignments = [
                f"{key}={val}"
                for key, val in self.solver.theory.assignment(model.thread_id)
            ]

    def get_available_solve_time(self, time_limit: int) -> int:
        """
        Calculate available solve time.
        (rounded to int)

        :param time_limit: Time limit for solve call.
        :type time_limit: int
        :return: Available solve time.
        :rtype: int
        """
        avail_time = self.avail_time
        if avail_time >= time_limit:
            return time_limit
        return avail_time

    def main(self) -> None:
        """
        Run Large-Neighbourhood Search according to set parameters.
        """
        # c, b, n: current, best, new model
        # pre_setup()
        # solver_setup()
        # post_setup()
        # c = first_sol()
        # post_first_sol()
        # while check_stop()
        #   pre_relax()
        #   n = repair(relax(c))
        #   post_repair()
        #   check_accept(n)
        #       c = n
        #       accepted()
        #   check_better(n,b)
        #       b = n
        #       better()

        signal.signal(signal.SIGINT, self.interrupt_handler)
        signal.signal(signal.SIGTERM, self.interrupt_handler)

        self.start_time = time.time()
        self.step_c = -1

        self.strategy.pre_setup(self)

        start_sol = []
        if self.param_values["start_sol"]:
            start_sol = str_to_symbols(self.param_values["start_sol"])

        self.solver.setup(self)

        self.strategy.post_setup(self)

        self.step_c = 0

        # get first solution - to be reworked
        if not self.strategy.get_first_solution(
            self,
            start_sol,
            self.get_available_solve_time(self.param_values["fs_time_limit"]),
            self.param_values["fs_model_limit"],
        ):
            print("First solution could not be obtained")
            raise SystemExit

        self.strategy.post_first_solution(self)

        while not (self.strategy.check_stop(self) or self.stopped):
            self.step_c += 1
            if self.step_c % 50 == 0:
                print(
                    f"{time.time() - self.start_time:.3f}s: {self.step_c}|{self.param_values['max_steps']}"
                )
            self.strategy.pre_relax(self)
            fixed_atoms = self.strategy.relax(
                self.new_model,
                {
                    "relax_rate": self.param_values["relax_rate"],
                    "base_relax_rate": self.param_values["base_relax_rate"],
                },
            )
            if self.strategy.repair(
                self,
                fixed_atoms,
                self.get_available_solve_time(self.param_values["solve_time_limit"]),
            ).satisfiable:
                self.strategy.post_repair(self)
                if self.strategy.check_accept(self):
                    self.current_model = self.new_model
                    self.strategy.accepted(self)
                if self.strategy.check_better(self):
                    self.best_model = self.new_model
                    print(
                        f'{time.time() - self.start_time:.3f}s: {self.step_c}|{self.param_values["max_steps"]} '
                        f"New best solution: {self.best_model.get_cost_str()}"
                    )
                    self.strategy.better(self)
        print("==================")
        print("SEARCH FINISHED:")
        self.best_model.print_model()
        print(f"Overall steps: {self.step_c}")
        print(f"Overall time: {time.time() - self.start_time:.3f}s")

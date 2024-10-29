"""
The large_neighbourhood_search project.
"""

import random
import signal
import time
from types import FrameType
from typing import Any, Dict, List, Sequence, Union

import clingo

from large_neighbourhood_search.lib.utils import str_to_symbols

from .interfaces.solver import SolverInterface
from .interfaces.strategy import StrategyInterface
from .lib.solvers.clingo_solver import ClingoSolver
from .lib.strategies.hc_weighted_sum_rnd import HCWeightedSumRnd


# pylint: disable=dangerous-default-value,too-many-instance-attributes
class LNS:
    """
    Class handling and  performing LNS.

    :param files: Problem encodings.
    :type files: List[str]
    :param solver: Solver class used during LNS.
    :type solver: SolverInterface
    :default solver: ClingoSolver
    :param strategy: Strategy class used during LNS.
    :type strategy: StrategyInterface
    :default strategy: HCWeightedSumRnd
    :param params: Search parameters.
    :type params: Dict[str, Any]
    :default params: {}
    """

    def __init__(
        self,
        files: List[str],
        solver: SolverInterface = ClingoSolver(),
        strategy: StrategyInterface = HCWeightedSumRnd(),
        params: Dict[str, Any] = {},
    ):
        """
        Initialization of the lns object.
        """
        self.pre_solver: SolverInterface = type(solver)()
        self.solver: SolverInterface = solver
        self.strategy: StrategyInterface = strategy
        self.start_time: float = 0
        self.step_c: int = 0
        self.no_improv_c = 0
        self.stopped = False

        new_model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]] = {}
        current_model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]] = {}
        best_model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]] = {}
        self.models: Dict[str, Any] = {
            "new_model": new_model,
            "current_model": current_model,
            "best_model": best_model,
        }

        self.param_values: Dict[str, Any] = {
            "files": files,
            "seed": None,
            "relax_rate": 0.2,
            "max_steps": 2000,
            "clingo_args": {"rand-freq": 0.8},
            "solve_time_limit": 20,
            "overall_time_limit": 600,
            "stuck_after_no_improv": 1000,
            "start_sol": None,
            "vari_accept": 0,
            "pre_files": [],
            "pre_tl": 1800,
        }
        self.param_values = {**self.param_values, **params}
        self.avail_time = self.param_values["overall_time_limit"]

    def set_seed(self, seed: int) -> None:
        """
        Set seed.

        :param seed: Seed to be set.
        :type seed: int
        """
        random.seed(self.param_values["seed"])
        self.param_values["seed"] = seed
        if seed is not None:
            self.param_values["clingo_args"] = {
                **self.param_values["clingo_args"],
                **{"seed": seed},
            }

    def get_params(self) -> Dict[str, Any]:
        """
        Get LNS parameters.
        """
        return self.param_values

    def set_params(self, params: Dict[str, Any]) -> None:
        """
        Set LNS parameters.

        :param params: LNS parameters.
        :type params: Dict[str, Any]
        """
        self.param_values = {**self.param_values, **params}
        self.set_seed(self.param_values["seed"])

    def print_model(self, model: Dict[str, Any]) -> str:
        """
        Print given model.

        :param model: Model.
        :type model: Dict[str, Any]
        :return: Printed string.
        :rtype: str
        """
        answer_string = " ".join([str(atom) for atom in model["shown"]])
        if "assignments" in model:
            answer_string += "\nAssignments:\n" + " ".join(model["assignments"])
        s = "Answer\n" f"{answer_string}\n" f'Cost: {model["cost"]}\n'
        print(s)
        return s

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
        self.print_model(self.models["best_model"])
        print(f"Overall steps: {self.step_c}")
        print(f"Overall time: {time.time() - self.start_time:.3f}s")
        raise SystemExit

    def on_model(self, model: clingo.solving.Model) -> None:  # nocoverage
        """
        Saves model for later use.

        :param model: Model found during solving.
        :type model: clingo.solving.Model
        """
        self.models["new_model"] = {}
        self.models["new_model"]["shown"] = model.symbols(shown=True)
        self.models["new_model"]["true"] = model.symbols(atoms=True)
        self.models["new_model"]["cost"] = self.strategy.calc_cost(
            self.models["new_model"]
        )
        # dl
        if self.solver.thy:
            self.solver.thy.on_model(model=model)
            self.models["new_model"]["assignments"] = [
                f"{key}={val}"
                for key, val in self.solver.thy.assignment(model.thread_id)
            ]
        # pre solving
        if self.param_values["pre_files"] and self.step_c == -1:
            print(model.cost)

    def main(self) -> None:
        """
        Run Large-Neighbourhood Search according to set parameters.
        """
        # c, b, n: current, best, new model
        # setup
        # c = first sol/pre-solve
        # while check_stop
        #   n = repair(relax(c))
        #   check accept(n)
        #       c = n
        #   check better
        #       b = n

        signal.signal(signal.SIGINT, self.interrupt_handler)

        self.start_time = time.time()
        self.step_c = -1

        start_sol = []
        if self.param_values["start_sol"]:
            start_sol = str_to_symbols(self.param_values["start_sol"])

        self.solver.setup(self)

        # pre solving
        if self.param_values["pre_files"]:
            print(f"Start pre-solving ({self.param_values['pre_tl']}s):")
            self.pre_solver.setup(self, self.param_values["pre_files"])
            self.pre_solver.ground_base(self)
            if self.pre_solver.pre_solve(self).satisfiable:
                print("Pre-solving done.")
                start_sol = self.models["new_model"]["shown"]

            else:
                print("Pre-solving failed")
                raise SystemExit

        self.step_c = 0

        if not self.strategy.first_solution(self, start_sol):
            print("First solution could not be obtained")
            raise SystemExit

        while not (self.strategy.check_stop(self) or self.stopped):
            self.step_c += 1
            improv = False
            if self.step_c % 50 == 0:
                print(
                    f"{time.time() - self.start_time:.3f}s: {self.step_c}|{self.param_values['max_steps']}"
                )
            fixed_atoms = self.strategy.relax(
                self.models["new_model"],
                {"relax_rate": self.param_values["relax_rate"]},
            )
            if self.strategy.repair(self, fixed_atoms).satisfiable:
                if self.strategy.check_accept(self):
                    self.models["current_model"] = self.models["new_model"].copy()
                if self.strategy.check_better(self):
                    self.models["best_model"] = self.models["new_model"].copy()
                    print(
                        f'{time.time() - self.start_time:.3f}s: {self.step_c}|{self.param_values["max_steps"]} '
                        f'New best solution: {self.models["best_model"]["cost"]}'
                    )
                    self.strategy.update_grounding(self)
                    self.no_improv_c = 0
                    improv = True
            if not improv:
                self.no_improv_c += 1
                self.strategy.stuck_handling(self)
        print("==================")
        print("SEARCH FINISHED:")
        self.print_model(self.models["best_model"])
        print(f"Overall steps: {self.step_c}")
        print(f"Overall time: {time.time() - self.start_time:.3f}s")

        # old callables
        # s     "setup": theory.setup_clingo,
        # st    "get_first_solution": search.get_first_solution_hc_weighted_sum,
        # st r  "relax": search.relax_random,
        # s st  "repair": theory.repair_clingo,
        # st    "check_accept": search.check_accept_always,
        # st    "check_better": search.check_better_always,
        # st    "check_stop": boundary.check_stop_steps,
        # st    "calc_opt_value": lns_utils.calc_opt_val_weighted_sum,
        # st    "better_solution_found": search.better_solution_found_hc_weighted_sum,
        # --    "boundary_handling": boundary.boundary_overall,
        # --    "finish": boundary.finish,
        # st    "check_stuck": search.check_stuck_never,
        # st    "is_stuck": search.is_stuck,
        # --    "timeout": search.timeout,

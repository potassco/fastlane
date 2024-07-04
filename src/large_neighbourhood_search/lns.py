import random
import signal
import time
from types import FrameType
from typing import Any, Dict, List, Sequence, Type, Union

import clingo
from interfaces.solver import SolverInterface
from interfaces.strategy import StrategyInterface


# replace LNS class in __init__
class LNS:
    """
    Class handling and  performing LNS.

    :param files: Problem encodings.
    :type files: List[str]
    :param solver: Solver class used during LNS.
    :type solver: Type[SolverInterface]
    :param strategy: Strategy class used during LNS.
    :type strategy: Type[StrategyInterface]
    :param params: Search parameters.
    :type params: Dict[str, Any]
    :default params: {}
    """

    def __init__(
        self,
        files: List[str],
        solver: Type[SolverInterface],
        strategy: Type[StrategyInterface],
        params: Dict[str, Any] = {},
    ):
        """
        Initialization of the lns object.
        """
        self._solver = solver
        self._strategy = strategy
        self._start_time = 0
        self._step_c = 0

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
        }
        self.param_values = {**self.param_values, **params}
        self._avail_time = self.param_values["overall_time_limit"]

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

    def print_model(self, model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]):
        answer_string = " ".join([str(atom) for atom in model["shown"]])
        if "assignments" in model:
            answer_string += "\n".join(model["assignments"])
        print(("Answer\n" f"{answer_string}\n" f'Cost: {model["cost"]}\n'))

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
        print(f"Overall steps: {self._step_c}")
        print(f"Overall time: {time.time() - self._start_time:.3f}s")
        raise SystemExit

    def on_model(self, model: clingo.solving.Model) -> None:  # nocoverage
        """
        Saves model for later use.

        :param model: Model found during solving.
        :type model: clingo.solving.Model
        """
        # dl
        if self._solver._thy:
            self._solver._thy.on_model(model=model)
            self.models["new_model"]["assignments"] = [
                f"{key}={val}"
                for key, val in self._solver._thy.assignment(model.thread_id)
            ]

        self.models["new_model"] = {}
        self.models["new_model"]["shown"] = model.symbols(shown=True)
        self.models["new_model"]["true"] = model.symbols(atoms=True)
        self.models["new_model"]["cost"] = self._strategy.calc_cost(
            self.models["new_model"]
        )

    def main(self):
        """
        Run Large-Neighbourhood Search according to set parameters.
        """
        # c, b, n: current, best, new model
        # setup
        # c = first sol
        # while check_stop
        #   n = repair(relax(c))
        #   check accept(n)
        #       c = n
        #   check better
        #       b = n

        signal.signal(signal.SIGINT, self.interrupt_handler)

        self._solver.setup(self)

        if not self._strategy.first_solution(self):
            raise SystemExit

        while not self._strategy.check_stop(self):
            self._step_c += 1
            fixed_atoms = self._strategy.relax(
                self.models["current_model"],
                {"relax_rate": self.param_values["relax_rate"]},
            )
            if self._strategy.repair(self, fixed_atoms).satisfiable:
                if self._strategy.check_accept(self):
                    self.models["current_model"] = self.models["new_model"].copy()
                if self._strategy.check_better(self):
                    self.models["best_model"] = self.models["new_model"].copy()
                    self._strategy.update_grounding(self)
        print("==================")
        print("SEARCH FINISHED:")
        self.print_model(self.models["best_model"])
        print(f"Overall steps: {self._step_c}")
        print(f"Overall time: {time.time() - self._start_time:.3f}s")

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
        #       "check_stuck": search.check_stuck_never,
        #       "is_stuck": search.is_stuck,
        # --    "timeout": search.timeout,

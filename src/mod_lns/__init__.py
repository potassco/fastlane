"""
The large_neighbourhood_search project.
"""

import random
import signal
import time
from types import FrameType
from typing import Any, Dict, List, Sequence, Union

import clingo

from mod_lns.lib.utils import str_to_symbols

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
        config: ConfigInterface(),
        options: Dict[str, Any] = {},
    ):
        """
        Initialization of the lns object.
        """
        self.solver: SolverInterface = config.solver
        #self.strategy: StrategyInterface = strategy
        self.start_time: float = 0
        self.step_c: int = 0
        #self.no_improv_c = 0
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
            "relax_rate": 0.1,
            "max_steps": "2000",
            "clingo_args": {"rand-freq": 0.1},
            #"solve_time_limit": 20,
            "overall_time_limit": 600,
            #"stuck_after_no_improv": None,
            "start_sol": None,
            #"vari_accept": 0,
            #"pre_files": [],
            #"pre_tl": 1800,
            #"base_relax_rate": 0,
            heuristic = False,
            hc = False,
            decl = False, 
        }
        self.param_values = {**self.param_values, **options}
        self.avail_time = self.param_values["overall_time_limit"]

        if isinstance(self.param_values["max_steps"], str):
            if self.param_values["max_steps"].isdigit():
                self.param_values["max_steps"] = int(self.param_values["max_steps"])
            else:
                self.param_values["max_steps"] = None
        elif isinstance(self.param_values["max_steps"], int):
            pass
        else:
            self.param_values["max_steps"] = None

        #if isinstance(self.param_values["stuck_after_no_improv"], str):
        #    if self.param_values["stuck_after_no_improv"].isdigit():
        #        self.param_values["stuck_after_no_improv"] = int(
        #            self.param_values["stuck_after_no_improv"]
        #        )
        #    else:
        #        self.param_values["stuck_after_no_improv"] = None
        #elif isinstance(self.param_values["stuck_after_no_improv"], int):
        #    pass
        #else:
        #    self.param_values["stuck_after_no_improv"] = None

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

    def get_parameters(self) -> Dict[str, Any]:
        """
        Get LNS parameters.
        """
        return self.param_values

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """
        Set LNS parameters.

        :param params: LNS parameters.
        :type params: Dict[str, Any]
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

        #if isinstance(self.param_values["stuck_after_no_improv"], str):
        #    if self.param_values["stuck_after_no_improv"].isdigit():
        #        self.param_values["stuck_after_no_improv"] = int(
        #            self.param_values["stuck_after_no_improv"]
        #        )
        #    else:
        #        self.param_values["stuck_after_no_improv"] = None
        #elif isinstance(self.param_values["stuck_after_no_improv"], int):
        #    pass
        #else:
        #    self.param_values["stuck_after_no_improv"] = None

    # moved to utils.functions
    from utils.functions import get_cost_str
    from utils.functions import print_model
    

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
        self.models["new_model"]["cost"] = self.strategy.calculate_cost(
            self.models["new_model"]
        )
        # dl - to be improved
        if self.solver.theory:
            self.solver.theory.on_model(model=model)
            self.models["new_model"]["assignments"] = [
                f"{key}={val}"
                for key, val in self.solver.theory.assignment(model.thread_id)
            ]
        ## pre solving
        #if self.param_values["pre_files"] and self.step_c == -1:
        #    print(model.cost)

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

        ## pre solving
        #if self.param_values["pre_files"]:
        #    print(f"Start pre-solving ({self.param_values['pre_tl']}s):")
        #    self.pre_solver.setup(self, self.param_values["pre_files"])
        #    self.pre_solver.ground_base(self)
        #    if self.pre_solver.solve(self).satisfiable:
        #        print("Pre-solving done.")
        #        start_sol = self.models["new_model"]["shown"]
        #
        #    else:
        #       print("Pre-solving failed")
        #       raise SystemExit

        self.step_c = 0

        # get first solution - to be reworked
        if not self.strategy.get_first_solution(self, start_sol):
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
                {
                    "relax_rate": self.param_values["relax_rate"],
                    "base_relax_rate": self.param_values["base_relax_rate"],
                },
            )
            if self.strategy.repair(self, fixed_atoms).satisfiable:
                if self.strategy.check_accept(self):
                    self.models["current_model"] = self.models["new_model"].copy()
                if self.strategy.check_better(self):
                    self.models["best_model"] = self.models["new_model"].copy()
                    print(
                        f'{time.time() - self.start_time:.3f}s: {self.step_c}|{self.param_values["max_steps"]} '
                        f'New best solution: {self.get_cost_str(self.models["best_model"])}'
                    )
                    self.strategy.update_grounding(self)
                    self.no_improv_c = 0
                    improv = True
            #if not improv:
             #   self.no_improv_c += 1
                # self.strategy.stuck_handling(self)
        print("==================")
        print("SEARCH FINISHED:")
        self.print_model(self.models["best_model"])
        print(f"Overall steps: {self.step_c}")
        print(f"Overall time: {time.time() - self.start_time:.3f}s")

# c, b, n: current, best, new model
        # inter0()
        # solver_setup()
        # inter1()
        # c = first_sol()
        # inter2()
        # while check_stop()
        #   inter3()
        #   n = repair(relax(c))
        #   inter4()
        #   check_accept(n)
        #       c = n
        #       accepted()
        #   check_better(n,b)
        #       b = n
        #       better()

# mod_lns --dl --heu --decl -rr=3
# mod_lns --x_strat -r=2 
# main:
# config -> select strat or options
#        -> select solver



# class mod_lns
#   params
#       config
#           solver
#           heu
#           mode: hc cl
#           detect rnd decl
#

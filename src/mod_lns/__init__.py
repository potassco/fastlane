"""
The large_neighbourhood_search project.
"""

import copy
import random
import signal
import time
from types import FrameType, MethodType
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import clingo
from clingo.symbol import Function, Number

from mod_lns.lib.utils import str_to_symbols, symbol_to_str

from .interfaces.solver import SolverInterface
from .interfaces.strategy import StrategyInterface
from .lib.solvers.clingo_solver import ClingoSolver
from .lib.strategies.classic_lexicographic_rnd import ClassicLexiRnd
from .lib.strategies.default_strategy import DefaultStrategy
from .lib.strategies.hc_weighted_sum_rnd import HCWeightedSumRnd
from .utils.functions import get_cost_str, print_model
from .lib.relaxation import relax_declarative


# move to extra file
# pylint: disable=dangerous-default-value,
class LNSConfig:
    """
    LNS configuration class.
    Defines base solver and strategy objects and modifies them
    according to the given LNS options.
    Passing a strategy object inside lns_options["strategy"] overrides the base
    strategy and its modifications and just uses the given strategy as is.


    :param params: LNS options
    :type params: Dict[str, Any]
    :default params: {}
    :param base_solver: Solver object used as base for LNS.
    :type base_solver: SolverInterface
    :default base_solver: ClingoSolver()
    :param base_strategy: Strategy object used as base for LNS.
    :type base_strategy: StrategyInterface
    :default base_strategy: DefaultStrategy()
    """

    def __init__(
        self,
        lns_options: Dict[str, Any] = {},
        base_solver: SolverInterface = ClingoSolver(),
        base_strategy: StrategyInterface = DefaultStrategy(),
    ):
        """
        Initialize lns config.
        """
        default_options = {
            "strategy": None,
            "heu": False,
            "hc": False,
            "decl": False,
        }

        self.lns_options = {**default_options, **lns_options}

        # solver
        self.solver = base_solver
        if self.lns_options["heu"]:
            self.enable_heuristic()

        # strategy
        if isinstance(self.lns_options["strategy"], StrategyInterface):
            self.strategy = self.lns_options["strategy"]
        else:
            self.strategy = base_strategy
            if self.lns_options["hc"]:
                self.enable_constrained_approach()
            if self.lns_options["decl"]:
                self.enable_declarative()

    def enable_heuristic(self) -> None:
        """
        Adjust base solver to use heuristics for reparation.
        """
        base = type(self.solver)

        class EnHeu(base):
            def setup(
                self,
                lns_object: LNS,
                files: Optional[List[str]] = None,
                args: Optional[Dict[str, Any]] = None,
            ) -> None:
                """
                Set up heuristics.

                :param lns_object: LNS object.
                :type lns_object: large_neighbourhood_search.LNS
                :param files: ASP files to be loaded, default: lns_object.param_values["files"].
                :type files: Optional[List[str]]
                :param args: clingo arguments, default: lns_object.param_values["clingo_args"].
                :type args: Optional[Dict[str,Any]]
                """
                if args is None:
                    args = {
                        **lns_object.param_values["clingo_args"],
                        **{"heuristic": "Domain"},
                    }
                else:
                    args = {**args, **{"heuristic": "Domain"}}

                super(EnHeu, self).setup(lns_object, files, args)

                # used for heuristics, see solve_fixed()
                self.control.add("_lns_h_step", ["s"], "#external _lns_h_step(s).")

            def repair(
                self,
                lns_object: LNS,
                fixed_atoms: List[Tuple[clingo.symbol.Symbol, bool]],
            ) -> clingo.solving.SolveResult:
                """
                Use heuristics during reparation.

                :param lns_object: LNS object.
                :type lns_object: large_neighbourhood_search.LNS
                :param assumptions: Assumptions for solving (fixed atoms).
                :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
                :return: Solve result.
                :rtype: clingo.solving.SolveResult
                """
                # add rules for heuristics
                # to correctly enable and disable heuristics at each step
                # #external _lns_h_step(s) is used
                # example for step=1, fixed_atoms=[
                #   Function("meets", [Number(2), Number(3), Number(4)], True),
                #   Function("meets", [Number(5), Number(6), Number(7)], True),] :
                # #external _lns_h_step(1).
                # #heuristic meets(2,3,4) : _lns_h_step(1). [1, true]
                # #heuristic meets(5,6,7) : _lns_h_step(1). [1, true]

                # setup external of current step
                step = lns_object.step_c
                if isinstance(self.control, clingo.control.Control):
                    self.control.ground([("_lns_h_step", [Number(step)])])
                    self.control.assign_external(
                        Function("_lns_h_step", [Number(step)]), True
                    )

                    # set heuristics
                    rules = " ".join(
                        [
                            f"#heuristic {symbol_to_str(atom[0])} : _lns_h_step({step}). [1, true]"
                            for atom in fixed_atoms
                        ]
                    )

                    self.control.add("heuristics", [], rules)
                    self.control.ground([("heuristics", [])])

                # solve
                res = super(EnHeu, self).repair(lns_object, fixed_atoms)

                # release externals
                if isinstance(self.control, clingo.control.Control):
                    self.control.release_external(
                        Function("_lns_h_step", [Number(step)])
                    )
                return res

        self.solver = EnHeu()

    def enable_constrained_approach(self) -> None:
        """
        Adjust base strategy to use constrained approach.
        """
        base = type(self.strategy)

        class EnCons(base):
            def post_first_solution(self, lns_object: LNS) -> None:
                """
                Enforce better solution by implementing initial cost as hard constraint.

                :param lns_object: LNS object.
                :type lns_object: large_neighbourhood_search.LNS
                """
                super(EnCons, self).post_first_solution(lns_object)
                cost = lns_object.models["new_model"]["cost"]
                # add rules to force better solution with each iteration
                # encoding has to contain _lns_penalty(N,I,W) predicates and _lns_priority(N,P) facts
                # where N: name, I: identifier, W: weight, P: priority
                # higher priority = more important
                # priorities have to be declared consecutively, e.g. only 1 and 3 not allowed
                # example of generated rules with ground values for cost={1:3, 2:4}
                #   #external _lns_l_step(s).
                #   _lns_bettereq(P+1,s) :- _lns_priority(_,P), not _lns_penalty(_,P+1), _lns_l_step(s).
                #   :- not _lns_better(_,s), _lns_l_step(s).
                #   _lns_better(1,s) :- _lns_priority(N,1), #sum{W,I: _lns_penalty(N,I,W)} < 3,
                #                       _lns_bettereq(1,s), _lns_l_step(s).
                #   _lns_bettereq(1,s) :- _lns_priority(N,1), #sum{W,I: _lns_penalty(N,I,W)} <= 3,
                #                         _lns_bettereq(2,s), _lns_l_step(s).
                #   _lns_better(2,s) :- _lns_priority(N,2), #sum{W,I: _lns_penalty(N,I,W)} < 4,
                #                       _lns_bettereq(2,s), _lns_l_step(s).
                #   _lns_bettereq(2,s) :- _lns_priority(N,2), #sum{W,I: _lns_penalty(N,I,W)} <= 4,
                #                         _lns_bettereq(3,s), _lns_l_step(s).
                s = ["s"] + list(map(lambda x: f"cost{x}", sorted(cost.keys())))
                rules = (
                    "#external _lns_l_step(s).\
                _lns_bettereq(P+1,s) :- _lns_priority(_,P), not _lns_priority(_,P+1), _lns_l_step(s).\
                :- not _lns_better(_,s), _lns_l_step(s)."
                    + " ".join(
                        list(
                            map(
                                lambda x: f"_lns_better({x},s) :- _lns_priority(N,{x}),\
                                #sum{{W,I: _lns_penalty(N,I,W)}} < cost{x}, _lns_bettereq({x},s), _lns_l_step(s).",
                                cost.keys(),
                            )
                        )
                        + list(
                            map(
                                lambda x: f"_lns_bettereq({x},s) :- _lns_priority(N,{x}),\
                                #sum{{W,I: _lns_penalty(N,I,W)}} <= cost{x}, _lns_bettereq({x+1},s), _lns_l_step(s).",
                                cost.keys(),
                            )
                        )
                    )
                )
                if isinstance(lns_object.solver.control, clingo.control.Control):
                    lns_object.solver.control.add("cost", s, rules)
                    lns_object.solver.control.ground(
                        [
                            (
                                "cost",
                                [Number(0)]
                                + [Number(cost[prio]) for prio in sorted(cost.keys())],
                            )
                        ]
                    )
                    lns_object.solver.control.assign_external(
                        Function("_lns_l_step", [Number(0)]), True
                    )

            def check_better(self, lns_object: LNS) -> bool:
                """
                Check whether new model is better.
                Enforced through constraint.

                :param lns_object: LNS object.
                :type lns_object: large_neighbourhood_search.LNS
                :return: Whether new model is better or not.
                :rtype: bool
                """
                return True

            def better(self, lns_object: LNS) -> None:
                """
                Update constraint after new best solution was found.

                :param lns_object: LNS object.
                :type lns_object: large_neighbourhood_search.LNS
                """
                super(EnCons, self).better(lns_object)
                step = lns_object.step_c
                if isinstance(lns_object.solver.control, clingo.control.Control):
                    lns_object.solver.control.release_external(
                        Function("_lns_l_step", [Number(step - 1)])
                    )
                    cost = lns_object.models["best_model"]["cost"]
                    lns_object.solver.control.ground(
                        [
                            (
                                "cost",
                                [Number(step)]
                                + [Number(cost[prio]) for prio in sorted(cost.keys())],
                            )
                        ]
                    )
                    lns_object.solver.control.assign_external(
                        Function("_lns_l_step", [Number(step)]), True
                    )

        self.strategy = EnCons()

    def enable_declarative(self) -> None:
        """
        Adjust base strategy to use declarative relaxation.
        """
        base=type(self.strategy)

        class EnDecl(base):
            def relax(
                self,
                model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]],
                relax_parameters: Dict[str, Any],
            ) -> List[Tuple[clingo.symbol.Symbol, bool]]:
                """
                Relax portion of atoms given by the relax_parameters.
                Use declarative random relaxation.

                :param model: Dictionary containing list of shown and true atoms.
                :type model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
                :param relax_parameters: Parameters used to determine relaxed atoms.
                :type relax_parameters: Dict[str, Any]
                :return: Fixed (not relaxed) atoms.
                :rtype: List[Tuple[clingo.symbol.Symbol, bool]]
                """
                return relax_declarative(model, relax_parameters)

        self.strategy = EnDecl()


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
        lns_config: LNSConfig,
        clingo_options: Dict[str, Any] = {},
    ):
        """
        Initialization of the lns object.
        """
        self.solver: SolverInterface = lns_config.solver
        self.strategy: StrategyInterface = lns_config.strategy
        self.start_time: float = 0
        self.step_c: int = 0
        # self.no_improv_c = 0
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
            # move to clingo opts
            "solve_time_limit": 20,
            "overall_time_limit": 600,
            "stuck_after_no_improv": None,
            "start_sol": None,
            "vari_accept": 0,
            "pre_files": [],
            "pre_tl": 1800,
            "base_relax_rate": 0,
        }
        self.param_values = {**self.param_values, **lns_config.lns_options}
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

        # if isinstance(self.param_values["stuck_after_no_improv"], str):
        #    if self.param_values["stuck_after_no_improv"].isdigit():
        #        self.param_values["stuck_after_no_improv"] = int(
        #            self.param_values["stuck_after_no_improv"]
        #        )
        #    else:
        #        self.param_values["stuck_after_no_improv"] = None
        # elif isinstance(self.param_values["stuck_after_no_improv"], int):
        #    pass
        # else:
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

        # if isinstance(self.param_values["stuck_after_no_improv"], str):
        #    if self.param_values["stuck_after_no_improv"].isdigit():
        #        self.param_values["stuck_after_no_improv"] = int(
        #            self.param_values["stuck_after_no_improv"]
        #        )
        #    else:
        #        self.param_values["stuck_after_no_improv"] = None
        # elif isinstance(self.param_values["stuck_after_no_improv"], int):
        #    pass
        # else:
        #    self.param_values["stuck_after_no_improv"] = None

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
        print_model(self.models["best_model"])
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
        # if self.param_values["pre_files"] and self.step_c == -1:
        #    print(model.cost)

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

        self.start_time = time.time()
        self.step_c = -1

        self.strategy.pre_setup(self)

        start_sol = []
        if self.param_values["start_sol"]:
            start_sol = str_to_symbols(self.param_values["start_sol"])

        self.solver.setup(self)

        self.strategy.post_setup(self)

        ## pre solving
        # if self.param_values["pre_files"]:
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

        self.strategy.post_first_solution(self)

        while not (self.strategy.check_stop(self) or self.stopped):
            self.step_c += 1
            if self.step_c % 50 == 0:
                print(
                    f"{time.time() - self.start_time:.3f}s: {self.step_c}|{self.param_values['max_steps']}"
                )
            self.strategy.pre_relax(self)
            fixed_atoms = self.strategy.relax(
                self.models["new_model"],
                {
                    "relax_rate": self.param_values["relax_rate"],
                    "base_relax_rate": self.param_values["base_relax_rate"],
                },
            )
            if self.strategy.repair(self, fixed_atoms).satisfiable:
                self.strategy.post_repair(self)
                if self.strategy.check_accept(self):
                    self.models["current_model"] = self.models["new_model"].copy()
                    self.strategy.accepted(self)
                if self.strategy.check_better(self):
                    self.models["best_model"] = self.models["new_model"].copy()
                    print(
                        f'{time.time() - self.start_time:.3f}s: {self.step_c}|{self.param_values["max_steps"]} '
                        f'New best solution: {get_cost_str(self.models["best_model"])}'
                    )
                    self.strategy.better(self)
                    self.no_improv_c = 0
            # if not improv:
            #   self.no_improv_c += 1
            # self.strategy.stuck_handling(self)
        print("==================")
        print("SEARCH FINISHED:")
        print_model(self.models["best_model"])
        print(f"Overall steps: {self.step_c}")
        print(f"Overall time: {time.time() - self.start_time:.3f}s")


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

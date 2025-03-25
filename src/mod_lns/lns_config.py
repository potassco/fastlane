"""
Configuration class used for LNS framework.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence, Type, Union, no_type_check

import clingo
from clingo.symbol import Function, Number

from .interfaces.solver import SolverInterface
from .interfaces.strategy import StrategyInterface
from .lib.relaxation import relax_declarative
from .lib.solvers.clingo_solver import ClingoSolver
from .lib.strategies.default_strategy import DefaultStrategy
from .utils.conversions import symbol_to_str

if TYPE_CHECKING:
    from mod_lns import LNS  # nocoverage


# pylint: disable=too-few-public-methods, dangerous-default-value
class LNSConfig:
    """
    LNS configuration class.
    Defines base solver and strategy objects and modifies them
    according to the given LNS options.

    :param lns_options: LNS options.
    :type lns_options: dict[str, Any]
    :default lns_options: {}
    :param clingo_options: clingo options.
    :type clingo_options: list[str]
    :default clingo_options: []
    :param solver: Solver object used as base for LNS.
    :type solver: SolverInterface
    :default solver: ClingoSolver()
    :param strategy: Strategy object used as base for LNS.
    :type strategy: StrategyInterface
    :default strategy: DefaultStrategy()
    """

    def __init__(
        self,
        lns_options: dict[str, Any] = {},
        clingo_options: list[str] = [],
        solver: SolverInterface = ClingoSolver(),
        strategy: StrategyInterface = DefaultStrategy(),
    ):
        """
        Initialize lns config.
        """
        default_options = {
            "heuristics": False,
            "constrained": False,
            "declarative": False,
            "relax_rate": 0.2,
            "max_steps": "2000",
            "solve_time_limit": 20,
            "overall_time_limit": 600,
        }

        self.lns_options = {**default_options, **lns_options}
        self.clingo_options = clingo_options

        # solver
        self.solver = solver
        if self.lns_options["heuristics"]:
            self._enable_heuristics()

        # strategy
        self.strategy = strategy
        if self.lns_options["constrained"]:
            self._enable_constrained_approach()
        elif not any(o.startswith("--rand-freq") for o in self.clingo_options):
            self.clingo_options = self.clingo_options + ["--rand-freq=0.05"]
        if self.lns_options["declarative"]:
            self._enable_declarative()

    def _enable_heuristics(self) -> None:
        """
        Adjust base solver to use heuristics for reparation.
        """

        @no_type_check
        def setup(
            self,
            lns_object: LNS,
            files: Optional[list[str]] = None,
            args: list[str] = [],
        ) -> None:
            """
            Set up heuristics.

            :param lns_object: LNS object.
            :type lns_object: large_neighbourhood_search.LNS
            :param files: ASP files to be loaded, default: lns_object.param_values["files"].
            :type files: Optional[list[str]]
            :param args: clingo arguments, default: lns_object.param_values["clingo_args"].
            :type args: list[str]
            :default args: []
            """
            if len(args) == 0:
                args = lns_object.clingo_options + ["--heuristic=Domain"]
            else:
                args = args + ["--heuristic=Domain"]

            super(EnHeu, self).setup(  # pylint: disable=bad-super-call
                lns_object, files, args
            )

            # used for heuristics, see solve_fixed()
            self.control.add("_lns_h_step", ["s"], "#external _lns_h_step(s).")

        @no_type_check
        def repair(
            self,
            lns_object: LNS,
            fixed_atoms: list[tuple[clingo.symbol.Symbol, bool]],
        ) -> clingo.solving.SolveResult:
            """
            Use heuristics during reparation.

            :param lns_object: LNS object.
            :type lns_object: large_neighbourhood_search.LNS
            :param assumptions: Assumptions for solving (fixed atoms).
            :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
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
            res = super(EnHeu, self).repair(  # pylint: disable=bad-super-call
                lns_object, fixed_atoms
            )

            # release externals
            if isinstance(self.control, clingo.control.Control):
                self.control.release_external(Function("_lns_h_step", [Number(step)]))
            return res

        base: Type[SolverInterface] = type(self.solver)
        EnHeu = type("EnHeu", (base,), {"setup": setup, "repair": repair})
        self.solver = EnHeu()

    def _enable_constrained_approach(self) -> None:
        """
        Adjust base strategy to use constrained approach.
        """

        @no_type_check
        def post_first_solution(self, lns_object: LNS) -> None:
            """
            Enforce better solution by implementing initial cost as hard constraint.

            :param lns_object: LNS object.
            :type lns_object: large_neighbourhood_search.LNS
            """
            super(EnCons, self).post_first_solution(  # pylint: disable=bad-super-call
                lns_object
            )
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

        # pylint: disable=unused-argument
        @no_type_check
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

        @no_type_check
        def better(self, lns_object: LNS) -> None:
            """
            Update constraint after new best solution was found.

            :param lns_object: LNS object.
            :type lns_object: large_neighbourhood_search.LNS
            """
            super(EnCons, self).better(lns_object)  # pylint: disable=bad-super-call
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

        base: Type[StrategyInterface] = type(self.strategy)
        EnCons = type(
            "EnCons",
            (base,),
            {
                "post_first_solution": post_first_solution,
                "check_better": check_better,
                "better": better,
            },
        )
        self.strategy = EnCons()

    @no_type_check
    def _enable_declarative(self) -> None:
        """
        Adjust base strategy to use declarative relaxation.
        """

        # pylint: disable=unused-argument
        def relax(
            self,
            model: dict[str, Union[Sequence[clingo.symbol.Symbol], Any]],
            relax_parameters: dict[str, Any],
        ) -> list[tuple[clingo.symbol.Symbol, bool]]:
            """
            Relax portion of atoms given by the relax_parameters.
            Use declarative random relaxation.

            :param model: dictionary containing list of shown and true atoms.
            :type model: dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
            :param relax_parameters: Parameters used to determine relaxed atoms.
            :type relax_parameters: dict[str, Any]
            :return: Fixed (not relaxed) atoms.
            :rtype: list[tuple[clingo.symbol.Symbol, bool]]
            """
            return relax_declarative(model, relax_parameters)

        base: Type[StrategyInterface] = type(self.strategy)
        EnDecl = type("EnDecl", (base,), {"relax": relax})
        self.strategy = EnDecl()

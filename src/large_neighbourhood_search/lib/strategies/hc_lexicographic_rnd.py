"""
Strategy implementing LNS using hard constraints with lexicographic optimization criteria and random relaxation.
Based on HCWeightedSumRnd class.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, List, Sequence

import clingo
from clingo.symbol import Function, Number, SymbolType

from large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd import (
    HCWeightedSumRnd,
)
from large_neighbourhood_search.lib.utils import fix_symbols

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class HCLexiRnd(HCWeightedSumRnd):
    """
    LNS using hard constraints with lexicographic optimization criteria and random relaxation.
    """

    def calc_cost(self, model: Dict[str, Sequence[clingo.symbol.Symbol]]) -> Any:
        """
        Calculate cost of given model using lexicographic ordering.

        :param model: Model.
        :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
        :return: Cost of given model.
        :rtype: Any
        """
        priorities: Dict[str, int] = {}
        temp_val: Dict[str, int] = {}
        cost: Dict[int, int] = {}
        for atom in model["true"]:
            if atom.match("_lns_priority", 2):
                if (
                    atom.arguments[0].type is SymbolType.String
                    and atom.arguments[1].type is SymbolType.Number
                ):
                    priorities[atom.arguments[0].string] = atom.arguments[1].number
            elif atom.match("_lns_penalty", 3):
                if (
                    atom.arguments[0].type is SymbolType.String
                    and atom.arguments[2].type is SymbolType.Number
                ):
                    temp_val[atom.arguments[0].string] = (
                        temp_val.get(atom.arguments[0].string, 0)
                        + atom.arguments[2].number
                    )
        for item in priorities.items():
            cost[item[1]] = cost.get(item[1], 0) + temp_val.get(item[0], 0)
        return cost

    # pylint: disable=dangerous-default-value
    def first_solution(
        self, lns_object: LNS, start_sol: List[clingo.symbol.Symbol] = []
    ) -> bool:
        """
        Find initial solution.
        Ground found optimization value as hard constraint.
        Use lexicographic optimization.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param start_sol: optional start solution.
        :type start_sol: List[clingo.symbol.Symbol]
        :default start_sol: []
        :return: Whether a solution was found or not
        :rtype: bool
        """
        lns_object.solver.ground_base(lns_object)

        fixed_sym = []
        if start_sol:
            fixed_sym = fix_symbols(start_sol)

        # get first solution
        if lns_object.solver.solve_fixed(lns_object, fixed_sym).satisfiable:
            cost = lns_object.models["new_model"]["cost"]
            print(f"Initial solution found with cost: {cost}")

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
            if isinstance(lns_object.solver.ctl, clingo.control.Control):
                lns_object.solver.ctl.add("cost", s, rules)
                lns_object.solver.ctl.ground(
                    [
                        (
                            "cost",
                            [Number(0)]
                            + [Number(cost[prio]) for prio in sorted(cost.keys())],
                        )
                    ]
                )
                lns_object.solver.ctl.assign_external(
                    Function("_lns_l_step", [Number(0)]), True
                )

            lns_object.models["current_model"] = lns_object.models["new_model"].copy()
            lns_object.models["best_model"] = lns_object.models["new_model"].copy()
            return True
        print("No first solution found.")
        return False

    def check_stop(self, lns_object: LNS) -> bool:
        """
        Check whether to stop LNS.

        Stop if:
        cost = 0,
        max # of steps exceeded,
        overall time limit exceeded

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether to stop LNS or not.
        :rtype: bool
        """
        if all(
            lns_object.models["best_model"]["cost"][i] == 0
            for i in lns_object.models["best_model"]["cost"]
        ):
            return True
        return (
            lns_object.step_c >= lns_object.param_values["max_steps"]
            or time.time() - lns_object.start_time
            >= lns_object.param_values["overall_time_limit"]
        )

    def update_grounding(self, lns_object: LNS) -> None:
        """
        Update grounding after new best solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """
        step = lns_object.step_c
        if isinstance(lns_object.solver.ctl, clingo.control.Control):
            lns_object.solver.ctl.release_external(
                Function("_lns_l_step", [Number(step - 1)])
            )
            cost = lns_object.models["best_model"]["cost"]
            lns_object.solver.ctl.ground(
                [
                    (
                        "cost",
                        [Number(step)]
                        + [Number(cost[prio]) for prio in sorted(cost.keys())],
                    )
                ]
            )
            lns_object.solver.ctl.assign_external(
                Function("_lns_l_step", [Number(step)]), True
            )

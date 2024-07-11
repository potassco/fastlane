"""
Strategy implementing LNS using hard constraints with lexicographic optimization criteria and random relaxation.
Based on HCWeightedSumRND class.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, Sequence

import clingo
from clingo.symbol import Function, Number, SymbolType
from large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd import HCWeightedSumRnd

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class HCLexiRnd(HCWeightedSumRnd):
    """
    LNS using hard constraints with lexicographic optimization criteria and random relaxation.
    """

    def calc_cost(model: Dict[str, Sequence[clingo.symbol.Symbol]]) -> Any:
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

    def first_solution(self, lns_object: LNS) -> bool:
        """
        Find initial solution.
        Ground found optimization value as hard constraint.
        Use lexicographic optimization.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether a solution was found or not
        :rtype: bool
        """
        lns_object._solver.ground_base(lns_object)

        # get first solution
        if lns_object._solver.solve_under_assumptions(lns_object, []).satisfiable:
            cost = lns_object.models["new_model"]["cost"]
            print(f"Initial solution found with cost: {cost}")

            # add rules to force better solution with each iteration
            # encoding has to contain _lns_penalty(N,I,W) predicates and _lns_priority(N,P) facts
            # where N: name, I: identifier, W: weight, P: priority
            # higher priority = more important
            # priorities have to be declared consecutively, e.g. only 1 and 3 not allowed
            # example of generated rules with ground values for cost={1:3, 2:4}
            #   #external step(s).
            #   bettereq(P+1,s) :- _lns_priority(_,P), not _lns_penalty(_,P+1), step(s).
            #   :- not better(_,s), step(s).
            #   better(1,s) :- _lns_priority(N,1), #sum{V,I: _lns_penalty(N,I,W)} < 3, bettereq(1,s), step(s).
            #   bettereq(1,s) :- _lns_priority(N,1), #sum{V,I: _lns_penalty(N,I,W)} <= 3, bettereq(2,s), step(s).
            #   better(2,s) :- _lns_priority(N,2), #sum{V,I: _lns_penalty(N,I,W)} < 4, bettereq(2,s), step(s).
            #   bettereq(2,s) :- _lns_priority(N,2), #sum{V,I: _lns_penalty(N,I,W)} <= 4, bettereq(3,s), step(s).

            s = ["s"] + list(map(lambda x: f"cost{x}", cost.keys()))
            rules = "#external step(s).\
            bettereq(P+1,s) :- _lns_priority(_,P), not _lns_priority(_,P+1), step(s).\
            :- not better(_,s), step(s).".join(
                list(
                    map(
                        lambda x: f"better({x},s) :- _lns_priority(N,{x}),\
                            #sum{{V,I: _lns_penalty(N,I,V)}} < cost{x}, bettereq({x},s), step(s).",
                        cost.keys(),
                    )
                )
                + list(
                    map(
                        lambda x: f"bettereq({x},s) :- _lns_priority(N,{x}),\
                            #sum{{V,I: _lns_penalty(N,I,V)}} <= cost{x}, bettereq({x+1},s), step(s).",
                        cost.keys(),
                    )
                )
            )
            lns_object._solver._ctl.add("cost", s, rules)
            lns_object._solver._ctl.ground(
                [
                    (
                        "cost",
                        [Number(0)]
                        + [Number(cost[prio]) for prio in sorted(cost.keys())],
                    )
                ]
            )
            lns_object._solver._ctl.assign_external(Function("step", [Number(0)]), True)

            lns_object.models["current_model"] = lns_object.models["new_model"].copy()
            lns_object.models["best_model"] = lns_object.models["new_model"].copy()
            return True
        print("No first solution found.")
        return False

    def check_stop(self, lns_object: LNS) -> bool:
        """
        Check whether to stop LNS.
        Stop if:
            cost = 0
            max # of steps exceeded
            overall time limit exceeded

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether to stop LNS or not.
        :rtype: bool
        """
        if (
            all(
                [
                    lns_object.models["best_model"]["cost"][i]
                    for i in lns_object.models["best_model"]["cost"]
                ]
            )
            == 0
        ):
            return True
        return (
            lns_object._step_c >= lns_object.param_values["max_steps"]
            or time.time() - lns_object._start_time
            >= lns_object.param_values["overall_time_limit"]
        )

    # pylint: disable=unused-argument
    def update_grounding(self, lns_object: LNS) -> None:
        """
        Update grounding after new best solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """
        step = lns_object._step_c
        lns_object._solver._ctl.release_external(Function("step", [Number(step - 1)]))
        cost = lns_object.models["best_model"]["cost"]
        lns_object._solver._ctl.ground(
            [
                (
                    "cost",
                    [Number(step)]
                    + [Number(cost[prio]) for prio in sorted(cost.keys())],
                )
            ]
        )
        lns_object._solver._ctl.assign_external(Function("step", [Number(step)]), True)

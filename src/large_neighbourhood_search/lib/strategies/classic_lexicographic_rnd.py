"""
Strategy implementing classic LNS with lexicographic optimization criteria and random relaxation.
Based on ClassicWeightedSumRnd class.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, Sequence

import clingo
from clingo.symbol import SymbolType

from large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd import (
    ClassicWeightedSumRnd,
)
from large_neighbourhood_search.lib.utils import check_smaller_lexicographic

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class ClassicLexiRnd(ClassicWeightedSumRnd):
    """
    Classic LNS with lexicographic optimization criteria and random relaxation.
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

    def check_stop(self, lns_object: LNS) -> bool:
        """
        Check whether to stop LNS.

        Stop if:
        all cost = 0,
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
        if isinstance(lns_object.param_values["max_steps"], int):
            return (
                lns_object.step_c >= lns_object.param_values["max_steps"]
                or time.time() - lns_object.start_time
                >= lns_object.param_values["overall_time_limit"]
            )
        return (
            time.time() - lns_object.start_time
            >= lns_object.param_values["overall_time_limit"]
        )

    def check_better(
        self,
        lns_object: LNS,
    ) -> bool:
        """
        Check whether new model is better.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether new model is better or not.
        :rtype: bool
        """
        return check_smaller_lexicographic(
            lns_object.models["new_model"]["cost"],
            lns_object.models["best_model"]["cost"],
        )

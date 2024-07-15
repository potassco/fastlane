"""
Strategy implementing LNS using hard constraints with weighted sum as optimization criteria and random relaxation.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, List, Sequence, Tuple, Union

import clingo
from clingo.symbol import Number, SymbolType

from large_neighbourhood_search.interfaces.strategy import StrategyInterface
from large_neighbourhood_search.lib.relaxation import relax_random

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


# pylint: disable=duplicate-code
class HCWeightedSumRnd(StrategyInterface):
    """
    LNS using hard constraints with weighted sum as optimization criteria and random relaxation.
    """

    def calc_cost(
        self, model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
    ) -> Any:
        """
        Calculate cost of given model using weighted sum.

        :param model: Model.
        :type model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
        :return: Cost of given model.
        :rtype: Any
        """
        cost = 0
        for atom in model["true"]:
            if atom.match("_lns_penalty", 3):
                if atom.arguments[2].type is SymbolType.Number:
                    cost += atom.arguments[2].number
        return cost

    def first_solution(self, lns_object: LNS) -> bool:
        """
        Find initial solution.
        Ground found optimization value as hard constraint.
        Use weighted sum as optimization criteria.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether a solution was found or not
        :rtype: bool
        """
        lns_object.solver.ground_base(lns_object)

        # get first solution
        if lns_object.solver.solve_under_assumptions(lns_object, []).satisfiable:
            cost = lns_object.models["new_model"]["cost"]
            print(f"Initial solution found with cost: {cost}")

            # add constraint to force better solution with each iteration
            # encoding has to contain _lns_penalty(N,I,W) predicates
            # where N: name, I: identifier, W: weight
            if isinstance(lns_object.solver.ctl, clingo.control.Control):
                lns_object.solver.ctl.add(
                    "cost", ["c"], ":- #sum{W,I: _lns_penalty(_,I,W)} >= c."
                )
                lns_object.solver.ctl.ground([("cost", [Number(cost)])])

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
        if lns_object.models["best_model"]["cost"] == 0:
            return True
        return (
            lns_object.step_c >= lns_object.param_values["max_steps"]
            or time.time() - lns_object.start_time
            >= lns_object.param_values["overall_time_limit"]
        )

    def relax(
        self,
        model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]],
        relax_parameters: Dict[str, Any],
    ) -> List[Tuple[clingo.symbol.Symbol, bool]]:
        """
        Relax portion of atoms given by the relax_parameters.
        Use random relaxation.

        :param model: Dictionary containing list of shown and true atoms.
        :type model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
        :param relax_parameters: Parameters used to determine relaxed atoms.
        :type relax_parameters: Dict[str, Any]
        :return: Fixed (not relaxed) atoms.
        :rtype: List[Tuple[clingo.symbol.Symbol, bool]]
        """
        return relax_random(model, relax_parameters)

    def repair(
        self, lns_object: LNS, fixed_atoms: List[Tuple[clingo.symbol.Symbol, bool]]
    ) -> clingo.solving.SolveResult:
        """
        Repair solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param fixed_atoms: Fixed atoms.
        :type fixed_atoms: List[Tuple[clingo.symbol.Symbol, bool]]
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        return lns_object.solver.solve_under_assumptions(lns_object, fixed_atoms)

    # pylint: disable=unused-argument
    def check_accept(
        self,
        lns_object: LNS,
    ) -> bool:
        """
        Check whether new model is accepted.
        Always accept.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether new model is accepted or not.
        :rtype: bool
        """
        return True

    def check_better(
        self,
        lns_object: LNS,
    ) -> bool:
        """
        Check whether new model is better.
        Enforced by constraint.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether new model is better or not.
        :rtype: bool
        """
        return True

    # pylint: disable=unused-argument
    def update_grounding(self, lns_object: LNS) -> None:
        """
        Update grounding after new best solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """
        if isinstance(lns_object.solver.ctl, clingo.control.Control):
            lns_object.solver.ctl.ground(
                [("cost", [Number(lns_object.models["best_model"]["cost"])])]
            )

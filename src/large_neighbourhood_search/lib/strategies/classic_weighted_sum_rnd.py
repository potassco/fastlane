"""
Strategy implementing classic LNS with weighted sum as optimization criteria and random relaxation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Sequence, Tuple

import clingo
from clingo.symbol import Function, Number, SymbolType
from interfaces.strategy import StrategyInterface

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class ClassicWeightedSumRND(StrategyInterface):
    """
    Classic LNS with weighted sum as optimization criteria and random relaxation.
    """

    def calc_opt_val(self, model: Dict[str, Sequence[clingo.symbol.Symbol]]) -> Any:
        """
        Calculate optimization value of given model using weighted sum.

        :param model: Model.
        :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
        :return: Optimization value of given model.
        :rtype: Any
        """
        opt_val = 0
        for atom in model["true"]:
            if atom.match("_lns_penalty", 3):
                if atom.arguments[2].type is SymbolType.Number:
                    opt_val += atom.arguments[2].number
        return opt_val

    def first_solution(self, lns_object: LNS, ctl, thy: Any) -> bool:
        """
        Find initial solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param ctl: Control object used for search.
        :type ctl: clingo.control.Control
        :param thy: Theory object used for search.
        :type thy: Any
        :return: Whether a solution was found or not
        :rtype: bool
        """
        ctl.ground([("base", [])], context=lns_object)

        # get first solution
        if lns_object._solver.solve_under_assumptions(
            lns_object, ctl, [], thy
        ).satisfiable:
            new_opt_val = self.calc_opt_val(lns_object.models["new_model"])
            print(f"Initial solution found with opt_val: {new_opt_val}")
            lns_object.models["current_model"] = lns_object.models["new_model"].copy()
            lns_object.models["best_model"] = lns_object.models["new_model"].copy()
            return True
        print("No first solution found.")
        return False

    def check_stop(self, lns_object: LNS) -> bool:
        """
        Check whether to stop LNS.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether to stop LNS or not.
        :rtype: bool
        """
        raise NotImplementedError

    def relax(
        self,
        model: Dict[str, Sequence[clingo.symbol.Symbol]],
        relax_parameters: Dict[str, Any],
    ) -> List[Tuple[clingo.symbol.Symbol, bool]]:
        """
        Relax portion of atoms given by the relax_parameters.

        :param model: Dictionary containing list of shown and true atoms.
        :type model: Dict[str, Sequence[clingo.symbol.Symbol]]
        :param relax_parameters: Parameters used to determine relaxed atoms.
        :type relax_parameters: Dict[str, Any]
        :return: Fixed (not relaxed) atoms.
        :rtype: List[Tuple[clingo.symbol.Symbol, bool]]
        """
        raise NotImplementedError

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
        return lns_object._solver.solve_under_assumptions(lns_object, fixed_atoms)

    def check_accept(
        self,
        lns_object: LNS,
        new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
        current_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    ) -> bool:
        """
        Check whether new model is accepted.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param new_model: New model checked for acceptance.
        :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
        :param current_model: Current model used for comparison.
        :type current_model: Dict[str, Sequence[clingo.symbol.Symbol]]
        :return: Whether new model is accepted or not.
        :rtype: bool
        """
        raise NotImplementedError

    def check_better(
        self,
        lns_object: LNS,
        new_model: Dict[str, Sequence[clingo.symbol.Symbol]],
        best_model: Dict[str, Sequence[clingo.symbol.Symbol]],
    ) -> bool:
        """
        Check whether new model is better.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param new_model: New model being checked.
        :type new_model: Dict[str, Sequence[clingo.symbol.Symbol]]
        :param best_model: Current model used for comparison.
        :type best_model: Dict[str, Sequence[clingo.symbol.Symbol]]
        :return: Whether new model is better or not.
        :rtype: bool
        """
        raise NotImplementedError

    def update_grounding(self, lns_object: LNS, ctl: clingo.control.Control) -> None:
        """
        Update grounding after new best solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param ctl: Clingo control object used for solving.
        :type ctl: clingo.control.Control
        """
        raise NotImplementedError

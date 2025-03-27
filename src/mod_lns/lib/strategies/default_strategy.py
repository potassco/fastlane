"""
Default strategy implementing classic LNS with weighted sum as optimization criteria and random relaxation.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import clingo

from mod_lns import Model
from mod_lns.interfaces.strategy import StrategyInterface
from mod_lns.lib.relaxation import relax_random
from mod_lns.lib.utils import (
    calculate_variability,
    fix_symbols,
)

if TYPE_CHECKING:
    from mod_lns import LNS, Model  # nocoverage


# pylint: disable=duplicate-code
class DefaultStrategy(StrategyInterface):
    """
    Classic LNS with weighted sum as optimization criteria and random relaxation.
    """

    # pylint: disable=dangerous-default-value
    def get_first_solution(
        self, lns_object: LNS, start_sol: list[clingo.symbol.Symbol] = []
    ) -> bool:
        """
        Find initial solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param start_sol: optional start solution.
        :type start_sol: list[clingo.symbol.Symbol]
        :default start_sol: []
        :return: Whether a solution was found or not
        :rtype: bool
        """
        lns_object.solver.ground_base(lns_object)

        fixed_sym = []
        if start_sol:
            fixed_sym = fix_symbols(start_sol)

        # get first solution
        if lns_object.solver.repair(lns_object, fixed_sym).satisfiable:
            print(
                f"{time.time() - lns_object.start_time:.3f}s: Initial solution found with cost: "
                f"{lns_object.new_model.get_cost_str()}"
            )
            lns_object.current_model = lns_object.new_model
            lns_object.best_model = lns_object.new_model
            return True
        print("No first solution found.")
        return False

    def check_stop(self, lns_object: LNS) -> bool:
        """
        Check whether to stop LNS.

        Stop if:
        max # of steps exceeded,
        overall time limit exceeded

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether to stop LNS or not.
        :rtype: bool
        """
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

    def relax(
        self,
        model: Model,
        relax_parameters: dict[str, Any],
    ) -> list[tuple[clingo.symbol.Symbol, bool]]:
        """
        Relax portion of atoms given by the relax_parameters.
        Use random relaxation.

        :param model: dictionary containing list of shown and true atoms.
        :type model: Model
        :param relax_parameters: Parameters used to determine relaxed atoms.
        :type relax_parameters: dict[str, Any]
        :return: Fixed (not relaxed) atoms.
        :rtype: list[tuple[clingo.symbol.Symbol, bool]]
        """
        return relax_random(model, relax_parameters)

    def repair(
        self, lns_object: LNS, fixed_atoms: list[tuple[clingo.symbol.Symbol, bool]]
    ) -> clingo.solving.SolveResult:
        """
        Repair solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param fixed_atoms: Fixed atoms.
        :type fixed_atoms: list[tuple[clingo.symbol.Symbol, bool]]
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        return lns_object.solver.repair(lns_object, fixed_atoms)

    # pylint: disable=unused-argument
    def check_accept(
        self,
        lns_object: LNS,
    ) -> bool:
        """
        Check whether new model is accepted.
        Accept if desired variability is achieved.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether new model is accepted or not.
        :rtype: bool
        """
        vari = calculate_variability(
            lns_object.new_model.shown,
            lns_object.current_model.shown,
        )
        return vari >= lns_object.param_values["vari_accept"]

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
        return lns_object.new_model.cost < lns_object.best_model.cost

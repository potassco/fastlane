"""
Modification functions for Strategy classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence, Type, Union, no_type_check

import clingo

from mod_lns.interfaces.solver import SolverInterface
from mod_lns.interfaces.strategy import StrategyInterface
from mod_lns.lib.relaxation import relax_declarative

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


def enable_constrained_approach(
    solver: SolverInterface, strategy: StrategyInterface
) -> tuple[SolverInterface, StrategyInterface]:
    """
    Adjust base solver and strategy to use constrained approach.

    :param solver: Solver used as base.
    :type solver: SolverInterface
    :param strategy: Strategy used as base.
    :type strategy: StrategyInterface
    :return: Modified solver and strategy using constrained approach.
    :rtype: tuple[SolverInterface, StrategyInterface]
    """

    @no_type_check
    def repair(
        self,
        lns_object: LNS,
        fixed_atoms: list[tuple[clingo.symbol.Symbol, bool]],
        time_limit: Optional[int] = None,
        model_limit: int = 1,
    ) -> clingo.solving.SolveResult:
        """
        Force better solution in next iteration after cost is determined.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
        :param time_limit: Manually set time limit for solve call.
        :type time_limit: Optional[int]
        :default time_limit: None
        :param model_limit: Set number of calculated models.
        :type model_limit: int
        :default model_limit: 1
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        res = super(EnConsSolver, self).repair(  # pylint: disable=bad-super-call
            lns_object, fixed_atoms, time_limit, model_limit
        )
        cost = lns_object.new_model.cost
        if res.satisfiable:
            bound = cost[:-1] + [cost[-1] - 1]
            self.control.configuration.solve.opt_mode = "opt, " + ", ".join(
                [str(c) for c in bound]
            )
        return res

    sol_base: Type[SolverInterface] = type(solver)
    EnConsSolver = type("EnConsSolver", (sol_base,), {"repair": repair})

    # pylint: disable=unused-argument
    @no_type_check
    def check_better(self, lns_object: LNS) -> bool:
        """
        Check whether new model is better.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether new model is better or not.
        :rtype: bool
        """
        return True

    strat_base: Type[StrategyInterface] = type(strategy)
    EnConsStrat = type("EnConsStrat", (strat_base,), {"check_better": check_better})

    return EnConsSolver(), EnConsStrat()


@no_type_check
def enable_declarative(strategy: StrategyInterface) -> StrategyInterface:
    """
    Adjust base strategy to use declarative relaxation.

    :param strategy: Strategy used as base.
    :type strategy: StrategyInterface
    :return: Modified strategy using declarative relaxation.
    :rtype: StrategyInterface
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

    base: Type[StrategyInterface] = type(strategy)
    EnDecl = type("EnDecl", (base,), {"relax": relax})
    return EnDecl()

"""
Strategy interface used for LNS.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Dict, List, Sequence, Tuple, Union

import clingo

if TYPE_CHECKING:
    from mod_lns import LNS  # nocoverage

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


class StrategyInterface(metaclass=abc.ABCMeta):
    """
    Strategy interface.
    """

    @classmethod
    def __subclasshook__(cls, subclass):  # nocoverage
        return (
            hasattr(subclass, "get_first_solution")
            and callable(subclass.first_solution)
            and hasattr(subclass, "calculate_cost")
            and callable(subclass.calc_cost)
            and hasattr(subclass, "check_stop")
            and callable(subclass.check_stop)
            and hasattr(subclass, "relax")
            and callable(subclass.relax)
            and hasattr(subclass, "repair")
            and callable(subclass.repair)
            and hasattr(subclass, "check_accept")
            and callable(subclass.check_accept)
            and hasattr(subclass, "check_better")
            and callable(subclass.check_better)
            #  and hasattr(subclass, "update_grounding")
            # and callable(subclass.update_grounding)
            or NotImplemented
        )

    @abc.abstractmethod
    def calculate_cost(
        self, model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
    ) -> Any:  # nocoverage
        """
        Calculate cost of given model.

        :param model: Model.
        :type model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
        :return: Cost of given model.
        :rtype: Any
        """
        raise NotImplementedError

    def pre_setup(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something pre solver setup.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """

    def post_setup(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something post solver setup.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """

    @abc.abstractmethod
    def get_first_solution(
        self, lns_object: LNS, start_sol: List[clingo.symbol.Symbol]
    ) -> bool:  # nocoverage
        """
        Find initial solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param start_sol: optional start solution.
        :type lns_object: List[clingo.symbol.Symbol]
        :return: Whether a solution was found or not
        :rtype: bool
        """
        raise NotImplementedError

    def post_first_solution(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something post first solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """

    @abc.abstractmethod
    def check_stop(self, lns_object: LNS) -> bool:  # nocoverage
        """
        Check whether to stop LNS.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether to stop LNS or not.
        :rtype: bool
        """
        raise NotImplementedError

    def pre_relax(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something pre relaxation.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """

    @abc.abstractmethod
    def relax(
        self,
        model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]],
        relax_parameters: Dict[str, Any],
    ) -> List[Tuple[clingo.symbol.Symbol, bool]]:  # nocoverage
        """
        Relax portion of atoms given by the relax_parameters.

        :param model: Dictionary containing list of shown and true atoms.
        :type model: Dict[str, Union[Sequence[clingo.symbol.Symbol], Any]]
        :param relax_parameters: Parameters used to determine relaxed atoms.
        :type relax_parameters: Dict[str, Any]
        :return: Fixed (not relaxed) atoms.
        :rtype: List[Tuple[clingo.symbol.Symbol, bool]]
        """
        raise NotImplementedError

    @abc.abstractmethod
    def repair(
        self, lns_object: LNS, fixed_atoms: List[Tuple[clingo.symbol.Symbol, bool]]
    ) -> clingo.solving.SolveResult:  # nocoverage
        """
        Repair solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        raise NotImplementedError

    def post_repair(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something post repair.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """

    @abc.abstractmethod
    def check_accept(
        self,
        lns_object: LNS,
    ) -> bool:  # nocoverage
        """
        Check whether new model is accepted.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether new model is accepted or not.
        :rtype: bool
        """
        raise NotImplementedError

    def accepted(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something after new model is accepted and saved as the new current model.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """

    @abc.abstractmethod
    def check_better(
        self,
        lns_object: LNS,
    ) -> bool:  # nocoverage
        """
        Check whether new model is better.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether new model is better or not.
        :rtype: bool
        """
        raise NotImplementedError

    def better(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something after new model is better and saved as the new best model.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """

    # @abc.abstractmethod
    # def update_grounding(self, lns_object: LNS) -> None:  # nocoverage
    #    """
    #    Update grounding after new best solution.#
    #
    #    :param lns_object: LNS object.
    #    :type lns_object: large_neighbourhood_search.LNS
    #    """
    #    raise NotImplementedError

    # beeing reworked
    # pylint: disable=unused-argument
    # def stuck_handling(self, lns_object: LNS) -> None:
    #    """
    #    Check whether search is stuck and what to do if it is.
    #
    #    :param lns_object: LNS object.
    #    :type lns_object: large_neighbourhood_search.LNS
    #    """

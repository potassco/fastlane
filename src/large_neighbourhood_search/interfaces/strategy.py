"""
Strategy interface used for LNS.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Dict, List, Sequence, Tuple, Union

import clingo

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class StrategyInterface(metaclass=abc.ABCMeta):
    """
    Strategy interface.
    """

    @classmethod
    def __subclasshook__(cls, subclass):  # nocoverage
        return (
            hasattr(subclass, "first_solution")
            and callable(subclass.first_solution)
            and hasattr(subclass, "calc_cost")
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
            and hasattr(subclass, "update_grounding")
            and callable(subclass.update_grounding)
            or NotImplemented
        )

    @abc.abstractmethod
    def calc_cost(
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

    @abc.abstractmethod
    def first_solution(self, lns_object: LNS) -> bool:  # nocoverage
        """
        Find initial solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Whether a solution was found or not
        :rtype: bool
        """
        raise NotImplementedError

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

    @abc.abstractmethod
    def update_grounding(self, lns_object: LNS) -> None:  # nocoverage
        """
        Update grounding after new best solution.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """
        raise NotImplementedError

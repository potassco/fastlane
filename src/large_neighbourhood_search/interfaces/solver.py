"""
Solver interface used for LNS.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, List, Tuple, Union

import clingo

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class SolverInterface(metaclass=abc.ABCMeta):
    """
    Solver interface.
    """

    def __init__(self):
        self._ctl: Union[clingo.control.Control, None] = None
        self._thy: Any = None

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "setup")
            and callable(subclass.setup)
            and hasattr(subclass, "solve_under_assumptions")
            and callable(subclass.solve_under_assumptions)
            or NotImplemented
        )

    @abc.abstractmethod
    def setup(self, lns_object: LNS) -> None:
        """
        Initialization of the solver.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """
        raise NotImplementedError

    @abc.abstractmethod
    def solve_under_assumptions(
        self,
        lns_object: LNS,
        assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
    ) -> clingo.solving.SolveResult:
        """
        Solve under assumptions.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        raise NotImplementedError

    def ground_base(self, lns_object: LNS) -> None:
        self.ctl.ground([("base", [])], context=lns_object)

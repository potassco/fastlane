"""
Solver interface used for LNS.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

import clingo

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class SolverInterface(metaclass=abc.ABCMeta):
    """
    Solver interface.
    """

    def __init__(self):
        """
        Initialization of the solver object.
        """
        self.ctl: Optional[clingo.control.Control] = None
        self.thy: Any = None

    @classmethod
    def __subclasshook__(cls, subclass):  # nocoverage
        return (
            hasattr(subclass, "setup")
            and callable(subclass.setup)
            and hasattr(subclass, "solve_under_assumptions")
            and callable(subclass.solve_under_assumptions)
            or NotImplemented
        )

    @abc.abstractmethod
    def setup(self, lns_object: LNS) -> None:  # nocoverage
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
    ) -> clingo.solving.SolveResult:  # nocoverage
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
        """
        Ground base encoding.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """
        if isinstance(self.ctl, clingo.control.Control):
            self.ctl.ground([("base", [])], context=lns_object)

    def get_avail_solve_time(self, lns_object: LNS) -> int:
        """
        Calculate available solve time.
        (rounded to int)

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Available solve time.
        :rtype: int
        """
        avail_time = lns_object.avail_time
        if avail_time >= lns_object.param_values["solve_time_limit"]:
            return lns_object.param_values["solve_time_limit"]
        return avail_time

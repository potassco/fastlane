"""
Solver interface used for LNS.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Optional

import clingo

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class SolverInterface(metaclass=abc.ABCMeta):
    """
    Solver interface.
    """

    def __init__(self):
        """
        Initialization of the solver object.
        """
        self.control: Optional[clingo.control.Control] = None
        self.theory: Any = None

    @classmethod
    def __subclasshook__(cls, subclass):  # nocoverage
        return (
            hasattr(subclass, "setup")
            and callable(subclass.setup)
            and hasattr(subclass, "repair")
            and callable(subclass.repair)
            and hasattr(subclass, "solve")
            and callable(subclass.solve)
            or NotImplemented
        )

    # pylint: disable=dangerous-default-value
    @abc.abstractmethod
    def setup(
        self,
        lns_object: LNS,
        files: Optional[list[str]] = None,
        args: list[str] = [],
    ) -> None:  # nocoverage
        """
        Initialization of the solver.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param files: ASP files to be loaded.
        :type files: Optional[list[str]]
        :param args: clingo arguments.
        :type args: list[str]
        :default args: []
        """
        raise NotImplementedError

    @abc.abstractmethod
    def repair(
        self,
        lns_object: LNS,
        fixed_atoms: list[tuple[clingo.symbol.Symbol, bool]],
    ) -> clingo.solving.SolveResult:  # nocoverage
        """
        Solve with fixed atoms.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
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
        if isinstance(self.control, clingo.control.Control):
            self.control.ground([("base", [])], context=lns_object)

    def get_available_solve_time(self, lns_object: LNS) -> int:
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

    def get_stats(self) -> dict:
        """
        Get statistics of the last solve call.

        :return: Statistics dictionary.
        :rtype: dict
        """
        if isinstance(self.control, clingo.control.Control):
            return self.control.statistics
        return {}

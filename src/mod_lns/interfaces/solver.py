"""
Solver interface used for LNS.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Optional, Union

import clingo
from clingo.symbol import Symbol

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class SolverConfig:
    configuration: Optional[str]
    opt_strategy: Optional[str]
    opt_heuristic: Optional[str]
    restart_on_model: Optional[str]
    heuristic: Optional[str]
    opt_mode: Optional[str]
    solve_limit: Optional[str]
    time_limit: Optional[float]
    seed: Optional[int]
    variability: bool

    def __init__(self):
        self.configuration = None
        self.opt_strategy = None
        self.opt_heuristic = None
        self.restart_on_model = None
        self.heuristic = None
        self.opt_mode = None
        self.solve_limit = None
        self.time_limit = None
        self.seed = None
        self.variability = True


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
        self.finished: bool = False

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
        args: list[str] = [],
        files: Optional[list[str]] = None,
    ) -> None:  # nocoverage
        """
        Initialization of the solver.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param args: clingo arguments.
        :type args: list[str]
        :default args: []
        :param files: ASP files to be loaded.
        :type files: Optional[list[str]]
        :default files: None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def solve(
        self,
        lns_object: LNS,
        config: Optional[SolverConfig],
        assumptions: list[tuple[clingo.symbol.Symbol, bool]],
    ) -> clingo.solving.SolveResult:  # nocoverage
        """
        Solve with fixed atoms.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
        :param time_limit: Manually set time limit for solve call.
        :type time_limit: Optional[int]
        :default time_limit: None
        :param model_limit: Set number of calculated models.
        :type model_limit: int
        :default model_limit: 0
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        raise NotImplementedError

    def ground(
        self,
        parts: list[tuple[str, list[Symbol]]] = [("base", [])],
        context: Any = None,
    ) -> None:
        """
        Ground base encoding.

        :param parts: Parts to ground.
        :type parts: list[tuple[str, list[Symbol]]]
        :param context: Context for grounding.
        :type context: Any
        :default context: None
        """
        if isinstance(self.control, clingo.control.Control):
            self.control.ground(parts, context)

    def add(self, name: str, parameters: list[str], program: str) -> None:
        """
        Add a program to the solver.

        :param name: Name of the program.
        :type name: str
        :param parameters: Parameters for the program.
        :type parameters: list[str]
        :param program: Program to be added.
        :type program: str
        """
        if isinstance(self.control, clingo.control.Control):
            self.control.add(name, parameters, program)

    def assign_external(self, external: Union[Symbol, int], truth: bool) -> None:
        """
        Assign truth value to external atom.

        :param external: External atom.
        :type external: Union[clingo.symbol.Symbol,int]
        :param truth: Truth value.
        :type truth: bool
        """
        if isinstance(self.control, clingo.control.Control):
            self.control.assign_external(external, truth)

    def release_external(self, external: Union[Symbol, int]) -> None:
        """
        Release external atom.

        :param external: External atom.
        :type external: Union[clingo.symbol.Symbol,int]
        """
        if isinstance(self.control, clingo.control.Control):
            self.control.release_external(external)

    def get_stats(self) -> dict:
        """
        Get statistics of the last solve call.

        :return: Statistics dictionary.
        :rtype: dict
        """
        if isinstance(self.control, clingo.control.Control):
            return self.control.statistics
        return {}

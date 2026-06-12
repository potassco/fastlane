"""
Solver interface used for LNS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import Logger
from typing import TYPE_CHECKING, Any, Optional, Union

import clingo
from clingo.symbol import Symbol

if TYPE_CHECKING:  # nocoverage
    from mod_lns import Model
    from mod_lns.lns import LNS


# pylint: disable=too-many-instance-attributes
@dataclass
class SolverConfig:
    """
    Configuration for a solver.

    :param configuration: Used configuration.
    :type configuration: Optional[str]
    :default configuration: None
    :param opt_strategy: Optimization strategy.
    :type opt_strategy: Optional[str]
    :default opt_strategy: None
    :param opt_heuristic: Optimization in heuristic.
    :type opt_heuristic: Optional[str]
    :default opt_heuristic: None
    :param restart_on_model: Restart on model.
    :type restart_on_model: Optional[str]
    :default restart_on_model: None
    :param heuristic: Heuristic to use.
    :type heuristic: Optional[str]
    :default heuristic: None
    :param opt_mode: Optimization mode.
    :type opt_mode: Optional[str]
    :default opt_mode: None
    :param solve_limit: Solve limit.
    :type solve_limit: Optional[str]
    :default solve_limit: None
    :param time_limit: Time limit for solving.
    :type time_limit: Optional[int]
    :default time_limit: None
    :param cutoff: Cutoff value.
    :type cutoff: Optional[int]
    :default cutoff: None
    :param seed: Random seed.
    :type seed: Optional[int]
    :default seed: None
    :param variability: Variability.
    :type variability: bool
    :default variability: True
    """

    configuration: Optional[str] = None
    opt_strategy: Optional[str] = None
    opt_heuristic: Optional[str] = None
    restart_on_model: Optional[str] = None
    heuristic: Optional[str] = None
    opt_mode: Optional[str] = None
    solve_limit: Optional[str] = None
    time_limit: Optional[int] = None
    cutoff: Optional[int] = None
    seed: Optional[int] = None
    variability: bool = True


class Solver(ABC):
    """
    Solver interface.
    """

    def __init__(self) -> None:
        """
        Initialization of the solver object.
        """
        self.control: Optional[clingo.control.Control] = None
        self.theory: Any = None
        self.finished: bool = False
        self.result = "UNKNOWN"
        self.optimum = "unknown"
        self.minimize_variable: Optional[Symbol] = None
        self.logger: Logger
        self.stop: bool = False
        self._assumptions_used = False
        self.last_model: Optional[Model] = None

        self.stats: dict[str, Any] = {}

    @classmethod
    def __subclasshook__(cls, subclass: type) -> bool:  # nocoverage
        return (
            hasattr(subclass, "get_name")
            and callable(subclass.get_name)
            and hasattr(subclass, "setup")
            and callable(subclass.setup)
            and hasattr(subclass, "repair")
            and callable(subclass.repair)
            and hasattr(subclass, "solve")
            and callable(subclass.solve)
            or NotImplemented
        )

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:  # nocoverage
        """
        Get the name under which the solver will be listed in options.

        :return: Name of the solver.
        :rtype: str
        """
        raise NotImplementedError

    # pylint: disable=dangerous-default-value
    @abstractmethod
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

    @abstractmethod
    def solve(
        self,
        config: Optional[SolverConfig],
        assumptions: list[tuple[clingo.symbol.Symbol, bool]] = [],
    ) -> Optional[Model]:  # nocoverage
        """
        Solve with fixed atoms.

        :config: Solver configuration.
        :type config: SolverConfig
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
        :default assumptions: []
        :return: Last obtained model.
        :rtype: Model
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

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics of the last solve call.

        :return: Statistics dictionary.
        :rtype: dict[str, Any]
        """
        if isinstance(self.control, clingo.control.Control):
            return self.control.statistics
        return {}

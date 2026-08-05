"""
Solver interface used for LNS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Union

import clingo
from clingo.symbol import Symbol

from fastlane.utils.logger import LNSLogger

if TYPE_CHECKING:  # nocoverage
    from fastlane import Model
    from fastlane.lns import LNS


# pylint: disable=too-many-instance-attributes
@dataclass
class SolverConfig:
    """
    Configuration for a solver.
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

        Before solving, setup() method must be called to correctly initialize the solver.
        """
        self.control: clingo.control.Control = clingo.control.Control()
        self.theory: Any = None
        self.finished: bool = False
        self.result = "UNKNOWN"
        self.optimum = "unknown"
        self.minimize_variable: Optional[Symbol] = None
        self.logger: LNSLogger = LNSLogger("temporary_solver_logger")
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
        :param args: clingo arguments.
        :param files: ASP files to be loaded.
        """
        raise NotImplementedError

    @abstractmethod
    def solve(
        self,
        config: Optional[SolverConfig],
        assumptions: list[tuple[clingo.symbol.Symbol, bool]] = [],
        require_model: bool = False,
    ) -> Optional[Model]:  # nocoverage
        """
        Solve with fixed atoms.

        :param config: Solver configuration.
        :param assumptions: Assumptions for solving (fixed atoms).
        :param require_model: If True, ignore cutoff time until a model is found.
        :return: Last obtained model.
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
        :param context: Context for grounding.
        """
        self.control.ground(parts, context)

    def add(self, name: str, parameters: list[str], program: str) -> None:
        """
        Add a program to the solver.

        :param name: Name of the program.
        :param parameters: Parameters for the program.
        :param program: Program to be added.
        """
        self.control.add(name, parameters, program)

    def assign_external(self, external: Union[Symbol, int], truth: bool) -> None:
        """
        Assign truth value to external atom.

        :param external: External atom.
        :param truth: Truth value.
        """
        self.control.assign_external(external, truth)

    def release_external(self, external: Union[Symbol, int]) -> None:
        """
        Release external atom.

        :param external: External atom.
        """
        self.control.release_external(external)

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics of the last solve call.

        :return: Statistics dictionary.
        """
        return self.control.statistics

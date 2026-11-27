"""
Solver interface used for LNS.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Union

import clingo
from clingo.solving import Model as ClingoModel
from clingo.solving import SolveResult
from clingo.statistics import StatisticsMap
from clingo.symbol import Symbol

from fastlane import Model, Timer
from fastlane.utils.logger import LNSLogger, getLogger

if TYPE_CHECKING:  # nocoverage
    from fastlane.lns import LNS


# pylint: disable=too-many-instance-attributes
@dataclass
class SolverConfig:
    """
    Configuration for a solver.

    :ivar configuration: Solver configuration string.
    :ivar opt_strategy: Optimization strategy.
    :ivar opt_heuristic: Optimization heuristic.
    :ivar restart_on_model: Restart on model.
    :ivar heuristic: Heuristic.
    :ivar opt_mode: Optimization mode.
    :ivar solve_limit: Solve limit.
    :ivar time_limit: Time limit.
    :ivar cutoff: Cutoff time limit.
    :ivar seed: Random seed.
    :ivar variability: Variability flag.
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
        self.result: str = "UNKNOWN"
        self.optimum: str = "unknown"
        self.minimize_variable: Optional[Symbol] = None
        self.logger: LNSLogger = getLogger("LNS")
        self.stop: bool = False
        self._assumptions_used: bool = False
        self.interrupted: bool = False
        self.watcher: Optional[SolveWatcher] = None
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
            and hasattr(subclass, "postprocess_solve")
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

    @abstractmethod
    def postprocess_solve(self, model: Optional[ClingoModel], result: SolveResult) -> None:
        """
        Post-process the result of a solve.

        :param model: Last obtained Clingo model.
        :param result: Solve result.
        """
        raise NotImplementedError

    def request_stop(self) -> bool:
        """
        Request shutdown and interrupt any active (or upcoming) solve.

        Control.interrupt() is documented as thread-safe and safe to call from a
        signal handler, so this can be called directly from anywhere, including
        Fastlane's own signal handler.

        Return True while an active solve must still unwind before the caller can proceed.
        """
        self.stop = True
        self.finished = True
        self.interrupted = True
        self.control.interrupt()
        return self.watcher is not None and self.watcher.active

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

    def _prepare_solve(self) -> None:
        """
        Additional preparation before solving.
        """

    def _on_model(self, model: ClingoModel) -> None:
        """
        Handle a new model from the solver.

        :param model: The Clingo model received.
        """

    def _on_statistics(self, step: StatisticsMap, accu: StatisticsMap) -> None:
        """
        Handle statistics update from the solver.

        :param step: Current step statistics.
        :param accu: Accumulated statistics.
        """

    def _on_finish(self, result: SolveResult) -> None:
        """
        Handle the finalization of the solver.
        """


class SolveWatcher(ABC):
    """
    Coordinates one solve pass: deadlines and result handling.

    Deadlines are enforced by one-shot threading.Timer alarms that call stop()
    directly.
    Concrete watchers only need to implement how one backend-specific blocking
    solve is actually run (_run_solve) and interrupted (_interrupt).

    :ivar solver: The Solver instance being monitored.
    :ivar solve_timer: Timer tracking the overall time limit.
    :ivar cutoff_timer: Timer tracking the no-improvement cutoff.
    :ivar active: Whether a solve is currently in progress.
    """

    def __init__(self, solver: Solver) -> None:
        """
        Initialize the SolveWatcher.

        :param solver: The Solver instance being monitored.
        """
        self.solver: Solver = solver
        self.solve_timer: Timer = Timer()
        self.cutoff_timer: Timer = Timer()
        self.active: bool = False
        self._cutoff_seconds: Optional[int] = None
        self._cutoff_alarm: Optional[threading.Timer] = None

    def solve(
        self,
        time_limit: Optional[float],
        cutoff: Optional[int] = None,
        require_model: bool = False,
    ) -> None:
        """
        Run one solve pass to completion, blocking without polling.

        Call once per watcher.

        :param time_limit: Time limit for this solve pass.
        :param cutoff: Cutoff for this solve pass.
        :param require_model: Defer cutoff until the first model; the time limit still applies.
        """
        self.solve_timer.start(time_limit)
        self.cutoff_timer.start(cutoff, armed=not require_model)
        self._cutoff_seconds = cutoff
        self.active = True
        solve_alarm = self._schedule(time_limit)
        self._cutoff_alarm = None if require_model else self._schedule(cutoff)
        try:
            self._run_solve()
            for name, timer in (("Solve", self.solve_timer), ("Cutoff", self.cutoff_timer)):
                if timer.is_ringing:
                    self.solver.logger.info("%s timer ringing after %s seconds", name, timer.get_elapsed_time())
        finally:
            self._cancel(solve_alarm)
            self._cancel(self._cutoff_alarm)
            self._cutoff_alarm = None
            self.active = False
            self.solver.interrupted = False

    @abstractmethod
    def _run_solve(self) -> None:  # nocoverage
        """
        Run the backend-specific blocking solve pass and report its result.
        """
        raise NotImplementedError

    @abstractmethod
    def _interrupt(self) -> None:  # nocoverage
        """
        Interrupt the backend's search. Must be thread- and signal-safe.
        """
        raise NotImplementedError

    def stop(self) -> None:
        """
        Interrupt the current (or next) solve. Thread- and signal-safe.
        """
        self.solver.interrupted = True
        self._interrupt()

    def _rearm_cutoff(self) -> None:
        """
        Restart the cutoff timer and reschedule its alarm after a new model is found.

        Call this from a concrete watcher's model callback.
        """
        self.cutoff_timer.restart()
        self._cancel(self._cutoff_alarm)
        self._cutoff_alarm = self._schedule(self._cutoff_seconds)

    def _schedule(self, seconds: Optional[float]) -> Optional[threading.Timer]:
        """
        Schedule a one-shot interruption after the given delay.

        :param seconds: Delay in seconds, or None to not schedule an alarm.
        """
        if seconds is None:
            return None
        alarm = threading.Timer(seconds, self.stop)
        alarm.daemon = True
        alarm.start()
        return alarm

    @staticmethod
    def _cancel(alarm: Optional[threading.Timer]) -> None:
        """
        Cancel a scheduled alarm and wait for its thread to finish.

        :param alarm: Alarm to cancel, or None.
        """
        if alarm is not None:
            alarm.cancel()
            alarm.join()

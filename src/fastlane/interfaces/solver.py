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

from fastlane import Model, ThreadedTimer
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
        self._watcher_active: bool = False
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
        Request shutdown without acquiring locks or waiting.

        Return True while the solve loop must finish watcher cleanup before unwinding.
        """
        self.stop = True
        self.finished = True
        return self._watcher_active

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


class SolveWatcher(threading.Thread):
    """
    Watcher thread for monitoring the solving process.
    Handles timers and model callbacks.

    :ivar solver: The Solver instance being monitored.
    :ivar ctl: The Clingo control object from the solver.
    :ivar _stop_event: Event to signal stopping of the watcher thread.
    :ivar solve_timer: Timer for the solving process.
    :ivar cutoff_timer: Timer for the cutoff process.
    :ivar assumptions: Assumptions used in the solving process.
    :ivar exception: Stores any exception raised during solving.
    """

    def __init__(self, solver: Solver, assumptions: Optional[list[tuple[clingo.symbol.Symbol, bool]]] = None) -> None:
        """
        Initialize the SolveWatcher.

        :param solver: The Solver instance being monitored.
        :param assumptions: Assumptions used in the solving process.
        """
        super().__init__()
        self.solver: Solver = solver
        self.ctl: clingo.Control = solver.control
        self._stop_event: threading.Event = threading.Event()
        self.solve_timer: ThreadedTimer = ThreadedTimer(self.stop)
        self.cutoff_timer: ThreadedTimer = ThreadedTimer(self.stop)
        self.assumptions: list[tuple[clingo.symbol.Symbol, bool]] = assumptions or []
        self.exception: Optional[BaseException] = None

    # pylint: disable=protected-access
    def _on_model(self, model: clingo.Model) -> None:
        """
        Handle a new model from the solver.

        :param model: The Clingo model received.
        """
        self.solver._on_model(model)
        self.solver.logger.info("%.3f, %s", self.solve_timer.get_elapsed_time(), model.cost)
        self.solver.stats["time_to_last_model"] = self.cutoff_timer.get_elapsed_time()
        self.cutoff_timer.restart()

    # pylint: disable=protected-access
    def _on_finish(self, result: SolveResult) -> None:
        """
        Handle the finish of the solving process.

        :param result: The result of the solve.
        """
        self.solver._on_finish(result)
        self._stop_event.set()

    def run(self) -> None:
        """
        Run the watcher thread.
        """
        try:
            self._run_solve()
        except BaseException as error:  # pylint: disable=broad-exception-caught
            # Exceptions are stored and re-raised after cleanup.
            self.exception = error

    # pylint: disable=protected-access
    def _run_solve(self) -> None:
        """
        Run the solving process with Clingo asynchronously.
        Handles model callbacks, timer interruptions, and result processing.
        """
        with self.ctl.solve(
            async_=True,
            on_model=self._on_model,
            on_statistics=self.solver._on_statistics,
            on_finish=self._on_finish,
            assumptions=self.assumptions,
        ) as handle:
            self._stop_event.wait()
            # Cancellation may wait for model callbacks, so hold no timer locks.
            handle.cancel()
            # print timer interrupting
            for name, timer in (
                ("Solve", self.solve_timer),
                ("Cutoff", self.cutoff_timer),
            ):
                if timer.is_ringing:
                    self.solver.logger.info("%s timer ringing after %s seconds", name, timer.get_elapsed_time())

            self.solver.postprocess_solve(handle.last(), handle.get())

    def stop(self) -> None:
        """
        Request cancellation without blocking the timer callback.
        """
        self.solver.interrupted = True
        self._stop_event.set()

    def cleanup(self) -> None:
        """
        Let model callbacks finish before shutting down their timers.
        """
        self.stop()
        while self.is_alive():
            self.join(timeout=0.1)
        self.solve_timer.stop()
        self.cutoff_timer.stop()
        self.solve_timer.join()
        self.cutoff_timer.join()

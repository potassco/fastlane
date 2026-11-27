"""
clingo solver for LNS.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Optional

import clingo
from clingo.solving import Model as ClingoModel
from clingo.solving import SolveResult

from fastlane import Model
from fastlane.interfaces.solver import Solver, SolverConfig, SolveWatcher
from fastlane.utils.logger import DEBUG_EXTRA

if TYPE_CHECKING:
    from fastlane.lns import LNS  # nocoverage


class ClingoSolveWatcher(SolveWatcher):
    """
    SolveWatcher implementation driving clingo's asynchronous solve API.

    :ivar ctl: The Clingo control object from the solver.
    :ivar assumptions: Assumptions used in the solving process.
    """

    def __init__(self, solver: Solver, assumptions: Optional[list[tuple[clingo.symbol.Symbol, bool]]] = None) -> None:
        """
        Initialize the ClingoSolveWatcher.

        :param solver: The Solver instance being monitored.
        :param assumptions: Assumptions used in the solving process.
        """
        super().__init__(solver)
        self.ctl: clingo.Control = solver.control
        self.assumptions: list[tuple[clingo.symbol.Symbol, bool]] = assumptions or []

    # pylint: disable=protected-access
    def _run_solve(self) -> None:
        """
        Run the solving process with Clingo asynchronously and postprocess its result.
        """
        with self.ctl.solve(
            assumptions=self.assumptions,
            on_model=self._on_model,
            on_statistics=self.solver._on_statistics,
            on_finish=self.solver._on_finish,
            async_=True,
        ) as handle:
            handle.wait()
            self.solver.postprocess_solve(handle.last(), handle.get())

    def _interrupt(self) -> None:
        """
        Interrupt the active (or next) clingo solve. Thread- and signal-safe.
        """
        self.ctl.interrupt()

    # pylint: disable=protected-access
    def _on_model(self, model: clingo.Model) -> None:
        """
        Handle a new model from the solver and rearm the cutoff.

        :param model: The Clingo model received.
        """
        self.solver._on_model(model)
        self.solver.logger.info("%.3f, %s", self.solve_timer.get_elapsed_time(), model.cost)
        self.solver.stats["time_to_last_model"] = self.cutoff_timer.get_elapsed_time()
        self._rearm_cutoff()


# pylint: disable=too-many-instance-attributes
class ClingoSolver(Solver):
    """
    clingo solver.
    """

    def __init__(self) -> None:
        super().__init__()
        self._variability: bool = False

    @classmethod
    def get_name(cls) -> str:
        """
        Get the name under which the solver will be listed in options.

        :return: Name of the solver.
        """
        return "clingo"

    # pylint: disable=dangerous-default-value
    def setup(
        self,
        lns_object: LNS,
        args: list[str] = [],
        files: Optional[list[str]] = None,
    ) -> None:
        """
        Initialize clingo.Control object using clingo.

        :param lns_object: LNS object.
        :param args: clingo arguments, default: lns_object.clingo_options.
        :param files: ASP files to be loaded, default: lns_object.files.
        """
        if files is None:
            files = lns_object.files

        def custom_logger(mc: clingo.MessageCode, msg: str) -> None:  # nocoverage
            if mc != clingo.MessageCode.Other:
                print(msg, file=sys.stderr)

        ctl = clingo.Control(args, logger=custom_logger)
        for path in files:
            ctl.load(path)
        self.control, self.theory = ctl, None

    def _apply_config_to_control(self, config: SolverConfig) -> None:
        """
        Apply solver configuration to clingo.Control object.

        :param config: Solver configuration.
        """
        if config.configuration is not None:
            self.control.configuration.configuration = config.configuration
        if isinstance(self.control.configuration.solver, clingo.Configuration):
            if config.opt_strategy is not None:
                self.control.configuration.solver.opt_strategy = config.opt_strategy
            if config.opt_heuristic is not None:
                self.control.configuration.solver.opt_heuristic = config.opt_heuristic
            if config.restart_on_model is not None:
                self.control.configuration.solver.restart_on_model = config.restart_on_model
            if config.heuristic is not None:
                self.control.configuration.solver.heuristic = config.heuristic
        if isinstance(self.control.configuration.solve, clingo.Configuration):
            if config.opt_mode is not None:
                self._apply_opt_mode(config.opt_mode)
            if config.solve_limit is not None:
                self.control.configuration.solve.solve_limit = config.solve_limit

    def _apply_opt_mode(self, opt_mode: str) -> None:
        """
        Set the optimization mode for the current objective.

        :param opt_mode: Optimization mode string.
        """
        if isinstance(self.control.configuration.solve, clingo.Configuration):
            self.control.configuration.solve.opt_mode = opt_mode

    def _control_config_debug(self) -> None:
        """
        Debug print of clingo.Control configuration.
        """
        self.logger.debug_extra("clingo.Control configuration:")
        self.logger.debug_extra("configuration: %s", self.control.configuration.configuration)
        if isinstance(self.control.configuration.solver, clingo.Configuration):
            self.logger.debug_extra("opt-strategy: %s", self.control.configuration.solver.opt_strategy)
            self.logger.debug_extra("opt-heuristic: %s", self.control.configuration.solver.opt_heuristic)
            self.logger.debug_extra("restart-on-model: %s", self.control.configuration.solver.restart_on_model)
            self.logger.debug_extra("heuristic: %s", self.control.configuration.solver.heuristic)
        if isinstance(self.control.configuration.solve, clingo.Configuration):
            self.logger.debug_extra("opt-mode: %s", self.control.configuration.solve.opt_mode)
            self.logger.debug_extra("solve-limit: %s", self.control.configuration.solve.solve_limit)
            self.logger.debug_extra("parallel-mode: %s", self.control.configuration.solve.parallel_mode)

    # pylint: disable=too-many-branches
    def solve(
        self,
        config: Optional[SolverConfig] = None,
        assumptions: list[tuple[clingo.symbol.Symbol, bool]] = [],
        require_model: bool = False,
    ) -> Optional[Model]:
        """
        Solve under assumptions using clingo.
        Startup and worker failures are re-raised in the caller after timer cleanup.

        :param config: Solver configuration.
        :param assumptions: Assumptions for solving (fixed atoms).
        :param require_model: If True, defer cutoff until the first model; the time limit still applies.
        :return: Last obtained model.
        """
        self.last_model = None
        # remember assumptions were being used
        if assumptions:
            self._assumptions_used = True
        else:
            self._assumptions_used = False

        time_limit: Optional[int] = None
        cutoff: Optional[int] = None
        if config is not None:
            self._variability = config.variability
            time_limit = config.time_limit
            cutoff = config.cutoff
            self._apply_config_to_control(config)

        if self.logger.isEnabledFor(DEBUG_EXTRA):  # nocoverage
            self._control_config_debug()
            self.logger.debug_extra("time-limit: %s", time_limit)
            self.logger.debug_extra("cutoff: %s", cutoff)

        self._prepare_solve()
        self._run_watcher(assumptions, time_limit, cutoff, require_model)
        return self.last_model

    def _run_watcher(
        self,
        assumptions: list[tuple[clingo.Symbol, bool]],
        time_limit: Optional[float],
        cutoff: Optional[int] = None,
        require_model: bool = False,
    ) -> None:
        """
        Run one prepared solve pass and propagate errors after cleanup.

        :param assumptions: Assumptions for solving (fixed atoms).
        :param time_limit: Time limit for this solve pass.
        :param cutoff: Cutoff for this solve pass.
        :param require_model: If True, defer cutoff until the first model; the time limit still applies.
        """
        self.watcher = ClingoSolveWatcher(self, assumptions)
        self.watcher.solve(time_limit, cutoff, require_model)

    def _save_model(self, model: ClingoModel) -> None:
        """
        Save the given Clingo model into the solver's last model.

        :param model: Clingo model to save.
        """
        self.last_model = Model()
        self.last_model.shown = set(model.symbols(shown=True))
        self.last_model.true = set(model.symbols(atoms=True))
        self.last_model.cost = model.cost

    def postprocess_solve(self, model: Optional[ClingoModel], result: SolveResult) -> None:
        """
        Post-process the result of a solve.

        :param model: Last obtained Clingo model.
        :param result: Solve result.
        """
        if model is not None:
            self._save_model(model)

        if result.satisfiable:
            self.result = "SATISFIABLE"
            self.stats["result"] = "SATISFIABLE"
            if self.last_model is None:
                self.finished = True
                return
        if (
            self._variability
            and result.exhausted
            and not self.finished
            and not self.interrupted
            # cant prove optimum with assumptions
            and not self._assumptions_used
        ):
            if result.unsatisfiable:
                self.result = self.stats["result"] = "UNSATISFIABLE"
            else:
                self.result = self.stats["result"] = "OPTIMUM FOUND"
                self.optimum = "yes"
            self.finished = True

"""
clingo solver for LNS.
"""

from __future__ import annotations

import signal
import sys
from functools import partial
from types import FrameType
from typing import TYPE_CHECKING, Optional, Union

import clingo
from clingo.statistics import StatisticsMap

from mod_lns import Model, Timer
from mod_lns.interfaces.solver import SolverConfig, SolverInterface

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


# pylint: disable=too-many-instance-attributes
class ClingoSolver(SolverInterface):
    """
    clingo solver.
    """

    def __init__(self) -> None:
        super().__init__()
        self.last_model: Optional[Model] = None
        self._timer = Timer()
        self._interrupted = False
        self._variability: bool = False

    @classmethod
    def get_name(cls) -> str:
        """
        Get the name under which the solver will be listed in options.

        :return: Name of the solver.
        :rtype: str
        """
        return "clingo"

    def setup_interrupt_handling(self, lns_object: LNS) -> None:
        """
        Setup signal handling for interrupts (SIGINT, SIGTERM).

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """
        handler = partial(self.interrupt_handler, lns_object=lns_object)
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    # pylint: disable=unused-argument
    def interrupt_handler(self, sig: int, frame: Union[None, FrameType], lns_object: LNS) -> None:
        """
        Signal handler for interrupts (SIGINT, SIGTERM).

        :param sig: Signal number.
        :type sig: int
        :param frame: Current stack frame.
        :type frame: Union[None, FrameType]
        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """
        print("INTERRUPTED")
        self.finished = True
        if self.control is not None:
            self.control.interrupt()
        self.stop = True
        lns_object.strategy.print_result(lns_object)
        raise SystemExit

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
        :type lns_object: mod_lns.LNS
        :param args: clingo arguments, default: lns_object.clingo_options.
        :type args: list[str]
        :default args: []
        :param files: ASP files to be loaded, default: lns_object.files.
        :type files: Optional[list[str]]
        :default files: None
        """
        self.setup_interrupt_handling(lns_object)

        if files is None:
            files = lns_object.files

        self.logger = lns_object.logger

        def custom_logger(mc: clingo.MessageCode, msg: str) -> None:  # nocoverage
            if mc != clingo.MessageCode.Other:
                print(msg, file=sys.stderr)

        ctl = clingo.Control(args, logger=custom_logger)
        for path in files:
            ctl.load(path)
        self.control, self.theory = ctl, None

    def _on_model(self, model: clingo.Model) -> None:
        """
        Saves model for later use.

        :param model: Model found during solving.
        :type model: Model
        """
        self.last_model = Model()
        self.last_model.shown = list(model.symbols(shown=True))
        self.last_model.true = list(model.symbols(atoms=True))
        self.last_model.cost = model.cost

    def _on_statistics(self, step: StatisticsMap, accu: StatisticsMap) -> None:  # nocoverage
        """
        Update statistics.

        :param step: Current step statistics.
        :type step: StatisticsMap
        :param accu: Accumulated statistics.
        :type accu: StatisticsMap
        """
        return

    def _on_finish(self, res: clingo.SolveResult) -> None:  # nocoverage
        """
        Search finished.

        :param res: Result of the solving process.
        :type res: SolveResult
        """
        if res.satisfiable:
            self.result = "SATISFIABLE"
            if self.last_model is None:
                self.finished = True
                return
        if (
            self._variability
            and res.exhausted
            and not self.finished
            and not self._interrupted
            # cant prove optimum with assumptions
            and not self._assumptions_used
        ):
            if res.unsatisfiable:
                self.result = "UNSATISFIABLE"
            else:
                self.result = "OPTIMUM FOUND"
                self.optimum = "yes"
            self.finished = True

    def _find_first_solution(self, assumptions: list[tuple[clingo.symbol.Symbol, bool]] = []) -> None:
        """
        Try harder to find first solution.

        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
        """
        assert isinstance(self.control, clingo.control.Control)
        assert isinstance(self.control.configuration.solve, clingo.Configuration)
        solve_limit_tmp = self.control.configuration.solve.solve_limit
        models_tmp = self.control.configuration.solve.models
        self.control.configuration.solve.solve_limit = "umax"
        self.control.configuration.solve.models = 1
        self.logger.debug("solve-limit: %s", self.control.configuration.solve.solve_limit)
        self.logger.debug("models: %s", self.control.configuration.solve.models)

        with self.control.solve(
            assumptions=assumptions,
            on_model=self._on_model,
            on_finish=self._on_finish,
            on_statistics=self._on_statistics,
            async_=True,
        ) as handle:
            while not handle.wait(0):
                pass

        self.control.configuration.solve.solve_limit = solve_limit_tmp
        self.control.configuration.solve.models = models_tmp

    # pylint: disable=too-many-branches
    def solve(
        self,
        config: Optional[SolverConfig] = None,
        assumptions: list[tuple[clingo.symbol.Symbol, bool]] = [],
    ) -> Optional[Model]:
        """
        Solve under assumptions using clingo.

        :config: Solver configuration.
        :type config: SolverConfig
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
        :return: Last obtained model.
        :rtype: Model
        """
        assert isinstance(self.control, clingo.control.Control)
        assert isinstance(self.control.configuration.solve, clingo.Configuration)
        assert isinstance(self.control.configuration.solver, clingo.Configuration)

        # remember assumptions were are being used
        if assumptions:
            self._assumptions_used = True
        else:
            self._assumptions_used = False

        time_limit: Optional[int] = None
        if config is not None:
            self._variability = config.variability
            time_limit = config.time_limit
            if config.configuration is not None:
                self.control.configuration.configuration = config.configuration
            if config.opt_strategy is not None:
                self.control.configuration.solver.opt_strategy = config.opt_strategy
            if config.opt_heuristic is not None:
                self.control.configuration.solver.opt_heuristic = config.opt_heuristic
            if config.restart_on_model is not None:
                self.control.configuration.solver.restart_on_model = config.restart_on_model
            if config.heuristic is not None:
                self.control.configuration.solver.heuristic = config.heuristic
            if config.opt_mode is not None:
                self.control.configuration.solve.opt_mode = config.opt_mode
            if config.solve_limit is not None:
                self.control.configuration.solve.solve_limit = config.solve_limit

        self.logger.debug("configuration: %s", self.control.configuration.configuration)
        self.logger.debug("opt-strategy: %s", self.control.configuration.solver.opt_strategy)
        self.logger.debug("parallel-mode: %s", self.control.configuration.solve.parallel_mode)
        self.logger.debug("opt-heuristic: %s", self.control.configuration.solver.opt_heuristic)
        self.logger.debug("restart-on-model: %s", self.control.configuration.solver.restart_on_model)
        self.logger.debug("heuristic: %s", self.control.configuration.solver.heuristic)
        self.logger.debug("opt-mode: %s", self.control.configuration.solve.opt_mode)
        self.logger.debug("solve-limit: %s", self.control.configuration.solve.solve_limit)
        self.logger.debug("time-limit: %s", time_limit)

        self._timer.reset()
        self._timer.start(time_limit)
        with self.control.solve(
            assumptions=assumptions,
            on_model=self._on_model,
            on_finish=self._on_finish,
            async_=True,
        ) as handle:
            while not handle.wait(0):
                if self._timer.is_ringing and not self._interrupted and not self.finished:
                    self._interrupted = True
                    self.logger.debug("interrupted by timer")
                    handle.cancel()
        self._interrupted = False
        if self.last_model is None and not self.finished:
            self.logger.warning(
                "The solve-limit or time-limit is not enough to find a solution."
                "Therefore, the first solution found is used as the initial solution."
            )
            self._find_first_solution()

        return self.last_model

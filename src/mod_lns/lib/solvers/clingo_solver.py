"""
clingo solver for LNS.
"""

from __future__ import annotations

import signal
import sys
from types import FrameType
from typing import TYPE_CHECKING, Optional, Union

import clingo

from mod_lns import Model, Timer
from mod_lns.interfaces.solver import SolverConfig, SolverInterface

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class ClingoSolver(SolverInterface):
    """
    clingo solver.
    """

    def __init__(self):
        super().__init__()
        self.last_model = None
        self._result = "UNKNOWN"
        self._optimum = "unknown"
        self.__search_num = 0
        self.__timer = Timer()
        self.__interrupted = False
        self.__variability: bool = False
        signal.signal(signal.SIGINT, self.interrupt_handler)
        signal.signal(signal.SIGTERM, self.interrupt_handler)

    # pylint: disable=unused-argument
    def interrupt_handler(self, sig: int, frame: Union[None, FrameType]):
        """
        Signal handler for interrupts (SIGINT, SIGTERM).

        :param sig: Signal number.
        :type sig: int
        :param frame: Current stack frame.
        :type frame: Frame
        :rtype: dict[str, Any]
        """
        self.finished = True
        print("interrupted by signal")
        self.control.interrupt()

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
        if files is None:
            files = lns_object.files

        # if len(args) == 0:
        #    args = lns_object.clingo_options

        #! seed, paramode
        # set seed if given

        # args = []
        # if lns_object.seed is not None:
        #     args = args + [f"--seed={lns_object.seed}"]

        def custom_logger(mc, msg):  # nocoverage
            if mc != clingo.MessageCode.Other:
                print(msg, file=sys.stderr)

        ctl = clingo.Control(args, logger=custom_logger)
        for path in files:
            ctl.load(path)
        self.control, self.theory = ctl, None

    def _on_model(self, model: clingo.solving.Model) -> None:  # nocoverage
        """
        Saves model for later use.

        :param model: Model found during solving.
        :type model: clingo.solving.Model
        """
        self.last_model = Model()
        self.last_model.shown = model.symbols(shown=True)
        self.last_model.true = model.symbols(atoms=True)
        self.last_model.cost = model.cost

        # dl - to be improved
        if self.theory:
            self.theory.on_model(model=model)
            self.last_model.assignments = [
                f"{key}={val}" for key, val in self.theory.assignment(model.thread_id)
            ]

    # dl, con
    # def __on_statistics(self, step: StatisticsMap, accu: StatisticsMap):
    #     if self.theory is not None:
    #         self.theory.on_statistics(step, accu)

    # res: SolverResult
    def _on_finish(self, res):
        if res.satisfiable:
            self._result = "SATISFIABLE"
            if self.last_model is None:
                self.finished = True
                return

        if (
            self.__variability
            and res.exhausted
            and not self.finished
            and not self.__interrupted
        ):
            if res.unsatisfiable:
                self._result = "UNSATISFIABLE"
            else:
                self._result = "OPTIMUM FOUND"
                self._optimum = "yes"
            self.finished = True

    def __find_first_solution(
        self, lns_object: LNS, assumptions: list[tuple[clingo.symbol.Symbol, bool]]
    ) -> None:
        """
        Try harder to find first solution.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
        """
        solve_limit_tmp = self.control.configuration.solve.solve_limit
        models_tmp = self.control.configuration.solve.models
        self.control.configuration.solve.solve_limit = "umax"
        self.control.configuration.solve.models = 1
        lns_object.logger.debug(
            "solve-limit:", self.control.configuration.solve.solve_limit
        )
        lns_object.logger.debug("models:", self.control.configuration.solve.models)

        with self.control.solve(
            assumptions=assumptions,
            on_model=self._on_model,
            on_finish=self._on_finish,
            async_=True,
        ) as handle:
            while not handle.wait(0):
                pass

        self.control.configuration.solve.solve_limit = solve_limit_tmp
        self.control.configuration.solve.models = models_tmp

    def solve(
        self,
        lns_object: LNS,
        config: Optional[SolverConfig] = None,
        assumptions: list[tuple[clingo.symbol.Symbol, bool]] = [],
    ) -> Optional[Model]:
        """
        Solve under assumptions using clingo.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :config: Solver configuration.
        :type config: SolverConfig
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        self.__search_num += 1
        if config.time_limit is None:
            time_limit = 0
        else:
            time_limit = config.time_limit
        if config is not None:
            if config.configuration is not None:
                self.control.configuration.configuration = config.configuration
            if config.opt_strategy is not None:
                self.control.configuration.solver.opt_strategy = config.opt_strategy
            if config.opt_heuristic is not None:
                self.control.configuration.solver.opt_heuristic = config.opt_heuristic
            if config.restart_on_model is not None:
                self.control.configuration.solver.restart_on_model = (
                    config.restart_on_model
                )
            if config.heuristic is not None:
                self.control.configuration.solver.heuristic = config.heuristic
            if config.opt_mode is not None:
                self.control.configuration.solve.opt_mode = config.opt_mode
            if config.solve_limit is not None:
                self.control.configuration.solve.solve_limit = config.solve_limit

        lns_object.logger.debug(
            f"configuration: {self.control.configuration.configuration}"
        )
        lns_object.logger.debug(
            f"opt-strategy: {self.control.configuration.solver.opt_strategy}"
        )
        lns_object.logger.debug(
            f"parallel-mode: {self.control.configuration.solve.parallel_mode}"
        )
        lns_object.logger.debug(
            f"opt-heuristic: {self.control.configuration.solver.opt_heuristic}"
        )
        lns_object.logger.debug(
            f"restart-on-model: {self.control.configuration.solver.restart_on_model}"
        )
        lns_object.logger.debug(
            f"heuristic: {self.control.configuration.solver.heuristic}"
        )
        lns_object.logger.debug(
            f"opt-mode: {self.control.configuration.solve.opt_mode}"
        )
        lns_object.logger.debug(
            f"opt-mode: {self.control.configuration.solve.opt_mode}"
        )
        lns_object.logger.debug(
            f"solve-limit: {self.control.configuration.solve.solve_limit}"
        )
        lns_object.logger.debug(f"time-limit: {time_limit}")
        self.__variability = config.variability
        self.__timer.reset()
        with self.control.solve(
            assumptions=assumptions,
            on_model=self._on_model,
            on_finish=self._on_finish,
            async_=True,
        ) as handle:
            if time_limit > 0:
                self.__timer.start(time_limit)
            while not handle.wait(0):
                if (
                    self.__timer.is_ringing
                    and not self.__interrupted
                    and not self.finished
                ):
                    self.__interrupted = True
                    lns_object.logger.debug("interrupted by timer")
                    handle.cancel()
        self.__interrupted = False

        if self.last_model is None and not self.finished:
            lns_object.logger.warning(
                "The solve-limit or time-limit is not enough to find a solution."
                "Therefore, the first solution found is used as the initial solution."
            )
            self.__find_first_solution(lns_object)

        return self.last_model

"""
clingcon solver for LNS.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Optional

import clingo
from clingcon import ClingconTheory
from clingo import ast
from clingo.statistics import StatisticsMap

from mod_lns import Model
from mod_lns.interfaces.solver import SolverConfig
from mod_lns.lib.solvers.clingo_solver import ClingoSolver

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage

LINE = "--------------------------------------------------------------------------------------"


# pylint: disable=too-many-instance-attributes
class ClingconSolver(ClingoSolver):
    """
    clingcon solver.
    """

    @classmethod
    def get_name(cls) -> str:
        """
        Get the name under which the solver will be listed in options.

        :return: Name of the solver.
        :rtype: str
        """
        return "clingcon"

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
        self.setup_interrupt_handling()

        if files is None:
            files = lns_object.files

        self.logger = lns_object.logger

        def custom_logger(mc, msg):  # nocoverage
            if mc != clingo.MessageCode.Other:
                print(msg, file=sys.stderr)

        thy = ClingconTheory()
        ctl = clingo.Control(args, logger=custom_logger)
        thy.register(ctl)

        with ast.ProgramBuilder(ctl) as builder:
            ast.parse_files(
                files,
                lambda ast: thy.rewrite_ast(ast, builder.add),
            )

        self.control, self.theory = ctl, thy

    def _on_model(self, model: clingo.solving.Model) -> None:  # nocoverage
        """
        Saves model for later use.

        :param model: Model found during solving.
        :type model: clingo.solving.Model
        """
        assert isinstance(self.theory, ClingconTheory)
        self.theory.on_model(model=model)

        self.last_model = Model()
        self.last_model.shown = model.symbols(shown=True)
        self.last_model.true = model.symbols(atoms=True)
        self.last_model.cost = model.cost

        self.last_model.assignments = [
            f"{key}={val}" for key, val in self.theory.assignment(model.thread_id)
        ]
        if not self.last_model.cost:
            for thy_symb in model.symbols(theory=True):
                if thy_symb.name == "__csp_cost":
                    self.last_model.cost = [int(thy_symb.arguments[0].string)]
                    print("Optimization:", *self.last_model.cost)
                    break

    def _on_statistics(self, step: StatisticsMap, accu: StatisticsMap) -> None:
        """
        Update statistics.

        :param step: Current step statistics.
        :type step: StatisticsMap
        :param accu: Accumulated statistics.
        :type accu: StatisticsMap
        """
        assert isinstance(self.theory, ClingconTheory)
        self.theory.on_statistics(step, accu)

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
        assert isinstance(self.theory, ClingconTheory)
        assert isinstance(self.control.configuration.solve, clingo.Configuration)
        assert isinstance(self.control.configuration.solver, clingo.Configuration)
        time_limit = 0
        if config is not None:
            self._variability = config.variability
            if config.time_limit is not None:
                time_limit = config.time_limit
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

        self.logger.debug("configuration: %s", self.control.configuration.configuration)
        self.logger.debug(
            "opt-strategy: %s", self.control.configuration.solver.opt_strategy
        )
        self.logger.debug(
            "parallel-mode: %s", self.control.configuration.solve.parallel_mode
        )
        self.logger.debug(
            "opt-heuristic: %s", self.control.configuration.solver.opt_heuristic
        )
        self.logger.debug(
            "restart-on-model: %s", self.control.configuration.solver.restart_on_model
        )
        self.logger.debug("heuristic: %s", self.control.configuration.solver.heuristic)
        self.logger.debug("opt-mode: %s", self.control.configuration.solve.opt_mode)
        self.logger.debug(
            "solve-limit: %s", self.control.configuration.solve.solve_limit
        )
        self.logger.debug("time-limit: %s", time_limit)

        self.theory.prepare(self.control)

        self._timer.reset()
        with self.control.solve(
            assumptions=assumptions,
            on_model=self._on_model,
            on_finish=self._on_finish,
            on_statistics=self._on_statistics,
            async_=True,
        ) as handle:
            if time_limit > 0:
                self._timer.start(time_limit)
            while not handle.wait(0):
                if (
                    self._timer.is_ringing
                    and not self._interrupted
                    and not self.finished
                ):
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

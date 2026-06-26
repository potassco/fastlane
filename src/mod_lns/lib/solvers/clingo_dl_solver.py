"""
clingo-dl solver for LNS.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Optional

import clingo
from clingo import ast
from clingo.solving import SolveResult
from clingo.statistics import StatisticsMap
from clingo.symbol import Function, Number
from clingodl import ClingoDLTheory

from mod_lns import Model
from mod_lns.interfaces.solver import SolverConfig
from mod_lns.lib.solvers.clingo_solver import ClingoSolver

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage

LINE = "--------------------------------------------------------------------------------------"


# pylint: disable=too-many-instance-attributes
class ClingoDLSolver(ClingoSolver):
    """
    clingo-dl solver.
    """

    def __init__(self) -> None:
        super().__init__()
        self._search_num: int = 0
        self._exhausted: bool = False
        self.bound: Optional[int] = None

    @classmethod
    def get_name(cls) -> str:
        """
        Get the name under which the solver will be listed in options.

        :return: Name of the solver.
        :rtype: str
        """
        return "clingo-dl"

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

        thy = ClingoDLTheory()  # type: ignore
        ctl = clingo.Control(args, logger=custom_logger)
        thy.register(ctl)

        with ast.ProgramBuilder(ctl) as builder:
            ast.parse_files(
                files,
                lambda ast: thy.rewrite_ast(ast, builder.add),
            )
            if self.minimize_variable is not None:
                bound_subprogram = f"#program bound(t). &diff {{ {self.minimize_variable} - 0 }} <= B :- __b(B,t)."
                lns_object.logger.debug(LINE)
                lns_object.logger.debug(bound_subprogram)
                ast.parse_string(bound_subprogram, lambda ast: thy.rewrite_ast(ast, builder.add))

        self.control, self.theory = ctl, thy

    def _on_model(self, model: clingo.solving.Model) -> None:  # nocoverage
        """
        Saves model for later use.

        :param model: Model found during solving.
        :type model: clingo.solving.Model
        """
        assert isinstance(self.theory, ClingoDLTheory)
        self.theory.on_model(model=model)

        self.last_model = Model()
        self.last_model.shown = set(model.symbols(shown=True))
        self.last_model.true = set(model.symbols(atoms=True))
        self.last_model.cost = model.cost

        self.last_model.assignments = [f"{key}={val}" for key, val in self.theory.assignment(model.thread_id)]
        if self.minimize_variable is not None:
            for symb, val in self.theory.assignment(model.thread_id):
                if symb == self.minimize_variable:
                    self.last_model.cost = [int(val)]  # type: ignore
                    print("Optimization:", *self.last_model.cost)
                    break

        self.stats["time_to_last_model"] = self._cutoff_timer.get_elapsed_time()
        self._cutoff_timer.restart()

    def _on_statistics(self, step: StatisticsMap, accu: StatisticsMap) -> None:  # nocoverage
        """
        Update statistics.

        :param step: Current step statistics.
        :type step: StatisticsMap
        :param accu: Accumulated statistics.
        :type accu: StatisticsMap
        """
        assert isinstance(self.theory, ClingoDLTheory)
        self.theory.on_statistics(step, accu)

    def _on_finish(self, res: SolveResult) -> None:  # nocoverage
        """
        Search finished.

        :param res: Result of the solving process.
        :type res: SolveResult
        """
        self._exhausted = res.exhausted
        super()._on_finish(res)

    def _release_bound(self, bound: int) -> None:
        """
        Release a bound from the solver for the current iteration.
        """
        bound_atom = Function("__b", [Number(bound), Number(self._search_num)])
        self.control.release_external(bound_atom)
        self.logger.debug("release external %s.", bound_atom)

    def _add_bound(self, bound: int) -> None:
        """
        Add a bound to the solver for the current iteration.

        :param bound: The bound to add.
        :type bound: int
        """
        bound_atom = Function("__b", [Number(bound), Number(self._search_num)])
        ext_statement = f"#external {bound_atom}."
        self.control.add("bound", ["t"], ext_statement)
        self.logger.debug(ext_statement)
        self.control.ground([("bound", [Number(self._search_num)])])
        self.control.assign_external(bound_atom, True)
        self.logger.debug("assign external %s True.", bound_atom)

    # pylint: disable=too-many-branches
    def _minimize_variable(self, prev_bound: Optional[int] = None) -> None:
        """
        Minimize the variable by updating solve limit and bounds.

        :param prev_bound: Bound of the previous iteration.
        :type prev_bound: Optional[int]
        """
        assert isinstance(self.theory, ClingoDLTheory)
        assert isinstance(self.control.configuration.solve, clingo.Configuration)
        assert isinstance(self.control.configuration.solve.solve_limit, str)
        solve_limit = self.control.configuration.solve.solve_limit.split(",")
        conflicts: int = 0
        restarts: int = 0
        bound = prev_bound

        while not self.finished and not self._exhausted and not self._solve_timer.is_ringing:
            new_solve_limit = ["umax", "umax"]
            if solve_limit[0] != "umax":
                conflicts += self.control.statistics["solving"]["solvers"]["conflicts"]
                if conflicts >= int(solve_limit[0]):
                    break
                new_solve_limit[0] = str(int(solve_limit[0]) - conflicts)
            if solve_limit[1] != "umax":
                restarts += self.control.statistics["solving"]["solvers"]["restarts"]
                if restarts >= int(solve_limit[1]):
                    break
                new_solve_limit[1] = str(int(solve_limit[1]) - restarts)
            self.control.configuration.solve.solve_limit = f"{new_solve_limit[0]},{new_solve_limit[1]}"
            self.logger.debug("solve-limit: %s", self.control.configuration.solve.solve_limit)

            if bound is not None:
                self._release_bound(bound)
            assert isinstance(self.last_model, Model)
            bound = self.last_model.cost[0] - 1
            self._add_bound(bound)

            self.theory.prepare(self.control)

            with self.control.solve(
                on_model=self._on_model,
                on_statistics=self._on_statistics,
                on_finish=self._on_finish,
                async_=True,
            ) as handle:
                while not handle.wait(0):
                    if self._solve_timer.is_ringing and not self._interrupted and not self.finished:
                        self._interrupted = True
                        self.logger.debug("interrupted by timer")
                        handle.cancel()
            self._interrupted = False

        if not self.finished:
            self.control.configuration.solve.solve_limit = f"{solve_limit[0]},{solve_limit[1]}"
            if bound is not None:
                self._release_bound(bound)
        else:
            if self.result == "UNSATISFIABLE":
                self.result = "OPTIMUM FOUND"
                self.optimum = "yes"

    def _apply_config_to_control(self, config: SolverConfig) -> None:
        """
        Apply solver configuration to the clingo control object.

        :param config: Solver configuration.
        :type config: SolverConfig
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
                if self.minimize_variable is not None:
                    split_opt_mode = config.opt_mode.split(",")
                    if len(split_opt_mode) == 2:
                        self.bound = int(split_opt_mode[1])
                        self._add_bound(self.bound)
                else:
                    self.control.configuration.solve.opt_mode = config.opt_mode
            if config.solve_limit is not None:
                self.control.configuration.solve.solve_limit = config.solve_limit

    # pylint: disable=too-many-branches, too-many-statements
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
        assert isinstance(self.theory, ClingoDLTheory)

        # remember assumptions were are being used
        if assumptions:
            self._assumptions_used = True
        else:
            self._assumptions_used = False

        time_limit: Optional[int] = None
        cutoff: Optional[int] = None
        self._search_num += 1
        self.bound = None
        if config is not None:
            self._variability = config.variability
            time_limit = config.time_limit
            cutoff = config.cutoff
            self._apply_config_to_control(config)

        self._control_config_debug()
        self.logger.debug("time-limit: %s", time_limit)
        self.logger.debug("cutoff: %s", cutoff)

        self.theory.prepare(self.control)

        self._solve_timer.reset()
        self._solve_timer.start(time_limit)
        self._cutoff_timer.reset()
        self._cutoff_timer.start(cutoff)
        with self.control.solve(
            assumptions=assumptions,
            on_model=self._on_model,
            on_finish=self._on_finish,
            on_statistics=self._on_statistics,
            async_=True,
        ) as handle:
            ringing_timers = []
            while not handle.wait(0):
                if self._solve_timer.is_ringing:
                    ringing_timers.append("solve_timer")
                    self.logger.debug("solve timer ringing after %s seconds", self._solve_timer.get_elapsed_time())
                if self._cutoff_timer.is_ringing:
                    ringing_timers.append("cutoff_timer")
                    self.logger.debug("cutoff timer ringing after %s seconds", self._cutoff_timer.get_elapsed_time())
                if ringing_timers and not self._interrupted and not self.finished:
                    self._interrupted = True
                    self.logger.debug("interrupted by timer(s): %s", ", ".join(ringing_timers))
                    handle.cancel()
        self._interrupted = False

        if self.minimize_variable is not None:
            # use remaining time to minimize variable
            # cutoff timer ignored
            self._minimize_variable(self.bound)
        # if self.last_model is None and not self.finished:
        #     self.logger.warning(
        #         "The solve-limit or time-limit is not enough to find a solution."
        #         "Therefore, the first solution found is used as the initial solution."
        #     )
        #     self._find_first_solution()

        return self.last_model

"""
clingo-dl solver for LNS.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Optional

import clingo
from clingo import ast
from clingo.solving import Model as ClingoModel
from clingo.solving import SolveResult
from clingo.statistics import StatisticsMap
from clingo.symbol import Function, Number
from clingodl import ClingoDLTheory

from fastlane import Model
from fastlane.interfaces.solver import SolverConfig
from fastlane.lib.solvers.clingo_solver import ClingoSolver

if TYPE_CHECKING:
    from fastlane.lns import LNS  # nocoverage

LINE = "--------------------------------------------------------------------------------------"


# pylint: disable=too-many-instance-attributes
class ClingoDLSolver(ClingoSolver):
    """
    clingo-dl solver.
    """

    def __init__(self) -> None:
        super().__init__()
        self._search_num: int = 0
        self.bound: Optional[int] = None

    @classmethod
    def get_name(cls) -> str:
        """
        Get the name under which the solver will be listed in options.

        :return: Name of the solver.
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
        :param args: clingo arguments, default: lns_object.clingo_options.
        :param files: ASP files to be loaded, default: lns_object.files.
        """
        if files is None:
            files = lns_object.files

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
                self.logger.debug(LINE)
                self.logger.debug(bound_subprogram)
                ast.parse_string(bound_subprogram, lambda ast: thy.rewrite_ast(ast, builder.add))

        self.control, self.theory = ctl, thy

    def _on_model(self, model: clingo.solving.Model) -> None:  # nocoverage
        """
        Saves model for later use.

        :param model: Model found during solving.
        """
        assert isinstance(self.theory, ClingoDLTheory)
        self.theory.on_model(model=model)

    def _on_statistics(self, step: StatisticsMap, accu: StatisticsMap) -> None:  # nocoverage
        """
        Update statistics.

        :param step: Current step statistics.
        :param accu: Accumulated statistics.
        """
        assert isinstance(self.theory, ClingoDLTheory)
        self.theory.on_statistics(step, accu)

    def _prepare_solve(self) -> None:
        """
        Additional preparation before solving.
        """
        assert isinstance(self.theory, ClingoDLTheory)
        self.theory.prepare(self.control)

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
        """
        bound_atom = Function("__b", [Number(bound), Number(self._search_num)])
        ext_statement = f"#external {bound_atom}."
        self.control.add("bound", ["t"], ext_statement)
        self.logger.debug(ext_statement)
        self.control.ground([("bound", [Number(self._search_num)])])
        self.control.assign_external(bound_atom, True)
        self.logger.debug("assign external %s True.", bound_atom)

    # pylint: disable=too-many-branches
    def _minimize_variable(self, assumptions: list[tuple[clingo.Symbol, bool]], time_limit: Optional[int]) -> None:
        """
        Tighten the bound using the time, conflicts and restarts left by previous passes.

        :param assumptions: Assumptions for solving (fixed atoms).
        :param time_limit: Time limit for this minimization pass.
        """
        assert self.watcher is not None
        first_timer = self.watcher.solve_timer
        solve = self.control.configuration.solve
        assert isinstance(solve, clingo.Configuration) and isinstance(solve.solve_limit, str)
        original_limit = solve.solve_limit
        remaining = [None if value == "umax" else int(value) for value in original_limit.split(",")]

        try:
            while self.last_model is not None and not self.finished:
                # prepare solve limit
                if time_limit is not None and first_timer.get_elapsed_time() >= time_limit:
                    break
                stats = self.control.statistics["solving"]["solvers"]
                for i, key in enumerate(("conflicts", "restarts")):
                    limit = remaining[i]
                    if limit is not None:
                        remaining[i] = limit - int(stats[key])
                if any(value is not None and value <= 0 for value in remaining):
                    break
                solve.solve_limit = ",".join("umax" if value is None else str(value) for value in remaining)

                incumbent = self.last_model
                if self.bound is not None:
                    self._release_bound(self.bound)
                self.bound = incumbent.cost[0] - 1
                self._add_bound(self.bound)
                self._prepare_solve()
                seconds = None if time_limit is None else time_limit - first_timer.get_elapsed_time()
                if seconds is not None and seconds <= 0:
                    break
                self._run_watcher(assumptions, seconds)
                if self.last_model is incumbent:  # No better model (UNSAT or interrupted).
                    break
        finally:
            solve.solve_limit = original_limit

    def _apply_opt_mode(self, opt_mode: str) -> None:
        """
        Set the optimization mode for the solver.

        :param opt_mode: Optimization mode string.
        """
        if self.minimize_variable is None:
            super()._apply_opt_mode(opt_mode)
        else:
            parts = opt_mode.split(",")
            if len(parts) == 2:
                self.bound = int(parts[1])
                self._add_bound(self.bound)

    # pylint: disable=too-many-branches, too-many-statements
    def solve(
        self,
        config: Optional[SolverConfig] = None,
        assumptions: list[tuple[clingo.symbol.Symbol, bool]] = [],
        require_model: bool = False,
    ) -> Optional[Model]:
        """
        Solve under assumptions using clingo.

        :config: Solver configuration.
        :param assumptions: Assumptions for solving (fixed atoms).
        :param require_model: If True, ignore cutoff time until a model is found.
        :return: Last obtained model.
        """
        self._search_num += 1
        try:
            model = super().solve(config, assumptions, require_model)
            if self.minimize_variable is not None and model is not None and not self.finished:
                # Minimize variable with remaining time and solve limit
                self._minimize_variable(assumptions, config.time_limit if config else None)
            return self.last_model
        finally:
            if self.bound is not None:
                self._release_bound(self.bound)
                self.bound = None

    # pylint: disable=too-many-boolean-expressions
    def postprocess_solve(self, model: Optional[ClingoModel], result: SolveResult) -> None:
        """
        Postprocess the result of the solve.
        If minimizing a variable, update the last model with the assignments and cost.

        :param model: The last obtained clingo model.
        :param result: The result of the solve.
        """
        if self.minimize_variable is None:
            super().postprocess_solve(model, result)
        else:
            if model is not None:
                self._save_model(model)
            if result.satisfiable:
                self.result = self.stats["result"] = "SATISFIABLE"
                if self.last_model is None:
                    self.finished = True
                    return
            if (
                result.unsatisfiable
                and result.exhausted
                and self._variability
                and not self.finished
                and not self.interrupted
                and not self._assumptions_used
            ):
                if self.last_model is None:
                    self.result = self.stats["result"] = "UNSATISFIABLE"
                else:
                    # No tighter bound is feasible: the last model is optimal.
                    self.result = self.stats["result"] = "OPTIMUM FOUND"
                    self.optimum = "yes"
                self.finished = True

        if model is None:
            return
        assert self.last_model is not None
        # on_model attached these values before the theory backtracked.
        assignments = [atom.arguments for atom in model.symbols(theory=True) if atom.match("dl", 2)]
        self.last_model.assignments = [f"{key}={value}" for key, value in assignments]
        if self.minimize_variable is not None:
            for key, value in assignments:
                if key == self.minimize_variable:
                    self.last_model.cost = [value.number]
                    print("Optimization:", *self.last_model.cost)
                    break
            else:
                raise ValueError(f"No DL assignment for minimize variable {self.minimize_variable}")

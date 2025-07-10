"""
clingo-dl solver for LNS.
"""

from __future__ import annotations

import sys
import time
from typing import TYPE_CHECKING, Optional

import clingo
from clingo import ast
from clingodl import ClingoDLTheory

from mod_lns.interfaces.solver import SolverInterface

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


class ClingoDLSolver(SolverInterface):
    """
    clingo-dl solver.
    """

    # pylint: disable=dangerous-default-value
    def setup(
        self,
        lns_object: LNS,
        files: Optional[list[str]] = None,
        args: list[str] = [],
    ) -> None:
        """
        Initialize clingo.Control object using clingo-dl.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param files: ASP files to be loaded, default: lns_object.param_values["files"].
        :type files: Optional[list[str]]
        :param args: clingo arguments, default: lns_object.clingo_options.
        :type args: list[str]
        :default args: []
        """
        if files is None:
            files = lns_object.param_values["files"]

        if len(args) == 0:
            args = lns_object.clingo_options

        # set seed if given
        if lns_object.param_values["seed"] is not None:
            args = args + [f"--seed={lns_object.param_values['seed']}"]

        def custom_logger(mc, msg):  # nocoverage
            if mc != clingo.MessageCode.Other:
                print(msg, file=sys.stderr)

        thy = ClingoDLTheory()
        ctl = clingo.Control(args, logger=custom_logger)
        thy.register(ctl)
        with ast.ProgramBuilder(ctl) as builder:
            ast.parse_files(
                files,
                lambda ast: thy.rewrite_ast(ast, builder.add),
            )
        self.control, self.theory = ctl, thy

    def repair(
        self,
        lns_object: LNS,
        fixed_atoms: list[tuple[clingo.symbol.Symbol, bool]],
        time_limit: Optional[int] = None,
        model_limit: int = 0,
    ) -> clingo.solving.SolveResult:
        """
        Solve under assumptions using clingo.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
        :param time_limit: Manually set time limit for solve call.
        :type time_limit: Optional[int]
        :default time_limit: None
        :param model_limit: Set number of calculated models.
        :type model_limit: int
        :default model_limit: 0
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        res = clingo.solving.SolveResult(2)
        start_time = int(time.time())
        if isinstance(self.control, clingo.control.Control):
            if isinstance(self.control.configuration.solve, clingo.Configuration):
                self.control.configuration.solve.models = model_limit
            self.theory.prepare(self.control)
            with self.control.solve(
                assumptions=fixed_atoms,
                on_model=lns_object.on_model,
                async_=True,  # yield_=True
            ) as handle:
                done = handle.wait(time_limit)
                if not done:
                    handle.cancel()
                    print(
                        f"{time.time() - lns_object.start_time:.3f}s: "
                        f'Search interrupted after  ({lns_object.param_values["solve_time_limit"]}s).'
                    )
                res = handle.get()
        lns_object.avail_time -= int(time.time()) - start_time
        return res

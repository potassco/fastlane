"""
clingo-dl solver for LNS.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, List, Tuple

import clingo
from clingo import ast
from clingodl import ClingoDLTheory

from large_neighbourhood_search.interfaces.solver import SolverInterface

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class ClingoDLSolver(SolverInterface):
    """
    clingo-dl solver.
    """

    def setup(self, lns_object: LNS) -> None:
        """
        Initialize clingo.Control object using clingo-dl.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """
        # set seed if given
        if lns_object.param_values["seed"] is not None:
            lns_object.set_seed(lns_object.param_values["seed"])
        args = [
            f"--{i[0]}={i[1]}" for i in lns_object.param_values["clingo_args"].items()
        ]

        thy = ClingoDLTheory()
        ctl = clingo.Control(args)
        thy.register(ctl)
        with ast.ProgramBuilder(ctl) as builder:
            ast.parse_files(
                lns_object.param_values["files"],
                lambda ast: thy.rewrite_ast(ast, builder.add),
            )
        self.ctl, self.thy = ctl, thy

    def solve_fixed(
        self,
        lns_object: LNS,
        fixed_atoms: List[Tuple[clingo.symbol.Symbol, bool]],
    ) -> clingo.solving.SolveResult:
        """
        Solve under assumptions using clingo-dl.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        res = clingo.solving.SolveResult(2)
        start_time = int(time.time())
        solve_time = self.get_avail_solve_time(lns_object)
        if isinstance(self.ctl, clingo.control.Control):
            self.thy.prepare(self.ctl)
            with self.ctl.solve(
                assumptions=fixed_atoms,
                on_model=lns_object.on_model,
                async_=True,  # yield_=True
            ) as handle:
                done = handle.wait(solve_time)
                if not done:
                    handle.cancel()
                    print(
                        f"{time.time() - start_time:.3f}s: "
                        f'Unable to repair model during time limit ({lns_object.param_values["solve_time_limit"]}s).'
                    )
                res = handle.get()
        lns_object.avail_time -= int(time.time()) - start_time
        return res

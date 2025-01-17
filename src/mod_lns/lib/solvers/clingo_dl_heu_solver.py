"""
Heuristic clingo-dl solver for LNS.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import clingo
from clingo import ast
from clingo.symbol import Function, Number
from clingodl import ClingoDLTheory

from mod_lns.interfaces.solver import SolverInterface
from mod_lns.lib.utils import symbol_to_str

if TYPE_CHECKING:
    from mod_lns import LNS  # nocoverage


class ClingoDLHeuSolver(SolverInterface):
    """
    Heursitic clingo-dl solver.
    """

    def setup(
        self,
        lns_object: LNS,
        files: Optional[List[str]] = None,
        args: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize clingo.Control object using clingo.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param files: ASP files to be loaded, default: lns_object.param_values["files"].
        :type files: Optional[List[str]]
        :param args: clingo arguments, default: lns_object.param_values["clingo_args"].
        :type args: Optional[Dict[str,Any]]
        """
        if files is None:
            files = lns_object.param_values["files"]

        if args is None:
            args = lns_object.param_values["clingo_args"]

        # set seed if given
        if lns_object.param_values["seed"] is not None:
            lns_object.set_seed(lns_object.param_values["seed"])
        argsl = [f"--{i[0]}={i[1]}" for i in args.items()] + ["--heuristic=Domain"]

        thy = ClingoDLTheory()
        ctl = clingo.Control(argsl)
        thy.register(ctl)
        with ast.ProgramBuilder(ctl) as builder:
            ast.parse_files(
                files,
                lambda ast: thy.rewrite_ast(ast, builder.add),
            )

        # used for heuristics, see solve_fixed()
        ctl.add("_lns_h_step", ["s"], "#external _lns_h_step(s).")

        self.ctl, self.thy = ctl, thy

    def solve_fixed(
        self,
        lns_object: LNS,
        fixed_atoms: List[Tuple[clingo.symbol.Symbol, bool]],
    ) -> clingo.solving.SolveResult:
        """
        Solve with heuristics using clingo.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        # add rules for heuristics
        # to correctly enable and disable heuristics at each step
        # #external _lns_h_step(s) is used
        # example for step=1, fixed_atoms=[
        #   Function("meets", [Number(2), Number(3), Number(4)], True),
        #   Function("meets", [Number(5), Number(6), Number(7)], True),] :
        # #external _lns_h_step(1).
        # #heuristic meets(2,3,4) : _lns_h_step(1). [1, true]
        # #heuristic meets(5,6,7) : _lns_h_step(1). [1, true]

        # setup external of current step
        step = lns_object.step_c
        if isinstance(self.ctl, clingo.control.Control):
            self.ctl.ground([("_lns_h_step", [Number(step)])])
            self.ctl.assign_external(Function("_lns_h_step", [Number(step)]), True)

            # set heuristics
            rules = " ".join(
                [
                    f"#heuristic {symbol_to_str(atom[0])} : _lns_h_step({step}). [1, true]"
                    for atom in fixed_atoms
                ]
            )
            self.ctl.add("heuristics", [], rules)
            self.ctl.ground([("heuristics", [])])

        # solve
        res = clingo.solving.SolveResult(2)
        start_time = int(time.time())
        solve_time = self.get_avail_solve_time(lns_object)
        if isinstance(self.ctl, clingo.control.Control):
            self.thy.prepare(self.ctl)
            with self.ctl.solve(on_model=lns_object.on_model, async_=True) as handle:
                done = handle.wait(solve_time)
                if not done:
                    handle.cancel()
                    print(
                        f"{time.time() - lns_object.start_time:.3f}s: "
                        f'Search interrupted after  ({lns_object.param_values["solve_time_limit"]}s).'
                    )
                res = handle.get()
        lns_object.avail_time -= int(time.time()) - start_time

        # release externals
        if isinstance(self.ctl, clingo.control.Control):
            self.ctl.release_external(Function("_lns_h_step", [Number(step)]))
        return res

    def pre_solve(self, lns_object: LNS) -> clingo.solving.SolveResult:
        """
        Pre-solve using clingo-dl.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        res = clingo.solving.SolveResult(2)
        if isinstance(self.ctl, clingo.control.Control):
            self.thy.prepare(self.ctl)
            with self.ctl.solve(on_model=lns_object.on_model, async_=True) as handle:
                done = handle.wait(lns_object.param_values["pre_tl"])
                if not done:
                    handle.cancel()
                    print(
                        f"{time.time() - lns_object.start_time:.3f}s: "
                        f'Search interrupted after ({lns_object.param_values["pre_tl"]}s).'
                    )
                res = handle.get()
        return res

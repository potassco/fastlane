"""
clingo solver for LNS.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import clingo

from large_neighbourhood_search.interfaces.solver import SolverInterface

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class ClingoSolver(SolverInterface):
    """
    clingo solver.
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
        argsl = [f"--{i[0]}={i[1]}" for i in args.items()]

        ctl = clingo.Control(argsl)
        for path in files:
            ctl.load(path)
        self.ctl, self.thy = ctl, None

    def solve_fixed(
        self,
        lns_object: LNS,
        fixed_atoms: List[Tuple[clingo.symbol.Symbol, bool]],
    ) -> clingo.solving.SolveResult:
        """
        Solve under assumptions using clingo.

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
            with self.ctl.solve(
                assumptions=fixed_atoms, on_model=lns_object.on_model, async_=True
            ) as handle:
                done = handle.wait(solve_time)
                if not done:
                    handle.cancel()
                    print(
                        f"{time.time() - lns_object.start_time:.3f}s: "
                        f'Search interrupted after ({lns_object.param_values["solve_time_limit"]}s).'
                    )
                res = handle.get()
        lns_object.avail_time -= int(time.time()) - start_time
        return res

    def pre_solve(self, lns_object: LNS) -> clingo.solving.SolveResult:
        """
        Pre-solve using clingo.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        :return: Solve result.
        :rtype: clingo.solving.SolveResult
        """
        res = clingo.solving.SolveResult(2)
        if isinstance(self.ctl, clingo.control.Control):
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

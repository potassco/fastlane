"""
clingo solver for LNS.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, List, Tuple

import clingo

from large_neighbourhood_search.interfaces.solver import SolverInterface

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class ClingoSolver(SolverInterface):
    """
    clingo solver.
    """

    def setup(self, lns_object: LNS) -> None:
        """
        Initialize clingo.Control object using clingo.

        :param lns_object: LNS object.
        :type lns_object: large_neighbourhood_search.LNS
        """
        # set seed if given
        if lns_object.param_values["seed"] is not None:
            lns_object.set_seed(lns_object.param_values["seed"])
        args = [
            f"--{i[0]}={i[1]}" for i in lns_object.param_values["clingo_args"].items()
        ]

        ctl = clingo.Control(args)
        for path in lns_object.param_values["files"]:
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
                        f'Unable to repair model during time limit ({lns_object.param_values["solve_time_limit"]}s).'
                    )
                res = handle.get()
        lns_object.avail_time -= int(time.time()) - start_time
        return res

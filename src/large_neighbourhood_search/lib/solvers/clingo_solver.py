"""
clingo solver for LNS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple

import clingo
from interfaces.solver import SolverInterface

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class ClingoSolver(SolverInterface):
    """
    clingo solver.
    """

    def setup(self, lns_object: LNS) -> Tuple[clingo.control.Control, Any]:
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
        self._ctl, self._thy = ctl, None

    # pylint: disable=unused-argument
    def solve_under_assumptions(
        self,
        lns_object: LNS,
        assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
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
        with self.ctl.solve(
            assumptions=assumptions, on_model=lns_object.on_model, async_=True
        ) as handle:
            done = handle.wait(lns_object.param_values["time_limit"])
            if not done:
                handle.cancel()
                # lns_object.callables["timeout"](lns_object)
            res = handle.get()
        return res

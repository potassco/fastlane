from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple

import clingo
from interfaces.solver import SolverInterface

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


class ClingoDLSolver(SolverInterface):

    def setup(self, lns_object: LNS) -> Tuple[clingo.control.Control, Any]:
        pass

    def solve_under_assumptions(
        self,
        lns_object: LNS,
        assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
    ) -> clingo.solving.SolveResult:
        pass

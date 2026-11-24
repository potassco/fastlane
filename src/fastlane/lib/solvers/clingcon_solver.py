"""
clingcon solver for LNS.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Optional

import clingo
from clingcon import ClingconTheory
from clingo import ast
from clingo.solving import Model as ClingoModel
from clingo.statistics import StatisticsMap

from fastlane.lib.solvers.clingo_solver import ClingoSolver

if TYPE_CHECKING:
    from fastlane.lns import LNS  # nocoverage

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
        :param args: clingo arguments, default: lns_object.clingo_options.
        :param files: ASP files to be loaded, default: lns_object.files.
        """
        if files is None:
            files = lns_object.files

        def custom_logger(mc: clingo.MessageCode, msg: str) -> None:  # nocoverage
            if mc != clingo.MessageCode.Other:
                print(msg, file=sys.stderr)

        thy = ClingconTheory()  # type: ignore
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
        """
        assert isinstance(self.theory, ClingconTheory)
        self.theory.on_model(model=model)

    def _on_statistics(self, step: StatisticsMap, accu: StatisticsMap) -> None:  # nocoverage
        """
        Update statistics.

        :param step: Current step statistics.
        :param accu: Accumulated statistics.
        """
        assert isinstance(self.theory, ClingconTheory)
        self.theory.on_statistics(step, accu)

    def _prepare_solve(self) -> None:
        """
        Additional preparation before solving.
        """
        assert isinstance(self.theory, ClingconTheory)
        self.theory.prepare(self.control)

    def _save_model(self, model: ClingoModel) -> None:
        """
        Extend the saved model with clingcon assignments and cost.
        """
        super()._save_model(model)
        assert self.last_model is not None
        assert isinstance(self.theory, ClingconTheory)
        self.last_model.assignments = [f"{key}={val}" for key, val in self.theory.assignment(model.thread_id)]
        if not self.last_model.cost:
            for thy_symb in model.symbols(theory=True):
                if thy_symb.match("__csp_cost", 1):
                    self.last_model.cost = [int(thy_symb.arguments[0].string)]
                    print("Optimization:", *self.last_model.cost)
                    break

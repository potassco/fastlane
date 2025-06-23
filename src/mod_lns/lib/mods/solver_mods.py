"""
Modification functions for Solver classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type, no_type_check

import clingo
from clingo.symbol import Function, Number

from mod_lns.interfaces.solver import SolverInterface
from mod_lns.utils.conversions import symbol_to_str

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage


# pylint: disable=dangerous-default-value
def enable_heuristics(solver: SolverInterface) -> SolverInterface:
    """
    Adjust base solver to use heuristics for reparation.

    :param solver: Solver used as base.
    :type solver: SolverInterface
    :return: Modified solver using heuristics.
    :rtype: SolverInterface
    """

    @no_type_check
    def setup(
        self,
        lns_object: LNS,
        files: Optional[list[str]] = None,
        args: list[str] = [],
    ) -> None:
        """
        Set up heuristics.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param files: ASP files to be loaded, default: lns_object.param_values["files"].
        :type files: Optional[list[str]]
        :param args: clingo arguments, default: lns_object.param_values["clingo_args"].
        :type args: list[str]
        :default args: []
        """
        if len(args) == 0:
            args = lns_object.clingo_options + ["--heuristic=Domain"]
        else:
            args = args + ["--heuristic=Domain"]

        super(EnHeu, self).setup(  # pylint: disable=bad-super-call
            lns_object, files, args
        )

        # used for heuristics, see solve_fixed()
        self.control.add("_lns_h_step", ["s"], "#external _lns_h_step(s).")

    @no_type_check
    def repair(
        self,
        lns_object: LNS,
        fixed_atoms: list[tuple[clingo.symbol.Symbol, bool]],
        time_limit: Optional[int] = None,
        model_limit: int = 1,
    ) -> clingo.solving.SolveResult:
        """
        Use heuristics during reparation.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[tuple[clingo.symbol.Symbol, bool]]
        :param time_limit: Manually set time limit for solve call.
        :type time_limit: Optional[int]
        :default time_limit: None
        :param model_limit: Set number of calculated models.
        :type model_limit: int
        :default model_limit: 1
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
        if isinstance(self.control, clingo.control.Control):
            self.control.ground([("_lns_h_step", [Number(step)])])
            self.control.assign_external(Function("_lns_h_step", [Number(step)]), True)

            # set heuristics
            rules = " ".join(
                [
                    f"#heuristic {symbol_to_str(atom[0])} : _lns_h_step({step}). [1, true]"
                    for atom in fixed_atoms
                ]
            )

            self.control.add("heuristics", [], rules)
            self.control.ground([("heuristics", [])])

        # solve
        res = super(EnHeu, self).repair(  # pylint: disable=bad-super-call
            lns_object, fixed_atoms, time_limit, model_limit
        )

        # release externals
        if isinstance(self.control, clingo.control.Control):
            self.control.release_external(Function("_lns_h_step", [Number(step)]))
        return res

    base: Type[SolverInterface] = type(solver)
    EnHeu = type("EnHeu", (base,), {"setup": setup, "repair": repair})
    return EnHeu()

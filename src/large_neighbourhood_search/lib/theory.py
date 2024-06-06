"""
Collection of functions implementing different theories used for LNS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple

import clingo
from clingo import ast
from clingodl import ClingoDLTheory

if TYPE_CHECKING:
    from large_neighbourhood_search import LNS  # nocoverage


def setup_clingo_dl(lns_object: LNS) -> Tuple[clingo.control.Control, ClingoDLTheory]:
    """
    Initialize clingo.Control object using clingo-dl.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :return: Control and theory object used for LNS
    :rytpe: Tuple[clingo.control.Control, clingodl.ClingoDlTheory]
    """
    # set seed if given
    if lns_object.param_values["seed"] is not None:
        lns_object.set_seed(lns_object.param_values["seed"])
    args = [f"--{i[0]}={i[1]}" for i in lns_object.param_values["clingo_args"].items()]

    thy = ClingoDLTheory()
    lns_object.theory = thy
    ctl = clingo.Control(args)
    thy.register(ctl)
    # no input files not supported
    # if not lns_object._files:
    #    lns_object._files = ["-"]
    # for path in lns_object.config_values["files"]:
    with ast.ProgramBuilder(ctl) as builder:
        ast.parse_files(
            lns_object.param_values["files"],
            lambda ast: thy.rewrite_ast(ast, builder.add),
        )
    return ctl, thy


def setup_clingo(lns_object: LNS) -> Tuple[clingo.control.Control, None]:
    """
    Initialize clingo.Control object using clingo.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :return: Control and theory object used for LNS
    :rytpe: Tuple[clingo.control.Control, clingodl.ClingoDlTheory]
    """
    # set seed if given
    if lns_object.param_values["seed"] is not None:
        lns_object.set_seed(lns_object.param_values["seed"])
    args = [f"--{i[0]}={i[1]}" for i in lns_object.param_values["clingo_args"].items()]

    ctl = clingo.Control(args)
    # no input files not supported
    # if not lns_object._files:
    #    lns_object._files = ["-"]
    for path in lns_object.param_values["files"]:
        ctl.load(path)
    return ctl, None


# pylint: disable=unused-argument
def repair_clingo(
    lns_object: LNS,
    ctl: clingo.control.Control,
    assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
    thy: Any,
) -> clingo.solving.SolveResult:
    """
    Solve under given assumptions using clingo.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Clingo Control object used for solving.
    :type ctl: clingo.control.Control
    :param assumptions: Assumptions for solving (fixed atoms).
    :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
    :param thy: Theory object.
    :type thy: Any
    :return: Solve result.
    :rtype: clingo.solving.SolveResult
    """
    with ctl.solve(
        assumptions=assumptions, on_model=lns_object.on_model, async_=True
    ) as handle:
        done = handle.wait(lns_object.param_values["time_limit"])
        if not done:
            handle.cancel()
            lns_object.callables["time_out"](lns_object)
        res = handle.get()
    return res


def repair_clingo_dl(
    lns_object: LNS,
    ctl: clingo.control.Control,
    assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
    thy: ClingoDLTheory,
) -> clingo.solving.SolveResult:
    """
    Solve under given assumptions using clingo.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Clingo Control object used for solving.
    :type ctl: clingo.control.Control
    :param assumptions: Assumptions for solving (fixed atoms).
    :type assumptions: List[Tuple[clingo.symbol.Symbol, bool]]
    :param thy: clingo-dl theory object.
    :type thy: clingodl.ClingoDlTheory
    :return: Solve result.
    :rtype: clingo.solving.SolveResult
    """
    thy.prepare(ctl)
    with ctl.solve(
        assumptions=assumptions, yield_=True, on_model=lns_object.on_model, async_=True
    ) as handle:
        done = handle.wait(lns_object.param_values["time_limit"])
        if not done:
            handle.cancel()
            lns_object.callables["time_out"](lns_object)
        res = handle.get()
    return res


def ground_base(lns_object: LNS, ctl: clingo.Control) -> None:
    """
    Ground base using control object.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Clingo Control object used for solving.
    :type ctl: clingo.control.Control
    """
    ctl.ground([("base", [])], context=lns_object)

"""
Collection of functions implementing different theories used for LNS.
"""

from __future__ import annotations

import random
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
    thy = ClingoDLTheory()
    ctl = clingo.Control(lns_object.param_values["clingo_args"])
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

    # set seed if given
    if lns_object.param_values["seed"] is not None:
        random.seed(lns_object.param_values["seed"])
        lns_object.param_values["clingo_args"].append(
            f"--seed={lns_object.param_values['seed']}"
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
    ctl = clingo.Control(lns_object.param_values["clingo_args"])
    # no input files not supported
    # if not lns_object._files:
    #    lns_object._files = ["-"]
    for path in lns_object.param_values["files"]:
        ctl.load(path)

    # set seed if given
    if lns_object.param_values["seed"] is not None:
        random.seed(lns_object.param_values["seed"])
        lns_object.param_values["clingo_args"].append(
            f"--seed={lns_object.param_values['seed']}"
        )
    return (ctl, None)


# pylint: disable=unused-argument
def repair_clingo(
    lns_object: LNS,
    ctl: clingo.control.Control,
    assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
    thy: Any,
) -> bool:
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
    :return: Whether model was found.
    :rtype: bool
    """
    with ctl.solve(assumptions=assumptions, yield_=True, async_=True) as handle:
        for model in handle:
            lns_object.models["new_model"] = {}
            lns_object.models["new_model"]["shown"] = model.symbols(shown=True)
            lns_object.models["new_model"]["true"] = model.symbols(atoms=True)
            if model:
                return True
    return False


def repair_clingo_dl(
    lns_object: LNS,
    ctl: clingo.control.Control,
    assumptions: List[Tuple[clingo.symbol.Symbol, bool]],
    thy: ClingoDLTheory,
) -> bool:
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
    :return: Whether model was found.
    :rtype: bool
    """
    thy.prepare(ctl)
    with ctl.solve(
        assumptions=assumptions, yield_=True, on_model=thy.on_model, async_=True
    ) as handle:
        for model in handle:
            lns_object.models["new_model"] = {}
            lns_object.models["new_model"]["shown"] = model.symbols(shown=True)
            lns_object.models["new_model"]["true"] = model.symbols(atoms=True)
            lns_object.models["new_model"]["assignments"] = [
                f"{key}={val}" for key, val in thy.assignment(model.thread_id)
            ]
            if model:
                return True
    return False


def ground_base(lns_object: LNS, ctl: clingo.Control) -> None:
    """
    Ground base using control object.

    :param lns_object: LNS object.
    :type lns_object: large_neighbourhood_search.LNS
    :param ctl: Clingo Control object used for solving.
    :type ctl: clingo.control.Control
    """
    ctl.ground([("base", [])], context=lns_object)

"""
The command line parser for the project.
"""

import logging
import sys
from argparse import ArgumentParser
from textwrap import dedent
from typing import Any, cast

from mod_lns.interfaces import solver, strategy
from mod_lns.lib.solvers import *
from mod_lns.lib.strategies import *


__all__ = ["get_parser"]

if sys.version_info[1] < 8:
    import importlib_metadata as metadata  # nocoverage
else:
    from importlib import metadata  # nocoverage

VERSION = metadata.version("mod_lns")


def get_parser() -> ArgumentParser:
    """
    Return the parser for command line options.
    """
    parser = ArgumentParser(
        prog="mod_lns",
        description=dedent(
            """\
            Modular Large Neighbourhood Search (LNS) Framework using ASP.\n
            Check the documentation for a guide on how to use this framework
            and all possible options for configuration.

            --heuristic, --constrained and --declarative options should not be used
            when using custom solvers and/or strategies.  
            """
        ),
    )

    # dict of supported solvers
    solvers = [(cls.__name__, cls()) for cls in solver.SolverInterface.__subclasses__()]
    
    # dict of all supported strategies
    strategies = [(cls.__name__, cls()) for cls in strategy.StrategyInterface.__subclasses__()]

    levels = [
        ("error", logging.ERROR),
        ("warning", logging.WARNING),
        ("info", logging.INFO),
        ("debug", logging.DEBUG),
    ]

    def get(levels, name):
        for key, val in levels:
            if key == name:
                return val
        return None  # nocoverage

    parser.add_argument(
        "--log",
        default="warning",
        choices=[val for _, val in levels],
        metavar=f"{{{','.join(key for key, _ in levels)}}}",
        help="set log level [%(default)s]",
        type=cast(Any, lambda name: get(levels, name)),
    )

    parser.add_argument(
        "--version", "-v", action="version", version=f"%(prog)s {VERSION}"
    )

    parser.add_argument(
        "-i", "--input_files", help="ASP input file(s)", nargs="+", required=True
    )

    parser.add_argument(
        "--solver",
        default="ClingoSolver",
        choices=[val for _, val in solvers],
        metavar=f"{{{','.join(key for key, _ in solvers)}}}",
        help="set LNS solver [%(default)s]",
        type=cast(Any, lambda name: get(solvers, name)),
    )

    parser.add_argument(
        "--strategy",
        default="DefaultStrategy",
        choices=[val for _, val in strategies],
        metavar=f"{{{','.join(key for key, _ in strategies)}}}",
        help="set LNS strategy [%(default)s]",
        type=cast(Any, lambda name: get(strategies, name)),
    )

    parser.add_argument(
        "--heuristic",
        action="store_true",
        help="enable heuristics during reparation",
    )

    parser.add_argument(
        "--constrained",
        action="store_true",
        help="enable constrained approach",
    )

    parser.add_argument(
        "--declarative",
        action="store_true",
        help="enable declarative relaxation",
    )

    parser.add_argument(
        "--seed",
        help="set lns seed [%(default)s]",
        default=None,
        type=int,
    )

    parser.add_argument(
        "-r",
        "--relax_rate",
        help="set relax rate 0 < [%(default)s] <= 1",
        default=0.2,
        type=float,
    )

    parser.add_argument(
        "--time_limit",
        help="set time limit in seconds [%(default)s]",
        default=600,
        type=int,
    )

    parser.add_argument(
        "--solve_time_limit",
        help="set time limit for each solve call [%(default)s]",
        default=20,
        type=int,
    )

    parser.add_argument(
        "--max_steps",
        help="set maximum number of steps [%(default)s], non-int string for no limit",
        default="2000",
        type=str,
    )

    return parser

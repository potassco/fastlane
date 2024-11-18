"""
The command line parser for the project.
"""

import logging
import sys
from argparse import ArgumentParser
from textwrap import dedent
from typing import Any, cast

from large_neighbourhood_search.lib.solvers.clingo_dl_heu_solver import (
    ClingoDLHeuSolver,
)
from large_neighbourhood_search.lib.solvers.clingo_dl_solver import ClingoDLSolver
from large_neighbourhood_search.lib.solvers.clingo_heu_solver import ClingoHeuSolver
from large_neighbourhood_search.lib.solvers.clingo_solver import ClingoSolver
from large_neighbourhood_search.lib.strategies.classic_lexicographic_declarative import (
    ClassicLexiDecl,
)
from large_neighbourhood_search.lib.strategies.classic_lexicographic_rnd import (
    ClassicLexiRnd,
)
from large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd import (
    ClassicWeightedSumRnd,
)
from large_neighbourhood_search.lib.strategies.hc_lexicographic_declarative import (
    HCLexiDecl,
)
from large_neighbourhood_search.lib.strategies.hc_lexicographic_rnd import HCLexiRnd
from large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd import (
    HCWeightedSumRnd,
)

__all__ = ["get_parser"]

if sys.version_info[1] < 8:
    import importlib_metadata as metadata  # nocoverage
else:
    from importlib import metadata  # nocoverage

VERSION = metadata.version("large_neighbourhood_search")


def get_parser() -> ArgumentParser:
    """
    Return the parser for command line options.
    """
    parser = ArgumentParser(
        prog="large_neighbourhood_search",
        description=dedent(
            """\
            ASP using Large-Neighbourhood Search (LNS).\n
            Check the documentation for a guide on how to use this framework
            and all possible options for configuration.
            """
        ),
    )

    # dict of supported solvers
    solvers = [
        ("ClingoSolver", ClingoSolver()),
        ("ClingoHeuSolver", ClingoHeuSolver()),
        ("ClingoDLSolver", ClingoDLSolver()),
        ("ClingoDLHeuSolver", ClingoDLHeuSolver()),
    ]

    # dict of all supported strategies
    strategies = [
        ("ClassicWeightedSumRnd", ClassicWeightedSumRnd()),
        ("ClassicLexiRnd", ClassicLexiRnd()),
        ("ClassicLexiDecl", ClassicLexiDecl()),
        ("HCWeightedSumRnd", HCWeightedSumRnd()),
        ("HCLexiRnd", HCLexiRnd()),
        ("HCLexiDecl", HCLexiDecl()),
    ]

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
        default="ClassicWeightedSumRnd",
        choices=[val for _, val in strategies],
        metavar=f"{{{','.join(key for key, _ in strategies)}}}",
        help="set LNS strategy [%(default)s]",
        type=cast(Any, lambda name: get(strategies, name)),
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

    parser.add_argument(
        "--no_improv",
        help="set maximum number of steps without improvement [%(default)s], non-int string for no limit",
        default="1000",
        type=str,
    )

    parser.add_argument(
        "--vari_accept",
        help="accept solution if specified variability is achieved 0 <= [%(default)s] < relax_rate",
        default=0,
        type=float,
    )

    parser.add_argument(
        "--pre_files",
        help="ASP input file(s) for pre-solving [%(default)s]",
        nargs="*",
        default=[],
    )

    parser.add_argument(
        "--pre_tl", help="pre-solving time-limit [%(default)s]", default=1800, type=int
    )

    parser.add_argument(
        "--start_sol",
        help="set initial solution in the form of: 'atom(1) atom(2) ...'",
        default=None,
        type=str,
    )

    return parser

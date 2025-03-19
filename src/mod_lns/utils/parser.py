"""
The command line parser for the project.
"""

import logging
import sys
from argparse import ArgumentParser
from textwrap import dedent
from typing import Any, cast

__all__ = ["get_parser"]

if sys.version_info[1] < 8:
    import importlib_metadata as metadata  # nocoverage
else:
    from importlib import metadata  # nocoverage

VERSION = metadata.version("mod_lns")

import importlib
import inspect
import pkgutil

# temporary solution
def get_classes_from_package(package: str) -> list[type]:
    """
    Return all classes inside given package.

    :param package: Package string.
    :type package: str
    :return: List of classes in package.
    :rtype: list[type]
    """
    classes_in_package = []
    # Go through the modules in the package
    for _importer, module_name, _ in pkgutil.iter_modules(
        importlib.import_module(package).__path__
    ):
        full_module_name = f"{package}.{module_name}"
        # Load the module for inspection
        module = importlib.import_module(full_module_name)

        # Filter for class objects and only objects that exist within the module
        for _name, obj in inspect.getmembers(
            module,
            lambda member, module_name=full_module_name: inspect.isclass(member)
            and member.__module__ == module_name,
        ):
            classes_in_package.append(obj)
    return classes_in_package


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
    # list of supported solvers
    solvers = [
        (cls.__name__, cls()) for cls in get_classes_from_package("mod_lns.lib.solvers")
    ]

    # list of supported strategies
    strategies = [
        (cls.__name__, cls())
        for cls in get_classes_from_package("mod_lns.lib.strategies")
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

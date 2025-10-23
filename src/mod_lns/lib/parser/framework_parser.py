"""
The command line parser for framework arguments.
"""

import importlib
import inspect
import logging
import pkgutil
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from textwrap import dedent
from typing import Any, cast, no_type_check

from mod_lns.interfaces.strategy import StrategyInterface

__all__ = ["get_framework_parser"]

if sys.version_info[1] < 8:
    import importlib_metadata as metadata  # nocoverage
else:
    from importlib import metadata  # nocoverage

VERSION = metadata.version("mod_lns")


# temporary solution
@no_type_check
def get_classes_from_package(package: str, base: type) -> list[type]:
    """
    Return all classes inside given package.

    :param package: Package string.
    :type package: str
    :param base: Base class to filter by.
    :type base: type
    :return: List of classes in package.
    :rtype: list[type]
    """
    classes_in_package = []
    # Go through the modules in the package
    for _, module_name, _ in pkgutil.iter_modules(
        importlib.import_module(package).__path__
    ):
        full_module_name = f"{package}.{module_name}"
        # Load the module for inspection
        module = importlib.import_module(full_module_name)

        # Filter for class objects and only objects that exist within the module
        for _, obj in inspect.getmembers(
            module,
            lambda member, module_name=full_module_name, base=base: inspect.isclass(
                member
            )
            and member.__module__ == module_name
            and base in inspect.getmro(member),
        ):
            classes_in_package.append(obj)
    return classes_in_package


def get_framework_parser() -> ArgumentParser:
    """
    Return the parser for command line options.
    """

    def formatter(prog: str) -> RawTextHelpFormatter:
        return RawTextHelpFormatter(
            prog,
            max_help_position=10,
            width=100,
        )

    parser = ArgumentParser(
        prog="mod_lns",
        description=dedent(
            """\
            Modular Large Neighbourhood Search (LNS) Framework using ASP.\n
            Check the documentation for a guide on how to use this framework
            and all possible options for configuration.

            This framework can not be run on its own but requires the use of a
            sub command to run a specific LNS strategy.
            """
        ),
        formatter_class=formatter,
    )

    # list of supported strategies
    strategies = [
        (cls.__name__, cls())
        for cls in get_classes_from_package("mod_lns.lib.strategies", StrategyInterface)
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
        "--log-level",
        default="warning",
        choices=[val for _, val in levels],
        metavar=f"{{{','.join(key for key, _ in levels)}}}",
        help="set log level [%(default)s]",
        type=cast(Any, lambda name: get(levels, name)),
        dest="log_level",
    )

    parser.add_argument(
        "--version", "-v", action="version", version=f"%(prog)s {VERSION}"
    )

    parser.add_argument("files", help="ASP input file(s)", nargs="+")

    subparsers = parser.add_subparsers(
        title="LNS Systems", help="LNS System", required=True
    )
    for system in strategies:
        system[1].get_parser(subparsers)

    return parser

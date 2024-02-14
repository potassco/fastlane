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

VERSION = metadata.version("large_neighbourhood_search")


def get_parser() -> ArgumentParser:
    """
    Return the parser for command line options.
    """
    parser = ArgumentParser(
        prog="large_neighbourhood_search",
        description=dedent(
            """\
            ASP using Large-Neighbourhood Search (LNS)
            """
        ),
    )

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
        "-i", help="Input file(s)", nargs="+"
    )

    parser.add_argument(
        "--lns_seed", help="Random seed for LNS.", default=None, type=int
    )

    parser.add_argument(
        "--bnb_search", help="Perform standard branch-and-bound search (no LNS).", action="store_true"
    )

    parser.add_argument(
        "--declarative", help="Perform LNS using declarative neighbourhood.", action="store_true"
    )

    return parser

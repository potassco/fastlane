"""
Parser for default strategy in LNS.
"""

from argparse import ArgumentParser, RawTextHelpFormatter, _SubParsersAction
import logging
from textwrap import dedent
from typing import no_type_check, Optional
import pkgutil
import importlib
import sys
import inspect
from clingo import Configuration, Control

from mod_lns.interfaces.solver import SolverInterface
from mod_lns.lib import parser
from mod_lns.lns_config import LNSConfig
from mod_lns.lib.converter import (
    AutoDestructionConverter,
    AverageDestructionConverter,
    LastImprovementDestructionConverter,
)

if sys.version_info[1] < 8:
    import importlib_metadata as metadata  # nocoverage
else:
    from importlib import metadata  # nocoverage

VERSION = metadata.version("mod_lns")

class OptionsParser:
    """
    Parser for command line options.
    """

    @no_type_check
    @staticmethod
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
        for _, module_name, _ in pkgutil.iter_modules(importlib.import_module(package).__path__):
            full_module_name = f"{package}.{module_name}"
            # Load the module for inspection
            module = importlib.import_module(full_module_name)

            # Filter for class objects and only objects that exist within the module
            for _, obj in inspect.getmembers(
                module,
                lambda member, module_name=full_module_name, base=base: inspect.isclass(member)
                and member.__module__ == module_name
                and base in inspect.getmro(member),
            ):
                classes_in_package.append(obj)
        return classes_in_package

    @staticmethod
    def formatter(prog: str) -> RawTextHelpFormatter:
        return RawTextHelpFormatter(
            prog,
            max_help_position=10,
            width=100,
        )

    @classmethod
    def get_parser(cls) -> ArgumentParser:
        """
        Return the parser for command line options.
        """
        parser = ArgumentParser(
            prog="mod_lns",
            description=dedent("""\
                Modular Large Neighbourhood Search (LNS) Framework using ASP.\n
                Check the documentation for a guide on how to use this framework
                and all possible options for configuration.

                This framework can not be run on its own but requires the use of a
                sub command to run a specific LNS strategy.

                You can access the sub command help by using 'mod_lns <strategy> -h'.
                """),
            formatter_class=cls.formatter,
        )


        logging_levels = {
            "error": logging.ERROR,
            "warning": logging.WARNING,
            "info": logging.INFO,
            "debug": logging.DEBUG,
        }

        parser.register("type", "logging_level", lambda name: logging_levels.get(name))

        solvers = {solver_cls.get_name(): solver_cls() for solver_cls in cls.get_classes_from_package("mod_lns.lib.solvers", SolverInterface)}

        def parse_solver(solvers: dict[str, SolverInterface], string: str) -> SolverInterface:
            """
            Parse the solver string.
            """
            solver = solvers.get(string)
            if solver is None:
                parser.error(f"'{string}': Invalid solver. Choose from {','.join(solvers.keys())}")
            return solver
        
        parser.register("type", "solver", lambda string: parse_solver(solvers, string))

        def parse_pos_int_or_none(string: str) -> Optional[int]:
            """
            Parse an positive integer or None.
            """
            if string.lower() == "none":
                return None
            try:
                value = int(string)
            except ValueError:
                parser.error(f"'{string}': Invalid positive integer.")
            if value < 0:
                parser.error(f"'{string}': Value must be non-negative.")
            return value

        parser.register("type", "pos_int_or_none", parse_pos_int_or_none)

        def parse_solve_limit(string: str) -> Optional[str]:
            """
            Parse the solve limit string.
            """
            ctl = Control()
            assert isinstance(ctl.configuration.solve, Configuration)
            if string.lower() == "none":
                return None
            try:
                ctl.configuration.solve.solve_limit = string
            except RuntimeError:
                parser.error(f"'{string}': Invalid solve limit.")
            return string
    
        parser.register("type", "solve_limit", parse_solve_limit)

        def parse_percent(string: str, msg: str = "Invalid percentage, percentage must be between 0 and 100.") -> int:
            """
            Parse percentage.
            """
            try:
                value = int(string)
            except ValueError:
                parser.error(f"'{string}': {msg}")
            if not (0 <= value <= 100):
                parser.error(f"'{string}': {msg}")
            return value
        
        parser.register("type", "percent", parse_percent)

        def parse_relaxation(string: str) -> tuple[bool, int]:
            """
            Parse the relaxation string.
            """
            if string == "declarative":
                return True, 0
            if string.startswith("simple,"):
                rate = string.split(",", 1)[1]
                if rate.lower() == "auto":
                    return False, -1
                rate = parse_percent(rate, msg="Invalid relax rate, rate must be between 0 and 100 or 'auto'.")
                return False, rate
            else:
                parser.error(f"'{string}': Invalid relaxation. Choose from {{simple,<rate>|declarative}}")

        parser.register("type", "relaxation", parse_relaxation)

        converters: dict[str, AutoDestructionConverter] = {
            "avg": AverageDestructionConverter(),
            "last-improv": LastImprovementDestructionConverter(),
        }

        def parse_auto_converter(converters: dict[str, AutoDestructionConverter], string: str) -> AutoDestructionConverter:
            """
            Parse the auto converter string.
            """
            converter = converters.get(string)
            if converter is None:
                parser.error(
                    f"'{string}': Invalid auto converter. Choose from {','.join(converters.keys())}"
                )
            return converter

        parser.register("type", "auto_converter", lambda string: parse_auto_converter(converters, string))

        ##########
        # general options
        parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {VERSION}")

        parser.add_argument(
            "--log-level",
            default="warning",
            choices=logging_levels.values(),
            metavar=f"{{{','.join(logging_levels.keys())}}}",
            help="set log level [%(default)s]",
            type="logging_level",
            dest="log_level",
        )

        parser.add_argument(
            "--solver",
            default="clingo",
            choices=solvers.values(),
            metavar=f"{{{','.join(solvers.keys())}}}",
            help="set LNS solver [%(default)s]",
            type="solver",
        )

        parser.add_argument(
            "--seed",
            default=LNSConfig.seed,
            metavar="<n>",
            help="set lns seed [%(default)s]",
            type=int,
        )

        parser.add_argument(
            "--time-limit",
            help="set time limit in seconds [%(default)s]",
            default=LNSConfig.time_limit,
            type="pos_int_or_none",
            dest="time_limit",
            metavar="<n>",
        )

        parser.add_argument(
            "--max-steps",
            help="set maximum number of LNS steps [%(default)s]",
            default=LNSConfig.max_steps,
            type="pos_int_or_none",
            dest="max_steps",
            metavar="<n>",
        )

        ##########
        # init solver options
        init_solver_group = parser.add_argument_group(
            "Initial Solver Configuration",
            "Configuration options for the initial solver\n"
            "used to find the first solution.",
        )

        init_solver_group.add_argument(
            "--init-solve-limit",
            help="set initial solver solve limit [%(default)s]",
            default=LNSConfig.init_solve_limit,
            type="solve_limit",
            dest="init_solve_limit",
            metavar="<n>[,<m>]",
        )

        init_solver_group.add_argument(
            "--init-time-limit",
            help="set initial solver time limit [%(default)s]",
            default=LNSConfig.init_time_limit,
            type="pos_int_or_none",
            dest="init_time_limit",
            metavar="<n>",
        )

        # model limit

        ##########
        # lns options
        lns_group = parser.add_argument_group(
            "LNS Configuration",
            "Configuration options for the LNS.",
        )

        # --bound?
        lns_group.add_argument(
            "--constrained",
            help="set LNS to use constrained optimization",
            action="store_true",
            dest="constrained",
        )

        lns_group.add_argument(
            "--relaxation",
            help=(
                "set relaxation mode and rate for simple relaxation in percent [%(default)s]\n"
                "<rate>:      Relaxation rate between 0 and 100 or 'auto' for automatic rate.\n"
                "             See --auto-converter options for details on how the automatic rate is calculated.\n"
                "declarative: Use declarative relaxation, LNS configuration encoding has to be provided as input file."
            ),
            default=f"{LNSConfig.relaxation[0]},{LNSConfig.relaxation[1] if LNSConfig.relaxation[1] > 0 else 'auto'}",
            type="relaxation",
            dest="relaxation",
            metavar="{simple,<rate>|declarative}",
        )

        lns_group.add_argument(
            "--auto-converter",
            help=(
                "Set automatic destroy percentage converter [%(default)s]\n" \
                "last-improv: Set auto destroy rate based on actually relaxed atoms during last improvement.\n"
                "avg:         Set auto destroy rate based on average percentages of relaxed atoms during all improvements.\n"
                "Note: Used for --relaxation=simple,auto and _lns_relax_op/2 for --relaxation=declarative.\n"
                "      Best used together with --repair=heuristics"
            ),
            default="last-improv",
            choices=list(converters.values()),
            type="auto_converter",
            dest="auto_converter",
            metavar=f"{{{','.join(converters.keys())}}}",
        )
        
        lns_group.add_argument(
            "--accept-variability",
            help="set required variability to accept new solutions in percent [%(default)s]",
            default=LNSConfig.accept_variability,
            type="percent",
            dest="accept_variability",
            metavar="<n>",
        )

        lns_group.add_argument(
            "--preset",
            help=(
                f"Set LNS configuration preset\n"
                f"<arg>: {{basic}}\n"
                f"basic:  Basic configuration suitable for many problems.\n"
                f"Presets:\n"
                f"[basic]:\n"
                f" --time-limit={LNSConfig.preset_values['basic']['time_limit']}"
                f" --max-steps={LNSConfig.preset_values['basic']['max_steps']}"
                f" --relaxation={LNSConfig.preset_values['basic']['relaxation'][0]},{LNSConfig.preset_values['basic']['relaxation'][1] if LNSConfig.preset_values['basic']['relaxation'][1] > 0 else 'auto'}\n"
                f" --init-time-limit={LNSConfig.preset_values['basic']['init_time_limit']}"
                f" --init-solve-limit={LNSConfig.preset_values['basic']['init_solve_limit']}\n"
                f" --lns-time-limit={LNSConfig.preset_values['basic']['lns_time_limit']}"
                f" --lns-solve-limit={LNSConfig.preset_values['basic']['lns_solve_limit']}"
            ),
            choices=["basic"],
            default=LNSConfig.preset,
            type=str,
            dest="preset",
            metavar="<arg>",
        )

        ##########
        # lns solver options
        lns_solver_group = parser.add_argument_group(
            "LNS Solver Configuration",
            "Configuration options for the LNS solver.",
        )

        lns_solver_group.add_argument(
            "--lns-solve-limit",
            help="set LNS solve limit [%(default)s]",
            default=LNSConfig.lns_solve_limit,
            type="solve_limit",
            metavar="<n>[,<m>]",
            dest="lns_solve_limit",
        )

        lns_solver_group.add_argument(
            "--lns-time-limit",
            help="set LNS time limit [%(default)s]",
            default=LNSConfig.lns_time_limit,
            type="pos_int_or_none",
            metavar="<n>",
            dest="lns_time_limit",
        )

        ##########
        # parameters
    
        parser.add_argument("files", help="ASP input file(s)", nargs="+")

        return parser





"""
Parser for LNS options.
"""

import importlib
import inspect
import logging
import os
import pkgutil
import sys
import uuid
from argparse import ArgumentParser, ArgumentTypeError, BooleanOptionalAction, RawTextHelpFormatter
from textwrap import dedent
from typing import Any, Optional, no_type_check

from clingo import Configuration, Control, parse_term
from clingo.symbol import Symbol

from mod_lns import UNSET
from mod_lns.interfaces.auto_destruction_converter import AutoDestructionConverter
from mod_lns.interfaces.solver import Solver
from mod_lns.lib.auto_destruction_converters.average import (
    AverageDestructionConverter,
)
from mod_lns.lib.auto_destruction_converters.last_improv import LastImprovementDestructionConverter
from mod_lns.lns_options import LNSOptions

if sys.version_info[1] < 8:
    import importlib_metadata as metadata  # nocoverage
else:
    from importlib import metadata  # nocoverage

VERSION = metadata.version("mod_lns")

# pylint: disable=line-too-long


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
        """
        Get custom formatter for command line options.

        :param prog: Program name.
        :type prog: str
        :return: Custom formatter.
        :rtype: RawTextHelpFormatter
        """
        return RawTextHelpFormatter(
            prog,
            max_help_position=10,
            width=100,
        )

    # pylint: disable=too-many-statements
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

        parser.register("type", "logging_level", logging_levels.get)

        solvers = {
            solver_cls.get_name(): solver_cls()
            for solver_cls in cls.get_classes_from_package("mod_lns.lib.solvers", Solver)
        }

        def parse_solver(solvers: dict[str, Solver], string: str) -> Solver:
            """
            Parse the solver string.
            """
            solver = solvers.get(string)
            if solver is None:
                raise ArgumentTypeError(f"'{string}': Invalid solver. Choose from {','.join(solvers.keys())}")
            return solver

        parser.register("type", "solver", lambda string: parse_solver(solvers, string))

        def parse_pos_int(string: str) -> int:
            """
            Parse a positive integer.
            """
            try:
                value = int(string)
            except ValueError as e:
                raise ArgumentTypeError(f"'{string}': Invalid positive integer.") from e
            if value < 0:
                raise ArgumentTypeError(f"'{string}': Value must be non-negative.")
            return value

        parser.register("type", "pos_int", parse_pos_int)

        def parse_pos_int_or_none(string: str) -> Optional[int]:
            """
            Parse an positive integer or None.
            """
            if string.lower() == "none":
                return None
            return parse_pos_int(string)

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
            except RuntimeError as e:
                raise ArgumentTypeError(f"'{string}': Invalid solve limit.") from e
            return string

        parser.register("type", "solve_limit", parse_solve_limit)

        def parse_0_1_float(string: str) -> float:
            """
            Parse a float between 0 and 1.
            """
            try:
                value = float(string)
            except ValueError as e:
                raise ArgumentTypeError(f"'{string}': Invalid float value.") from e
            if not 0 < value < 1:
                raise ArgumentTypeError(f"'{string}': Value must be between 0 and 1.")
            return value

        parser.register("type", "0_1_float", parse_0_1_float)

        def parse_percent(string: str, msg: str = "Invalid percentage, percentage must be between 0 and 100.") -> int:
            """
            Parse percentage between 0 and 100.
            """
            try:
                value = int(string)
            except ValueError as e:
                raise ArgumentTypeError(f"'{string}': {msg}") from e
            if not 0 <= value <= 100:
                raise ArgumentTypeError(f"'{string}': {msg}")
            return value

        parser.register("type", "percent", parse_percent)

        def parse_relaxation(string: str) -> tuple[str, int]:
            """
            Parse the relaxation string.
            """
            if string == "declarative":
                return "declarative", 0
            if string.startswith("simple,"):
                rate = string.split(",", 1)[1]
                if rate.lower() == "auto":
                    return "simple", -1
                rate = parse_percent(rate, msg="Invalid relax rate, rate must be between 0 and 100 or 'auto'.")
                return "simple", rate
            raise ArgumentTypeError(f"'{string}': Invalid relaxation. Choose from {{simple,<rate>|declarative}}")

        parser.register("type", "relaxation", parse_relaxation)

        def parse_parallel_mode(string: str) -> str:
            """
            Parse the parallel mode string.
            """
            values = string.split(",")
            if len(values) == 1:
                try:
                    x = int(values[0])
                except ValueError as e:
                    raise ArgumentTypeError(f"'{string}': Invalid number of threads. Integer expected.") from e
                try:
                    assert 1 <= x <= 64
                except AssertionError as e:
                    raise ArgumentTypeError(f"'{string}': Invalid number of threads. 1 <= x <= 64 expected.") from e
            elif len(values) == 2:
                if values[1] not in ("compete", "split"):
                    raise ArgumentTypeError(f"'{string}': Invalid mode. {{compete|split}} expected.")
            else:
                raise ArgumentTypeError(f"'{string}': Invalid argument.")
            return string

        parser.register("type", "parallel_mode", parse_parallel_mode)

        def parse_minimize_variable(string: str) -> Symbol:
            """
            Parse the minimize variable string.
            """
            try:
                term = parse_term(string)
            except RuntimeError as e:
                raise ArgumentTypeError(f"'{string}': Invalid minimize variable.") from e
            return term

        parser.register("type", "minimize_variable", parse_minimize_variable)

        # def parse_falsify(string: str) -> str:
        #     """
        #     Parse the falsify string.
        #     """
        #     if string == "inf":
        #         return string
        #     try:
        #         int(string)
        #     except ValueError as e:
        #         raise ArgumentTypeError(f"'{string}': Invalid falsify variable. {{<n>, inf}} expected.") from e
        #     return string

        # parser.register("type", "falsify", parse_falsify)

        def _can_instantiate_without_args(cls: type) -> bool:
            """
            Check whether class can be instantiated without passing user arguments.
            """
            try:
                signature = inspect.signature(cls)
            except (TypeError, ValueError):
                return False

            for parameter in signature.parameters.values():
                if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue
                if parameter.default is inspect.Parameter.empty:
                    return False
            return True

        def _context_parser(string: str) -> Any:
            """
            Parse context object whose methods are called during grounding using the @-syntax.
            """
            path = os.path.abspath(os.path.expanduser(string))
            if not os.path.isfile(path):
                raise ArgumentTypeError(f"'{string}': File does not exist.")

            spec = importlib.util.spec_from_file_location(f"context_{uuid.uuid4().hex}", path)
            if spec is None or spec.loader is None:
                raise ArgumentTypeError(f"'{string}': Failed to load context module.")

            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                raise ArgumentTypeError(f"'{string}': Error while importing context module: {exc}") from exc

            classes = [
                cls
                for _, cls in inspect.getmembers(module, inspect.isclass)
                if cls.__module__ == module.__name__ and _can_instantiate_without_args(cls)
            ]

            if len(classes) == 1:
                return classes[0]()
            if len(classes) == 0:
                raise ArgumentTypeError(f"'{string}': No valid context class found in provided module.")
            raise ArgumentTypeError(
                f"'{string}': Multiple valid context classes found "
                f"({','.join(class_.__name__ for class_ in classes)}). Provide only one."
            )

        parser.register("type", "context", _context_parser)

        adaptive_strategies: list[str] = LNSOptions.get_supported_adaptive_strategy_names()

        def parse_adaptive_strategy(string: str) -> str:
            """
            Parse the adaptive strategy string.
            """
            if string not in adaptive_strategies:
                raise ArgumentTypeError(
                    f"'{string}': Invalid adaptive strategy. Choose from {{{','.join(adaptive_strategies)}}}"
                )
            return string

        parser.register("type", "adaptive_strategy", parse_adaptive_strategy)

        converters: dict[str, AutoDestructionConverter] = {
            "avg": AverageDestructionConverter(),
            "last-improv": LastImprovementDestructionConverter(),
        }

        def parse_auto_converter(
            converters: dict[str, AutoDestructionConverter], string: str
        ) -> AutoDestructionConverter:
            """
            Parse the auto converter string.
            """
            converter = converters.get(string)
            if converter is None:
                raise ArgumentTypeError(
                    f"'{string}': Invalid auto converter. Choose from {','.join(converters.keys())}"
                )
            return converter

        parser.register("type", "auto_converter", lambda string: parse_auto_converter(converters, string))

        def parse_init_opt_mode(string: str) -> str:
            """
            Parse the optimization mode string.
            """
            ctl = Control()
            try:
                ctl.configuration.solve.opt_mode = string  # type: ignore
            except RuntimeError as e:
                raise ArgumentTypeError(f"'{string}': Invalid opt mode.") from e
            return string

        parser.register("type", "init_opt_mode", parse_init_opt_mode)

        # pylint: disable=too-many-branches
        def parse_lns_opt_mode(string: str) -> dict[str, Any]:
            """
            Parse the lns optimization mode string.
            """
            opt_mode: dict[str, Any] = {}
            values = string.split(",")
            if values[0] not in ("opt", "enum", "optN", "ignore"):
                raise ArgumentTypeError(f"'{string}': Invalid optimization mode. {{opt|enum|optN|ignore}} expected.")
            opt_mode["mode"] = values[0]
            if len(values) == 1:
                opt_mode["nf"] = None
                opt_mode["modifier"] = None
            elif len(values) == 2:
                try:
                    float(values[1])
                except ValueError as e:
                    raise ArgumentTypeError(f"'{string}': Invalid bound. float expected.") from e
                opt_mode["nf"] = values[1]
                opt_mode["modifier"] = "dynamic"
            elif len(values) >= 3:
                if values[-1] == "static":
                    try:
                        for v in values[1:-1]:
                            int(v)
                    except ValueError as e:
                        raise ArgumentTypeError(f"'{string}': Invalid bounds. integers expected.") from e
                    opt_mode["nf"] = ",".join(values[1:-1])
                    opt_mode["modifier"] = "static"
                elif values[-1] == "dynamic":
                    if len(values) >= 4:
                        raise ArgumentTypeError(f"'{string}': Invalid number of bounds. Only one boundary expected.")
                    try:
                        float(values[1])
                    except ValueError as e:
                        raise ArgumentTypeError(f"'{string}': Invalid bound. float expected.") from e
                    opt_mode["nf"] = values[1]
                    opt_mode["modifier"] = "dynamic"
                else:
                    raise ArgumentTypeError(f"'{string}': Invalid boundary mode. {{static|dynamic}} expected.")
            return opt_mode

        parser.register("type", "lns_opt_mode", parse_lns_opt_mode)

        def parse_opt_strategy(string: str) -> str:
            """
            Parse the optimization strategy string.
            """
            ctl = Control()
            try:
                ctl.configuration.solver.opt_strategy = string  # type: ignore
            except RuntimeError as e:
                raise ArgumentTypeError(f"'{string}': Invalid opt strategy.") from e
            return string

        parser.register("type", "opt_strategy", parse_opt_strategy)

        def parse_configuration(string: str) -> str:
            """
            Parse the configuration string.
            """
            ctl = Control()
            try:
                ctl.configuration.configuration = string
            except RuntimeError as e:
                raise ArgumentTypeError(f"'{string}': Invalid configuration.") from e
            return string

        parser.register("type", "configuration", parse_configuration)

        def parse_heuristic(string: str) -> str:
            """
            Parse the heuristic string.
            """
            ctl = Control()
            try:
                ctl.configuration.solver.heuristic = string  # type: ignore
            except RuntimeError as e:
                raise ArgumentTypeError(f"'{string}': Invalid heuristic.") from e
            return string

        parser.register("type", "heuristic", parse_heuristic)

        def replace_default(text: str, default_value: Any) -> str:
            """Render config defaults in help while argparse default remains UNSET."""
            return text.replace("%(default)s", str(default_value))

        ##########
        # general options
        parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {VERSION}")

        parser.add_argument(
            "--log-level",
            default=UNSET,
            choices=logging_levels.values(),
            metavar=f"{{{','.join(logging_levels.keys())}}}",
            help=replace_default("Set log level [%(default)s]", "warning"),
            type="logging_level",
            dest="log_level",
        )

        parser.add_argument(
            "--solver",
            default=UNSET,
            choices=solvers.values(),
            metavar=f"{{{','.join(solvers.keys())}}}",
            help=replace_default("Set LNS solver [%(default)s]", "clingo"),
            type="solver",
        )

        parser.add_argument(
            "--preset",
            help=(
                f"Set LNS configuration preset [{LNSOptions.preset}]\n"
                "Manually set parameters take precedence over presets.\n"
                "Presets can be used as a base configuration and then manually adjust individual parameters as needed.\n"
                "<arg>: {basic-assumptions|auto-heuristics|adaptive-heulingo}\n"
                "basic-assumptions:  Basic configuration using assumptions and a fixed relax rate.\n"
                "auto-heuristics:  Configuration using heuristics and an automatically calculated relax rate.\n"
                "adaptive-heulingo:  Configuration corresponding to default adaptive heulingo. Config encoding is required!\n"
                "Presets:\n"
                "[basic-assumptions]:\n"
                f" --relaxation={LNSOptions.preset_values['basic-assumptions']['relaxation'][0]},{LNSOptions.preset_values['basic-assumptions']['relaxation'][1]}"
                f" --init-time-limit={LNSOptions.preset_values['basic-assumptions']['init_time_limit']}"
                f" --lns-time-limit={LNSOptions.preset_values['basic-assumptions']['lns_time_limit']}\n"
                f" --fix={LNSOptions.preset_values['basic-assumptions']['fix']}\n"
                "[auto-heuristics]:\n"
                f" --relaxation={LNSOptions.preset_values['auto-heuristics']['relaxation'][0]},{LNSOptions.preset_values['auto-heuristics']['relaxation'][1]}"
                f" --init-time-limit={LNSOptions.preset_values['auto-heuristics']['init_time_limit']}"
                f" --init-solve-limit={LNSOptions.preset_values['auto-heuristics']['init_solve_limit']}\n"
                f" --lns-time-limit={LNSOptions.preset_values['auto-heuristics']['lns_time_limit']}"
                f" --lns-solve-limit={LNSOptions.preset_values['auto-heuristics']['lns_solve_limit']}"
                f" --fix={LNSOptions.preset_values['auto-heuristics']['fix']}\n"
                "[adaptive-heulingo]:\n"
                f" --relaxation={LNSOptions.preset_values['adaptive-heulingo']['relaxation'][0]},{LNSOptions.preset_values['adaptive-heulingo']['relaxation'][1]}"
                f" --fix={LNSOptions.preset_values['adaptive-heulingo']['fix']}"
                f" --default-adaptive-strategy={LNSOptions.preset_values['adaptive-heulingo']['default_adaptive_strategy_name']}\n"
                f" --learning-rate={LNSOptions.preset_values['adaptive-heulingo']['learning_rate']}"
                f" --lex-weight={LNSOptions.preset_values['adaptive-heulingo']['lex_weight']}"
                f' --auto-converter="last-improv"\n'
                f" --lns-restart-on-model={LNSOptions.preset_values['adaptive-heulingo']['lns_restart_on_model']}"
                f" --init-cutoff={LNSOptions.preset_values['adaptive-heulingo']['init_cutoff']}"
                f" --lns-cutoff={LNSOptions.preset_values['adaptive-heulingo']['lns_cutoff']}\n"
                f" --lns-cutoff-threshold={LNSOptions.preset_values['adaptive-heulingo']['lns_cutoff_threshold']}"
                f" --lns-cutoff-increase-rate={LNSOptions.preset_values['adaptive-heulingo']['lns_cutoff_increase_rate']}"
                f" --lns-heuristic={LNSOptions.preset_values['adaptive-heulingo']['lns_heuristic']}\n"
            ),
            choices=["basic-assumptions", "auto-heuristics", "adaptive-heulingo"],
            default=UNSET,
            type=str,
            dest="preset",
            metavar="<arg>",
        )

        parser.add_argument(
            "--seed",
            default=UNSET,
            metavar="<n>",
            help=replace_default("Set LNS seed [%(default)s]", LNSOptions.seed),
            type=int,
        )

        parser.add_argument(
            "--time-limit",
            help=replace_default("Set time limit in seconds [%(default)s]", LNSOptions.time_limit),
            default=UNSET,
            type="pos_int_or_none",
            dest="time_limit",
            metavar="<n>",
        )

        parser.add_argument(
            "--max-steps",
            help=replace_default("Set maximum number of LNS steps [%(default)s]", LNSOptions.max_steps),
            default=UNSET,
            type="pos_int_or_none",
            dest="max_steps",
            metavar="<n>",
        )

        parser.add_argument(
            "--parallel_mode",
            "-t",
            help=(
                "Run parallel search with given number of threads.\n"
                "<arg>: <n {1..64}>[,<mode {compete|split}>]\n"
                "  <n>: Number of threads to use in search\n"
                "  <mode>: Run competition or splitting based search [compete]\n"
            ),
            default=UNSET,
            type="parallel_mode",
            metavar="<arg>",
            dest="parallel_mode",
        )

        parser.add_argument(
            "--clingo-args",
            help=(
                f"Set additional clingo arguments [{LNSOptions.clingo_args}]\n"
                "Only gringo options (without --text) and clasp's search options are supported.\n"
            ),
            default=UNSET,
            type=str,
            dest="clingo_args",
            metavar="<arg[,arg,...]>",
        )

        parser.add_argument(
            "--context",
            help=replace_default(
                "Path to context file defining context class for @-syntax [%(default)s]", LNSOptions.context
            ),
            default=UNSET,
            type="context",
            dest="context",
            metavar="<arg>",
        )

        parser.add_argument(
            "--minimize-variable",
            help=replace_default(
                "Minimize the integer variable <arg> (only useful with clingo-dl) [%(default)s]",
                LNSOptions.minimize_variable,
            ),
            default=UNSET,
            type="minimize_variable",
            dest="minimize_variable",
            metavar="<arg>",
        )

        # parser.add_argument(
        #     "--falsify",
        #     help=replace_default("Falsify not projected atoms with the priority [%(default)s]", LNSOptions.falsify),
        #     default=UNSET,
        #     type="falsify",
        #     dest="falsify",
        #     metavar="{<n>|inf}",
        # )

        ##########
        # init solver options
        init_solver_group = parser.add_argument_group(
            "Initial Solver Configuration",
            "Configuration options for the initial solver\nused to find the first solution.",
        )

        init_solver_group.add_argument(
            "--init-time-limit",
            help=replace_default("Set initial solver time limit [%(default)s]", LNSOptions.init_time_limit),
            default=UNSET,
            type="pos_int_or_none",
            dest="init_time_limit",
            metavar="<n>",
        )

        init_solver_group.add_argument(
            "--init-cutoff",
            help=replace_default("Set initial solver cutoff [%(default)s]", LNSOptions.init_cutoff),
            default=UNSET,
            type="pos_int_or_none",
            dest="init_cutoff",
            metavar="<arg>",
        )

        init_solver_group.add_argument(
            "--init-solve-limit",
            help=replace_default("Set initial solver solve limit [%(default)s]", LNSOptions.init_solve_limit),
            default=UNSET,
            type="solve_limit",
            dest="init_solve_limit",
            metavar="<n>[,<m>]",
        )

        # fmt: on
        init_solver_group.add_argument(
            "--init-configuration",
            help=replace_default("Set initial solver configuration [%(default)s]", LNSOptions.init_configuration),
            default=UNSET,
            type="configuration",
            dest="init_configuration",
            metavar="<arg>",
        )
        init_solver_group.add_argument(
            "--init-opt-strategy",
            help=replace_default(
                "Set initial solver optimization strategy [%(default)s]", LNSOptions.init_opt_strategy
            ),
            default=UNSET,
            type="opt_strategy",
            dest="init_opt_strategy",
            metavar="<arg>",
        )
        init_solver_group.add_argument(
            "--init-opt-heuristic",
            help=replace_default(
                "Set initial solver optimization heuristic [%(default)s]", LNSOptions.init_opt_heuristic
            ),
            default=UNSET,
            type=str,
            dest="init_opt_heuristic",
            choices=["sign", "model"],
        )
        init_solver_group.add_argument(
            "--init-restart-on-model",
            help=replace_default("Set initial solver restart on model [%(default)s]", LNSOptions.init_restart_on_model),
            action=BooleanOptionalAction,
            default=UNSET,
            dest="init_restart_on_model",
        )
        init_solver_group.add_argument(
            "--init-opt-mode",
            help=(
                "Configure optimization algorithm while finding first solution\n"
                "<arg>: <mode>[,<bound>...]\n"
                "  <mode> : {opt|enum|optN|ignore}\n"
                "    opt   : Find optimal model\n"
                "    enum  : Find models with costs <= initial bound set based on <bound>\n"
                "    optN  : Find optimum, then enumerate optimal models\n"
                "    ignore: Ignore optimize statements\n"
                "  <bound>: <n>\n"
                "    Set initial bound for objective function(s)"
            ),
            default=UNSET,
            type="init_opt_mode",
            dest="init_opt_mode",
            metavar="<arg>",
        )

        # model limit

        ##########
        # adaptive options
        adaptive_group = parser.add_argument_group(
            "Adaptive Configuration",
            "Configuration options for adaptive LNS strategies.\n"
            "These options are only relevant for strategies that implement adaptive features and are ignored by other strategies.",
        )

        adaptive_group.add_argument(
            "--default-adaptive-strategy",
            help=(
                "Set default adaptive strategy for selecting LNS configurations in each iteration.\n"
                f"Will be overwritten by strategy defined in config encoding. [{LNSOptions.default_adaptive_strategy_name}]\n"
            ),
            default=UNSET,
            choices=adaptive_strategies,
            type="adaptive_strategy",
            dest="default_adaptive_strategy_name",
            metavar=f"{{{','.join(adaptive_strategies)}}}",
        )

        adaptive_group.add_argument(
            "--lex-weight",
            help=replace_default(
                "Set weight factor for scalarizing lexicographic costs to <n> (<n> > 0) [%(default)s]",
                LNSOptions.lex_weight,
            ),
            default=UNSET,
            type="pos_int",
            dest="lex_weight",
            metavar="<n>",
        )

        adaptive_group.add_argument(
            "--learning-rate",
            help=replace_default(
                "Set learning rate for updating config weights to <f> (0 < <f> < 1) [%(default)s]",
                LNSOptions.learning_rate,
            ),
            default=UNSET,
            type="0_1_float",
            dest="learning_rate",
            metavar="<f>",
        )

        ##########
        # lns options
        lns_group = parser.add_argument_group(
            "LNS Configuration",
            "Configuration options for the LNS.",
        )

        # --bound?
        lns_group.add_argument(
            "--constrained",
            help=replace_default(
                "Short-hand for --lns-opt-mode=opt,0,dynamic, set LNS to use constrained optimization [%(default)s]",
                LNSOptions.constrained,
            ),
            action="store_true",
            default=UNSET,
            dest="constrained",
        )

        lns_group.add_argument(
            "--relaxation",
            help=replace_default(
                (
                    "Set relaxation mode and rate for simple relaxation in percent [%(default)s]\n"
                    "<rate>:      Relaxation rate between 0 and 100 or 'auto' for automatic rate.\n"
                    "             See --auto-converter options for details on how the automatic rate is calculated.\n"
                    "declarative: Use declarative relaxation, LNS configuration encoding has to be provided as input file."
                ),
                f"{LNSOptions.relaxation[0]},{LNSOptions.relaxation[1] if LNSOptions.relaxation[1] > 0 else 'auto'}",
            ),
            default=UNSET,
            type="relaxation",
            dest="relaxation",
            metavar="{simple,<rate>|declarative}",
        )

        lns_group.add_argument(
            "--fix",
            help=replace_default(
                "Set method to fix non-relaxed atoms during repair [%(default)s]",
                LNSOptions.fix,
            ),
            default=UNSET,
            type=str,
            dest="fix",
            choices=["assumptions", "heuristics"],
        )

        lns_group.add_argument(
            "--auto-converter",
            help=(
                "Set automatic destroy percentage converter [last-improv]\n"
                "last-improv: Set auto destroy rate based on actually relaxed atoms during last improvement.\n"
                "avg:         Set auto destroy rate based on average percentages of relaxed atoms during all improvements.\n"
                "Note: Used for --relaxation=simple,auto and _lns_relax_op/2 for --relaxation=declarative.\n"
                "      Best used together with --repair=heuristics"
            ),
            default=UNSET,
            choices=list(converters.values()),
            type="auto_converter",
            dest="auto_converter",
            metavar=f"{{{','.join(converters.keys())}}}",
        )

        lns_group.add_argument(
            "--accept-variability",
            help=replace_default(
                "Set required variability to accept new solutions in percent [%(default)s]",
                LNSOptions.accept_variability,
            ),
            default=UNSET,
            type="percent",
            dest="accept_variability",
            metavar="<n>",
        )

        lns_group.add_argument(
            "--accept-improvement",
            help=(
                "Do not accept solution whose objective value is at least <n>%% worse\n"
                f"than current incumbent solution in each iteration [{LNSOptions.accept_improvement}]"
            ),
            default=UNSET,
            type="percent",
            dest="accept_improvement",
            metavar="<n>",
        )

        ##########
        # lns solver options
        lns_solver_group = parser.add_argument_group(
            "LNS Solver Configuration",
            "Configuration options for the LNS solver.",
        )

        lns_solver_group.add_argument(
            "--lns-time-limit",
            help=replace_default("Set LNS time limit [%(default)s]", LNSOptions.lns_time_limit),
            default=UNSET,
            type="pos_int_or_none",
            metavar="<n>",
            dest="lns_time_limit",
        )

        lns_solver_group.add_argument(
            "--lns-cutoff",
            help=replace_default("Set LNS cutoff [%(default)s]", LNSOptions.lns_cutoff),
            default=UNSET,
            type="pos_int_or_none",
            metavar="<n>",
            dest="lns_cutoff",
        )

        lns_solver_group.add_argument(
            "--lns-solve-limit",
            help=replace_default("Set LNS solve limit [%(default)s]", LNSOptions.lns_solve_limit),
            default=UNSET,
            type="solve_limit",
            metavar="<n>[,<m>]",
            dest="lns_solve_limit",
        )

        lns_solver_group.add_argument(
            "--lns-configuration",
            help=replace_default("Set LNS configuration [%(default)s]", LNSOptions.lns_configuration),
            default=UNSET,
            type="configuration",
            metavar="<arg>",
            dest="lns_configuration",
        )

        lns_solver_group.add_argument(
            "--lns-opt-strategy",
            help=replace_default("Set LNS optimization strategy [%(default)s]", LNSOptions.lns_opt_strategy),
            default=UNSET,
            type="opt_strategy",
            metavar="<arg>",
            dest="lns_opt_strategy",
        )
        lns_solver_group.add_argument(
            "--lns-opt-heuristic",
            help=replace_default("Set LNS optimization heuristic [%(default)s]", LNSOptions.lns_opt_heuristic),
            default=UNSET,
            type=str,
            choices=["sign", "model"],
            dest="lns_opt_heuristic",
        )
        lns_solver_group.add_argument(
            "--lns-heuristic",
            help=replace_default("Set LNS decision heuristic [%(default)s]", LNSOptions.lns_heuristic),
            default=UNSET,
            type="heuristic",
            dest="lns_heuristic",
        )
        lns_solver_group.add_argument(
            "--lns-restart-on-model",
            help=replace_default("Set LNS restart on model [%(default)s]", LNSOptions.lns_restart_on_model),
            action=BooleanOptionalAction,
            default=UNSET,
            dest="lns_restart_on_model",
        )
        # !todo "lt" vs "leq"
        lns_solver_group.add_argument(
            "--lns-opt-mode",
            help=(
                "Configure optimization algorithm in iterations\n"
                "<arg>: <mode>[,<bound>]\n"
                "  <mode> : {opt|enum|optN|ignore}\n"
                "    opt   : Find optimal model\n"
                "    enum  : Find models with costs <= initial bound set based on <bound>\n"
                "    optN  : Find optimum, then enumerate optimal models\n"
                "    ignore: Ignore optimize statements\n"
                "  <bound>: {<n>...,static|<f>[,dynamic]}\n"
                "    <n>...,static: In every iteration, set initial bound for objective function(s) to <n>...\n"
                "    <f>[,dynamic]: In every iteration, set initial bound for objective function(s) to\n"
                "                   ((100 + <f>)%% of the current solution cost) - 1"
            ),
            default=UNSET,
            type="lns_opt_mode",
            dest="lns_opt_mode",
            metavar="<arg>",
        )

        lns_solver_group.add_argument(
            "--lns-time-limit-increase-rate",
            help=replace_default(
                "Set time limit increase rate in percent [%(default)s]", LNSOptions.lns_time_limit_increase_rate
            ),
            default=UNSET,
            type="percent",
            dest="lns_time_limit_increase_rate",
            metavar="<n>",
        )

        lns_solver_group.add_argument(
            "--lns-cutoff-threshold",
            help=(
                f"Increase cut-off-time if the number of consecutive iterations without improvement reaches <n> [{LNSOptions.lns_cutoff_threshold}]"
            ),
            default=UNSET,
            type="pos_int_or_none",
            metavar="<n>",
            dest="lns_cutoff_threshold",
        )
        lns_solver_group.add_argument(
            "--lns-cutoff-increase-rate",
            help=(
                f"Increase cut-off-time by <n>%% if the number of consecutive iterations without improvement reaches cut-off-no-improv-threshold [{LNSOptions.lns_cutoff_increase_rate}]"
            ),
            default=UNSET,
            type="percent",
            metavar="<n>",
            dest="lns_cutoff_increase_rate",
        )

        lns_solver_group.add_argument(
            "--lns-solve-limit-increase-rate",
            help=replace_default(
                "Set solve limit increase rate in percent [%(default)s]", LNSOptions.lns_solve_limit_increase_rate
            ),
            default=UNSET,
            type="percent",
            dest="lns_solve_limit_increase_rate",
            metavar="<n>",
        )

        ##########
        # parameters

        parser.add_argument("files", help="ASP input file(s)", nargs="+")

        return parser

"""
Parser for LNS options.
"""

import importlib
import importlib.util
import inspect
import logging
import os
import pkgutil
import sys
import uuid
from argparse import ArgumentParser, ArgumentTypeError, BooleanOptionalAction, RawTextHelpFormatter
from textwrap import dedent
from typing import Any, Optional, no_type_check

from clingo import Control, parse_term
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

# pylint: disable=line-too-long, too-many-lines


def _parse_solver(solvers: dict[str, Solver], string: str) -> Solver:
    """
    Parse the solver string.

    :param solvers: Dictionary of available solvers.
    :param string: String to parse.
    :return: Solver instance.
    """
    solver = solvers.get(string)
    if solver is None:
        raise ArgumentTypeError(f"'{string}': Invalid solver. Choose from {','.join(solvers.keys())}")
    return solver


def _parse_pos_int(string: str) -> int:
    """
    Parse a positive integer.

    :param string: String to parse.
    :return: Parsed positive integer.
    """
    try:
        value = int(string)
    except ValueError as e:
        raise ArgumentTypeError(f"'{string}': Invalid positive integer.") from e
    if value < 0:
        raise ArgumentTypeError(f"'{string}': Value must be non-negative.")
    return value


def _parse_pos_int_or_none(string: str) -> Optional[int]:
    """
    Parse a positive integer or None.

    :param string: String to parse.
    :return: Parsed positive integer or None.
    """
    if string.lower() == "none":
        return None
    return _parse_pos_int(string)


def _parse_solve_limit(string: str) -> Optional[str]:
    """
    Parse the solve limit string.

    :param string: String to parse.
    :return: Parsed solve limit or None.
    """
    ctl = Control()
    if string.lower() == "none":
        return None
    try:
        ctl.configuration.solve.solve_limit = string  # type: ignore
    except RuntimeError as e:
        raise ArgumentTypeError(f"'{string}': Invalid solve limit.") from e
    return string


def _parse_0_1_float(string: str) -> float:
    """
    Parse a float between 0 and 1 (inclusive).

    :param string: String to parse.
    :return: Parsed float value.
    """
    try:
        value = float(string)
    except ValueError as e:
        raise ArgumentTypeError(f"'{string}': Invalid float value.") from e
    if not 0 <= value <= 1:
        raise ArgumentTypeError(f"'{string}': Value must be between 0 and 1 (inclusive).")
    return value


def _parse_percent(
    string: str, msg: str = "Invalid percentage, percentage must be between 0 and 100 (inclusive)."
) -> int:
    """
    Parse percentage between 0 and 100 (inclusive).

    :param string: String to parse.
    :param msg: Error message to display if parsing fails.
    :return: Parsed percentage value.
    """
    try:
        value = int(string)
    except ValueError as e:
        raise ArgumentTypeError(f"'{string}': {msg}") from e
    if not 0 <= value <= 100:
        raise ArgumentTypeError(f"'{string}': {msg}")
    return value


def _parse_destruction(string: str) -> tuple[str, int]:
    """
    Parse the destruction string.

    :param string: String to parse.
    :return: Parsed destruction type and rate.
    """
    if string == "declarative":
        return "declarative", 0
    if string.startswith("simple,"):
        rate_str = string.split(",", 1)[1]
        if rate_str.lower() == "auto":
            return "simple", -1
        rate = _parse_percent(
            rate_str, msg="Invalid destruction rate, rate must be between 0 and 100 (inclusive) or 'auto'."
        )
        return "simple", rate
    raise ArgumentTypeError(f"'{string}': Invalid destruction. Choose from {{simple,<rate>|declarative}}")


def _parse_parallel_mode(string: str) -> str:
    """
    Parse the parallel mode string.

    :param string: String to parse.
    :return: Parsed parallel mode string.
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


def _parse_minimize_variable(string: str) -> Symbol:
    """
    Parse the minimize variable string.

    :param string: String to parse.
    :return: Parsed minimize variable.
    """
    try:
        term = parse_term(string)
    except RuntimeError as e:
        raise ArgumentTypeError(f"'{string}': Invalid minimize variable.") from e
    return term


# def _parse_falsify(string: str) -> str:
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


def _can_instantiate_without_args(cls: type) -> bool:
    """
    Check whether class can be instantiated without passing user arguments.

    :param cls: Class to check.
    :return: True if class can be instantiated without arguments, False otherwise.
    """
    try:
        signature = inspect.signature(cls)
    except (TypeError, ValueError):  # nocoverage
        return False

    for parameter in signature.parameters.values():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if parameter.default is inspect.Parameter.empty:
            return False
    return True


def _parse_context(string: str) -> Any:
    """
    Parse context object whose methods are called during grounding using the @-syntax.

    :param string: String to parse.
    :return: Parsed context object.
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


def _parse_adaptive_strategy(adaptive_strategies: list[str], string: str) -> str:
    """
    Parse the adaptive strategy string.

    :param adaptive_strategies: List of valid adaptive strategies.
    :param string: String to parse.
    :return: Adaptive strategy name.
    """
    if string not in adaptive_strategies:
        raise ArgumentTypeError(
            f"'{string}': Invalid adaptive strategy. Choose from {{{','.join(adaptive_strategies)}}}"
        )
    return string


def _parse_auto_converter(converters: dict[str, AutoDestructionConverter], string: str) -> AutoDestructionConverter:
    """
    Parse the auto converter string.

    :param converters: Dictionary of available auto converters.
    :param string: String to parse.
    :return: Auto converter.
    """
    converter = converters.get(string)
    if converter is None:
        raise ArgumentTypeError(f"'{string}': Invalid auto converter. Choose from {','.join(converters.keys())}")
    return converter


def _parse_init_opt_mode(string: str) -> str:
    """
    Parse the initial optimization mode string.

    :param string: String to parse.
    :return: Initial optimization mode.
    """
    ctl = Control()
    try:
        ctl.configuration.solve.opt_mode = string  # type: ignore
    except RuntimeError as e:
        raise ArgumentTypeError(f"'{string}': Invalid opt mode.") from e
    return string


# pylint: disable=too-many-branches
def _parse_lns_opt_mode(string: str) -> dict[str, Any]:
    """
    Parse the lns optimization mode string.

    :param string: String to parse.
    :return: Parsed lns optimization mode.
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


def _parse_opt_strategy(string: str) -> str:
    """
    Parse the optimization strategy string.

    :param string: String to parse.
    :return: Optimization strategy.
    """
    ctl = Control()
    try:
        ctl.configuration.solver.opt_strategy = string  # type: ignore
    except RuntimeError as e:
        raise ArgumentTypeError(f"'{string}': Invalid opt strategy.") from e
    return string


def _parse_opt_heuristic(string: str) -> str:
    """
    Parse the optimization heuristic string.

    :param string: String to parse.
    :return: Optimization heuristic.
    """
    ctl = Control()
    try:
        ctl.configuration.solver.opt_heuristic = string  # type: ignore
    except RuntimeError as e:
        raise ArgumentTypeError(f"'{string}': Invalid opt heuristic.") from e
    return string


def _parse_configuration(string: str) -> str:
    """
    Parse the configuration string.

    :param string: String to parse.
    :return: Configuration.
    """
    ctl = Control()
    try:
        ctl.configuration.configuration = string
    except RuntimeError as e:
        raise ArgumentTypeError(f"'{string}': Invalid configuration.") from e
    return string


def _parse_heuristic(string: str) -> str:
    """
    Parse the heuristic string.

    :param string: String to parse.
    :return: Heuristic.
    """
    ctl = Control()
    try:
        ctl.configuration.solver.heuristic = string  # type: ignore
    except RuntimeError as e:
        raise ArgumentTypeError(f"'{string}': Invalid heuristic.") from e
    return string


def _replace_default(text: str, default_value: Any) -> str:
    """
    Render config defaults in help while argparse default remains UNSET.

    :param text: Text to render.
    :param default_value: Default value to replace.
    :return: Rendered text.
    """
    return text.replace("%(default)s", str(default_value))


def _format_preset_option_value(
    key: str,
    value: Any,
    converter_name_by_type: dict[type, str],
) -> str:
    """
    Format preset option values so they match expected CLI argument values.

    :param key: Preset option key.
    :param value: Preset option value.
    :param converter_name_by_type: Mapping from converter type to converter CLI name.
    :return: String representation suitable for CLI help output.
    """
    if key == "destruction" and isinstance(value, tuple):
        return f"{value[0]},{value[1]}"
    if key == "auto_converter":
        return converter_name_by_type.get(type(value), str(value))
    return str(value)


def _build_preset_help_text(
    preset_values: dict[str, dict[str, Any]],
    converter_name_by_type: dict[type, str],
) -> str:
    """
    Build formatted preset summary text for preset help text.

    :param preset_values: Preset definitions.
    :param converter_name_by_type: Mapping from converter type to converter CLI name.
    :return: Formatted preset summary text.
    """
    key_aliases = {
        "default_adaptive_strategy_name": "default-adaptive-strategy",
    }

    chunks: list[str] = []
    for preset_name, options in preset_values.items():
        lines = [f"[{preset_name}]:"]
        option_texts: list[str] = []
        for key, value in options.items():
            if key == "description":
                continue
            arg_name = key_aliases.get(key, key.replace("_", "-"))
            arg_value = _format_preset_option_value(key, value, converter_name_by_type)
            option_texts.append(f" --{arg_name}={arg_value}")

        for i in range(0, len(option_texts), 2):
            pair = option_texts[i : i + 2]
            lines.append(" ".join(pair))

        chunks.append("\n".join(lines))
    return "\n".join(chunks)


def _build_preset_description_text(preset_values: dict[str, dict[str, Any]]) -> str:
    """
    Build formatted preset description text for argument help text.

    :param preset_values: Preset definitions.
    :return: Formatted preset descriptions text.
    """
    return "\n".join(
        f"{preset_name}: {options.get('description', 'Configuration preset.')}"
        for preset_name, options in preset_values.items()
    )


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
        :param base: Base class to filter by.
        :return: List of classes in package.
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
        :return: Custom formatter.
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
        adaptive_strategies: list[str] = LNSOptions.get_supported_adaptive_strategy_names()
        converters: dict[str, AutoDestructionConverter] = {
            "avg": AverageDestructionConverter(),
            "last-improv": LastImprovementDestructionConverter(),
        }
        converter_name_by_type = {type(instance): name for name, instance in converters.items()}

        preset_choice_names = list(LNSOptions.preset_values.keys())
        preset_description_text = _build_preset_description_text(LNSOptions.preset_values)
        preset_help_lines = _build_preset_help_text(LNSOptions.preset_values, converter_name_by_type)

        parser.register("type", "solver", lambda string: _parse_solver(solvers, string))
        parser.register("type", "pos_int", _parse_pos_int)
        parser.register("type", "pos_int_or_none", _parse_pos_int_or_none)
        parser.register("type", "solve_limit", _parse_solve_limit)
        parser.register("type", "0_1_float", _parse_0_1_float)
        parser.register("type", "percent", _parse_percent)
        parser.register("type", "destruction", _parse_destruction)
        parser.register("type", "parallel_mode", _parse_parallel_mode)
        parser.register("type", "minimize_variable", _parse_minimize_variable)
        # parser.register("type", "falsify", parse_falsify)
        parser.register("type", "context", _parse_context)
        parser.register(
            "type", "adaptive_strategy", lambda string: _parse_adaptive_strategy(adaptive_strategies, string)
        )
        parser.register("type", "auto_converter", lambda string: _parse_auto_converter(converters, string))
        parser.register("type", "init_opt_mode", _parse_init_opt_mode)
        parser.register("type", "lns_opt_mode", _parse_lns_opt_mode)
        parser.register("type", "opt_strategy", _parse_opt_strategy)
        parser.register("type", "opt_heuristic", _parse_opt_heuristic)
        parser.register("type", "configuration", _parse_configuration)
        parser.register("type", "heuristic", _parse_heuristic)

        ##########
        # general options
        parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {VERSION}")

        parser.add_argument(
            "--log-level",
            default=UNSET,
            choices=logging_levels.values(),
            metavar=f"{{{','.join(logging_levels.keys())}}}",
            help=_replace_default("Set log level [%(default)s]", "warning"),
            type="logging_level",
            dest="log_level",
        )

        parser.add_argument(
            "--solver",
            default=UNSET,
            choices=solvers.values(),
            metavar=f"{{{','.join(solvers.keys())}}}",
            help=_replace_default("Set LNS solver [%(default)s]", "clingo"),
            type="solver",
        )

        parser.add_argument(
            "--preset",
            help=(
                f"Set LNS configuration preset [{LNSOptions.preset}]\n"
                "Manually set parameters take precedence over presets.\n"
                "Presets can be used as a base configuration and then manually adjusted as needed.\n"
                f"<arg>: {{{'|'.join(preset_choice_names)}}}\n"
                f"{preset_description_text}\n"
                "Presets:\n"
                f"{preset_help_lines}\n"
            ),
            choices=preset_choice_names,
            default=UNSET,
            type=str,
            dest="preset",
            metavar="<arg>",
        )

        parser.add_argument(
            "--seed",
            default=UNSET,
            metavar="<n>",
            help=_replace_default("Set LNS seed [%(default)s]", LNSOptions.seed),
            type=int,
        )

        parser.add_argument(
            "--time-limit",
            help=_replace_default("Set time limit in seconds [%(default)s]", LNSOptions.time_limit),
            default=UNSET,
            type="pos_int_or_none",
            dest="time_limit",
            metavar="<n>",
        )

        parser.add_argument(
            "--max-steps",
            help=_replace_default("Set maximum number of LNS steps [%(default)s]", LNSOptions.max_steps),
            default=UNSET,
            type="pos_int_or_none",
            dest="max_steps",
            metavar="<n>",
        )

        parser.add_argument(
            "--parallel-mode",
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
            help=_replace_default(
                "Path to context file defining context class for @-syntax [%(default)s]", LNSOptions.context
            ),
            default=UNSET,
            type="context",
            dest="context",
            metavar="<arg>",
        )

        parser.add_argument(
            "--minimize-variable",
            help=_replace_default(
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
        #     help=_replace_default("Falsify not projected atoms with the priority [%(default)s]", LNSOptions.falsify),
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
            help=_replace_default("Set initial solver time limit [%(default)s]", LNSOptions.init_time_limit),
            default=UNSET,
            type="pos_int_or_none",
            dest="init_time_limit",
            metavar="<n>",
        )

        init_solver_group.add_argument(
            "--init-cutoff",
            help=_replace_default("Set initial solver cutoff [%(default)s]", LNSOptions.init_cutoff),
            default=UNSET,
            type="pos_int_or_none",
            dest="init_cutoff",
            metavar="<arg>",
        )

        init_solver_group.add_argument(
            "--init-solve-limit",
            help=_replace_default("Set initial solver solve limit [%(default)s]", LNSOptions.init_solve_limit),
            default=UNSET,
            type="solve_limit",
            dest="init_solve_limit",
            metavar="<n>[,<m>]",
        )

        # fmt: on
        init_solver_group.add_argument(
            "--init-configuration",
            help=_replace_default("Set initial solver configuration [%(default)s]", LNSOptions.init_configuration),
            default=UNSET,
            type="configuration",
            dest="init_configuration",
            metavar="<arg>",
        )
        init_solver_group.add_argument(
            "--init-opt-strategy",
            help=_replace_default(
                "Set initial solver optimization strategy [%(default)s]", LNSOptions.init_opt_strategy
            ),
            default=UNSET,
            type="opt_strategy",
            dest="init_opt_strategy",
            metavar="<arg>",
        )
        init_solver_group.add_argument(
            "--init-opt-heuristic",
            help=_replace_default(
                "Set initial solver optimization heuristic [%(default)s]", LNSOptions.init_opt_heuristic
            ),
            default=UNSET,
            type=str,
            dest="init_opt_heuristic",
            choices=["sign", "model"],
        )
        init_solver_group.add_argument(
            "--init-restart-on-model",
            help=_replace_default(
                "Set initial solver restart on model [%(default)s]", LNSOptions.init_restart_on_model
            ),
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
            help=_replace_default(
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
            help=_replace_default(
                "Set learning rate for updating config weights to <f> (0 <= <f> <= 1) [%(default)s]",
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
            help=_replace_default(
                "Short-hand for --lns-opt-mode=opt,0,dynamic, set LNS to use constrained optimization [%(default)s]",
                LNSOptions.constrained,
            ),
            action="store_true",
            default=UNSET,
            dest="constrained",
        )

        lns_group.add_argument(
            "--destruction",
            help=_replace_default(
                (
                    "Set destruction mode and rate for simple destruction in percent [%(default)s]\n"
                    "<rate>:      Destruction rate between 0 and 100 or 'auto' for automatic rate.\n"
                    "             See --auto-converter options for details on how the automatic rate is calculated.\n"
                    "declarative: Use declarative destruction, LNS configuration encoding has to be provided as input file."
                ),
                f"{LNSOptions.destruction[0]},{LNSOptions.destruction[1] if LNSOptions.destruction[1] > 0 else 'auto'}",
            ),
            default=UNSET,
            type="destruction",
            dest="destruction",
            metavar="{simple,<rate>|declarative}",
        )

        lns_group.add_argument(
            "--fix",
            help=_replace_default(
                "Set method to fix non-destroyed atoms during repair [%(default)s]",
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
                "Set automatic destruction percentage converter [last-improv]\n"
                "last-improv: Set auto destruction rate based on actually destroyed atoms during last improvement.\n"
                "avg:         Set auto destruction rate based on average percentages of destroyed atoms during all improvements.\n"
                "Note: Used for --destruction=simple,auto and _destruction_op/2 for --destruction=declarative.\n"
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
            help=_replace_default(
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
            help=_replace_default("Set LNS time limit [%(default)s]", LNSOptions.lns_time_limit),
            default=UNSET,
            type="pos_int_or_none",
            metavar="<n>",
            dest="lns_time_limit",
        )

        lns_solver_group.add_argument(
            "--lns-cutoff",
            help=_replace_default("Set LNS cutoff [%(default)s]", LNSOptions.lns_cutoff),
            default=UNSET,
            type="pos_int_or_none",
            metavar="<n>",
            dest="lns_cutoff",
        )

        lns_solver_group.add_argument(
            "--lns-solve-limit",
            help=_replace_default("Set LNS solve limit [%(default)s]", LNSOptions.lns_solve_limit),
            default=UNSET,
            type="solve_limit",
            metavar="<n>[,<m>]",
            dest="lns_solve_limit",
        )

        lns_solver_group.add_argument(
            "--lns-configuration",
            help=_replace_default("Set LNS configuration [%(default)s]", LNSOptions.lns_configuration),
            default=UNSET,
            type="configuration",
            metavar="<arg>",
            dest="lns_configuration",
        )

        lns_solver_group.add_argument(
            "--lns-opt-strategy",
            help=_replace_default("Set LNS optimization strategy [%(default)s]", LNSOptions.lns_opt_strategy),
            default=UNSET,
            type="opt_strategy",
            metavar="<arg>",
            dest="lns_opt_strategy",
        )
        lns_solver_group.add_argument(
            "--lns-opt-heuristic",
            help=_replace_default("Set LNS optimization heuristic [%(default)s]", LNSOptions.lns_opt_heuristic),
            default=UNSET,
            type="opt_heuristic",
            dest="lns_opt_heuristic",
        )
        lns_solver_group.add_argument(
            "--lns-heuristic",
            help=_replace_default("Set LNS decision heuristic [%(default)s]", LNSOptions.lns_heuristic),
            default=UNSET,
            type="heuristic",
            dest="lns_heuristic",
        )
        lns_solver_group.add_argument(
            "--lns-restart-on-model",
            help=_replace_default("Set LNS restart on model [%(default)s]", LNSOptions.lns_restart_on_model),
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
            help=_replace_default(
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
            help=_replace_default(
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

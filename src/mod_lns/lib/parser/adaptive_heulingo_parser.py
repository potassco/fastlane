"""
Parser for Heulingo strategy in LNS.
"""

import importlib.util
import inspect
import os
import uuid
from argparse import (
    ArgumentParser,
    BooleanOptionalAction,
    RawTextHelpFormatter,
    _SubParsersAction,
)
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Optional

from clingo import Configuration, Control, Symbol, parse_term

from mod_lns import UNSET
from mod_lns.interfaces.solver import SolverInterface
from mod_lns.lib.converter import (
    AutoDestructionConverter,
    AverageDestructionConverter,
    LastImprovementDestructionConverter,
)
from mod_lns.lib.parser.framework_parser import get_classes_from_package

if TYPE_CHECKING:
    from mod_lns.lib.strategies.adaptive_heulingo import AdaptiveHeulingoConfig  # nocoverage

VERSION = "1.0.1"


# pylint: disable=too-many-statements
def get_adap_heulingo_parser(
    config_cls: type["AdaptiveHeulingoConfig"], subparsers: "_SubParsersAction[ArgumentParser]"
) -> ArgumentParser:
    """
    Parse command line options.

    :param subparsers: Subparsers action
    :type subparsers: _SubParsersAction[ArgumentParser]
    """

    config = config_cls()

    def formatter(prog: str) -> RawTextHelpFormatter:
        """
        Formatter for help messages.
        """
        return RawTextHelpFormatter(
            prog,
            max_help_position=10,
            width=100,
        )

    parser = subparsers.add_parser(
        "adaptive_heulingo",
        help="Adaptive Heulingo strategy for LNS",
        description=dedent("""\
            adaptive_heulingo
            An implementation of Large Neighbourhood Search (LNS) and
            Large Neighbourhood Prioritized Search (LNPS) based on
            Answer Set Programming (ASP).

            Check the documentation for a guide on how to use this
            strategy.
            """),
        formatter_class=formatter,
    )

    def parse_parallel_mode(string: str) -> str:
        """
        Parse the parallel mode string.
        """
        values = string.split(",")
        if len(values) == 1:
            try:
                x = int(values[0])
            except ValueError:
                parser.error(f"'{string}': Invalid number of threads. Integer expected.")
            try:
                assert 1 <= x <= 64
            except AssertionError:
                parser.error(f"'{string}': Invalid number of threads. 1 <= x <= 64 expected.")
        elif len(values) == 2:
            if values[1] not in ("compete", "split"):
                parser.error(f"'{string}': Invalid mode. {{compete|split}} expected.")
        else:
            parser.error(f"'{string}': Invalid argument.")
        return string

    parser.register("type", "parallel_mode", parse_parallel_mode)

    def parse_init_opt_mode(string: str) -> str:
        """
        Parse the optimization mode string.
        """
        ctl = Control()
        try:
            ctl.configuration.solve.opt_mode = string  # type: ignore
        except RuntimeError:
            parser.error(f"'{string}': Invalid opt mode.")
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
            parser.error(f"'{string}': Invalid optimization mode. {{opt|enum|optN|ignore}} expected.")
        opt_mode["mode"] = values[0]
        if len(values) == 1:
            opt_mode["nf"] = None
            opt_mode["modifier"] = None
        elif len(values) == 2:
            try:
                float(values[1])
            except ValueError:
                parser.error(f"'{string}': Invalid bound. float expected.")
            opt_mode["nf"] = values[1]
            opt_mode["modifier"] = "dynamic"
        elif len(values) >= 3:
            if values[-1] == "static":
                try:
                    for v in values[1:-1]:
                        int(v)
                except ValueError:
                    parser.error(f"'{string}': Invalid bounds. integers expected.")
                opt_mode["nf"] = ",".join(values[1:-1])
                opt_mode["modifier"] = "static"
            elif values[-1] == "dynamic":
                if len(values) >= 4:
                    parser.error(f"'{string}': Invalid number of bounds. Only one boundary expected.")
                try:
                    float(values[1])
                except ValueError:
                    parser.error(f"'{string}': Invalid bound. float expected.")
                opt_mode["nf"] = values[1]
                opt_mode["modifier"] = "dynamic"
            else:
                parser.error(f"'{string}': Invalid boundary mode. {{static|dynamic}} expected.")
        return opt_mode

    parser.register("type", "lns_opt_mode", parse_lns_opt_mode)

    def parse_opt_strategy(string: str) -> str:
        """
        Parse the optimization strategy string.
        """
        ctl = Control()
        try:
            ctl.configuration.solver.opt_strategy = string  # type: ignore
        except RuntimeError:
            parser.error(f"'{string}': Invalid opt strategy.")
        return string

    parser.register("type", "opt_strategy", parse_opt_strategy)

    def parse_configuration(string: str) -> str:
        """
        Parse the configuration string.
        """
        ctl = Control()
        try:
            ctl.configuration.configuration = string
        except RuntimeError:
            parser.error(f"'{string}': Invalid configuration.")
        return string

    parser.register("type", "configuration", parse_configuration)

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

    def parse_minimize_variable(string: str) -> Symbol:
        """
        Parse the minimize variable string.
        """
        try:
            term = parse_term(string)
        except RuntimeError:
            parser.error(f"'{string}': Invalid minimize variable.")
        return term

    parser.register("type", "minimize_variable", parse_minimize_variable)

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

    def parse_learning_rate(string: str) -> float:
        """
        Parse the learning rate string.
        """
        try:
            value = float(string)
        except ValueError:
            parser.error(f"'{string}': Invalid learning rate. Float expected.")
        if not (0 < value < 1):
            parser.error(f"'{string}': Invalid learning rate. 0 < value < 1 expected.")
        return value

    parser.register("type", "learning_rate", parse_learning_rate)

    # list of supported solvers
    solvers = [(cls.get_name(), cls()) for cls in get_classes_from_package("mod_lns.lib.solvers", SolverInterface)]

    def get_solver(solvers: list[tuple[str, SolverInterface]], name: str) -> SolverInterface | None:
        for key, val in solvers:
            if key == name:
                return val
        return None  # nocoverage

    def parse_solver(string: str) -> SolverInterface:
        """
        Parse the solver string.
        """
        solver = get_solver(solvers, string)
        if solver is None:
            parser.error(f"'{string}': Invalid solver. Choose from {{{','.join(key for key, _ in solvers)}}}")
        return solver

    parser.register("type", "solver", parse_solver)

    converters: list[tuple[str, AutoDestructionConverter]] = [
        ("avg", AverageDestructionConverter()),
        ("last-improv", LastImprovementDestructionConverter()),
    ]

    def get_converter(
        converter_values: list[tuple[str, AutoDestructionConverter]], name: str
    ) -> AutoDestructionConverter | None:
        for key, val in converter_values:
            if key == name:
                return val
        return None

    def parse_auto_converter(string: str) -> AutoDestructionConverter:
        """
        Parse the auto converter string.
        """
        converter = get_converter(converters, string)
        if converter is None:
            parser.error(
                f"'{string}': Invalid auto converter. Choose from {{{','.join(key for key, _ in converters)}}}"
            )
        return converter

    parser.register("type", "auto_converter", parse_auto_converter)

    adaptive_strategies: list[str] = config_cls.get_supported_adaptive_strategy_names()

    def parse_adaptive_strategy(string: str) -> str:
        """
        Parse the adaptive strategy string.
        """
        if string not in adaptive_strategies:
            parser.error(f"'{string}': Invalid adaptive strategy. Choose from {{{','.join(adaptive_strategies)}}}")
        return string

    parser.register("type", "adaptive_strategy", parse_adaptive_strategy)

    def parse_context(string: str) -> Any:
        path = os.path.abspath(os.path.expanduser(string))
        if not os.path.isfile(path):
            raise ValueError(f"'{string}': File does not exist.")

        spec = importlib.util.spec_from_file_location(f"context_{uuid.uuid4().hex}", path)
        if spec is None:
            raise ValueError(f"'{string}': Failed to load context module.")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        classes = [
            cls
            for _, cls in inspect.getmembers(module, inspect.isclass)
            if cls.__module__ == module.__name__
            and (cls.__init__ is object.__init__ or len(inspect.signature(cls.__init__).parameters) == 1)
        ]

        if classes:
            return classes[0]()
        return None

    parser.register("type", "context", parse_context)

    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {VERSION}")

    parser.add_argument(
        "--solver",
        default="clingo",
        choices=[val for _, val in solvers],
        metavar=f"{{{','.join(key for key, _ in solvers)}}}",
        help="set LNS solver [%(default)s]",
        type=parse_solver,
    )

    parser.add_argument(
        "--seed",
        help="set lns seed [%(default)s]",
        default=config.seed,
        type="pos_int_or_none",
    )

    parser.add_argument(
        "--time-limit",
        help="set time limit in seconds [%(default)s]",
        default=config.time_limit,
        type="pos_int_or_none",
        dest="time_limit",
        metavar="<n>",
    )

    parser.add_argument(
        "--max-steps",
        help="set maximum number of LNS steps [%(default)s]",
        default=config.max_steps,
        type="pos_int_or_none",
        dest="max_steps",
        metavar="<n>",
    )

    parser.add_argument(
        "--clingo-args",
        help=(
            "set additional clingo arguments [%(default)s]\n"
            "only gringo options (without --text) and clasp's search options are supported\n"
        ),
        default=config.clingo_args,
        type=str,
        dest="clingo_args",
        metavar="<arg[,arg,...]>",
    )

    parser.add_argument(
        "--parallel_mode",
        "-t",
        help=(
            "run parallel search with given number of threads\n"
            "<arg>: <n {1..64}>[,<mode {compete|split}>]\n"
            "  <n>: Number of threads to use in search\n"
            "  <mode>: Run competition or splitting based search [compete]\n"
        ),
        default=config.parallel_mode,
        type="parallel_mode",
        metavar="<arg>",
        dest="parallel_mode",
    )

    parser.add_argument(
        "--minimize-variable",
        help="Minimize the integer variable <arg> (only useful with clingo-dl)",
        default=config.minimize_variable,
        type="minimize_variable",
        dest="minimize_variable",
        metavar="<arg>",
    )

    parser.add_argument(
        "--default-adaptive-strategy",
        help=(
            "Set default adaptive strategy for selecting LNS configurations in each iteration.\n"
            "Will be overwritten by strategy defined in config encoding. [%(default)s]\n"
        ),
        default=config.default_adaptive_strategy_name,
        choices=adaptive_strategies,
        type="adaptive_strategy",
        dest="default_adaptive_strategy_name",
        metavar=f"{{{','.join(adaptive_strategies)}}}",
    )

    parser.add_argument(
        "--learning-rate",
        help="Set learning rate for updating config weights to <f> (0 < <f> < 1) [%(default)s]",
        default=config.learning_rate,
        type="learning_rate",
        dest="learning_rate",
        metavar="<f>",
    )

    parser.add_argument(
        "--auto-converter",
        help="Set automatic destroy percentage converter [%(default)s]",
        default="last-improv",
        choices=[val for _, val in converters],
        type="auto_converter",
        dest="auto_converter",
        metavar=f"{{{','.join(key for key, _ in converters)}}}",
    )

    parser.add_argument(
        "--context",
        help="Path to context file defining context class for @-syntax [%(default)s]",
        default=config.context,
        type="context",
        dest="context",
        metavar="<arg>",
    )

    #######################
    # Solver options for first solution, collected by hidden parser
    # fmt: off
    solver_group = parser.add_argument_group(
        "Initial Solver Configuration",
        "Configuration options for the initial solver\n"
        "used to find the first solution.",
    )
    # fmt: on
    solver_group.add_argument(
        "--init-configuration",
        help="set initial solver configuration [%(default)s]",
        default=config.init_configuration,
        type="configuration",
        dest="init_configuration",
        metavar="<arg>",
    )
    solver_group.add_argument(
        "--init-opt-strategy",
        help="set initial solver optimization strategy [%(default)s]",
        default=config.init_opt_strategy,
        type="opt_strategy",
        dest="init_opt_strategy",
        metavar="<arg>",
    )
    solver_group.add_argument(
        "--init-opt-heuristic",
        help="set initial solver optimization heuristic [%(default)s]",
        default=config.init_opt_heuristic,
        type=str,
        dest="init_opt_heuristic",
        choices=["sign", "model"],
    )
    solver_group.add_argument(
        "--init-restart-on-model",
        help="set initial solver restart on model",
        action=BooleanOptionalAction,
        dest="init_restart_on_model",
    )
    solver_group.add_argument(
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
        default=config.init_opt_mode,
        type="init_opt_mode",
        dest="init_opt_mode",
        metavar="<arg>",
    )
    solver_group.add_argument(
        "--init-solve-limit",
        help="set initial solver solve limit [%(default)s]",
        default=config.init_solve_limit,
        type="solve_limit",
        dest="init_solve_limit",
        metavar="<n>[,<m>]",
    )
    solver_group.add_argument(
        "--init-time-limit",
        help="set initial solver time limit [%(default)s]",
        default=config.init_time_limit,
        type="pos_int_or_none",
        dest="init_time_limit",
        metavar="<arg>",
    )
    solver_group.add_argument(
        "--init-cutoff",
        help="set initial solver cutoff [%(default)s]",
        default=config.init_cutoff,
        type="pos_int_or_none",
        dest="init_cutoff",
        metavar="<arg>",
    )
    # model limit

    ###################
    # lns options
    lns_group = parser.add_argument_group("LNS Configuration", "Configuration options for the LNS")

    lns_group.add_argument(
        "--solve-limit-increase-rate",
        help="set solve limit increase rate in percent [%(default)s]",
        default=config.lns_solve_limit_increase_rate,
        type=float,
        dest="solve_limit_increase_rate",
        metavar="<f>",
    )

    lns_group.add_argument(
        "--time-limit-increase-rate",
        help="set time limit increase rate in percent [%(default)s]",
        default=config.lns_time_limit_increase_rate,
        type=float,
        dest="time_limit_increase_rate",
        metavar="<f>",
    )

    lns_group.add_argument(
        "--acceptance-rate",
        help=(
            "Do not accept solution whose objective value is at least <f>%% worse\n"
            "than current incumbent solution in each iteration [%(default)s]"
        ),
        default=config.acceptance_rate,
        type=float,
        dest="acceptance_rate",
        metavar="<f>",
    )

    lns_group.add_argument(
        "--preset",
        help=(
            f"Set heulingo configuration preset\n"
            f"<arg>: {{basic}}\n"
            f"  basic: Standard defaults\n"
            f"Presets:\n"
            f"[basic]:\n"
            f" --default-adaptive-strategy={config_cls.preset_values['basic']['default_adaptive_strategy_name']}"
            f" --learning-rate={config_cls.preset_values['basic']['learning_rate']}"
            f" --auto-converter=last-improv\n"
            f" --lex-weight={config_cls.preset_values['basic']['lex_weight']}"
            f" --init-opt-strategy={config_cls.preset_values['basic']['init_opt_strategy']}"
            f" --init-solve-limit={config_cls.preset_values['basic']['init_solve_limit']}\n"
            f" --init-cutoff={config_cls.preset_values['basic']['init_cutoff']}"
            f" --lns-configuration={config_cls.preset_values['basic']['lns_configuration']}"
            f" --lns-opt-strategy={config_cls.preset_values['basic']['lns_opt_strategy']}\n"
            f" --lns-opt-heuristic={config_cls.preset_values['basic']['lns_opt_heuristic']}"
            f" --lns-restart-on-model"
            f" --lns-solve-limit={config_cls.preset_values['basic']['lns_solve_limit']}\n"
            f" --solve-limit-increase-rate={config_cls.preset_values['basic']['solve_limit_increase_rate']}"
            f" --lns-time-limit={config_cls.preset_values['basic']['lns_time_limit']}\n"
            f" --lns-time-limit-increase-rate={config_cls.preset_values['basic']['time_limit_increase_rate']}"
            f" --lns-cutoff={config_cls.preset_values['basic']['lns_cutoff']}\n"
            f" --cutoff-no-improv-threshold={config_cls.preset_values['basic']['cutoff_no_improv_threshold']}"
            f" --cutoff-time-increase-rate={config_cls.preset_values['basic']['cutoff_time_increase_rate']}\n"
        ),
        choices=[
            "basic",
        ],
        default=config.preset,
        type=str,
        dest="preset",
        metavar="<arg>",
    )

    ##############################
    # lns solver options
    lns_solver_group = parser.add_argument_group("LNS Solver Configuration", "Configuration options for the LNS solver")

    lns_solver_group.add_argument(
        "--lns-configuration",
        help="set LNS configuration [%(default)s]",
        default=config.lns_configuration,
        type="configuration",
        metavar="<arg>",
        dest="lns_configuration",
    )

    lns_solver_group.add_argument(
        "--lns-opt-strategy",
        help="set LNS optimization strategy [%(default)s]",
        default=config.lns_opt_strategy,
        type="opt_strategy",
        metavar="<arg>",
        dest="lns_opt_strategy",
    )
    lns_solver_group.add_argument(
        "--lns-opt-heuristic",
        help="set LNS optimization heuristic [%(default)s]",
        default=config.lns_opt_heuristic,
        type=str,
        choices=["sign", "model"],
        dest="lns_opt_heuristic",
    )
    lns_solver_group.add_argument(
        "--lns-restart-on-model",
        help="set LNS restart on model",
        action=BooleanOptionalAction,
        dest="lns_restart_on_model",
    )
    # TODO "lt" vs "leq"
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
            "    <n>...,static: In every iteration, set <n>... as initial bound for objective function(s)\n"
            "    <f>[,dynamic]: Set initial bound for objective function(s) in each iteration such that\n"
            "                   solutions whose objective value is at least <f>%% worse than\n"
            "                   current incumbent solution are not obtained"
        ),
        default=UNSET,
        type="lns_opt_mode",
        dest="lns_opt_mode",
        metavar="<arg>",
    )
    lns_solver_group.add_argument(
        "--lns-solve-limit",
        help="set LNS solve limit [%(default)s]",
        default=config.lns_solve_limit,
        type="solve_limit",
        metavar="<n>[,<m>]",
        dest="lns_solve_limit",
    )
    lns_solver_group.add_argument(
        "--lns-time-limit",
        help="set LNS time limit [%(default)s]",
        default=config.lns_time_limit,
        type="pos_int_or_none",
        metavar="<n>",
        dest="lns_time_limit",
    )
    lns_solver_group.add_argument(
        "--lns-cutoff",
        help="set LNS cutoff [%(default)s]",
        default=config.lns_cutoff,
        type="pos_int_or_none",
        metavar="<n>",
        dest="lns_cutoff",
    )
    lns_solver_group.add_argument(
        "--cutoff-no-improv-threshold",
        help=(
            "Increase cut-off-time if the number of consecutive iterations without improvement reaches <n> [%(default)s]"
        ),
        default=config.cutoff_no_improv_threshold,
        type="pos_int_or_none",
        metavar="<n>",
        dest="cutoff_no_improv_threshold",
    )
    lns_solver_group.add_argument(
        "--cutoff-time-increase-rate",
        help=(
            "Increase cut-off-time by <n>%% if the number of consecutive iterations without improvement reaches cut-off-no-improv-threshold [%(default)s]"
        ),
        default=config.cutoff_time_increase_rate,
        type="pos_int_or_none",
        metavar="<n>",
        dest="cutoff_time_increase_rate",
    )
    return parser

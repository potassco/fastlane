"""
Parser for Heulingo strategy in LNS.
"""

from argparse import (
    ArgumentParser,
    BooleanOptionalAction,
    RawTextHelpFormatter,
    _SubParsersAction,
)
from textwrap import dedent
from typing import TYPE_CHECKING, Any

from clingo import Configuration, Control, Symbol, parse_term

from mod_lns.interfaces.solver import SolverInterface
from mod_lns.lib.parser.framework_parser import get_classes_from_package

if TYPE_CHECKING:
    from mod_lns.lib.strategies.heulingo import HeulingoConfig  # nocoverage

VERSION = "1.0.0"


# pylint: disable=too-many-statements
def get_parser(
    config_cls: type["HeulingoConfig"], subparsers: "_SubParsersAction[ArgumentParser]"
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
        "heulingo",
        help="Heulingo strategy for LNS",
        description=dedent(
            """\
            heulingo
            An implementation of Large Neighbourhood Search (LNS) and
            Large Neighbourhood Prioritized Search (LNPS) based on
            Answer Set Programming (ASP).

            Check the documentation for a guide on how to use this
            strategy.
            """
        ),
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
                parser.error(
                    f"'{string}': Invalid number of threads. Integer expected."
                )
            try:
                assert 1 <= x <= 64
            except AssertionError:
                parser.error(
                    f"'{string}': Invalid number of threads. 1 <= x <= 64 expected."
                )
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
    def parse_lns_opt_mode(string: str) -> dict:
        """
        Parse the lns optimization mode string.
        """
        opt_mode: dict[str, Any] = {}
        values = string.split(",")
        if values[0] not in ("opt", "enum", "optN", "ignore"):
            parser.error(
                f"'{string}': Invalid optimization mode. {{opt|enum|optN|ignore}} expected."
            )
        opt_mode["mode"] = values[0]
        if len(values) == 1:
            opt_mode["nf"] = None
            opt_mode["modifier"] = None
        elif len(values) == 2:
            try:
                float(values[1])
            except ValueError:
                parser.error(f"'{string}': Invalid bound. float expected.")
            opt_mode["nf"] = float(values[1])
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
                    parser.error(
                        f"'{string}': Invalid number of bounds. Only one boundary expected."
                    )
                try:
                    float(values[1])
                except ValueError:
                    parser.error(f"'{string}': Invalid bound. float expected.")
                opt_mode["nf"] = float(values[1])
                opt_mode["modifier"] = "dynamic"
            else:
                parser.error(
                    f"'{string}': Invalid boundary mode. {{static|dynamic}} expected."
                )
        else:
            parser.error(
                f"'{string}': Invalid optimization mode. {{opt|enum|optN|ignore}} expected."
            )
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

    def parse_solve_limit(string: str) -> str:
        """
        Parse the solve limit string.
        """
        ctl = Control()
        assert isinstance(ctl.configuration.solve, Configuration)
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

    def parse_falsify(string: str) -> str:
        """
        Parse the falsify string.
        """
        if string == "inf":
            return string
        try:
            int(string)
        except ValueError:
            parser.error(
                f"'{string}': Invalid falsify variable. {{<n>, inf}} expected."
            )
        return string

    parser.register("type", "falsify", parse_falsify)

    # list of supported solvers
    solvers = [
        (cls.get_name(), cls())
        for cls in get_classes_from_package("mod_lns.lib.solvers", SolverInterface)
    ]

    def get(levels, name):
        for key, val in levels:
            if key == name:
                return val
        return None  # nocoverage

    def parse_solver(string: str) -> SolverInterface:
        """
        Parse the solver string.
        """
        solver = get(solvers, string)
        if solver is None:
            parser.error(
                f"'{string}': Invalid solver. Choose from {{{','.join(key for key, _ in solvers)}}}"
            )
        return solver

    parser.register("type", "solver", parse_solver)

    parser.add_argument(
        "--version", "-v", action="version", version=f"%(prog)s {VERSION}"
    )

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
        type=int,
    )

    parser.add_argument(
        "--time-limit",
        help="set time limit in seconds [%(default)s]",
        default=config.time_limit,
        type=int,
        dest="time_limit",
        metavar="<n>",
    )

    parser.add_argument(
        "--max-steps",
        help="set maximum number of LNS steps [%(default)s]",
        default=config.max_steps,
        type=int,
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
        type=parse_minimize_variable,
        dest="minimize_variable",
        metavar="<arg>",
    )

    parser.add_argument(
        "--falsify",
        help="Falsify not projected atoms with the priority",
        default=config.falsify,
        type=parse_falsify,
        dest="falsify",
        metavar="{<n>|inf}",
    )

    #######################
    # Solver options for first solution, collected by hidden parser
    solver_group = parser.add_argument_group(
        "Initial Solver Configuration",
        "Configuration options for the initial solver\n"
        "used to find the first solution.",
    )
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
        type=parse_solve_limit,
        dest="init_solve_limit",
        metavar="<n>[,<m>]",
    )
    solver_group.add_argument(
        "--init-time-limit",
        help="set initial solver time limit [%(default)s]",
        default=config.init_time_limit,
        type=int,
        dest="init_time_limit",
        metavar="<arg>",
    )
    # model limit

    ###################
    # lns options
    lns_group = parser.add_argument_group(
        "LNS Configuration", "Configuration options for the LNS"
    )

    lns_group.add_argument(
        "--solve-limit-increase-rate",
        help="set solve limit increase rate in percent [%(default)s]",
        default=config.solve_limit_increase_rate,
        type=float,
        dest="solve_limit_increase_rate",
        metavar="<f>",
    )

    lns_group.add_argument(
        "--time-limit-increase-rate",
        help="set time limit increase rate in percent [%(default)s]",
        default=config.time_limit_increase_rate,
        type=float,
        dest="time_limit_increase_rate",
        metavar="<f>",
    )

    lns_group.add_argument(
        "--heulingo-configuration",
        help=(
            f"Set heulingo configuration\n"
            f"<arg>: {{teaspoon|tsp|sgp|spg|wsc[,<scale>]|sd}}\n"
            f"  teaspoon: Use defaults geared towards CB-CTT problems\n"
            f"  tsp     : Use defaults geared towards traveling salesperson problem\n"
            f"  sgp     : Use defaults geared towards social golfer problem\n"
            f"  spg     : Use defaults geared towards sudoku puzzle generation\n"
            f"  wsc     : Use defaults geared towards weighted strategic companies\n"
            f"    <scale>: Use defaults geared towards {{medium|large}} instances [medium]\n"
            f"  sd      : Use defaults geared towards shift design\n"
            f"  pup     : Use defaults geared towards partner units problem\n"
            f"Heulingo configurations:\n"
            f"[teaspoon]:\n"
            f" --init-configuration={config_cls.lns_configuration_values['teaspoon']['init_configuration']}"
            f" --init-opt-strategy={config_cls.lns_configuration_values['teaspoon']['init_opt_strategy']}"
            f" --init-solve-limit={config_cls.lns_configuration_values['teaspoon']['init_solve_limit']}\n"
            f" --lns-configuration={config_cls.lns_configuration_values['teaspoon']['lns_configuration']}"
            f" --lns-opt-strategy={config_cls.lns_configuration_values['teaspoon']['lns_opt_strategy']}"
            f" --lns-opt-heuristic={config_cls.lns_configuration_values['teaspoon']['lns_opt_heuristic']}\n"
            f" --lns-restart-on-model"
            f" --lns-solve-limit={config_cls.lns_configuration_values['teaspoon']['lns_solve_limit']}\n"
            f"[tsp]:\n"
            f" --init-solve-limit={config_cls.lns_configuration_values['tsp']['init_solve_limit']}"
            f" --lns-solve-limit={config_cls.lns_configuration_values['tsp']['lns_solve_limit']}\n"
            f"[sgp]:\n"
            f" --init-solve-limit={config_cls.lns_configuration_values['sgp']['init_solve_limit']}"
            f" --lns-opt-mode={config_cls.lns_configuration_values['sgp']['lns_opt_mode']}"
            f" --lns-solve-limit={config_cls.lns_configuration_values['sgp']['lns_solve_limit']}\n"
            f"[spg]:\n"
            f" -t{config_cls.lns_configuration_values['spg']['parallel_mode']}"
            f" --init-configuration={config_cls.lns_configuration_values['spg']['init_configuration']}"
            f" --init-solve-limit={config_cls.lns_configuration_values['spg']['init_solve_limit']}"
            f" --lns-solve-limit={config_cls.lns_configuration_values['spg']['lns_solve_limit']}\n"
            f"[wsc-medium]:\n"
            f" --init-opt-strategy={config_cls.lns_configuration_values['wsc-medium']['init_opt_strategy']}"
            f" --init-solve-limit={config_cls.lns_configuration_values['wsc-medium']['init_solve_limit']}"
            f" --lns-opt-strategy={config_cls.lns_configuration_values['wsc-medium']['lns_opt_strategy']}\n"
            f" --lns-solve-limit={config_cls.lns_configuration_values['wsc-medium']['lns_solve_limit']}\n"
            f"[wsc-large]:\n"
            f" --init-opt-strategy={config_cls.lns_configuration_values['wsc-large']['init_opt_strategy']}"
            f" --init-solve-limit={config_cls.lns_configuration_values['wsc-large']['init_solve_limit']}"
            f" --lns-opt-strategy={config_cls.lns_configuration_values['wsc-large']['lns_opt_strategy']}\n"
            f" --lns-solve-limit={config_cls.lns_configuration_values['wsc-large']['lns_solve_limit']}\n"
            f"[sd]:\n"
            f" --init-configuration={config_cls.lns_configuration_values['sd']['init_configuration']}"
            f" --init-opt-strategy={config_cls.lns_configuration_values['sd']['init_opt_strategy']}"
            f" --init-solve-limit={config_cls.lns_configuration_values['sd']['init_solve_limit']}\n"
            f" --lns-opt-mode={config_cls.lns_configuration_values['sd']['lns_opt_mode']}"
            f" --lns-solve-limit={config_cls.lns_configuration_values['sd']['lns_solve_limit']}\n"
            f"[pup]:\n"
            f" --init-configuration={config_cls.lns_configuration_values['pup']['init_configuration']}"
            f" --init-opt-strategy={config_cls.lns_configuration_values['pup']['init_opt_strategy']}"
            f" --init-solve-limit={config_cls.lns_configuration_values['pup']['init_solve_limit']}\n"
            f" --lns-opt-strategy={config_cls.lns_configuration_values['pup']['lns_opt_strategy']}"
            f" --lns-solve-limit={config_cls.lns_configuration_values['pup']['lns_solve_limit']}\n"
            f"[pmsp]:\n"
            f" --init-solve-limit={config_cls.lns_configuration_values['pmsp']['init_solve_limit']}"
            f" --init-time-limit={config_cls.lns_configuration_values['pmsp']['init_time_limit']}"
            f" --lns-opt-mode={config_cls.lns_configuration_values['pmsp']['lns_opt_mode']}\n"
            f" --lns-solve-limit={config_cls.lns_configuration_values['pmsp']['lns_solve_limit']}"
            f" --lns-time-limit={config_cls.lns_configuration_values['pmsp']['lns_time_limit']}\n"
            f"[tlsp]:\n"
            f" --init-configuration={config_cls.lns_configuration_values['tlsp']['init_configuration']}"
            f" --init-opt-strategy={config_cls.lns_configuration_values['tlsp']['init_opt_strategy']}"
            f" --init-solve-limit={config_cls.lns_configuration_values['tlsp']['init_solve_limit']}\n"
            f" --lns-opt-strategy={config_cls.lns_configuration_values['tlsp']['lns_opt_strategy']}"
            f" --lns-opt-mode={config_cls.lns_configuration_values['tlsp']['lns_opt_mode']}"
            f" --lns-solve-limit={config_cls.lns_configuration_values['tlsp']['lns_solve_limit']}"
        ),
        choices=[
            "teaspoon",
            "tsp",
            "sgp",
            "spg",
            "wsc",
            "wsc-medium",
            "wsc-large",
            "sd",
            "pup",
            "pmsp",
            "tlsp",
        ],
        default=config.heulingo_configuration,
        type=str,
        dest="heulingo_configuration",
    )

    ##############################
    # lns solver options
    lns_solver_group = parser.add_argument_group(
        "LNS Solver Configuration", "Configuration options for the LNS solver"
    )

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
        default=None,
        type="lns_opt_mode",
        dest="lns_opt_mode",
        metavar="<arg>",
    )
    lns_solver_group.add_argument(
        "--lns-solve-limit",
        help="set LNS solve limit [%(default)s]",
        default=config.lns_solve_limit,
        type=parse_solve_limit,
        metavar="<n>[,<m>]",
        dest="lns_solve_limit",
    )
    lns_solver_group.add_argument(
        "--lns-time-limit",
        help="set LNS time limit [%(default)s]",
        default=config.lns_time_limit,
        type=int,
        metavar="<n>",
        dest="lns_time_limit",
    )
    return parser

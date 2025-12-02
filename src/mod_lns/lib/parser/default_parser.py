"""
Parser for default strategy in LNS.
"""

from argparse import ArgumentParser, RawTextHelpFormatter, _SubParsersAction
from textwrap import dedent
from typing import TYPE_CHECKING, Optional

from clingo import Configuration, Control

from mod_lns.interfaces.solver import SolverInterface
from mod_lns.lib.parser.framework_parser import get_classes_from_package

if TYPE_CHECKING:
    from mod_lns.lib.strategies.default_strategy import LNSConfig  # nocoverage

VERSION = "1.0.1"


# pylint: disable=too-many-statements
def get_default_parser(
    config_cls: type["LNSConfig"], subparsers: "_SubParsersAction[ArgumentParser]"
) -> ArgumentParser:
    """
    Parse command line options.

    :param args: Command line arguments
    :type args: str
    """

    config = config_cls()

    def formatter(prog: str) -> RawTextHelpFormatter:
        return RawTextHelpFormatter(
            prog,
            max_help_position=10,
            width=100,
        )

    parser = subparsers.add_parser(
        "default",
        help="Default strategy for LNS",
        description=dedent(
            """\
            Default strategy
            An implementation of Large Neighbourhood Search (LNS)
            based on Answer Set Programming (ASP).

            Check the documentation for a guide on how to use this
            strategy.
            """
        ),
        formatter_class=formatter,
    )

    # list of supported solvers
    solvers = [(cls.get_name(), cls()) for cls in get_classes_from_package("mod_lns.lib.solvers", SolverInterface)]

    def get(solvers: list[tuple[str, SolverInterface]], name: str) -> SolverInterface | None:
        for key, val in solvers:
            if key == name:
                return val
        return None  # nocoverage

    def parse_solver(string: str) -> SolverInterface:
        """
        Parse the solver string.
        """
        solver = get(solvers, string)
        if solver is None:
            parser.error(f"'{string}': Invalid solver. Choose from {{{','.join(key for key, _ in solvers)}}}")
        return solver

    parser.register("type", "solver", parse_solver)

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

    parser.register("type", "solve_limit", parse_solve_limit)
    parser.register("type", "pos_int_or_none", parse_pos_int_or_none)

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
        type=int,
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
        "--relax-rate",
        help="set relaxation rate in percent [%(default)s]",
        default=config.relax_rate,
        type=int,
        dest="relax_rate",
        metavar="<n>",
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
        metavar="<n>",
    )
    # model limit

    ###################
    # lns options
    lns_group = parser.add_argument_group("LNS Configuration", "Configuration options for the LNS")

    lns_group.add_argument(
        "--lns-constrained",
        help="set LNS to use constrained optimization",
        action="store_true",
        dest="constrained",
    )
    lns_group.add_argument(
        "--lns-declarative",
        help="set LNS to use declarative optimization",
        action="store_true",
        dest="declarative",
    )
    lns_group.add_argument(
        "--lns-accept-variability",
        help="set required variability to accept new solutions in percent [%(default)s]",
        default=config.accept_variability,
        type=int,
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
            f" --time-limit={config_cls.preset_values['basic']['time_limit']}"
            f" --max-steps={config_cls.preset_values['basic']['max_steps']}"
            f" --relax-rate={config_cls.preset_values['basic']['relax_rate']}\n"
            f" --init-time-limit={config_cls.preset_values['basic']['init_time_limit']}"
            f" --init-solve-limit={config_cls.preset_values['basic']['init_solve_limit']}\n"
            f" --lns-time-limit={config_cls.preset_values['basic']['lns_time_limit']}"
            f" --lns-solve-limit={config_cls.preset_values['basic']['lns_solve_limit']}"
        ),
        choices=["basic"],
        default=config.preset,
        type=str,
        dest="preset",
        metavar="<arg>",
    )

    ##############################
    # lns solver options
    lns_solver_group = parser.add_argument_group("LNS Solver Configuration", "Configuration options for the LNS solver")

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
    return parser

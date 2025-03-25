"""
The main entry point for the application.
"""

from . import LNS
from .lns_config import LNSConfig
from .utils.logger import setup_logger
from .utils.parser import get_parser


def main():
    """
    Run the main function.
    """
    parser = get_parser()
    args, rest = parser.parse_known_args()
    log = setup_logger("main", args.log)

    log.info("info")
    log.warning("warning")
    log.debug("debug")
    log.error("error")

    config = LNSConfig(
        {
            "heuristics": args.heuristics,
            "constrained": args.constrained,
            "declarative": args.declarative,
            "seed": args.seed,
            "relax_rate": args.relax_rate,
            "overall_time_limit": args.time_limit,
            "solve_time_limit": args.solve_time_limit,
            "max_steps": args.max_steps,
        },
        rest,
        args.solver,
        args.strategy,
    )

    lns = LNS(
        args.input_files,
        config,
    )
    lns.main()


if __name__ == "__main__":
    main()

"""
The main entry point for the application.
"""

from . import LNS
from .utils.logger import setup_logger
from .utils.parser import get_parser


def main():
    """
    Run the main function.
    """
    parser = get_parser()
    args, _ = parser.parse_known_args()
    log = setup_logger("main", args.log)

    log.info("info")
    log.warning("warning")
    log.debug("debug")
    log.error("error")

    lns = LNS(
        args.input_files,
        args.solver,
        args.strategy,
        {
            "seed": args.seed,
            "relax_rate": args.relax_rate,
            "overall_time_limit": args.time_limit,
            "solve_time_limit": args.solve_time_limit,
            "max_steps": args.max_steps,
            "stuck_after_no_improv": args.no_improv,
            "vari_accept": args.vari_accept,
            "pre_files": args.pre_files,
            "pre_tl": args.pre_tl,
            "start_sol": args.start_sol,
        },
    )
    lns.main()


if __name__ == "__main__":
    main()

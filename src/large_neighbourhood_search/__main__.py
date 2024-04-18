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
    args, rest = parser.parse_known_args()
    log = setup_logger("main", args.log)

    log.info("info")
    log.warning("warning")
    log.debug("debug")
    log.error("error")

    lns = LNS(args.i, seed=None, relax_rates=[0.2, 0.4], clingo_args=rest)
    lns.main()


if __name__ == "__main__":
    main()

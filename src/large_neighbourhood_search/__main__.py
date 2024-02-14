"""
The main entry point for the application.
"""

import sys
import clingo
from .utils.logger import setup_logger
from .utils.parser import get_parser
from . import LNS

def main():
    """
    Run the main function.
    """
    parser = get_parser()
    args,rest = parser.parse_known_args()
    log = setup_logger("main", args.log)

    log.info("info")
    log.warning("warning")
    log.debug("debug")
    log.error("error")

    lns = LNS(
        args.i,
        rest,
        args.lns_seed,
        args.bnb_search,
        args.declarative
    )
    lns.main()

if __name__ == "__main__":
    main()

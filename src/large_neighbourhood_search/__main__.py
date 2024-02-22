"""
The main entry point for the application.
"""

import sys
import clingo
import json
from .utils.logger import setup_logger
from .utils.parser import get_parser
from . import LNS

def gen_example_params(path: str):
        """
        Generate example parameter file.
        """
        params = {}
        # name of parameter file
        params["name"] = "example_params"
        params["relaxation"] = {}
        # mode: decl, rndm
        params["relaxation"]["mode"] = "decl"
        # relax rates
        params["relaxation"]["rates"] = [0.2, 0.4, 0.6]

        params["search"] = {}
        # mode: hard_const, (classic)
        params["search"]["mode"] = "hard_const"
        # overall bound (atm number of steps)
        params["search"]["bound"] = 100

        with open(path+"/example_params.json", 'w', encoding='utf-8') as f:
            json.dump(params, f, ensure_ascii=False, indent=4)
            f.close()

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

    if (args.gen_example):
        gen_example_params(args.gen_example)
        return

    lns = LNS(
        args.i,
        rest,
        args.lns_seed,
        args.rr,
        args.bnb_search,
        args.declarative
    )
    lns.main()

if __name__ == "__main__":
    main()

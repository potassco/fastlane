"""
The main entry point for the application.
"""

from . import LNS
from .utils.logger import setup_logger
from .utils.parser import get_parser
from .utils.pf_handling import create_param_file, gen_example_params


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

    if args.gen_example:
        gen_example_params(args.gen_example)
        return

    if args.new_param_file:
        create_param_file(args.new_param_file)
        return

    lns = LNS(
        args.i,
        rest,
        args.lns_seed,
        args.relax_rate,
        args.declarative,
        args.load_param_file,
    )
    lns.main()


if __name__ == "__main__":
    main()

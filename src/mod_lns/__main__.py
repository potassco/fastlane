"""
The main entry point for the application.
"""

from mod_lns.lib.parser.options_parser import OptionsParser
from mod_lns.lns import LNS


def main() -> None:
    """
    Run the main function.
    """
    # parser as cls with cls.methods
    parser = OptionsParser.get_parser()
    args = parser.parse_args()

    # args.files=["examples/golf.lp"]

    if len(args.files) == 0:
        parser.error("No input files provided.")

    lns = LNS(args.files, vars(args))
    lns.main()


if __name__ == "__main__":
    main()

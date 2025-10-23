"""
The main entry point for the application.
"""

from mod_lns.lib.parser.framework_parser import get_framework_parser
from mod_lns.lns import LNS


def main():
    """
    Run the main function.
    """

    parser = get_framework_parser()
    args = parser.parse_args()

    if len(args.files) == 0:
        parser.error("No input files provided.")

    lns = LNS(args.files, args.strategy, vars(args))
    lns.main()


if __name__ == "__main__":
    main()

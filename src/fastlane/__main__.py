"""
The main entry point for the application.
"""

import sys

from fastlane.lns import LNS
from fastlane.parsers.options_parser import OptionsParser


def main() -> None:
    """
    Run the main function.
    """
    # parser as cls with cls.methods
    parser = OptionsParser.get_parser()
    args = parser.parse_args()

    if not args.files:
        if sys.stdin.isatty():
            parser.error("No input files provided.")
        args.files = ["-"]

    lns = LNS(args.files, vars(args))
    lns.main()


if __name__ == "__main__":
    main()

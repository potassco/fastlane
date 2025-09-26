"""
Strategy interface used for LNS.
"""

from __future__ import annotations

import abc
from argparse import ArgumentParser, Namespace, _SubParsersAction
from logging import Logger
from typing import TYPE_CHECKING, Any, Optional

import clingo

from mod_lns import Model
from mod_lns.interfaces.solver import SolverInterface
from mod_lns.utils.logger import setup_logger

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage

# c, b, n: current, best, new model
# pre_setup()
# solver_setup()
# post_setup()
# c = first_sol()
# post_first_sol()
# while check_stop()
#   pre_relax()
#   n = repair(relax(c))
#   post_repair()
#   check_accept(n)
#       c = n
#       accepted()
#   check_better(n,b)
#       b = n
#       better()


class StrategyInterface(metaclass=abc.ABCMeta):
    """
    Strategy interface.
    """

    def __init__(self) -> None:
        """
        Initialize strategy interface.
        """
        self._log_level: int = 30  # logging.WARNING
        self.logger: Logger = setup_logger("DefaultStrategyLogger", self._log_level)
        self.solver: Optional[SolverInterface] = None

    @classmethod
    def __subclasshook__(cls, subclass):  # nocoverage
        return (
            hasattr(subclass, "get_parser")
            and callable(subclass.get_parser)
            and hasattr(subclass, "parse_options")
            and callable(subclass.parse_options)
            and hasattr(subclass, "setup_solver")
            and callable(subclass.setup_solver)
            and hasattr(subclass, "get_first_solution")
            and callable(subclass.get_first_solution)
            and hasattr(subclass, "check_stop")
            and callable(subclass.check_stop)
            and hasattr(subclass, "relax")
            and callable(subclass.relax)
            and hasattr(subclass, "repair")
            and callable(subclass.repair)
            and hasattr(subclass, "check_accept")
            and callable(subclass.check_accept)
            and hasattr(subclass, "check_better")
            and callable(subclass.check_better)
            and hasattr(subclass, "print_result")
            and callable(subclass.print_result)
            or NotImplemented
        )

    @abc.abstractmethod
    def get_parser(
        self, subparsers: _SubParsersAction[ArgumentParser]
    ) -> ArgumentParser:  # nocoverage
        """
        Get parser for strategy.

        :param subparsers: Subparsers action.
        :type subparsers: _SubParsersAction[ArgumentParser]
        :return: Argument parser.
        :rtype: ArgumentParser
        """
        raise NotImplementedError

    @abc.abstractmethod
    def parse_options(self, args: Namespace) -> dict[str, Any]:  # nocoverage
        """
        Parse options from args.

        :param args: Parsed arguments.
        :type args: Namespace
        :return: Remaining unparsed options.
        :rtype: dict[str, Any]
        """
        raise NotImplementedError

    def init_logger(self, logger: Logger) -> None:  # nocoverage
        """
        Initialize logger for strategy.

        :param logger: Logger object.
        :type logger: logging.Logger
        """
        self.logger = logger

    def pre_setup(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something pre solver setup.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """

    @abc.abstractmethod
    def setup_solver(self, lns_object: LNS) -> None:  # nocoverage
        """
        Setup solver for LNS.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """
        raise NotImplementedError

    def post_setup(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something post solver setup.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """

    @abc.abstractmethod
    def get_first_solution(
        self,
        lns_object: LNS,
    ) -> bool:  # nocoverage
        """
        Find initial solution.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: Whether a solution was found or not
        :rtype: bool
        """
        raise NotImplementedError

    def post_first_solution(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something post first solution.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """

    @abc.abstractmethod
    def check_stop(self, lns_object: LNS) -> bool:  # nocoverage
        """
        Check whether to stop LNS.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: Whether to stop LNS or not.
        :rtype: bool
        """
        raise NotImplementedError

    def pre_relax(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something pre relaxation.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """

    @abc.abstractmethod
    def relax(
        self,
        lns_object: LNS,
    ) -> list[clingo.symbol.Symbol]:  # nocoverage
        """
        Relax portion of atoms given by the relax_parameters.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: Fixed (not relaxed) atoms.
        :rtype: list[clingo.symbol.Symbol, bool]
        """
        raise NotImplementedError

    @abc.abstractmethod
    def repair(
        self,
        lns_object: LNS,
        fixed_atoms: list[clingo.symbol.Symbol],
    ) -> Optional[Model]:  # nocoverage
        """
        Repair solution.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param assumptions: Assumptions for solving (fixed atoms).
        :type assumptions: list[clingo.symbol.Symbol, bool]
        :return: Repaired model.
        :rtype: Optional[Model]
        """
        raise NotImplementedError

    def post_repair(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something post repair.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """

    @abc.abstractmethod
    def check_accept(
        self,
        lns_object: LNS,
    ) -> bool:  # nocoverage
        """
        Check whether new model is accepted.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: Whether new model is accepted or not.
        :rtype: bool
        """
        raise NotImplementedError

    def accepted(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something after new model is accepted and saved as the new current model.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """

    @abc.abstractmethod
    def check_better(
        self,
        lns_object: LNS,
    ) -> bool:  # nocoverage
        """
        Check whether new model is better.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: Whether new model is better or not.
        :rtype: bool
        """
        raise NotImplementedError

    def better(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something after new model is better and saved as the new best model.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """

    def pre_next_iteration(self, lns_object: LNS) -> None:  # nocoverage
        """
        Do something after all checks pre next iteration.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """

    @abc.abstractmethod
    def print_result(
        self,
        lns_object: LNS,
    ) -> None:  # nocoverage
        """
        Print results of LNS.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """
        raise NotImplementedError

    # being reworked
    # pylint: disable=unused-argument
    # @classmethod
    # def stuck_handling(self, lns_object: LNS) -> None:
    #    """
    #    Check whether search is stuck and what to do if it is.
    #
    #    :param lns_object: LNS object.
    #    :type lns_object: mod_lns.LNS
    #    """

"""
Default strategy, supports both a classic and constrained LNS approach as well as
declarative and random relaxation.
"""

from __future__ import annotations

import random
from argparse import ArgumentParser, _SubParsersAction
from dataclasses import dataclass, field
from math import log10
from typing import TYPE_CHECKING, Any, Optional

import clingo
from clingo import Symbol

from mod_lns import Model
from mod_lns.interfaces.solver import SolverConfig, SolverInterface
from mod_lns.interfaces.strategy import StrategyInterface
from mod_lns.lib.parser.default_parser import get_default_parser
from mod_lns.lib.relaxation import relax_declarative, relax_random
from mod_lns.lib.solvers import ClingoSolver
from mod_lns.lib.utils import calculate_variability

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage

LINE = "--------------------------------------------------------------------------------------"


# pylint: disable=too-many-instance-attributes
@dataclass
class LNSConfig:
    """
    Configuration for LNS.

    :param log_level: Logging level.
    :type log_level: int
    :param solver: Solver to use.
    :type solver: SolverInterface
    :param seed: Random seed.
    :type seed: int
    :param time_limit: Time limit for each LNS iteration.
    :type time_limit: int
    :param max_steps: Maximum number of steps for LNS.
    :type max_steps: int
    :param relax_rate: Relaxation rate for LNS.
    :type relax_rate: int
    :param init_time_limit: Time limit for the initial solver.
    :type init_time_limit: int
    :param init_solve_limit: Solve limit for the initial solver.
    :type init_solve_limit: str
    :param constrained: Whether to use constrained optimization.
    :type constrained: bool
    :param declarative: Whether to use declarative relaxation.
    :type declarative: bool
    :param accept_variability: Required variability for new solutions.
    :type accept_variability: int
    :param lns_time_limit: Time limit for LNS solver.
    :type lns_time_limit: int
    :param lns_solve_limit: Solve limit for LNS solver.
    :type lns_solve_limit: str
    """

    # utils
    log_level: int = 30

    # general configuration
    # solver default has to be set manually in parser
    solver: SolverInterface = field(default_factory=ClingoSolver)
    seed: Optional[int] = None
    time_limit: Optional[int] = 600
    max_steps: Optional[int] = 2000
    relax_rate: int = 20
    status_interval: int = 50

    # init solver configuration
    init_time_limit: int = 20
    init_solve_limit: Optional[str] = "2500000,5000"

    # lns configuration
    constrained: bool = False
    declarative: bool = False
    accept_variability: int = 0

    # lns solver configuration
    lns_time_limit: int = 20
    lns_solve_limit: Optional[str] = "2500000,5000"

    def get_init_solver_configuration(self) -> SolverConfig:
        """
        Get the initial solver configuration.

        :return: Initial Solver configuration.
        :rtype: SolverConfig
        """
        config = SolverConfig()
        config.solve_limit = self.init_solve_limit
        config.time_limit = self.init_time_limit
        config.seed = self.seed
        return config

    def get_lns_solver_configuration(self) -> SolverConfig:
        """
        Get the LNS solver configuration.

        :return: LNS solver configuration.
        :rtype: SolverConfig
        """
        config = SolverConfig()
        config.solve_limit = self.lns_solve_limit
        config.time_limit = self.lns_time_limit
        config.seed = self.seed
        return config


# pylint: disable=duplicate-code
class DefaultStrategy(StrategyInterface):
    """
    Classic LNS with weighted sum as optimization criteria and random relaxation.
    """

    def __init__(self) -> None:
        """
        Initialize default strategy.
        """
        super().__init__()
        self.prev_fixed_atoms: list[clingo.symbol.Symbol] = []
        self.config = LNSConfig()

        self._iter_format: str = ""
        self._printout: bool = False

    def get_parser(
        self, subparsers: _SubParsersAction[ArgumentParser]
    ) -> ArgumentParser:
        """
        Parse command line options.

        :param subparsers: Subparsers for the argument parser.
        :type subparsers: _SubParsersAction[ArgumentParser]
        :return: Argument parser for the strategy.
        :rtype: ArgumentParser
        """
        parser = get_default_parser(LNSConfig, subparsers)
        parser.set_defaults(strategy=self)
        return parser

    def parse_options(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Parse options from args.

        :param args: Parsed arguments.
        :type args: dict[str, Any]
        :return: Remaining unparsed options.
        :rtype: dict[str, Any]
        """
        rest = {}
        for attr, value in args.items():
            if value is not None:
                if hasattr(self.config, attr):
                    setattr(self.config, attr, value)
                else:
                    rest[attr] = value
        self.solver = self.config.solver
        self._log_level = self.config.log_level
        return rest

    def pre_setup(self, lns_object: "LNS"):
        """
        Perform actions before solver setup.

        :param lns_object: LNS
        :type lns_object: mod_lns.LNS
        """
        self.timer.start(self.config.time_limit)  # None for no time limit

        self.init_solver_config = self.config.get_init_solver_configuration()
        self.lns_solver_config = self.config.get_lns_solver_configuration()

        # set time limit if no solve time limit given or larger than overall time limit
        init_tl = self.init_solver_config.time_limit
        tl = self.config.time_limit
        if tl is not None:
            if init_tl is None:
                self.init_solver_config.time_limit = tl
            elif tl < init_tl:
                self.init_solver_config.time_limit = tl

        random.seed(self.config.seed)

    def setup_solver(self, lns_object):
        """
        Setup the solver for LNS.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        """
        assert isinstance(self.solver, SolverInterface)
        args = []
        if self.config.seed is not None:
            args.append(f"--seed={self.config.seed}")
        self.solver.setup(lns_object, args)

    def post_setup(self, lns_object: "LNS"):
        """
        Perform actions after solver setup.

        :param lns_object: LNS
        :type lns_object: mod_lns.LNS
        """
        assert isinstance(self.solver, SolverInterface)
        self.solver.ground()

    def _update_time_limit(self, solver_config: SolverConfig) -> None:
        """
        Update solve time-limit.

        :param solver_config: Solver configuration to update.
        :type solver_config: SolverConfig
        """
        if self.config.time_limit is not None:
            solver_tl = solver_config.time_limit
            if solver_tl is None:
                solver_config.time_limit = self.timer.remaining_time()
            elif self.timer.remaining_time() < solver_tl:
                solver_config.time_limit = self.timer.remaining_time()
                self.logger.debug(
                    "elapsed time: %d seconds", self.timer.get_elapsed_time()
                )
                self.logger.debug(
                    "Time limit for solver reduced to %d seconds "
                    "to fit into overall time limit.",
                    solver_config.time_limit,
                )

    # pylint: disable=dangerous-default-value
    def get_first_solution(
        self,
        lns_object: LNS,
    ) -> bool:
        """
        Find initial solution.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: Whether a solution was found or not
        :rtype: bool
        """
        assert isinstance(self.solver, SolverInterface)
        self._update_time_limit(self.init_solver_config)
        lns_object.new_model = self.solver.solve(self.init_solver_config)
        if lns_object.new_model is None:
            return False
        lns_object.current_model = lns_object.new_model
        lns_object.best_model = lns_object.new_model
        return True

    def _calc_opt_bound(self, solver_config: SolverConfig, cost: list[int]) -> None:
        """
        Calculate bound for next step.

        :param solver_config: Solver configuration
        :type solver_config: SolverConfig
        :param cost: Current cost list
        :type cost: list[int]
        """
        bound = cost[:-1] + [cost[-1] - 1]
        solver_config.opt_mode = "opt, " + ", ".join([str(c) for c in bound])

    def post_first_solution(self, lns_object):
        """
        Actions to perform after finding the first solution.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        """
        if not self.solver.finished:
            self._update_time_limit(self.lns_solver_config)

            if self.config.constrained:
                self._calc_opt_bound(
                    self.lns_solver_config,
                    lns_object.current_model.cost,
                )

        # prepare output format and print header
        time_digits = 5 + 1 + 3  # 5 digits + dot + 3 digits
        step_digits = 7
        cost_digits = max(len(lns_object.best_model.get_cost_str()), 4)
        if self.config.time_limit is not None:
            time_digits = max(
                int(log10(self.config.time_limit)) + 1 + 1 + 3, time_digits
            )
        if self.config.max_steps is not None:
            step_digits = max(int(log10(self.config.max_steps)) + 1, step_digits)

        header = f"{{0:>{time_digits}}} - {{1:>{step_digits}}}: {{2:>{cost_digits}}}"
        print(header.format("time in s", "step", "cost"))

        self._iter_format = (
            f"{{0:>{time_digits}.3f}} - {{1:>{step_digits}}}: {{2:>{cost_digits}}}"
        )
        print(
            self._iter_format.format(
                self.timer.get_elapsed_time(),
                "initial",
                lns_object.best_model.get_cost_str(),
            ),
            flush=True,
        )

    def check_stop(self, lns_object: LNS) -> bool:
        """
        Check whether to stop LNS.

        Stop if:
        max # of steps exceeded,
        overall time limit exceeded

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: Whether to stop LNS or not.
        :rtype: bool
        """
        assert isinstance(self.solver, SolverInterface)
        stop = False
        if self.config.time_limit is not None:
            if self.timer.is_ringing:
                print(f"Time limit ({self.config.time_limit} seconds) reached.")
                stop = True

        if self.config.max_steps is not None:
            if lns_object.step_c >= self.config.max_steps:
                print(f"Maximum number of steps ({self.config.max_steps}) reached.")
                stop = True
        if self.solver.stop:
            stop = True
        return stop

    def pre_relax(self, lns_object: LNS) -> None:
        """
        Actions to perform before relaxing the solution,
        at the start of a new iteration.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """
        self._printout = False

    def relax(
        self,
        lns_object: LNS,
    ) -> list[Symbol]:
        """
        Relax portion of atoms given by the relax_parameters.
        Use random relaxation.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param relax_rate: Percentage of atoms to be relaxed.
        :type relax_rate: float
        :return: Fixed (not relaxed) atoms.
        :rtype: list[Symbol]
        """
        if self.config.declarative:
            return relax_declarative(lns_object.current_model, self.config.relax_rate)
        return relax_random(lns_object.current_model, self.config.relax_rate)

    def repair(
        self,
        lns_object: LNS,
        fixed_atoms: list[Symbol],
    ) -> Optional[Model]:
        """
        Repair solution.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :param fixed_atoms: Fixed atoms.
        :type fixed_atoms: list[Symbol]
        :return: Repaired model.
        :rtype: Optional[Model]
        """
        assert isinstance(self.solver, SolverInterface)
        self._update_time_limit(self.lns_solver_config)
        new_model = self.solver.solve(
            self.lns_solver_config, list(map(lambda x: (x, True), fixed_atoms))
        )
        return new_model

    # pylint: disable=unused-argument
    def check_accept(
        self,
        lns_object: LNS,
    ) -> bool:
        """
        Check whether new model is accepted.
        Accept if desired variability is achieved.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: Whether new model is accepted or not.
        :rtype: bool
        """
        if lns_object.new_model is None:
            self.logger.debug("No new model found, not accepted.")
            return False
        vari = calculate_variability(
            lns_object.new_model.shown,
            lns_object.current_model.shown,
        )
        self.logger.debug("variability: %s", vari)
        self.logger.debug("threshold: %s", self.config.accept_variability)
        if vari >= self.config.accept_variability:
            return True
        self.logger.debug("new model declined")
        return False

    def accepted(self, lns_object: "LNS") -> None:
        """
        Do something after new model is accepted and saved as the new current model.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: None
        """
        self.logger.debug("new model accepted")
        if self.config.constrained:
            self._calc_opt_bound(
                self.lns_solver_config,
                lns_object.current_model.cost,
            )

    def check_better(
        self,
        lns_object: LNS,
    ) -> bool:
        """
        Check whether new model is better.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        :return: Whether new model is better or not.
        :rtype: bool
        """
        if lns_object.new_model is None:
            self.logger.debug("No new model found, not better.")
            return False
        return lns_object.new_model.cost < lns_object.best_model.cost

    def better(self, lns_object: "LNS") -> None:
        """
        Do something after new model is better than the best model.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: None
        """
        self.logger.debug("new best model")
        self._printout = True

    def pre_next_iteration(self, lns_object: "LNS") -> None:
        """
        Do something before next iteration.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: None
        """
        if self._iter_format == "":
            raise RuntimeError("pre_relax called before post_first_solution")
        if self._printout or lns_object.step_c % self.config.status_interval == 0:
            print(
                self._iter_format.format(
                    self.timer.get_elapsed_time(),
                    lns_object.step_c,
                    lns_object.best_model.get_cost_str(),
                ),
                flush=True,
            )

    def print_result(
        self,
        lns_object: "LNS",
    ) -> None:  # nocoverage
        """
        Print the result of the LNS process.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: None
        """
        assert isinstance(self.solver, SolverInterface)
        print(LINE)
        print("Result")
        print(LINE)
        lns_object.best_model.print_model()
        try:
            print(self.solver.result)
        except AttributeError:
            print("UNKNOWN")
        try:
            print("Optimum:", self.solver.optimum)
        except AttributeError:
            print("Optimum: unknown")
        print(f"Iterations: {lns_object.step_c}")
        print(f"Overall time: {self.timer.get_elapsed_time():.3f}s")
        print(LINE)

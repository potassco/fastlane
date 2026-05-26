"""
A modifiable large neighborhood search framework.
"""

import random
from typing import Any, Optional

from clingo import Function, Number, Symbol

from mod_lns import UNSET, Model, Timer
from mod_lns.interfaces.solver import SolverConfig
from mod_lns.lib.adaptive_strategies import AdaptiveStrategy, StaticStrategy
from mod_lns.lib.modules.constrained import get_opt_bound
from mod_lns.lib.modules.heuristics import generate_heuristic_subprogram
from mod_lns.lib.modules.output import get_output_format
from mod_lns.lib.parser.new_config_parser import ConfigParser
from mod_lns.lib.relaxation import relax_declarative, relax_random
from mod_lns.lib.utils import calculate_variability, update_time_limit
from mod_lns.lns_config import LNSConfig
from mod_lns.utils.logger import setup_logger

LINE = "--------------------------------------------------------------------------------------"


# pylint: disable=too-many-instance-attributes
class LNS:
    """
    Class handling and  performing LNS.

    :param files: Problem encodings.
    :type files: list[str]
    :param lns_config: LNSConfig object.
    :type lns_config: mod_lns.LNSConfig
    :default lns_config: LNSConfig()
    """

    # pylint: disable=dangerous-default-value
    def __init__(
        self,
        files: list[str],
        args: dict[str, Any] = {},
        config: Optional[LNSConfig] = LNSConfig(),
    ):
        """
        Initialization of the lns object.
        """
        self.config: LNSConfig = config
        self.parse_options(args)
        self.logger = setup_logger("LNS", self.config.log_level)

        self.files: list[str] = files

        self.step_c: int = 0

        self.new_model: Optional[Model] = None
        self.current_model: Model = Model()
        self.best_model: Model = Model()

        # parsed declarative configuration
        self._declarative_config: dict[str, Any] = {}
        # declarative configuration for current iteration
        self._declarative_config_current: dict[str, Any] = {}
        self.prev_fixed_atoms: set[Symbol] = set()
        self._variable_model: bool = False
        self._adaptive_strategy: AdaptiveStrategy = StaticStrategy()
        # remove?
        self._falsified: bool = False
        self._false_weight: Function = Function("inf")

        self.init_solver_config: SolverConfig = SolverConfig()
        self.lns_solver_config: SolverConfig = SolverConfig()

        self.timer: Timer = Timer()

        self._printout: bool = False
        self._iter_format: str = ""

    def parse_options(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Parse options from args.

        :param args: Parsed arguments.
        :type args: dict[str, Any]
        :return: Remaining unparsed options.
        :rtype: dict[str, Any]
        """
        # argument priority (from high to low):
        # 1. directly set arguments
        # 2. configuration preset
        # 3. directly set config values (defaults)
        rest = {}
        if "preset" in args and args["preset"] is not None:
            self.config.preset = args["preset"]
        if self.config.preset is not None:
            self.config.apply_preset()
        for attr, value in args.items():
            if value is not UNSET:
                if hasattr(self.config, attr):
                    setattr(self.config, attr, value)
                else:
                    rest[attr] = value
        self.config.prepare()
        self.solver = self.config.solver
        self._log_level = self.config.log_level
        return rest

    def pre_setup(self) -> None:
        """
        Perform actions before solver setup.
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

        lns_opt_mode = self.config.lns_opt_mode
        if lns_opt_mode["modifier"] is not None and lns_opt_mode["nf"] is not None:
            if lns_opt_mode["modifier"] == "dynamic":
                if float(lns_opt_mode["nf"]) <= 0:
                    self.logger.warning(
                        "heulingo may finish without proving optimality because of 0 or less percent of lns-opt-mode"
                    )
                if float(lns_opt_mode["nf"]) < self.config.accept_improvement:
                    self.logger.warning("Rate of lns-opt-mode is less than improvement acceptance rate")

        random.seed(self.config.seed)

        # if self.config.falsify is not None:
        #     self._falsified = True
        #     if self.config.falsify != "inf":
        #         self._false_weight = Number(int(self.config.falsify))

    def setup_solver(self) -> None:
        """
        Setup the solver for LNS.
        """
        if self.config.minimize_variable is not None:
            self.solver.minimize_variable = self.config.minimize_variable

        args = []
        if self.config.seed is not None:
            args.append(f"--seed={self.config.seed}")
        if self.config.parallel_mode is not None:
            args.append(f"--parallel-mode={self.config.parallel_mode}")
        if self.config.clingo_args is not None:
            args.extend(self.config.clingo_args.split(","))
        self.solver.setup(self, args)

    def post_setup(self) -> None:
        """
        Perform actions after solver setup.
        """
        self.solver.ground()

    def get_first_solution(self) -> bool:
        """
        Find initial solution.

        :return: Whether a solution was found or not
        :rtype: bool
        """
        update_time_limit(self, self.init_solver_config)
        self.new_model = self.solver.solve(self.init_solver_config)
        if self.new_model is None:
            return False
        self.current_model = self.new_model
        self.best_model = self.new_model
        return True

    def post_first_solution(self) -> None:
        """
        Actions to perform after finding the first solution.
        """
        if not self.solver.finished:
            update_time_limit(self, self.lns_solver_config)

            if self.config.declarative or self.config.use_heuristics or self.config.adaptive:
                self._declarative_config = ConfigParser.parse_lns_config(self)

                # adaptive
                if self.config.adaptive:
                    self._adaptive_strategy = self.config.build_adaptive_strategy(self._declarative_config["strategy"])
                self._declarative_config_current = self._adaptive_strategy.get_initial_config(
                    self._declarative_config, self.current_model
                )

                # heuristics
                if self.config.use_heuristics:
                    heuristics = generate_heuristic_subprogram(self._declarative_config)
                    self.logger.debug("Adding heuristics:\n%s", heuristics)
                    self.solver.add("heuristic", ["t"], heuristics)

        # prepare output format and print header
        header, self._iter_format = get_output_format(
            self.best_model.get_cost_str(), self.config.time_limit, self.config.max_steps
        )
        print(header.format("time in s", "step", "cost"))
        print(
            self._iter_format.format(
                self.timer.get_elapsed_time(),
                "initial",
                self.best_model.get_cost_str(),
            ),
            flush=True,
        )

    def check_stop(self) -> bool:
        """
        Check whether to stop LNS.

        Stop if:
        max # of steps exceeded,
        overall time limit exceeded

        :return: Whether to stop LNS or not.
        :rtype: bool
        """
        stop = False
        if self.config.time_limit is not None:
            if self.timer.is_ringing:
                print(f"Time limit ({self.config.time_limit} seconds) reached.")
                stop = True

        if self.config.max_steps is not None:
            if self.step_c >= self.config.max_steps:
                print(f"Maximum number of steps ({self.config.max_steps}) reached.")
                stop = True
        if self.solver.stop:
            stop = True
        return stop

    def pre_relax(self) -> None:
        """
        Actions to perform before relaxing the solution,
        at the start of a new iteration.
        """
        self._printout = False

        self._variability = self._check_variability()

    def relax(self) -> set[Symbol]:
        """
        Relax portion of atoms given by the relax_parameters.
        Use random relaxation.

        :return: Fixed (not relaxed) atoms.
        :rtype: set[Symbol]
        """
        if self.config.declarative:
            # replace with relax from ALNPS (convert auto(rr=-1))
            return relax_declarative(self.current_model, self.config.relax_rate)
        return relax_random(self.current_model, self.config.relax_rate)

    def repair(self, fixed_atoms: set[Symbol]) -> Optional[Model]:
        """
        Repair solution.

        :param fixed_atoms: Fixed atoms.
        :type fixed_atoms: set[Symbol]
        :return: Repaired model.
        :rtype: Optional[Model]
        """
        lns_opt_mode = self.config.lns_opt_mode
        if lns_opt_mode["mode"] is not None:
            self.lns_solver_config.opt_mode = get_opt_bound(
                self.current_model.cost, lns_opt_mode["mode"], lns_opt_mode["modifier"], lns_opt_mode["nf"]
            )
        update_time_limit(self, self.lns_solver_config)
        # assumptions
        new_model = self.solver.solve(self.lns_solver_config, list(map(lambda x: (x, True), fixed_atoms)))
        return new_model

    def post_repair(self) -> None:
        """
        Actions to perform after repairing the solution.
        """

    def check_accept(self) -> bool:
        """
        Check whether new model is accepted.
        Accept if desired variability is achieved.

        :return: Whether new model is accepted or not.
        :rtype: bool
        """
        if self.new_model is None:
            self.logger.debug("No new model found, not accepted.")
            return False
        vari = calculate_variability(
            self.new_model.shown,
            self.current_model.shown,
        )
        self.logger.debug("variability: %s", vari)
        self.logger.debug("threshold: %s", self.config.accept_variability)
        if vari >= self.config.accept_variability:
            return True
        self.logger.debug("new model declined")
        return False

    def accepted(self) -> None:
        """
        Do something after new model is accepted.
        """
        self.logger.debug("new model accepted")

    def check_better(self) -> bool:
        """
        Check whether new model is better.

        :return: Whether new model is better or not.
        :rtype: bool
        """
        if self.new_model is None:
            self.logger.debug("No new model found, not better.")
            return False
        return self.new_model.cost < self.best_model.cost

    def better(self) -> None:
        """
        Do something after new model is better than the best model.
        """
        self.logger.debug("new best model")
        self._printout = True

    def pre_next_iteration(self) -> None:
        """
        Do something before next iteration.
        """
        if self._iter_format == "":
            raise RuntimeError("pre_relax called before post_first_solution")
        if self._printout or self.step_c % self.config.status_interval == 0:
            print(
                self._iter_format.format(
                    self.timer.get_elapsed_time(),
                    self.step_c,
                    self.best_model.get_cost_str(),
                ),
                flush=True,
            )

    def print_result(self) -> None:  # nocoverage
        """
        Print the result of the LNS process.
        """
        print(LINE)
        print("Result")
        print(LINE)
        self.best_model.print_model()
        try:
            print(self.solver.result)
        except AttributeError:
            print("UNKNOWN")
        try:
            print("Optimum:", self.solver.optimum)
        except AttributeError:
            print("Optimum: unknown")
        print(f"Iterations: {self.step_c}")
        print(f"Overall time: {self.timer.get_elapsed_time():.3f}s")
        print(LINE)

    def main(self) -> None:
        """
        Run Large-Neighbourhood Search according to set parameters.
        """
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

        self.logger.info("info")
        self.logger.warning("warning")
        self.logger.debug("debug")
        self.logger.error("error")

        self.step_c = -1

        self.logger.debug(LINE)
        self.logger.debug("pre_setup")
        self.pre_setup()

        self.logger.debug(LINE)
        self.logger.debug("solver_setup")
        self.setup_solver()

        self.logger.debug(LINE)
        self.logger.debug("post_setup")
        self.post_setup()

        self.step_c = 0

        # get first solution - to be reworked
        # TODO exit if optimum
        self.logger.debug(LINE)
        self.logger.debug("get first solution")
        if not self.get_first_solution():
            self.logger.error("First solution could not be obtained")
            raise SystemExit

        self.logger.debug(LINE)
        self.logger.debug("post first solution")
        self.post_first_solution()

        self.logger.debug(LINE)
        self.logger.debug("start LNS loop")
        while not self.check_stop():
            self.step_c += 1

            self.logger.debug(LINE)
            self.logger.debug(f"iteration {self.step_c}")
            self.logger.debug("pre_relax")
            self.pre_relax()

            self.logger.debug(LINE)
            self.logger.debug("relax")
            fixed_atoms = []
            fixed_atoms = self.relax()

            self.logger.debug(LINE)
            self.logger.debug(f"repair with {len(fixed_atoms)} fixed atoms")
            self.new_model = self.repair(fixed_atoms)

            self.logger.debug(LINE)
            self.logger.debug("post_repair")
            self.post_repair()

            if self.check_accept():
                assert isinstance(self.new_model, Model)
                self.current_model = self.new_model
                self.accepted()

            if self.check_better():
                assert isinstance(self.new_model, Model)
                self.best_model = self.new_model
                self.better()

            self.pre_next_iteration()

        self.print_result()

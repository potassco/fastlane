"""
A modifiable large neighborhood search framework.
"""

import math
import random
from typing import Any, Optional

from clingo import Function, Number, Symbol

from mod_lns import UNSET, Model, Timer
from mod_lns.interfaces.adaptive_strategy import AdaptiveStrategy
from mod_lns.interfaces.solver import SolverConfig
from mod_lns.lib.adaptive_strategies.static import StaticStrategy
from mod_lns.lib.components.constrained import get_opt_bound
from mod_lns.lib.components.heuristics import generate_heuristic_subprogram, get_fixed_atoms_heuristics
from mod_lns.lib.components.output import get_output_format
from mod_lns.lib.components.relaxation import relax_config
from mod_lns.lib.components.repair import repair_assumptions, repair_heuristics
from mod_lns.lib.utils import (
    calculate_variability,
    increase_cutoff,
    increase_solve_limit,
    increase_time_limit,
    update_time_limit,
)
from mod_lns.lns_options import LNSOptions
from mod_lns.parser.config_parser import ConfigParser
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

    def __init__(
        self,
        files: list[str],
        args: Optional[dict[str, Any]] = None,
        config: Optional[LNSOptions] = None,
    ):
        """
        Initialization of the lns object.
        """
        self.options: LNSOptions = config if config is not None else LNSOptions()
        self.parse_options(args if args is not None else {})
        self.logger = setup_logger("LNS", self.options.log_level)

        self.files: list[str] = files

        self.step_c: int = 0

        self.new_model: Optional[Model] = None
        self.current_model: Model = Model()
        self.best_model: Model = Model()

        self.stats: list[dict[str, Any]] = []
        # self.context: str

        # parsed config catalog, includes all available configs and operators
        self._config_catalog: dict[str, Any] = {}
        # selected config specification for current iteration
        self._active_config: dict[str, Any] = {}
        self.prev_fixed_atoms: set[Symbol] = set()
        self._is_variable: bool = False
        self._adaptive_strategy: AdaptiveStrategy = StaticStrategy()
        # remove?
        self._falsified: bool = False
        self._false_weight: Function = Function("inf")

        self.init_solver_config: SolverConfig = SolverConfig()
        self.lns_solver_config: SolverConfig = SolverConfig()

        self.timer: Timer = Timer()

        self._printout: bool = False
        self._iter_format: str = ""

    def _apply_overrides(self, overrides: dict[str, Any]) -> dict[str, Any]:
        """
        Apply overrides to config.

        UNSET values are ignored, all other values (including None) are applied.

        :param overrides: Candidate override values.
        :type overrides: dict[str, Any]
        :return: Remaining options that are not config attributes.
        :rtype: dict[str, Any]
        """
        rest = {}
        for attr, value in overrides.items():
            if value is UNSET:
                continue
            if hasattr(self.options, attr):
                setattr(self.options, attr, value)
            else:
                rest[attr] = value
        return rest

    def parse_options(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Parse options from args.

        :param args: Parsed arguments.
        :type args: dict[str, Any]
        :return: Remaining unparsed options.
        :rtype: dict[str, Any]
        """
        # argument priority (from high to low):
        # 1. CLI options (only explicitly provided values)
        # 2. configuration preset
        # 3. directly set config values
        if args.get("preset", UNSET) is not UNSET:
            self.options.preset = args["preset"]
        if self.options.preset is not None:
            self.options.apply_preset()
        rest = self._apply_overrides(args)
        self.options.prepare()
        self.solver = self.options.solver
        self._log_level = self.options.log_level
        return rest

    def pre_setup(self) -> None:
        """
        Perform actions before solver setup.
        """
        self.timer.start(self.options.time_limit)  # None for no time limit

        self.init_solver_config = self.options.get_init_solver_configuration()
        self.lns_solver_config = self.options.get_lns_solver_configuration()

        # set time limit if no solve time limit given or larger than overall time limit
        init_tl = self.init_solver_config.time_limit
        tl = self.options.time_limit
        if tl is not None:
            if init_tl is None:
                self.init_solver_config.time_limit = tl
            elif tl < init_tl:
                self.init_solver_config.time_limit = tl

        # TODO add warning that opt cant be proven when using assumptions
        lns_opt_mode = self.options.lns_opt_mode
        if lns_opt_mode["modifier"] is not None and lns_opt_mode["nf"] is not None:
            if lns_opt_mode["modifier"] == "dynamic":
                if float(lns_opt_mode["nf"]) <= 0:
                    self.logger.warning(
                        "LNS may finish without proving optimality because of 0 or less percent of lns-opt-mode"
                    )
                if float(lns_opt_mode["nf"]) < self.options.accept_improvement:
                    self.logger.warning("Rate of lns-opt-mode is less than improvement acceptance rate")

        random.seed(self.options.seed)

        # if self.params.falsify is not None:
        #     self._falsified = True
        #     if self.params.falsify != "inf":
        #         self._false_weight = Number(int(self.params.falsify))

    def setup_solver(self) -> None:
        """
        Setup the solver for LNS.
        """
        if self.options.minimize_variable is not None:
            self.solver.minimize_variable = self.options.minimize_variable

        args = []
        if self.options.seed is not None:
            args.append(f"--seed={self.options.seed}")
        if self.options.parallel_mode is not None:
            args.append(f"--parallel-mode={self.options.parallel_mode}")
        if self.options.clingo_args is not None:
            args.extend(self.options.clingo_args.split(","))
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
            self._config_catalog = ConfigParser.parse_lns_config(self)

            self._adaptive_strategy = self.options.build_adaptive_strategy(self._config_catalog["strategy"])
            self._active_config = self._adaptive_strategy.get_initial_config(self._config_catalog, self.current_model)

            # heuristics
            if self.options.use_heuristics:
                heuristics = generate_heuristic_subprogram(self._config_catalog)
                self.logger.debug("Adding heuristics:\n%s", heuristics)
                self.solver.add("heuristic", ["t"], heuristics)

        # prepare output format and print header
        header, self._iter_format = get_output_format(
            self.best_model.get_cost_str(), self.options.time_limit, self.options.max_steps
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
        if self.options.time_limit is not None:
            if self.timer.is_ringing:
                print(f"Time limit ({self.options.time_limit} seconds) reached.")
                stop = True

        if self.options.max_steps is not None:
            if self.step_c >= self.options.max_steps:
                print(f"Maximum number of steps ({self.options.max_steps}) reached.")
                stop = True
        if self.solver.stop or self.solver.finished:
            stop = True
        return stop

    def _check_variability(self) -> bool:
        """
        Check whether the LNPS configuration is variable.
        :return: True if variability is present, False otherwise
        :rtype: bool
        """
        for prioritize_operator in self._active_config["prioritize_operators"]:
            if prioritize_operator["value"] == "inf":
                return False
        return True

    def pre_relax(self) -> None:
        """
        Actions to perform before relaxing the solution,
        at the start of a new iteration.
        """
        self._printout = False

        self._is_variable = self._check_variability()

        # TODO self._op_specs =
        self._active_config["op_specs"] = ConfigParser.get_op_specs(self.current_model)

    def relax(self) -> set[Symbol]:
        """
        Relax portion of atoms given by the configuration.

        :return: Fixed (not relaxed) atoms.
        :rtype: set[Symbol]
        """
        return relax_config(self.current_model, self._active_config, self.logger)

    def repair(self, fixed_atoms: set[Symbol]) -> Optional[Model]:
        """
        Repair solution.

        :param fixed_atoms: Fixed atoms.
        :type fixed_atoms: set[Symbol]
        :return: Repaired model.
        :rtype: Optional[Model]
        """
        lns_opt_mode = self.options.lns_opt_mode
        if lns_opt_mode["mode"] is not None:
            self.lns_solver_config.opt_mode = get_opt_bound(
                self.current_model.cost, lns_opt_mode["mode"], lns_opt_mode["modifier"], lns_opt_mode["nf"]
            )
        update_time_limit(self, self.lns_solver_config)
        self.lns_solver_config.variability = self._is_variable

        # heuristics
        if self.options.use_heuristics:
            self.logger.debug("repair using heuristics")
            fixed_atoms_heuristics = get_fixed_atoms_heuristics(self._active_config, fixed_atoms, self.step_c)
            self.prev_fixed_atoms = fixed_atoms_heuristics.copy()
            new_model = repair_heuristics(
                self.solver,
                self.lns_solver_config,
                fixed_atoms_heuristics,
                self.prev_fixed_atoms,
                self.step_c,
                self.logger,
            )
        # assumptions
        else:
            self.logger.debug("repair using assumptions")
            new_model = repair_assumptions(self.solver, self.lns_solver_config, fixed_atoms)

        self.logger.debug("objective value of new solution: %s", new_model.cost)
        self.logger.debug(
            "objective value of current incumbent solution: %s",
            self.current_model.cost,
        )
        self.logger.debug("objective value of current best solution: %s", self.best_model.cost)
        self.logger.debug(LINE)

        # TODO stats?
        if self.stats:
            if self.solver.result in {"UNSATISFIABLE", "OPTIMUM FOUND"}:
                new_ic = self.stats[-1].get("no_improvement_cutoff_count", 0)
            elif self.solver.result == "SATISFIABLE" and new_model.cost < self.best_model.cost:
                new_ic = 0
            else:
                new_ic = self.stats[-1].get("no_improvement_cutoff_count", 0) + 1
        else:
            new_ic = 0
        self.stats.append(
            {
                **{
                    "step": self.step_c,
                    "elapsed_time": self.timer.get_elapsed_time(),
                    "no_improvement_cutoff_count": new_ic,
                },
                **self.solver.stats,
            }
        )
        self.logger.debug("stats: %s", self.stats[-1])
        return new_model

    def post_repair(self) -> None:
        """
        Actions to perform after repairing the solution.
        """
        self._active_config = self._adaptive_strategy.update_config(
            self._active_config, self._config_catalog, self.stats, self
        )

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
        self.logger.debug("variability threshold: %s", self.options.accept_variability)
        cost = self.current_model.cost
        cost_new = self.new_model.cost
        threshold = cost[:-1]
        threshold.append(cost[-1] + math.ceil(int(abs(cost[-1]) * self.options.accept_improvement / 100)))
        self.logger.debug(LINE)
        self.logger.debug("cost_new: %s", cost_new)
        self.logger.debug("cost: %s", cost)
        self.logger.debug("cost threshold: %s", threshold)
        if vari >= self.options.accept_variability and cost_new < threshold:
            self.logger.debug("acceptable")
            return True
        self.logger.debug("unacceptable")
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
        if self.lns_solver_config.solve_limit is not None:
            self.lns_solver_config.solve_limit = increase_solve_limit(
                self.lns_solver_config.solve_limit,
                self.options.lns_solve_limit_increase_rate,
            )
        if self.lns_solver_config.time_limit is not None:
            self.lns_solver_config.time_limit = increase_time_limit(
                self.timer,
                self.options.time_limit,
                self.lns_solver_config.time_limit,
                self.options.lns_time_limit_increase_rate,
            )
        if self.lns_solver_config.cutoff is not None:
            self.lns_solver_config.cutoff = increase_cutoff(
                self.lns_solver_config.cutoff,
                self.options.lns_cutoff_threshold,
                self.options.lns_cutoff_increase_rate,
                self.timer,
                self.options.time_limit,
                self.stats[-1],
            )

        if self._iter_format == "":
            raise RuntimeError("pre_relax called before post_first_solution")
        if self._printout or self.step_c % self.options.status_interval == 0:
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
            self.logger.debug(
                f"repair with {len(fixed_atoms)} fixed atoms ({(len(self.current_model.shown) - len(fixed_atoms))/len(self.current_model.shown)*100:.2f}% relaxed)"
            )
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

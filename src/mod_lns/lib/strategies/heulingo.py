"""
Default strategy implementing classic LNS with weighted sum as optimization criteria and random relaxation.
"""

from __future__ import annotations

import math
import random
from argparse import ArgumentParser, Namespace, _SubParsersAction
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Optional

import clingo
from clingo.control import Control
from clingo.symbol import Function, Number, Symbol, SymbolType

from mod_lns import Timer, Model
from mod_lns.interfaces.solver import SolverConfig, SolverInterface
from mod_lns.interfaces.strategy import StrategyInterface
from mod_lns.lib.parser.heulingo_parser import get_parser
from mod_lns.lib.solvers import ClingoSolver
from mod_lns.lib.utils import clamp, get_unique_list

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage

UINT_MAX = 4294967295
LINE = "--------------------------------------------------------------------------------------"

# pylint: disable=too-many-lines


# pylint: disable=too-many-instance-attributes
@dataclass
class HeulingoConfig:
    """
    Configuration class for Heulingo strategy.

    :param log_level: Logging level, default: logging.WARNING.
    :type log_level: int
    :default log_level: 30
    :param solver: Solver to be used.
    :type solver: SolverInterface
    :default solver: ClingoSolver
    :param seed: Seed for random number generation.
    :type seed: int
    :default seed: None
    :param time_limit: Overall time limit for the LNS process.
    :type time_limit: int
    :default time_limit: None
    :param max_steps: Maximum number of steps for the LNS process.
    :type max_steps: int
    :default max_steps: None
    :param parallel_mode: Parallel mode for the solver.
    :type parallel_mode: str
    :default parallel_mode: None
    :param relax_rate: Rate of relaxation for the solver.
    :type relax_rate: float
    :default relax_rate: None
    :param minimize_variable: Variable to minimize in the optimization process.
    :type minimize_variable: Symbol
    :default minimize_variable: None
    :param falsify: Falsification weight, default: None.
    :type falsify: str
    :default falsify: None
    :param heulingo_configuration: Configuration for Heulingo strategy.
    :type heulingo_configuration: str
    :default heulingo_configuration: None
    :param solve_limit_increase_rate: Rate to increase the solve limit.
    :type solve_limit_increase_rate: float
    :default solve_limit_increase_rate: 0.01
    :param time_limit_increase_rate: Rate to increase the time limit.
    :type time_limit_increase_rate: float
    :default time_limit_increase_rate: 0.01
    :param acceptance_rate: Acceptance rate for the LNS process.
    :type acceptance_rate: float
    :default acceptance_rate: 0.0
    :param lns_configuration: Configuration for LNS solver.
    :type lns_configuration: str
    :default lns_configuration: None
    :param lns_opt_strategy: Optimization strategy for LNS solver.
    :type lns_opt_strategy: str
    :default lns_opt_strategy: None
    :param lns_opt_heuristic: Optimization heuristic for LNS solver.
    :type lns_opt_heuristic: str
    :default lns_opt_heuristic: None
    :param lns_restart_on_model: Whether to restart on model for LNS solver.
    :type lns_restart_on_model: bool
    :default lns_restart_on_model: None
    :param lns_heuristic: Heuristic for LNS solver.
    :type lns_heuristic: str
    :default lns_heuristic: "Domain"
    :param lns_opt_mode: Optimization mode for LNS solver.
    :type lns_opt_mode: dict[str, Optional[str]]
    :default lns_opt_mode: {"mode": None, "nf": None, "modifier": None}
    :param lns_solve_limit: Solve limit for LNS solver.
    :type lns_solve_limit: str
    :default lns_solve_limit: None
    :param lns_time_limit: Time limit for LNS solver.
    :type lns_time_limit: int
    :default lns_time_limit: None
    """

    # utils
    log_level: int = 30  # logging.WARNING

    # general configuration
    ## solver default has to be set manually in parser
    solver: SolverInterface = field(default_factory=ClingoSolver)
    seed: Optional[int] = None
    time_limit: Optional[int] = None
    max_steps: Optional[int] = None
    parallel_mode: Optional[str] = None
    clingo_args: Optional[str] = None

    minimize_variable: Optional[Symbol] = None
    falsify: Optional[str] = None

    # init solver configuration
    init_configuration: Optional[str] = None
    init_opt_strategy: Optional[str] = None
    init_opt_heuristic: Optional[str] = None
    init_restart_on_model: Optional[bool] = None
    init_heuristic: Optional[str] = None
    init_opt_mode: Optional[str] = None
    init_solve_limit: Optional[str] = "2500000,5000"
    init_time_limit: Optional[int] = None

    # lns configuration
    heulingo_configuration: Optional[str] = None
    solve_limit_increase_rate: float = 0.01
    time_limit_increase_rate: float = 0.01
    acceptance_rate: float = 0.0

    # lns solver configuration
    lns_configuration: Optional[str] = None
    lns_opt_strategy: Optional[str] = None
    lns_opt_heuristic: Optional[str] = None
    lns_restart_on_model: Optional[bool] = None
    lns_heuristic: Optional[str] = "Domain"
    ## lns_opt_mode default has to be set manually in parser
    lns_opt_mode: dict[str, Any] = field(
        default_factory=lambda: {"mode": None, "nf": None, "modifier": None}
    )
    lns_solve_limit: Optional[str] = None
    lns_time_limit: Optional[int] = None

    # lns_configuration_values
    lns_configuration_values: ClassVar[dict[str, dict[str, Any]]] = {
        "teaspoon": {
            "parallel_mode": None,
            "init_configuration": "jumpy",
            "init_opt_strategy": "usc,11",
            "init_solve_limit": "2500000,5000",
            "init_time_limit": None,
            "lns_configuration": "tweety",
            "lns_opt_strategy": "bb,0",
            "lns_opt_heuristic": "3",
            "lns_restart_on_model": True,
            "lns_opt_mode": None,
            "lns_solve_limit": "30000",
            "lns_time_limit": None,
        },
        "tsp": {
            "parallel_mode": None,
            "init_configuration": None,
            "init_opt_strategy": None,
            "init_solve_limit": "1210000",
            "init_time_limit": None,
            "lns_configuration": None,
            "lns_opt_strategy": None,
            "lns_opt_heuristic": None,
            "lns_restart_on_model": None,
            "lns_opt_mode": None,
            "lns_solve_limit": "800000",
            "lns_time_limit": None,
        },
        "sgp": {
            "parallel_mode": None,
            "init_configuration": None,
            "init_opt_strategy": None,
            "init_solve_limit": "500000",
            "init_time_limit": None,
            "lns_configuration": None,
            "lns_opt_strategy": None,
            "lns_opt_heuristic": None,
            "lns_restart_on_model": None,
            "lns_opt_mode": "opt,0,dynamic",
            "lns_solve_limit": "500000",
            "lns_time_limit": None,
        },
        "spg": {
            "parallel_mode": "4",
            "init_configuration": "many",
            "init_opt_strategy": None,
            "init_solve_limit": "300000",
            "init_time_limit": None,
            "lns_configuration": None,
            "lns_opt_strategy": None,
            "lns_opt_heuristic": None,
            "lns_restart_on_model": None,
            "lns_opt_mode": None,
            "lns_solve_limit": "6000",
            "lns_time_limit": None,
        },
        "wsc-medium": {
            "parallel_mode": None,
            "init_configuration": None,
            "init_opt_strategy": "usc,15",
            "init_solve_limit": "1000000",
            "init_time_limit": None,
            "lns_configuration": None,
            "lns_opt_strategy": "bb,0",
            "lns_opt_heuristic": None,
            "lns_restart_on_model": None,
            "lns_opt_mode": None,
            "lns_solve_limit": "40000",
            "lns_time_limit": None,
        },
        "wsc-large": {
            "parallel_mode": None,
            "init_configuration": None,
            "init_opt_strategy": "usc,15",
            "init_solve_limit": "30000000",
            "init_time_limit": None,
            "lns_configuration": None,
            "lns_opt_strategy": "bb,0",
            "lns_opt_heuristic": None,
            "lns_restart_on_model": None,
            "lns_opt_mode": None,
            "lns_solve_limit": "60000",
            "lns_time_limit": None,
        },
        "sd": {
            "parallel_mode": None,
            "init_configuration": "handy",
            "init_opt_strategy": "usc,3",
            "init_solve_limit": "900000",
            "init_time_limit": None,
            "lns_configuration": None,
            "lns_opt_strategy": None,
            "lns_opt_heuristic": None,
            "lns_restart_on_model": None,
            "lns_opt_mode": "opt,0,dynamic",
            "lns_solve_limit": "40000",
            "lns_time_limit": None,
        },
        "pup": {
            "parallel_mode": None,
            "init_configuration": "trendy",
            "init_opt_strategy": "usc,3",
            "init_solve_limit": "90000",
            "init_time_limit": None,
            "lns_configuration": None,
            "lns_opt_strategy": "bb",
            "lns_opt_heuristic": None,
            "lns_restart_on_model": None,
            "lns_opt_mode": None,
            "lns_solve_limit": "2000",
            "lns_time_limit": None,
        },
        "pmsp": {
            "parallel_mode": None,
            "init_configuration": None,
            "init_opt_strategy": None,
            "init_solve_limit": "15000000",
            "init_time_limit": 450,
            "lns_configuration": None,
            "lns_opt_strategy": None,
            "lns_opt_heuristic": None,
            "lns_restart_on_model": None,
            "lns_opt_mode": "opt,0,dynamic",
            "lns_solve_limit": "750000",
            "lns_time_limit": 30,
        },
        "tlsp": {
            "parallel_mode": None,
            "init_configuration": "tweety",
            "init_opt_strategy": "usc,3",
            "init_solve_limit": "600000",
            "init_time_limit": None,
            "lns_configuration": None,
            "lns_opt_strategy": "bb",
            "lns_opt_heuristic": None,
            "lns_restart_on_model": None,
            "lns_opt_mode": "opt,0,dynamic",
            "lns_solve_limit": "4000",
            "lns_time_limit": None,
        },
    }

    # pylint: disable=too-many-nested-blocks
    def apply_config(self) -> None:
        """
        Apply default configuration values.
        """
        if self.heulingo_configuration is not None:
            for key, value in self.lns_configuration_values[
                self.heulingo_configuration
            ].items():
                if isinstance(getattr(self, key), dict):
                    if key == "lns_opt_mode":
                        if all(
                            x is None for x in getattr(self, key).values()
                        ) and isinstance(value, str):
                            opt_mode: dict[str, Any] = {}
                            val = value.split(",")
                            opt_mode["mode"] = val[0]
                            if len(val) == 1:
                                opt_mode["nf"] = None
                                opt_mode["modifier"] = None
                            elif len(val) == 2:
                                opt_mode["nf"] = float(val[1])
                                opt_mode["modifier"] = "dynamic"
                            elif len(val) >= 3:
                                if val[-1] == "static":
                                    opt_mode["nf"] = ",".join(val[1:-1])
                                    opt_mode["modifier"] = "static"
                                else:
                                    opt_mode["nf"] = float(val[1])
                                    opt_mode["modifier"] = "dynamic"
                            setattr(self, key, opt_mode)
                    # if all(x is None for x in getattr(self, key).values()):
                    #     setattr(self, key, value)
                elif getattr(self, key) is None:
                    setattr(self, key, value)

    def get_init_solver_configuration(self) -> SolverConfig:
        """
        Get the initial solver configuration.

        :return: Initial Solver configuration.
        :rtype: SolverConfig
        """
        config = SolverConfig()
        config.configuration = self.init_configuration
        config.opt_strategy = self.init_opt_strategy
        config.opt_heuristic = self.init_opt_heuristic
        if self.init_restart_on_model is not None:
            config.restart_on_model = str(int(self.init_restart_on_model))
        config.heuristic = self.init_heuristic
        config.opt_mode = self.init_opt_mode
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
        config.configuration = self.lns_configuration
        config.opt_strategy = self.lns_opt_strategy
        config.opt_heuristic = self.lns_opt_heuristic
        if self.lns_restart_on_model is not None:
            config.restart_on_model = str(int(self.lns_restart_on_model))
        config.heuristic = self.lns_heuristic
        config.solve_limit = self.lns_solve_limit
        config.time_limit = self.lns_time_limit
        config.seed = self.seed
        return config


# pylint: disable=duplicate-code, too-many-instance-attributes
class Heulingo(StrategyInterface):
    """
    Classic LNS with weighted sum as optimization criteria and random relaxation.
    """

    def __init__(self) -> None:
        """
        Initialize the HeulingoLNS strategy.
        """
        super().__init__()
        self.__lnps_config: list[dict[str, Any]] = []
        self.prev_fixed_atoms: list[Symbol] = []
        self.config = HeulingoConfig()
        self.init_solver_config = SolverConfig()
        self.lns_solver_config = SolverConfig()
        self.__variability: bool = False
        self.__falsified: bool = False
        self.__false_weight = Function("inf")
        self.timer = Timer()

    def get_parser(
        self, subparsers: _SubParsersAction[ArgumentParser]
    ) -> ArgumentParser:
        """
        Get the argument parser for the Heulingo strategy.

        :param subparsers: Subparsers action
        :type subparsers: _SubParsersAction[ArgumentParser]
        """
        parser = get_parser(HeulingoConfig, subparsers)
        parser.set_defaults(strategy=self)
        return parser

    def _prep_values(self) -> None:
        """
        Prepare some values to avoid errors or unexpected behavior.
        """
        self.config.solve_limit_increase_rate = clamp(
            self.config.solve_limit_increase_rate, 0, 100
        )
        self.config.time_limit_increase_rate = clamp(
            self.config.time_limit_increase_rate, 0, 100
        )

    def parse_options(self, args: Namespace) -> dict[str, Any]:
        """
        Parse command line options.

        :param args: Command line arguments
        :type args: Namespace
        """
        rest = {}
        if args.heulingo_configuration is not None:
            self.config.heulingo_configuration = args.heulingo_configuration
            self.config.apply_config()
        for attr, value in args.__dict__.items():
            if value is not None:
                if hasattr(self.config, attr) and value is not None:
                    setattr(self.config, attr, value)
                else:
                    rest[attr] = value
        self.solver = self.config.solver
        self.log_level = self.config.log_level

        self._prep_values()

        return rest

    def pre_setup(self, lns_object: "LNS"):
        """
        Perform actions before solver setup.

        :param lns_object: LNS
        :type lns_object: mod_lns.LNS
        """
        if self.config.time_limit is not None:
            self.timer.start(self.config.time_limit)

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
                if lns_opt_mode["nf"] <= 0:
                    self.logger.warning(
                        "heulingo may finish without proving optimality because of 0 or less percent of iter-opt-mode"
                    )
                if lns_opt_mode["nf"] < self.config.acceptance_rate:
                    self.logger.warning(
                        "Rate of iter-opt-mode is less than rate of acceptance-rate"
                    )

        random.seed(self.config.seed)

        if self.config.falsify is not None:
            self.__falsified = True
            if self.config.falsify != "inf":
                self.__false_weight = Number(int(self.config.falsify))

    def setup_solver(self, lns_object: "LNS") -> None:
        """
        Setup the solver for LNS.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        """
        assert isinstance(self.solver, SolverInterface)
        if self.config.minimize_variable is not None:
            self.solver.minimize_variable = self.config.minimize_variable
        args = []
        if self.config.seed is not None:
            args.append(f"--seed={self.config.seed}")
        if self.config.parallel_mode is not None:
            args.append(f"--parallel-mode={self.config.parallel_mode}")
        if self.config.clingo_args is not None:
            args.extend(self.config.clingo_args.split(","))
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
                self.logger.debug("elapsed time: %d seconds", self.timer.get_elapsed_time())
                self.logger.debug(
                    "Time limit for solver reduced to %d seconds "
                    "to fit into overall time limit.",
                    solver_config.time_limit,
                )

    # pylint: disable=dangerous-default-value
    def get_first_solution(
        self,
        lns_object: "LNS",
    ) -> bool:
        """
        Find initial solution.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: Whether a solution was found or not
        :rtype: bool
        """
        assert isinstance(self.solver, SolverInterface)
        # deduct time used for grounding if needed
        self._update_time_limit(self.init_solver_config)
        lns_object.new_model = self.solver.solve(self.init_solver_config)
        if lns_object.new_model is None:
            return False
        lns_object.current_model = lns_object.new_model
        lns_object.best_model = lns_object.new_model
        return True

    def __calc_opt_bound(self, solver_config: SolverConfig, cost: list[int]) -> None:
        """
        Calculate bound for next step.

        :param solver_config: Solver configuration
        :type solver_config: SolverConfig
        :param cost: Current cost list
        :type cost: list[int]
        """
        if self.config.lns_opt_mode["modifier"] == "static":
            solver_config.opt_mode = (
                self.config.lns_opt_mode["mode"] + "," + self.config.lns_opt_mode["nf"]
            )
        elif self.config.lns_opt_mode["modifier"] == "dynamic":
            bounds = cost[:-1]
            bounds.append(
                math.ceil(
                    cost[-1] + abs(cost[-1]) * self.config.lns_opt_mode["nf"] / 100
                )
                - 1
            )
            solver_config.opt_mode = (
                self.config.lns_opt_mode["mode"]
                + ","
                + (",".join([str(i) for i in bounds]))
            )
        elif self.config.lns_opt_mode["mode"] is not None:
            solver_config.opt_mode = self.config.lns_opt_mode["mode"]

    def __load_lnps_config(self, ctl: Control, shown_atoms: list[Symbol]) -> None:
        """
        Load LNPS config from model.

        :param ctl: Clingo Control object
        :type ctl: Control
        :param shown_atoms: List of shown atoms
        :type shown_atoms: list[Symbol]
        """
        # _lnps_project/2
        # which atoms subject to lnps
        for x in ctl.symbolic_atoms.by_signature("_lnps_project", 2):
            args = x.symbol.arguments
            self.__lnps_config.append(
                {"predicate_name": args[0].name, "arity": args[1].number}
            )

        # by default select all shown
        if not self.__lnps_config:
            atom_dicts = []
            for atom in shown_atoms:
                atom_dicts.append(
                    {"predicate_name": atom.name, "arity": len(atom.arguments)}
                )
            self.__lnps_config = get_unique_list(atom_dicts)

        for i, _ in enumerate(self.__lnps_config):
            # _lnps_destroy/4
            for x in ctl.symbolic_atoms.by_signature("_lnps_destroy", 4):
                args = x.symbol.arguments
                if (args[0].name == self.__lnps_config[i]["predicate_name"]) and (
                    args[1].number == self.__lnps_config[i]["arity"]
                ):
                    self.__lnps_config[i].setdefault("mask", []).append(args[2].number)
                    self.__lnps_config[i].setdefault("pn", []).append(args[3])
            # _lnps_prioritize/4
            for x in ctl.symbolic_atoms.by_signature("_lnps_prioritize", 4):
                args = x.symbol.arguments
                if (args[0].name == self.__lnps_config[i]["predicate_name"]) and (
                    args[1].number == self.__lnps_config[i]["arity"]
                ):
                    self.__lnps_config[i]["weight"] = args[2]
                    self.__lnps_config[i]["modifier"] = args[3]

            self.__lnps_config[i].setdefault(
                "mask", [2 ** self.__lnps_config[i]["arity"] - 1]
            )
            self.__lnps_config[i].setdefault("pn", [Function("p", [Number(0)])])
            self.__lnps_config[i].setdefault("weight", Number(1))
            self.__lnps_config[i].setdefault("modifier", Function("true"))

        self.logger.debug(LINE)
        for conf in self.__lnps_config:
            self.logger.debug(
                "_lnps_project(%s,%d).", conf["predicate_name"], conf["arity"]
            )
            for i in range(len(conf["mask"])):
                self.logger.debug(
                    "_lnps_destroy(%s,%d,%d,%s).",
                    conf["predicate_name"],
                    conf["arity"],
                    conf["mask"][i],
                    conf["pn"][i],
                )
            self.logger.debug(
                "_lnps_prioritize(%s,%d,%s,%s).",
                conf["predicate_name"],
                conf["arity"],
                conf["weight"],
                conf["modifier"],
            )
        self.logger.debug("lnps_config: %s", self.__lnps_config)

    def __check_variability(self):
        """
        Check whether the LNPS configuration is variable.
        :return: True if variability is present, False otherwise
        :rtype: bool"""
        for conf in self.__lnps_config:
            if conf["weight"].type == SymbolType.Function:
                if conf["weight"].name == "inf":
                    return False
        if self.__falsified:
            if self.__false_weight.type == SymbolType.Function:
                if self.__false_weight.name == "inf":
                    return False
        return True

    def post_first_solution(self, lns_object):
        """
        Actions to perform after finding the first solution.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        """
        if not self.solver.finished:
            self.__calc_opt_bound(
                self.lns_solver_config,
                lns_object.current_model.cost,
            )

            self.solver.ground([("config", [])])
            self.__load_lnps_config(self.solver.control, lns_object.current_model.shown)

            self.logger.debug(LINE)
            rules = ""
            self.logger.debug("#program heuristic(t).")
            for c in self.__lnps_config:
                a = (
                    c["predicate_name"]
                    + "("
                    + ",".join(["X" + str(i) for i in range(c["arity"])])
                    + ")"
                )
                true_constraint = f":- not {a}, heuristic({a},inf,true,t)."
                false_constraint = f":- {a}, heuristic({a},inf,false,t)."
                heu_statement = (
                    f"#heuristic {a} : heuristic({a},W,M,t), W != inf. [W,M]"
                )
                self.logger.debug(true_constraint)
                self.logger.debug(false_constraint)
                self.logger.debug(heu_statement)
                rules += true_constraint + false_constraint + heu_statement
                if self.__falsified:
                    constraint = f":- {a}, not projected({a},t), __w(inf,t)."
                    heu_statement = f"#heuristic {a} : {a}, not projected({a},t), __w(W,t), W != inf. [W,false]"
                    self.logger.debug(constraint)
                    self.logger.debug(heu_statement)
                    rules += constraint + heu_statement
            self.solver.add("heuristic", ["t"], rules)

            self.__variability = self.__check_variability()

    def check_stop(self, lns_object: "LNS") -> bool:
        """
        Check whether to stop LNS.

        Stop if:
        max # of steps exceeded,
        overall time limit exceeded

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: Whether to stop LNS or not
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
        if self.solver.finished:
            stop = True
        return stop

    def pre_relax(self, lns_object) -> None:
        print(
            f"{self.timer.get_elapsed_time():.3f}s: "
            f"Iteration: {lns_object.step_c} || {lns_object.best_model.get_cost_str()}"
        )

    def __project(
        self, shown_atoms: list[Symbol], conf: dict[str, Any]
    ) -> list[Symbol]:
        """
        Project atoms based on the configuration.

        :param shown_atoms: List of shown atoms
        :type shown_atoms: list[Symbol]
        :param conf: Configuration dictionary
        :type conf: dict
        :return: List of projected atoms
        :rtype: list[Symbol]
        """
        projected_atoms = []
        for atom in shown_atoms:
            if atom.match(conf["predicate_name"], conf["arity"]):
                projected_atoms.append(atom)

        for a in projected_atoms:
            self.logger.debug(
                "atom projected by _lnps_project(%s,%d): %s",
                conf["predicate_name"],
                conf["arity"],
                a,
            )
        self.logger.debug(LINE)

        return projected_atoms

    # pylint: disable=too-many-branches
    def __filter(
        self, atoms: list[Symbol], arity: int, mask: int, pn: Symbol
    ) -> list[Symbol]:
        """
        Filter atoms based on arity, mask, and pn.

        :param atoms: List of atoms
        :type atoms: list[Symbol]
        :param arity: Arity of the predicate
        :type arity: int
        :param mask: Bitmask for filtering
        :type mask: int
        :param pn: Symbol indicating number or percentage
        :type pn: Symbol
        :return: Filtered list of atoms
        :rtype: list[Symbol]
        """
        if mask == 0:
            return []
        bit_mask = list(format(mask, "0" + str(arity) + "b"))
        args_list = []
        for a in atoms:
            args = []
            for i in range(arity):
                if int(bit_mask[i]):
                    args.append(a.arguments[i])
            args_list.append(args)
        unique_args_list = get_unique_list(args_list)

        for a in unique_args_list:
            self.logger.debug(
                "arguments filtered by %d(%s): %s",
                mask,
                "".join(bit_mask),
                ",".join([str(v) for v in a]),
            )
        self.logger.debug(LINE)

        # absolute number of arguments
        num = 0
        if pn.name == "n":
            num = min(len(unique_args_list), abs(pn.arguments[0].number))
        # relative number of arguments
        elif pn.name == "p":
            num = round(len(unique_args_list) * abs(pn.arguments[0].number) / 100)
        selected_args_list = random.sample(unique_args_list, num)

        for a in selected_args_list:
            self.logger.debug(
                "selected arguments (%s): %s", pn, ",".join([str(v) for v in a])
            )
        self.logger.debug(LINE)

        filtered_atoms = []
        for a in atoms:
            args = []
            for i in range(arity):
                if int(bit_mask[i]):
                    args.append(a.arguments[i])
            for selected_args in selected_args_list:
                if args == selected_args:
                    filtered_atoms.append(a)

        for a in filtered_atoms:
            self.logger.debug("filtered atom (mask:%d, pn:%s): %s", mask, pn, a)
        self.logger.debug(LINE)

        return filtered_atoms

    def __destroy(
        self, shown_atoms: list[Symbol], conf: dict[str, Any]
    ) -> list[Symbol]:
        """
        Destroy a subset of atoms according to the configuration.

        :param shown_atoms: List of shown atoms
        :type shown_atoms: list[Symbol]
        :param conf: Configuration dictionary
        :type conf: dict
        :return: List of prioritized atoms
        :rtype: list[Symbol]
        """
        projected_atoms = []
        for symbol in shown_atoms:
            if symbol.match(conf["predicate_name"], conf["arity"]):
                projected_atoms.append(symbol)

        for a in projected_atoms:
            self.logger.debug(
                "atom projected by _lnps_project(%s,%d): %s",
                conf["predicate_name"],
                conf["arity"],
                a,
            )
        self.logger.debug(LINE)

        destroyed_atoms = []
        for i in range(len(conf["mask"])):
            filtered_atoms = self.__filter(
                projected_atoms, conf["arity"], conf["mask"][i], conf["pn"][i]
            )
            if conf["pn"][i].arguments[0].number >= 0:
                destroyed_atoms.extend(filtered_atoms)
            elif conf["pn"][i].arguments[0].number < 0:
                destroyed_atoms.extend(list(set(projected_atoms) - set(filtered_atoms)))

        for a in destroyed_atoms:
            destroy_operators = ", ".join(
                [
                    f"_lnps_destroy({conf['predicate_name']},{conf['arity']},{conf['mask'][i]},{conf['pn'][i]})"
                    for i in range(len(conf["mask"]))
                ]
            )
            self.logger.debug("atom destroyed by %s: %s", destroy_operators, a)
        self.logger.debug(LINE)

        prioritized_atoms = list(set(projected_atoms) - set(destroyed_atoms))

        for a in prioritized_atoms:
            self.logger.debug(
                "atom prioritized by _lnps_prioritize(%s,%d,%s,%s): %s",
                conf["predicate_name"],
                conf["arity"],
                conf["weight"],
                conf["modifier"],
                a,
            )
        self.logger.debug(LINE)

        return prioritized_atoms

    def __prioritize(
        self, targets: list[Symbol], conf: dict[str, Any], step: int
    ) -> list[Symbol]:
        """
        Prioritize atoms for heuristics.

        :param targets: List of target atoms
        :type targets: list[Symbol]
        :param conf: Configuration dictionary
        :type conf: dict
        :param step: Current LNS step
        :type step: int
        :return: List of heuristic atoms
        :rtype: list[Symbol]
        """
        heu_atoms: list[Symbol] = []
        for atom in targets:
            heu_atoms.append(
                Function(
                    "heuristic", [atom, conf["weight"], conf["modifier"], Number(step)]
                )
            )
        return heu_atoms

    def __generate_projected_atoms(
        self, atoms: list[Symbol], step: int
    ) -> list[Symbol]:
        """
        Generate projected atoms to be fixed.

        :param atoms: List of atoms to project
        :type atoms: list[Symbol]
        :param step: Current LNS step
        :type step: int
        :return: List of projected atoms
        :rtype: list[Symbol]
        """
        projected_atoms: list[Symbol] = []
        for atom in atoms:
            projected_atoms.append(Function("projected", [atom, Number(step)]))
        return projected_atoms

    def relax(
        self,
        lns_object: "LNS",
    ) -> list[Symbol]:
        """
        Relax portion of atoms given by the relax_parameters.
        Use random relaxation.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: List of heuristic atoms
        :rtype: list[Symbol]
        """
        fixed_atoms: list[Symbol] = []
        for conf in self.__lnps_config:
            projected = self.__project(lns_object.current_model.shown, conf)
            undestroyed = self.__destroy(lns_object.current_model.shown, conf)
            fixed_atoms.extend(self.__prioritize(undestroyed, conf, lns_object.step_c))
            if self.__falsified:
                fixed_atoms.extend(
                    self.__generate_projected_atoms(projected, lns_object.step_c)
                )
        if self.__falsified:
            fixed_atoms.append(
                Function("__w", [self.__false_weight, Number(lns_object.step_c)])
            )
        return fixed_atoms

    def repair(
        self,
        lns_object: "LNS",
        fixed_atoms: list[clingo.symbol.Symbol],
    ) -> Optional[Model]:
        """
        Repair solution.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :param fixed_atoms: Fixed atoms
        :type fixed_atoms: list[clingo.symbol.Symbol]
        :return: Repaired model
        :rtype: Optional[Model]
        """
        assert isinstance(self.solver, SolverInterface)
        for a in self.prev_fixed_atoms:
            self.solver.release_external(a)
            self.logger.debug("release external %s.", a)
        self.logger.debug(LINE)

        statements = ""
        for a in fixed_atoms:
            ext_statement = f"#external {a}."
            self.logger.debug(ext_statement)
            statements += ext_statement
        self.logger.debug(LINE)
        step = lns_object.step_c
        self.solver.add("external", ["t"], statements)
        self.solver.ground([("external", [Number(step)])])
        self.solver.ground([("heuristic", [Number(step)])])

        for a in fixed_atoms:
            self.solver.assign_external(a, True)
            self.logger.debug("assign external %s True.", a)
        self.logger.debug(LINE)
        self.prev_fixed_atoms = fixed_atoms.copy()

        self.logger.debug(
            "objective value of current incumbent solution: %s",
            lns_object.current_model.cost,
        )
        self.logger.debug(
            "objective value of current best solution: %s", lns_object.best_model.cost
        )
        self.logger.debug(LINE)

        self.lns_solver_config.variability = self.__variability

        self._update_time_limit(self.lns_solver_config)
        new_model = self.solver.solve(self.lns_solver_config)

        return new_model

    # pylint: disable=unused-argument
    def check_accept(
        self,
        lns_object: "LNS",
    ) -> bool:
        """
        Check whether new model is accepted.
        Accept if desired variability is achieved.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: Whether new model is accepted or not
        :rtype: bool
        """
        cost = lns_object.current_model.cost
        if lns_object.new_model is None:
            self.logger.debug("No new model found, not accepted.")
            return False
        cost_tmp = lns_object.new_model.cost
        threshold = cost[:-1]
        threshold.append(cost[-1] + abs(cost[-1]) * self.config.acceptance_rate / 100)
        self.logger.debug(LINE)
        self.logger.debug("cost_tmp: %s", cost_tmp)
        self.logger.debug("cost: %s", cost)
        self.logger.debug("threshold: %s", threshold)
        if cost_tmp < threshold:
            self.logger.debug("acceptable")
            return True
        self.logger.debug("unacceptable")
        return False

    def accepted(self, lns_object: "LNS") -> None:
        """
        Do something after new model is accepted and saved as the new current model.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: None
        """
        print("New model accepted")
        self.__calc_opt_bound(
            self.lns_solver_config,
            lns_object.current_model.cost,
        )

    def check_better(
        self,
        lns_object: "LNS",
    ) -> bool:
        """
        Check whether new model is better.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: Whether new model is better or not
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
        print(
            f"{self.timer.get_elapsed_time():.3f}s: "
            f"New best solution: {lns_object.best_model.get_cost_str()}"
        )

    def __increase_solve_limit(self, solver_config: SolverConfig) -> None:
        """
        Increase the solver's solve limit for the next iteration.

        :param solver_config: Solver configuration
        :type solver_config: SolverConfig
        :return: None
        """
        if solver_config.solve_limit is not None:
            increased_solve_limit = []
            for n in solver_config.solve_limit.split(","):
                if n == "umax":
                    increased_solve_limit.append(n)
                else:
                    new_n = math.ceil(
                        int(n) * self.config.solve_limit_increase_rate / 100 + int(n)
                    )
                    if new_n <= UINT_MAX:
                        increased_solve_limit.append(str(new_n))
                    else:
                        increased_solve_limit.append("umax")

            solver_config.solve_limit = ",".join(increased_solve_limit)

    def __increase_time_limit(self, solver_config: SolverConfig) -> None:
        """
        Increase the solver's time limit for the next iteration.

        :param solver_config: Solver configuration
        :type solver_config: SolverConfig
        :return: None
        """
        # dont increase time limit past overall time limit
        if self.config.time_limit is not None:
            if self.timer.remaining_time() < self.config.time_limit:
                return
        if solver_config.time_limit is not None:
            current_time_limit = solver_config.time_limit
            solver_config.time_limit = int(
                current_time_limit * self.config.time_limit_increase_rate / 100
                + current_time_limit
            )

    def pre_next_iteration(self, lns_object: "LNS") -> None:
        """
        Do something before next iteration.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: None
        """
        self.__increase_solve_limit(self.lns_solver_config)
        self.__increase_time_limit(self.lns_solver_config)

    def print_result(
        self,
        lns_object: "LNS",
    ) -> None:
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

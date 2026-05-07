"""
Heulingo, uses heuristics and a prioritized search supporting both random and
declarative relaxation via a configuration encoding.
"""

from __future__ import annotations

import math
import random
from argparse import ArgumentParser, _SubParsersAction
from dataclasses import dataclass, field, fields
from math import log10
from typing import TYPE_CHECKING, Any, ClassVar, Optional

import clingo
from clingo.control import Control
from clingo.symbol import Function, Number, Symbol, SymbolType

from mod_lns import UNSET, Model
from mod_lns.interfaces.solver import SolverConfig, SolverInterface
from mod_lns.interfaces.strategy import StrategyInterface
from mod_lns.lib.adaptive_strategies import AdaptiveStrategy, RouletteWheelStrategy
from mod_lns.lib.converter import AutoDestructionConverter, LastImprovementDestructionConverter
from mod_lns.lib.parser.adaptive_heulingo_parser import get_adap_heulingo_parser
from mod_lns.lib.parser.config_parser import ConfigParser
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.utils import clamp

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage

UINT_MAX = 4294967295
LINE = "--------------------------------------------------------------------------------------"

# pylint: disable=too-many-lines


# pylint: disable=too-many-instance-attributes
@dataclass
class AdaptiveHeulingoConfig:
    """
    Configuration class for Adaptive Heulingo strategy.

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
    # solver default has to be set manually in parser
    solver: SolverInterface = field(default_factory=ClingoSolver)
    seed: Optional[int] = UNSET
    # time limit for entire program
    time_limit: Optional[int] = UNSET
    max_steps: Optional[int] = UNSET
    status_interval: int = 5
    parallel_mode: Optional[str] = None
    clingo_args: Optional[str] = None

    minimize_variable: Optional[Symbol] = None
    # falsify: Optional[str] = None

    # init solver configuration
    init_configuration: Optional[str] = None
    init_opt_strategy: Optional[str] = None
    init_opt_heuristic: Optional[str] = None
    init_restart_on_model: Optional[bool] = None
    init_heuristic: Optional[str] = None
    init_opt_mode: Optional[str] = UNSET
    init_solve_limit: Optional[str] = UNSET
    # time limit for initial solution
    init_time_limit: Optional[int] = UNSET

    # heulingo configuration
    preset: Optional[str] = None
    acceptance_rate: float = 0.0

    # new alnps options
    context: Any = None
    lex_weight: int = 1000
    learning_rate: float = 0.5
    default_adaptive_strategy_name: str = "roulette"
    auto_converter: AutoDestructionConverter = field(default_factory=LastImprovementDestructionConverter)
    # time limit to find new model during initial solving
    init_cutoff: Optional[int] = UNSET
    # time limit to find new model during lns solving
    lns_cutoff: Optional[int] = UNSET
    cutoff_no_improv_threshold: Optional[int] = UNSET
    cutoff_time_increase_rate: Optional[int] = UNSET

    # lns solver configuration
    lns_configuration: Optional[str] = None
    lns_opt_strategy: Optional[str] = None
    lns_opt_heuristic: Optional[str] = None
    lns_restart_on_model: Optional[bool] = None
    lns_heuristic: Optional[str] = "Domain"
    # lns_opt_mode default has to be set manually in parser
    lns_opt_mode: dict[str, Any] = field(default_factory=lambda: {"mode": None, "nf": None, "modifier": None})
    lns_solve_limit: Optional[str] = UNSET
    lns_solve_limit_increase_rate: Optional[float] = UNSET  # 0.01
    # time limit for solver in each LNS step
    lns_time_limit: Optional[int] = UNSET
    lns_time_limit_increase_rate: Optional[float] = UNSET  # 0.01

    # lns_configuration_values
    # UNSET does not overwrite above default values when applying presets
    preset_values: ClassVar[dict[str, dict[str, Any]]] = {
        "basic": {
            "default_adaptive_strategy_name": "roulette",
            "learning_rate": 0.5,
            "auto_converter": field(default_factory=LastImprovementDestructionConverter),
            "lex_weight": 1000,
            "parallel_mode": None,
            "init_configuration": None,
            "init_opt_strategy": "usc,11",
            "init_solve_limit": "2500000,5000",
            "init_time_limit": None,
            "init_cutoff": 10,
            "lns_configuration": "tweety",
            "lns_opt_strategy": "bb,0",
            "lns_opt_heuristic": "3",
            "lns_restart_on_model": True,
            "lns_opt_mode": None,
            "lns_solve_limit": "30000",
            "solve_limit_increase_rate": 0.01,
            "lns_time_limit": None,
            "time_limit_increase_rate": 0.01,
            "lns_cutoff": 5,
            "cutoff_no_improv_threshold": 2,
            "cutoff_time_increase_rate": 5,
        },
    }

    @classmethod
    def get_supported_adaptive_strategy_names(cls) -> list[str]:
        """
        Return supported adaptive strategy names.
        """
        return ["roulette"]

    def build_adaptive_strategy(self, strategy_name: str) -> AdaptiveStrategy:
        """
        Build adaptive strategy instance from selected strategy name.
        """
        if strategy_name == "roulette":
            return RouletteWheelStrategy(self.learning_rate, self.lex_weight, self.auto_converter)
        raise ValueError(
            f"Unknown adaptive strategy '{strategy_name}'. "
            f"Supported strategies: {','.join(self.get_supported_adaptive_strategy_names())}"
        )

    # pylint: disable=too-many-nested-blocks, too-many-branches
    def apply_preset(self) -> None:
        """
        Apply preset configuration values.
        Dont override already set values.
        """
        if self.preset is not None:
            if self.preset in self.preset_values:
                for key, value in self.preset_values[self.preset].items():
                    if value is not UNSET:
                        if isinstance(getattr(self, key), dict):
                            if key == "lns_opt_mode":
                                if all(x is None for x in getattr(self, key).values()) and isinstance(value, str):
                                    opt_mode: dict[str, Any] = {}
                                    val = value.split(",")
                                    opt_mode["mode"] = val[0]
                                    if len(val) == 1:
                                        opt_mode["nf"] = None
                                        opt_mode["modifier"] = None
                                    elif len(val) == 2:
                                        opt_mode["nf"] = val[1]
                                        opt_mode["modifier"] = "dynamic"
                                    elif len(val) >= 3:
                                        if val[-1] == "static":
                                            opt_mode["nf"] = ",".join(val[1:-1])
                                            opt_mode["modifier"] = "static"
                                        else:
                                            opt_mode["nf"] = val[1]
                                            opt_mode["modifier"] = "dynamic"
                                    setattr(self, key, opt_mode)
                        elif hasattr(self, key):
                            setattr(self, key, value)
            else:
                raise ValueError(f"Unknown preset: {self.preset}")

    def prepare(self) -> None:
        """
        Prepare configuration by replacing UNSET with None
        and clamp some values to avoid errors or unexpected behavior.
        """
        for field_obj in fields(self):
            value = getattr(self, field_obj.name)
            if value is UNSET:
                setattr(self, field_obj.name, None)

        for field_name in (
            "lns_solve_limit_increase_rate",
            "lns_time_limit_increase_rate",
            "cutoff_time_increase_rate",
        ):
            limit = getattr(self, field_name)
            if limit is not None:
                setattr(self, field_name, clamp(limit, 0, 100))

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
        # heuristics for init solver are experimental
        config.heuristic = self.init_heuristic
        config.opt_mode = self.init_opt_mode
        config.solve_limit = self.init_solve_limit
        config.time_limit = self.init_time_limit
        config.cutoff = self.init_cutoff
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
        # opt_mode set during lns
        config.solve_limit = self.lns_solve_limit
        config.time_limit = self.lns_time_limit
        config.cutoff = self.lns_cutoff
        config.seed = self.seed
        return config


# pylint: disable=duplicate-code, too-many-instance-attributes
class AdaptiveHeulingo(StrategyInterface):
    """
    Classic LNS with weighted sum as optimization criteria and random relaxation.
    """

    def __init__(self) -> None:
        """
        Initialize the Adaptive HeulingoLNS strategy.
        """
        super().__init__()
        self._lnps_config: dict[str, Any] = {}
        self.prev_fixed_atoms: list[Symbol] = []
        self.config = AdaptiveHeulingoConfig()
        self._variability: bool = False
        self._falsified: bool = False
        self._false_weight = Function("inf")

        self._iter_format: str = ""
        self._printout: bool = False

        # ----
        self._adaptive_strategy: Optional[AdaptiveStrategy] = None
        self.context: str
        self.stats: list[dict[str, Any]] = []
        self._op_specs: dict[str, set[Symbol]] = {}

    def get_parser(self, subparsers: _SubParsersAction[ArgumentParser]) -> ArgumentParser:
        """
        Get the argument parser for the Adaptive Heulingo strategy.

        :param subparsers: Subparsers action
        :type subparsers: _SubParsersAction[ArgumentParser]
        """
        parser = get_adap_heulingo_parser(AdaptiveHeulingoConfig, subparsers)
        parser.set_defaults(strategy=self)
        return parser

    def parse_options(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Parse command line options.

        :param args: Command line arguments
        :type args: dict[str, Any]
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

    def _format_atoms(self, atoms: set[Symbol]) -> str:
        """
        Format set of atoms into sorted space-separated string.

        :param atoms: Set of atoms.
        :type atoms: set[Symbol]
        :return: Formatted atom string.
        :rtype: str
        """
        return " ".join([str(atom) for atom in sorted(atoms)])

    def pre_setup(self, lns_object: "LNS") -> None:
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

        lns_opt_mode = self.config.lns_opt_mode
        if lns_opt_mode["modifier"] is not None and lns_opt_mode["nf"] is not None:
            if lns_opt_mode["modifier"] == "dynamic":
                if float(lns_opt_mode["nf"]) <= 0:
                    self.logger.warning(
                        "heulingo may finish without proving optimality because of 0 or less percent of iter-opt-mode"
                    )
                if float(lns_opt_mode["nf"]) < self.config.acceptance_rate:
                    self.logger.warning("Rate of iter-opt-mode is less than rate of acceptance-rate")

        random.seed(self.config.seed)

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

    def post_setup(self, lns_object: "LNS") -> None:
        """
        Perform actions after solver setup.

        :param lns_object: LNS
        :type lns_object: mod_lns.LNS
        """
        assert isinstance(self.solver, SolverInterface)
        self.solver.ground(context=self.config.context)

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
                    "Time limit for solver reduced to %d seconds to fit into overall time limit.",
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
        # self.stats.append(self.solver.stats)
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
        if self.config.lns_opt_mode["modifier"] == "static":
            solver_config.opt_mode = self.config.lns_opt_mode["mode"] + "," + self.config.lns_opt_mode["nf"]
        elif self.config.lns_opt_mode["modifier"] == "dynamic":
            # TODO "lt" vs "leq"
            bounds = cost[:-1]
            bounds.append(math.ceil(cost[-1] + abs(cost[-1]) * float(self.config.lns_opt_mode["nf"]) / 100) - 1)
            solver_config.opt_mode = self.config.lns_opt_mode["mode"] + "," + (",".join([str(i) for i in bounds]))
        elif self.config.lns_opt_mode["mode"] is not None:
            solver_config.opt_mode = self.config.lns_opt_mode["mode"]

    # same as _has_variabilty()
    def _check_variability(self) -> bool:
        """
        Check whether the LNPS configuration is variable.
        :return: True if variability is present, False otherwise
        :rtype: bool
        """
        for prioritize_operator in self._lnps_config["prioritize_operators"]:
            if prioritize_operator["value"] == "inf":
                return False
        return True

    # TODO move to lib
    def _generate_heuristic_subprogram(self, alnps_config: dict[str, Any]) -> str:
        """
        Generate #heuristic statements for LNPS and integrity constraints for LNS
        from predicate signatures of projected atoms.

        :param alnps_config: ALNPS configuration dictionary.
        :type alnps_config: dict[str, Any]
        :return: #heuristic statements and integrity constraints.
        :rtype: str
        """
        heuristic_subprogram = ""
        # TODO maybe signatures into alnps dict
        for signature in set().union(*alnps_config["project_operators"].values()):
            name = signature[0]
            args = ",".join(["X" + str(i) for i in range(signature[1])])
            atom = f"{name}({args})"
            heuristic_subprogram += (
                f"#heuristic {atom} : __heuristic({atom},W,M,t), W != inf. [W,M]"
                f":- not {atom}, __heuristic({atom},inf,true,t)."
                f":- {atom}, __heuristic({atom},inf,false,t)."
            )
        # self.logger.debug(heuristic_subprogram)
        return heuristic_subprogram

    def post_first_solution(self, lns_object: "LNS") -> None:
        """
        Actions to perform after finding the first solution.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        """
        assert isinstance(self.solver, SolverInterface)
        assert isinstance(self.solver.control, Control)
        if not self.solver.finished:
            self._alnps_config = ConfigParser.parse_alnps_config(
                self.solver,
                self.config.get_supported_adaptive_strategy_names(),
                self.config.default_adaptive_strategy_name,
            )

            self._adaptive_strategy = self.config.build_adaptive_strategy(self._alnps_config["strategy"])
            self._lnps_config = self._adaptive_strategy.get_initial_config(self._alnps_config, lns_object.current_model)

            heuristics = self._generate_heuristic_subprogram(self._alnps_config)
            self.solver.add("heuristic", ["t"], heuristics)

        # prepare output format and print header
        time_digits = 5 + 1 + 3  # 5 digits + dot + 3 digits
        step_digits = 7
        cost_digits = max(len(lns_object.best_model.get_cost_str()), 4)
        if self.config.time_limit is not None:
            time_digits = max(int(log10(self.config.time_limit)) + 1 + 1 + 3, time_digits)
        if self.config.max_steps is not None:
            step_digits = max(int(log10(self.config.max_steps)) + 1, step_digits)

        header = f"{{0:>{time_digits}}} - {{1:>{step_digits}}}: {{2:>{cost_digits}}}"
        print(header.format("time in s", "step", "cost"))

        self._iter_format = f"{{0:>{time_digits}.3f}} - {{1:>{step_digits}}}: {{2:>{cost_digits}}}"
        print(
            self._iter_format.format(
                self.timer.get_elapsed_time(),
                "initial",
                lns_object.best_model.get_cost_str(),
            ),
            flush=True,
        )

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
        if self.solver.finished or self.solver.stop:
            stop = True
        return stop

    def pre_relax(self, lns_object: "LNS") -> None:
        """
        Actions to perform before relaxing the solution,
        at the start of a new iteration.

        :param lns_object: LNS object.
        :type lns_object: mod_lns.LNS
        """
        self._printout = False

        self._variability = self._check_variability()

        self._op_specs = ConfigParser.get_op_specs(lns_object.current_model)

    def _project(self, model: Model) -> set[Symbol]:
        """
        Project atoms based on the configuration.

        :return: Set of projected atoms
        :rtype: set[Symbol]
        """
        projected_atoms = set()

        for project_operator in self._lnps_config["project_operators"]:
            projected_atoms.update(ConfigParser.get_projected_atoms(model, self._op_specs, project_operator["name"]))

        self.logger.debug(f"{len(projected_atoms)} projected atoms: {self._format_atoms(projected_atoms)}")
        self.logger.debug(LINE)

        return projected_atoms

    def _destroy_atoms_if_term_selected(
        self, atom_term_pairs: list[dict[str, Symbol]], percent_or_number: dict[str, Any]
    ) -> set[Symbol]:
        """
        Randomly select terms by given percentage (or number)
        and return all atoms corresponding to selected terms.

        :param atom_term_pairs: Atoms subject to destruction and corresponding terms.
        :type atom_term_pairs: list[dict[str, Symbol]]
        :param percent_or_number: What percentage (or how many) terms are selected by.
        :type percent_or_number: dict[str, Any]
        :return: Destroyed atoms.
        :rtype: set[Symbol]
        """
        candidate_terms = set()
        for pair in atom_term_pairs:
            candidate_terms.add(pair["term"])

        destroyed_atoms = set()
        value = percent_or_number["value"]
        if percent_or_number["type"] == "p":
            num_selected_terms = round(len(candidate_terms) * value / 100)
        else:
            num_selected_terms = min(len(candidate_terms), value)
        selected_terms = random.sample(sorted(candidate_terms), num_selected_terms)
        for pair in atom_term_pairs:
            if pair["term"] in selected_terms:
                destroyed_atoms.add(pair["atom"])

        return destroyed_atoms

    def _is_tuple(self, term: Symbol) -> bool:
        """
        Check if given term is tuple.

        :param term: Term.
        :type term: Symbol
        :return: True if given term is tuple, False otherwise.
        :rtype: bool
        """
        return term.type == SymbolType.Function and not term.name

    # TODO subset of args selected
    def _destroy_atoms_if_all_args_selected(
        self, atom_term_pairs: list[dict[str, Symbol]], percents_or_numbers: list[dict[str, Any]]
    ) -> set[Symbol]:
        """
        Randomly select arguments by given percentages (or numbers)
        and return all atoms corresponding to terms whose all arguments are selected.

        :param atom_term_pairs: Atoms subject to destruction and corresponding terms.
        :type atom_term_pairs: list[dict[str, Symbol]]
        :param percents_or_numbers: What percentages (or how many) arguments are selected by.
        :type percents_or_numbers: list[dict[str, Any]]
        :return: Destroyed atoms.
        :rtype: set[Symbol]
        """
        candidate_args = [set() for i in range(len(percents_or_numbers))]
        selected_args = []

        for pair in atom_term_pairs:
            if self._is_tuple(pair["term"]) and len(pair["term"].arguments) == len(percents_or_numbers):
                for i, arg in enumerate(pair["term"].arguments):
                    candidate_args[i].add(arg)

        destroyed_atoms = set()
        for i, pn in enumerate(percents_or_numbers):
            value = pn["value"]
            if pn["type"] == "p":
                num_selected_args = round(len(candidate_args[i]) * value / 100)
            else:
                num_selected_args = min(len(candidate_args[i]), value)
            selected_args.append(random.sample(sorted(candidate_args[i]), num_selected_args))
        for pair in atom_term_pairs:
            if self._is_tuple(pair["term"]) and len(pair["term"].arguments) == len(percents_or_numbers):
                all_args_selected = all(arg in selected_args[i] for i, arg in enumerate(pair["term"].arguments))
                if all_args_selected:
                    destroyed_atoms.add(pair["atom"])

        return destroyed_atoms

    def _destroy(self, model: Model, projected_atoms: set[Symbol]) -> set[Symbol]:
        """
        Destroy a subset of atoms according to the configuration.

        :param model: Model containing the atoms.
        :type model: Model
        :param projected_atoms: Set of projected atoms
        :type projected_atoms: set[Symbol]
        :return: Set of prioritized atoms
        :rtype: set[Symbol]
        """
        destroyed_atoms: set[Symbol] = set()
        for destroy_operator in self._lnps_config["destroy_operators"]:
            atom_term_pairs = ConfigParser.get_atom_term_pairs(
                model, self._op_specs, projected_atoms, destroy_operator["name"]
            )
            if len(destroy_operator["percents_or_numbers"]) == 1:
                destroyed_atoms.update(
                    self._destroy_atoms_if_term_selected(atom_term_pairs, destroy_operator["percents_or_numbers"][0])
                )
            else:
                destroyed_atoms.update(
                    self._destroy_atoms_if_all_args_selected(atom_term_pairs, destroy_operator["percents_or_numbers"])
                )

        self.logger.debug(f"{len(destroyed_atoms)} destroyed atoms: {self._format_atoms(destroyed_atoms)}")
        self.logger.debug(LINE)

        prioritized_atoms = projected_atoms - destroyed_atoms

        self.logger.debug(f"{len(prioritized_atoms)} undestroyed atoms: {self._format_atoms(prioritized_atoms)}")
        self.logger.debug(LINE)

        return prioritized_atoms

    def _prioritize(self, model: Model, undestroyed_atoms: set[Symbol], step: int) -> set[Symbol]:
        """
        Prioritize atoms for heuristics.

        :param model: Model containing the atoms.
        :type model: Model
        :param undestroyed_atoms: Set of undestroyed atoms
        :type undestroyed_atoms: set[Symbol]
        :param step: Current LNS step
        :type step: int
        :return: Set of heuristic atoms
        :rtype: set[Symbol]
        """
        prioritized_atoms: set[Symbol] = set()
        heu_atoms: set[Symbol] = set()

        for prioritize_operator in self._lnps_config["prioritize_operators"]:
            targets = ConfigParser.get_heuristic_targets(
                model, self._op_specs, undestroyed_atoms, prioritize_operator["name"]
            )
            for target in targets:
                prioritized_atoms.add(target)
                if prioritize_operator["value"] == "inf":
                    value = Function("inf")
                else:
                    value = Number(prioritize_operator["value"])
                heu_atoms.add(
                    Function("__heuristic", [target, value, Function(prioritize_operator["modifier"]), Number(step)])
                )

        # without prioritize specification
        for atom in undestroyed_atoms - prioritized_atoms:
            heu_atoms.add(Function("__heuristic", [atom, Number(1), Function("true"), Number(step)]))

        return heu_atoms

    def _generate_projected_atoms(self, atoms: list[Symbol], step: int) -> list[Symbol]:
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

    # TODO relax components to lib as e.g. relax_config()
    def relax(
        self,
        lns_object: "LNS",
    ) -> set[Symbol]:
        """
        Relax portion of atoms as defined by LNPS configuration.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: Set of heuristic atoms
        :rtype: set[Symbol]
        """
        fixed_atoms: set[Symbol] = set()
        projected = self._project(lns_object.current_model)

        undestroyed = self._destroy(lns_object.current_model, projected)
        fixed_atoms.update(self._prioritize(lns_object.current_model, undestroyed, lns_object.step_c))
        return fixed_atoms

    # TODO relax components to lib as e.g. repair_config()/repair_heuristics
    def repair(
        self,
        lns_object: "LNS",
        fixed_atoms: set[clingo.symbol.Symbol],
    ) -> Optional[Model]:
        """
        Repair solution.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :param fixed_atoms: Fixed atoms
        :type fixed_atoms: set[clingo.symbol.Symbol]
        :return: Repaired model
        :rtype: Optional[Model]
        """
        assert isinstance(self.solver, SolverInterface)
        self.logger.debug("release externals:")
        for a in self.prev_fixed_atoms:
            self.solver.release_external(a)
            self.logger.debug("%s.", a)
        self.logger.debug(LINE)
        self.logger.debug("get new externals:")
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

        self.logger.debug("enable externals:")
        for a in fixed_atoms:
            self.solver.assign_external(a, True)
            self.logger.debug("%s.", a)
        self.logger.debug(LINE)
        self.prev_fixed_atoms = fixed_atoms.copy()

        self.logger.debug(
            "objective value of current incumbent solution: %s",
            lns_object.current_model.cost,
        )
        self.logger.debug("objective value of current best solution: %s", lns_object.best_model.cost)
        self.logger.debug(LINE)

        # TODO bound (constrained)
        self._calc_opt_bound(
            self.lns_solver_config,
            lns_object.current_model.cost,
        )

        self._update_time_limit(self.lns_solver_config)
        new_model = self.solver.solve(self.lns_solver_config)

        # TODO stats?
        if self.stats:
            if self.solver.result in {"UNSATISFIABLE", "OPTIMUM FOUND"}:
                new_ic = self.stats[-1].get("no_improvement_cutoff_count", 0)
            elif self.solver.result == "SATISFIABLE" and new_model.cost < lns_object.best_model.cost:
                new_ic = 0
            else:
                new_ic = self.stats[-1].get("no_improvement_cutoff_count", 0) + 1
        else:
            new_ic = 0
        self.stats.append(
            {
                **{"step": step, "elapsed_time": self.timer.get_elapsed_time(), "no_improvement_cutoff_count": new_ic},
                **self.solver.stats,
            }
        )
        self.logger.debug("stats: %s", self.stats[-1])

        return new_model

    def post_repair(self, lns_object):
        # update strategy
        assert isinstance(self._adaptive_strategy, AdaptiveStrategy)
        self._lnps_config = self._adaptive_strategy.update_config(
            self._lnps_config, self._alnps_config, self.stats, lns_object
        )

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
        cost_new = lns_object.new_model.cost
        threshold = cost[:-1]
        threshold.append(cost[-1] + int(abs(cost[-1]) * self.config.acceptance_rate / 100))
        self.logger.debug(LINE)
        self.logger.debug("cost_new: %s", cost_new)
        self.logger.debug("cost: %s", cost)
        self.logger.debug("threshold: %s", threshold)
        if cost_new < threshold:
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
        self.logger.debug("new model accepted")

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
        self.logger.debug("new best model")
        self._printout = True

    def _increase_solve_limit(self, solver_config: SolverConfig) -> None:
        """
        Increase the solver's solve limit for the next iteration.

        :param solver_config: Solver configuration
        :type solver_config: SolverConfig
        :return: None
        """
        if solver_config.solve_limit is not None and self.config.lns_solve_limit_increase_rate is not None:
            increased_solve_limit = []
            for n in solver_config.solve_limit.split(","):
                if n == "umax":
                    increased_solve_limit.append(n)
                else:
                    new_n = math.ceil(int(n) * self.config.lns_solve_limit_increase_rate / 100 + int(n))
                    if new_n <= UINT_MAX:
                        increased_solve_limit.append(str(new_n))
                    else:
                        increased_solve_limit.append("umax")

            solver_config.solve_limit = ",".join(increased_solve_limit)

    def _increase_time_limit(self, solver_config: SolverConfig) -> None:
        """
        Increase the solver's time limit for the next iteration.

        :param solver_config: Solver configuration
        :type solver_config: SolverConfig
        :return: None
        """
        if solver_config.time_limit is None:
            return
        # dont increase time limit past overall time limit
        if self.config.time_limit is not None:
            if self.timer.remaining_time() < solver_config.time_limit:
                return
        if self.config.lns_time_limit_increase_rate is not None:
            current_time_limit = solver_config.time_limit
            solver_config.time_limit = math.ceil(
                current_time_limit * self.config.lns_time_limit_increase_rate / 100 + current_time_limit
            )

    def _increase_cutoff(self, solver_config: SolverConfig) -> None:
        """
        Update the solver's cutoff for the next iteration.

        :param solver_config: Solver configuration
        :type solver_config: SolverConfig
        :return: None
        """
        if solver_config.cutoff is None:
            return
        # dont increase time limit past overall time limit
        if self.config.time_limit is not None:
            if self.timer.remaining_time() < solver_config.cutoff:
                return
        if self.config.cutoff_no_improv_threshold is not None and self.config.cutoff_time_increase_rate is not None:
            if (
                self.stats[-1].get("no_improvement_cutoff_count", 0) != 0
                and self.stats[-1].get("no_improvement_cutoff_count", 0) % self.config.cutoff_no_improv_threshold == 0
            ):
                current_cutoff = solver_config.cutoff
                solver_config.cutoff = math.ceil(
                    current_cutoff * self.config.cutoff_time_increase_rate / 100 + current_cutoff
                )

    def pre_next_iteration(self, lns_object: "LNS") -> None:
        """
        Do something before next iteration.

        :param lns_object: LNS object
        :type lns_object: mod_lns.LNS
        :return: None
        """
        self._increase_solve_limit(self.lns_solver_config)
        self._increase_time_limit(self.lns_solver_config)
        self._increase_cutoff(self.lns_solver_config)

        if self._iter_format == "":
            raise RuntimeError("output format not set, cannot print iteration info")
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

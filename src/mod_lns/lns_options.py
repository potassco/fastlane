"""
Class containing all LNS options and their default values, as well as methods for applying presets and overrides.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from logging import Logger
from typing import Any, ClassVar, Optional, TypeVar

from clingo import Symbol

from mod_lns import UNSET
from mod_lns.interfaces.adaptive_strategy import AdaptiveStrategy
from mod_lns.interfaces.auto_destruction_converter import AutoDestructionConverter
from mod_lns.interfaces.solver import Solver, SolverConfig
from mod_lns.lib.adaptive_strategies.roulette_wheel import RouletteWheelStrategy
from mod_lns.lib.adaptive_strategies.static import StaticStrategy
from mod_lns.lib.auto_destruction_converters.last_improv import LastImprovementDestructionConverter
from mod_lns.lib.solvers.clingo_solver import ClingoSolver

LINE = "--------------------------------------------------------------------------------------"

T = TypeVar("T", float, int)


def clamp(value: T, min_value: int, max_value: int) -> T:
    """
    Clamp a value between a minimum and maximum value.

    :param value: Value to clamp.
    :param min_value: Minimum value.
    :param max_value: Maximum value.
    :return: Clamped value.
    """
    return max(min_value, min(max_value, value))


# pylint: disable=too-many-instance-attributes
@dataclass(kw_only=True)
class LNSOptions:
    """
    Configuration for LNS.

    :param log_level: Logging level.
    :default log_level: 30
    :param solver: Solver to use.
    :default solver: ClingoSolver()
    :param seed: Random seed.
    :default seed: None
    :param time_limit: Time limit for entire program.
    :default time_limit: None
    :param max_steps: Maximum number of steps for LNS.
    :default max_steps: None
    :param status_interval: Interval for status updates.
    :default status_interval: 50
    :param parallel_mode: Parallel mode for solving.
    :default parallel_mode: None
    :param clingo_args: Additional arguments for Clingo solver.
    :default clingo_args: None
    :param context: Context for grounding.
    :default context: None
    :param minimize_variable: Variable to minimize, used by clingo-dl.
    :default minimize_variable: None
    :param preset: Options preset to use as base.
    :default preset: None
    :param lex_weight: Weight used to convert lexicographic cost into integer cost for adaptive strategies.
    :default lex_weight: 1000
    :param learning_rate: Learning rate used to update weights for adaptive strategies.
    :default learning_rate: 0.5
    :param default_adaptive_strategy_name: Default adaptive strategy name.
    :default default_adaptive_strategy_name: "static"
    :param auto_converter: Converter for computing destruction percentages of auto-mode destroy operators.
    :default auto_converter: LastImprovementDestructionConverter()
    :param init_time_limit: Time limit for initial solution.
    :default init_time_limit: 20
    :param init_solve_limit: Solve limit for initial solution.
    :default init_solve_limit: None
    :param init_cutoff: Time limit to find new model during initial solving.
    :default init_cutoff: None
    :param init_configuration: Solver configuration for initial solving.
    :default init_configuration: None
    :param init_opt_strategy: Optimization strategy for initial solving.
    :default init_opt_strategy: None
    :param init_opt_heuristic: Optimization heuristic for initial solving.
    :default init_opt_heuristic: None
    :param init_restart_on_model: Restart on model for initial solving.
    :default init_restart_on_model: None
    :param init_opt_mode: Optimization mode for initial solving.
    :default init_opt_mode: None
    :param constrained: Whether to use constrained LNS,
    Short-hand for lns-opt-mode={"mode": "opt", "nf": 0, "modifier": "dynamic"}.
    :default constrained: False
    :param relaxation: Relaxation type and rate.
    :default relaxation: ("simple", 20)
    :param declarative: Whether to use declarative relaxation.
    Can cause issue when set directly, use relaxation attribute.
    :default declarative: False
    :param relax_rate: Relaxation rate for simple relaxation.
    Can cause issue when set directly, use relaxation attribute.
    :default relax_rate: 20
    :param fix: How to fix atoms during repair.
    :default fix: False
    :param accept_variability: Required variability for accepting new model in percent.
    :default accept_variability: 0
    :param accept_improvement: Required improvement for accepting new model in percent.
    :default accept_improvement: 0
    :param lns_time_limit: Time limit for solver in each LNS step.
    :default lns_time_limit: 20
    :param lns_solve_limit: Solve limit for solver in each LNS step.
    :default lns_solve_limit: None
    :param lns_cutoff: Time limit to find new model during LNS solving.
    :default lns_cutoff: None
    :param lns_time_limit_increase_rate: Time limit increase rate in percent.
    :default lns_time_limit_increase_rate: 0
    :param lns_solve_limit_increase_rate: Solve limit increase rate in percent.
    :default lns_solve_limit_increase_rate: 0
    :param lns_cutoff_threshold: Cutoff threshold for increasing cutoff.
    :default lns_cutoff_threshold: None
    :param lns_cutoff_increase_rate: Cutoff increase rate in percent.
    :default lns_cutoff_increase_rate: 0
    :param lns_configuration: Solver configuration for LNS solving.
    :default lns_configuration: None
    :param lns_opt_strategy: Optimization strategy for LNS solving.
    :default lns_opt_strategy: None
    :param lns_opt_heuristic: Optimization heuristic for LNS solving.
    :default lns_opt_heuristic: None
    :param lns_restart_on_model: Restart on model for LNS solving.
    :default lns_restart_on_model: None
    :param lns_heuristic: Heuristic to use in LNS solving.
    :default lns_heuristic: "Domain"
    :param lns_opt_mode: Optimization mode for LNS solving.
    :default lns_opt_mode: {"mode": None, "nf": None, "modifier": None}
    """

    # utils
    log_level: int = 30

    # general configuration
    # solver default has to be set manually in parser
    solver: Solver = field(default_factory=ClingoSolver)
    seed: Optional[int] = None
    # time limit for entire program
    time_limit: Optional[int] = None
    max_steps: Optional[int] = None

    status_interval: int = 50

    parallel_mode: Optional[str] = None
    clingo_args: Optional[str] = None
    context: Any = None

    # remove?
    minimize_variable: Optional[Symbol] = None
    # falsify: Optional[str] = None

    preset: Optional[str] = None

    # adaptive
    # combine into one option --strategy=[roulette[learning_rate,lex_weight],static], default static
    lex_weight: int = 1000
    learning_rate: float = 0.5
    default_adaptive_strategy_name: str = "static"
    # converter default has to be set manually in parser
    auto_converter: AutoDestructionConverter = field(default_factory=LastImprovementDestructionConverter)

    # init solver configuration
    # time limit for initial solution
    init_time_limit: Optional[int] = 20
    init_solve_limit: Optional[str] = None
    # time limit to find new model during initial solving
    init_cutoff: Optional[int] = None

    init_configuration: Optional[str] = None
    init_opt_strategy: Optional[str] = None
    init_opt_heuristic: Optional[str] = None
    init_restart_on_model: Optional[bool] = None
    # init_heuristic: Optional[str] = None
    init_opt_mode: Optional[str] = None

    # lns configuration
    constrained: bool = False  # covered by lns_opt_mode
    # set via --relaxation=[simple,[rate],declarative]
    relaxation: tuple[str, int] = ("simple", 20)
    declarative: bool = False
    relax_rate: int = 20
    fix: str = "assumptions"  # "assumptions", "heuristics"
    accept_variability: int = 0
    accept_improvement: int = 0

    # lns solver configuration
    # time limit for solver in each LNS step
    lns_time_limit: Optional[int] = 20
    lns_solve_limit: Optional[str] = None
    # time limit to find new model during lns solving
    lns_cutoff: Optional[int] = None

    lns_time_limit_increase_rate: int = 0
    lns_solve_limit_increase_rate: int = 0
    lns_cutoff_threshold: Optional[int] = None
    lns_cutoff_increase_rate: int = 0

    lns_configuration: Optional[str] = None
    lns_opt_strategy: Optional[str] = None
    lns_opt_heuristic: Optional[str] = None
    lns_restart_on_model: Optional[bool] = None
    lns_heuristic: Optional[str] = "Domain"
    # lns_opt_mode default has to be set manually in parser
    lns_opt_mode: dict[str, Optional[str]] = field(default_factory=lambda: {"mode": None, "nf": None, "modifier": None})

    # configuration values
    preset_values: ClassVar[dict[str, dict[str, Any]]] = {
        "basic-assumptions": {
            "relaxation": ("simple", 40),
            "init_time_limit": 20,
            "lns_time_limit": 20,
            "fix": "assumptions",
        },
        "auto-heuristics": {
            "relaxation": ("simple", "auto"),
            "init_time_limit": 20,
            "init_solve_limit": "2500000,5000",
            "lns_time_limit": 20,
            "lns_solve_limit": "2500000,5000",
            "fix": "heuristics",
        },
        "adaptive-heulingo": {
            "relaxation": ("declarative", 0),
            "fix": "heuristics",
            "default_adaptive_strategy_name": "roulette",
            "learning_rate": 0.5,
            "auto_converter": LastImprovementDestructionConverter(),
            "lex_weight": 1000,
            "lns_restart_on_model": False,
            "init_cutoff": 10,
            "lns_cutoff": 5,
            "lns_cutoff_threshold": 2,
            "lns_cutoff_increase_rate": 5,
            "lns_heuristic": "Domain",
        },
    }

    def _parse_lns_opt_mode_string(self, value: str) -> dict[str, Any]:
        """
        Parse string representation of lns_opt_mode.

        :param value: String representation.
        :return: Parsed opt mode.
        """
        opt_mode: dict[str, Any] = {}
        val = value.split(",")
        opt_mode["mode"] = val[0]
        if len(val) == 1:
            opt_mode["nf"] = None
            opt_mode["modifier"] = None
        elif len(val) == 2:
            opt_mode["nf"] = val[1]
            opt_mode["modifier"] = "dynamic"
        elif val[-1] == "static":
            opt_mode["nf"] = ",".join(val[1:-1])
            opt_mode["modifier"] = "static"
        else:
            opt_mode["nf"] = val[1]
            opt_mode["modifier"] = "dynamic"
        return opt_mode

    def apply_overrides(self, overrides: dict[str, Any]) -> None:
        """
        Apply overrides to this config.

        UNSET values are ignored, all other values (including None) are applied.

        :param overrides: Candidate override values.
        """
        for key, value in overrides.items():
            if value is UNSET or not hasattr(self, key):
                continue
            if key == "lns_opt_mode" and isinstance(value, str):
                setattr(self, key, self._parse_lns_opt_mode_string(value))
            else:
                setattr(self, key, value)

    def apply_preset(self) -> None:
        """
        Apply preset configuration if specified.
        """
        if self.preset is not None:
            if self.preset in self.preset_values:
                self.apply_overrides(self.preset_values[self.preset])
            else:
                raise ValueError(f"Unknown preset: {self.preset}")

    @classmethod
    def get_supported_adaptive_strategy_names(cls) -> list[str]:
        """
        Return supported adaptive strategy names.
        """
        return ["roulette", "static"]

    # name -> strat object, init strat with params later (setup())
    def build_adaptive_strategy(self, strategy_name: str, logger: Logger) -> AdaptiveStrategy:
        """
        Build adaptive strategy instance from selected strategy name.
        """
        if strategy_name == "roulette":
            return RouletteWheelStrategy(logger, self.learning_rate, self.lex_weight, self.auto_converter)
        if strategy_name == "static":
            return StaticStrategy(self.auto_converter)
        raise ValueError(
            f"Unknown adaptive strategy '{strategy_name}'. "
            f"Supported strategies: {','.join(self.get_supported_adaptive_strategy_names())}"
        )

    def prepare(self) -> None:
        """
        Prepare configuration by replacing UNSET with None
        and resolving any other parameters.
        """
        for field_obj in fields(self):
            value = getattr(self, field_obj.name)
            if value is UNSET:
                setattr(self, field_obj.name, None)
        self.declarative = self.relaxation[0] == "declarative"
        self.relax_rate = self.relaxation[1] if isinstance(self.relaxation[1], int) else -1
        if self.constrained and self.lns_opt_mode["mode"] is None:
            self.lns_opt_mode["mode"] = "opt"
            self.lns_opt_mode["modifier"] = "dynamic"
            self.lns_opt_mode["nf"] = "0"
        self.lns_solve_limit_increase_rate = clamp(self.lns_solve_limit_increase_rate, 0, 100)
        self.lns_time_limit_increase_rate = clamp(self.lns_time_limit_increase_rate, 0, 100)

    def get_init_solver_configuration(self) -> SolverConfig:
        """
        Get the initial solver configuration.

        :return: Initial Solver configuration.
        """
        config = SolverConfig()
        config.solve_limit = self.init_solve_limit
        config.time_limit = self.init_time_limit
        config.seed = self.seed

        config.configuration = self.init_configuration
        config.opt_strategy = self.init_opt_strategy
        config.opt_heuristic = self.init_opt_heuristic
        if self.init_restart_on_model is not None:
            config.restart_on_model = str(int(self.init_restart_on_model))
        # heuristics for init solver are experimental
        # config.heuristic = self.init_heuristic
        config.opt_mode = self.init_opt_mode
        return config

    def get_lns_solver_configuration(self) -> SolverConfig:
        """
        Get the LNS solver configuration.

        :return: LNS solver configuration.
        """
        config = SolverConfig()
        config.solve_limit = self.lns_solve_limit
        config.time_limit = self.lns_time_limit
        config.seed = self.seed

        config.configuration = self.lns_configuration
        config.opt_strategy = self.lns_opt_strategy
        config.opt_heuristic = self.lns_opt_heuristic
        if self.lns_restart_on_model is not None:
            config.restart_on_model = str(int(self.lns_restart_on_model))
        if self.fix == "heuristics":
            config.heuristic = self.lns_heuristic
        # opt_mode set during lns
        return config

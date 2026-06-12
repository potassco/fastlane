"""
Class containing all LNS options and their default values, as well as methods for applying presets and overrides.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, ClassVar, Optional

import clingo
from clingo import Symbol

from mod_lns import UNSET
from mod_lns.interfaces.adaptive_strategy import AdaptiveStrategy
from mod_lns.interfaces.auto_destruction_converter import AutoDestructionConverter
from mod_lns.interfaces.solver import Solver, SolverConfig
from mod_lns.lib.adaptive_strategies.roulette_wheel import RouletteWheelStrategy
from mod_lns.lib.adaptive_strategies.static import StaticStrategy
from mod_lns.lib.auto_destruction_converters.last_improv import LastImprovementDestructionConverter
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.utils import clamp

if TYPE_CHECKING:
    from mod_lns.lns import LNS  # nocoverage

LINE = "--------------------------------------------------------------------------------------"


# pylint: disable=too-many-instance-attributes
@dataclass
class LNSOptions:
    """
    Configuration for LNS.

    :param log_level: Logging level.
    :type log_level: int
    :param solver: Solver to use.
    :type solver: Solver
    :param seed: Random seed.
    :type seed: int
    :param time_limit: Time limit for each LNS iteration.
    :type time_limit: Optional[int]
    :param max_steps: Maximum number of steps for LNS.
    :type max_steps: Optional[int]
    :param relax_rate: Relaxation rate for LNS.
    :type relax_rate: int
    :param status_interval: Interval for status updates.
    :type status_interval: int
    :param preset: Preset configuration name.
    :type preset: Optional[str]
    :param init_time_limit: Time limit for the initial solver.
    :type init_time_limit: Optional[int]
    :param init_solve_limit: Solve limit for the initial solver.
    :type init_solve_limit: Optional[str]
    :param constrained: Whether to use constrained optimization.
    :type constrained: bool
    :param declarative: Whether to use declarative relaxation.
    :type declarative: bool
    :param accept_variability: Required variability for new solutions.
    :type accept_variability: int
    :param lns_time_limit: Time limit for LNS solver.
    :type lns_time_limit: Optional[int]
    :param lns_solve_limit: Solve limit for LNS solver.
    :type lns_solve_limit: Optional[str]
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
    clingo_args: Optional[list[str]] = None
    context: Any = None

    # remove?
    minimize_variable: Optional[Symbol] = None
    falsify: Optional[str] = None

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
    use_heuristics: bool = False
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
    lns_cutoff_increase_rate: Optional[int] = 0

    lns_configuration: Optional[str] = None
    lns_opt_strategy: Optional[str] = None
    lns_opt_heuristic: Optional[str] = None
    lns_restart_on_model: Optional[bool] = None
    lns_heuristic: Optional[str] = "Domain"
    # lns_opt_mode default has to be set manually in parser
    lns_opt_mode: dict[str, Any] = field(default_factory=lambda: {"mode": None, "nf": None, "modifier": None})

    # configuration values
    preset_values: ClassVar[dict[str, dict[str, Any]]] = {
        "basic_assumptions": {
            "relaxation": ("simple", 40),
            "init_time_limit": 20,
            "lns_time_limit": 20,
            "use_heuristics": False,
        },
        "auto_heuristics": {
            "relaxation": ("simple", "auto"),
            "init_time_limit": 20,
            "init_solve_limit": "2500000,5000",
            "lns_time_limit": 20,
            "lns_solve_limit": "2500000,5000",
            "use_heuristics": True,
        },
        "adaptive_heulingo": {
            "relaxation": ("declarative", 0),
            "use_heuristics": True,
            "default_adaptive_strategy_name": "roulette",
            "learning_rate": 0.5,
            "auto_converter": field(default_factory=LastImprovementDestructionConverter),
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
        :type value: str
        :return: Parsed opt mode.
        :rtype: dict[str, Any]
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
        :type overrides: dict[str, Any]
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
    def build_adaptive_strategy(self, strategy_name: str) -> AdaptiveStrategy:
        """
        Build adaptive strategy instance from selected strategy name.
        """
        if strategy_name == "roulette":
            return RouletteWheelStrategy(self.learning_rate, self.lex_weight, self.auto_converter)
        elif strategy_name == "static":
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
            self.lns_opt_mode["nf"] = 0
        self.lns_solve_limit_increase_rate = clamp(self.lns_solve_limit_increase_rate, 0, 100)
        self.lns_time_limit_increase_rate = clamp(self.lns_time_limit_increase_rate, 0, 100)

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
        :rtype: SolverConfig
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
        if self.use_heuristics:
            config.heuristic = self.lns_heuristic
        # opt_mode set during lns
        return config

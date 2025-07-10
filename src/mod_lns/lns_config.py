"""
Configuration class used for LNS framework.
"""

from __future__ import annotations

from typing import Any

from .interfaces.solver import SolverInterface
from .interfaces.strategy import StrategyInterface
from .lib.mods.solver_mods import enable_heuristics
from .lib.mods.strategy_mods import enable_constrained_approach, enable_declarative
from .lib.solvers.clingo_solver import ClingoSolver
from .lib.strategies.default_strategy import DefaultStrategy


# pylint: disable=too-few-public-methods, dangerous-default-value
class LNSConfig:
    """
    LNS configuration class.
    Defines base solver and strategy objects and modifies them
    according to the given LNS options.

    :param lns_options: LNS options.
    :type lns_options: dict[str, Any]
    :default lns_options: {}
    :param clingo_options: clingo options.
    :type clingo_options: list[str]
    :default clingo_options: []
    :param solver: Solver object used as base for LNS.
    :type solver: SolverInterface
    :default solver: ClingoSolver()
    :param strategy: Strategy object used as base for LNS.
    :type strategy: StrategyInterface
    :default strategy: DefaultStrategy()
    """

    def __init__(
        self,
        lns_options: dict[str, Any] = {},
        clingo_options: list[str] = [],
        solver: SolverInterface = ClingoSolver(),
        strategy: StrategyInterface = DefaultStrategy(),
    ):
        """
        Initialize lns config.
        """
        default_options = {
            "heuristics": False,
            "constrained": False,
            "declarative": False,
            "relax_rate": 0.2,
            "max_steps": "2000",
            "solve_time_limit": 20,
            "model_limit": 0,
            "overall_time_limit": 600,
        }

        self.lns_options = {**default_options, **lns_options}
        self.clingo_options = clingo_options

        self.solver = solver
        if self.lns_options["heuristics"]:
            self.solver = enable_heuristics(self.solver)

        self.strategy = strategy
        if self.lns_options["constrained"]:
            self.solver, self.strategy = enable_constrained_approach(
                self.solver, self.strategy
            )
        # rand-freq for classic approach to avoid getting stuck
        elif not any(o.startswith("--rand-freq") for o in self.clingo_options):
            self.clingo_options = self.clingo_options + ["--rand-freq=0.05"]

        if self.lns_options["declarative"]:
            self.strategy = enable_declarative(self.strategy)

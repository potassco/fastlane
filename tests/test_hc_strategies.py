"""
Test cases for hard constraint strategy classes.
"""

import time

from clingo.symbol import Function, Number, String

from large_neighbourhood_search import LNS
from large_neighbourhood_search.interfaces.solver import SolverInterface
from large_neighbourhood_search.interfaces.strategy import StrategyInterface
from large_neighbourhood_search.lib.solvers.clingo_solver import ClingoSolver
from large_neighbourhood_search.lib.strategies.hc_lexicographic_declarative import (
    HCLexiDecl,
)
from large_neighbourhood_search.lib.strategies.hc_lexicographic_rnd import HCLexiRnd
from large_neighbourhood_search.lib.strategies.hc_weighted_sum_rnd import (
    HCWeightedSumRnd,
)

from .test_classic_strategies import TestStrategyClWsRnd


class TestStrategyHcWsRnd(TestStrategyClWsRnd):
    """
    Test cases for HCWeightedSumRnd class.

    Remaining test cases inherited from TestStrategyClWsRnd.
    """

    def setUp(self) -> None:
        self.solver: SolverInterface = ClingoSolver()
        self.strategy: StrategyInterface = HCWeightedSumRnd()
        self.lns = LNS(["./tests/ref/golf.lp"], self.solver, self.strategy)

    def test_check_better(self):
        """
        Test better check.
        """
        self.assertTrue(self.strategy.check_better(self.lns))
        self.lns.models["new_model"]["cost"] = 8
        self.assertTrue(self.strategy.check_better(self.lns))
        self.lns.models["new_model"]["cost"] = 5
        self.assertTrue(self.strategy.check_better(self.lns))

    def test_update_grounding(self):
        """
        Test grounding update.
        """
        self.lns.models["best_model"]["cost"] = 2
        self.solver.setup(self.lns)
        self.assertIsNone(self.strategy.update_grounding(self.lns))


class TestStrategyHcLexiRnd(TestStrategyHcWsRnd):
    """
    Test cases for HCLexiRnd class.

    Remaining test cases inherited from TestStrategyHcWsRnd.
    """

    def setUp(self) -> None:
        self.solver = ClingoSolver()
        self.strategy = HCLexiRnd()
        self.lns = LNS(["./tests/ref/golf.lp"], self.solver, self.strategy)

    def test_calc_cost(self):
        """
        Test cost calculation using lexicographic optimization.
        """
        model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
                Function("plays", [Number(5), Number(1), Number(1)], True),
                Function("plays", [Number(9), Number(1), Number(1)], True),
            ],
            "true": [
                Function("meets", [Number(7), Number(8), Number(3)], True),
                Function("meets", [Number(7), Number(9), Number(3)], True),
                Function("meets", [Number(8), Number(9), Number(3)], True),
                Function(
                    "_lns_priority",
                    [
                        String("min"),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min"),
                        Function("", [Number(1), Number(2)], True),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min"),
                        Function("", [Number(3), Number(5)], True),
                        Number(2),
                    ],
                    True,
                ),
                Function(
                    "_lns_priority",
                    [
                        String("min2"),
                        Number(3),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min2"),
                        Function("", [Number(1), Number(2)], True),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_priority",
                    [
                        String("min3"),
                        Number(2),
                    ],
                    True,
                ),
                Function(
                    "_lns_penalty",
                    [
                        String("min3"),
                        Function("", [Number(3), Number(5)], True),
                        Number(2),
                    ],
                    True,
                ),
            ],
        }
        ref = {1: 3, 3: 1, 2: 2}
        self.assertDictEqual(self.strategy.calc_cost(model), ref)

    def test_check_stop(self):
        """
        Test check_stop.
        """
        self.lns.start_time = time.time()
        self.lns.models["best_model"]["cost"] = {2: 0, 1: 0}
        self.assertTrue(self.strategy.check_stop(self.lns))
        self.lns.models["best_model"]["cost"] = {2: 1, 1: 0}
        self.assertFalse(self.strategy.check_stop(self.lns))
        self.lns.set_params({"overall_time_limit": 0})
        self.assertTrue(self.strategy.check_stop(self.lns))
        self.lns.set_params({"overall_time_limit": 10000, "max_steps": 1})
        self.lns.step_c = 2
        self.assertTrue(self.strategy.check_stop(self.lns))
        self.lns.set_params({"max_steps": "-"})
        self.assertFalse(self.strategy.check_stop(self.lns))
        self.lns.set_params({"overall_time_limit": 0})
        self.assertTrue(self.strategy.check_stop(self.lns))

    def test_check_better(self):
        """
        Test better check.
        """
        self.lns.models["new_model"]["cost"] = {2: 1, 1: 1}
        self.lns.models["best_model"]["cost"] = {2: 1, 1: 2}
        self.assertTrue(self.strategy.check_better(self.lns))
        self.lns.models["new_model"]["cost"] = {2: 2, 1: 0}
        self.assertTrue(self.strategy.check_better(self.lns))
        self.lns.models["new_model"]["cost"] = {2: 1, 1: 4}
        self.assertTrue(self.strategy.check_better(self.lns))
        self.lns.models["new_model"]["cost"] = {2: 1, 1: 2}
        self.assertTrue(self.strategy.check_better(self.lns))

    def test_update_grounding(self):
        """
        Test grounding update.
        """
        self.lns.models["best_model"]["cost"] = {2: 2, 1: 0}
        self.solver.setup(self.lns)
        self.assertIsNone(self.strategy.update_grounding(self.lns))


class TestStrategyClLexiDecl(TestStrategyHcLexiRnd):
    """
    Test cases for HCLexiDecl class.

    All test cases inherited from TestStrategyHcLexiRnd.
    Relax_declarative tested in test_relaxation.py
    """

    def setUp(self) -> None:
        self.solver = ClingoSolver()
        self.strategy = HCLexiDecl()
        self.lns = LNS(["./tests/ref/golf.lp"], self.solver, self.strategy)

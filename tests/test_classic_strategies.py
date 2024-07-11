"""
Test cases for classic strategy classes.
"""
from unittest import TestCase
from large_neighbourhood_search.lib.solvers.clingo_solver import ClingoSolver
from large_neighbourhood_search.lib.strategies.classic_lexicographic_rnd import ClassicLexiRnd
from large_neighbourhood_search.lib.strategies.classic_lexicographic_declarative import ClassicLexiDecl
from large_neighbourhood_search.lib.strategies.classic_weighted_sum_rnd import ClassicWeightedSumRnd
from large_neighbourhood_search import LNS
import time

from clingo.symbol import Function, Number, String
class TestStrategyClWsRnd(TestCase):
    """
    Test cases for ClassicWeightedSumRnd class.
    """
    def setUp(self) -> None:
        self.solver = ClingoSolver()
        self.strategy = ClassicWeightedSumRnd()
        self.lns = LNS(["./tests/ref/golf.lp"], self.solver, self.strategy)

    def test_calc_cost(self):
        """
        Test cost calculation using weighted sum.
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
                        Number(2),
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
                    "_lns_penalty",
                    [
                        String("min2"),
                        Function("", [Number(3), Number(5)], True),
                        Number(2),
                    ],
                    True,
                ),
            ],
        }
        self.assertEqual(self.strategy.calc_cost(model), 6)

    def test_first_solution(self):
        """
        Test finding of first solution.
        """
        self.lns.set_seed(123)
        self.solver.setup(self.lns)
        self.assertTrue(
            self.strategy.first_solution(self.lns)
        )
        self.assertIsNotNone(self.lns.models["new_model"])
        self.assertEqual(type(self.lns.models["new_model"]), dict)
        self.assertIsNotNone(self.lns.models["current_model"])
        self.assertEqual(type(self.lns.models["current_model"]), dict)
        self.assertIsNotNone(self.lns.models["best_model"])
        self.assertEqual(type(self.lns.models["best_model"]), dict)

        self.lns.set_params({"files": ["./tests/ref/bad_encoding.lp"], "seed": 123})
        self.solver.setup(self.lns)
        self.assertFalse(
            self.strategy.first_solution(self.lns)
        )

    def test_check_stop(self):
        """
        Test check_stop.
        """
        self.lns._start_time = time.time()
        self.lns.models["best_model"]["cost"] = 0
        self.assertTrue(self.strategy.check_stop(self.lns))
        self.lns.models["best_model"]["cost"] = 1
        self.assertFalse(self.strategy.check_stop(self.lns))
        self.lns.set_params({"overall_time_limit": 0})
        self.assertTrue(self.strategy.check_stop(self.lns))
        self.lns.set_params({"overall_time_limit": 10000, "max_steps": 1})
        self.lns._step_c = 2
        self.assertTrue(self.strategy.check_stop(self.lns))

    def test_relax(self):
        """
        Test atom relaxation.

        Concrete relaxation methods tested in test_relaxation.py.
        """
        model = {
            "shown": [
                Function("plays", [Number(3), Number(1), Number(1)], True),
                Function("plays", [Number(5), Number(1), Number(1)], True),
                Function("plays", [Number(9), Number(1), Number(1)], True),
                Function("plays", [Number(1), Number(2), Number(1)], True),
            ],
            "true": [
                Function("_lns_select", [Number(1)], True),
                Function("_lns_select", [Number(2)], True),
                Function("_lns_select", [Number(3)], True),
                Function(
                    "_lns_fix",
                    [
                        Function("plays", [Number(1), Number(1), Number(3)], True),
                        Number(1),
                    ],
                    True,
                ),
                Function(
                    "_lns_fix",
                    [
                        Function("plays", [Number(2), Number(1), Number(3)], True),
                        Number(2),
                    ],
                    True,
                ),
                Function(
                    "_lns_fix",
                    [
                        Function("plays", [Number(3), Number(1), Number(1)], True),
                        Number(3),
                    ],
                    True,
                ),
            ],
        }
        self.assertIsNotNone(self.strategy.relax(model, {"relax_rate": 0.2}))

    def test_repair(self):
        """
        Test atom reparation.

        Concrete repair methods tested in test_solvers.py.
        """
        self.solver.setup(self.lns)
        self.solver.ground_base(self.lns)
        self.assertTrue(self.strategy.repair(self.lns,[]).satisfiable)
        
    def test_check_accept(self):
        """
        Test acceptance check.
        """
        self.assertTrue(self.strategy.check_accept(self.lns))

    def test_check_better(self):
        """
        Test better check.
        """
        self.lns.models["new_model"]["cost"] = 3
        self.lns.models["best_model"]["cost"] = 5
        self.assertTrue(
            self.strategy.check_better(self.lns)
        )
        self.lns.models["new_model"]["cost"] = 8
        self.assertFalse(
            self.strategy.check_better(self.lns)
        )
        self.lns.models["new_model"]["cost"] = 5
        self.assertFalse(
            self.strategy.check_better(self.lns)
        )

class TestStrategyClLexiRnd(TestStrategyClWsRnd):
    """
    Test cases for ClassicLexiRnd class.

    Remaining test cases inherited from TestStrategyClWsRnd.
    """
    def setUp(self) -> None:
        self.solver = ClingoSolver()
        self.strategy = ClassicLexiRnd()
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
        self.lns._start_time = time.time()
        self.lns.models["best_model"]["cost"] = {2:0, 1:0}
        self.assertTrue(self.strategy.check_stop(self.lns))
        self.lns.models["best_model"]["cost"] = {2:1, 1:0}
        self.assertFalse(self.strategy.check_stop(self.lns))
        self.lns.set_params({"overall_time_limit": 0})
        self.assertTrue(self.strategy.check_stop(self.lns))
        self.lns.set_params({"overall_time_limit": 10000, "max_steps": 1})
        self.lns._step_c = 2
        self.assertTrue(self.strategy.check_stop(self.lns))

    def test_check_better(self):
        """
        Test better check.
        """
        self.lns.models["new_model"]["cost"] = {2:1, 1:1}
        self.lns.models["best_model"]["cost"] = {2:1, 1:2}
        self.assertTrue(
            self.strategy.check_better(self.lns)
        )
        self.lns.models["new_model"]["cost"] = {2:2, 1:0}
        self.assertFalse(
            self.strategy.check_better(self.lns)
        )
        self.lns.models["new_model"]["cost"] = {2:1, 1:4}
        self.assertFalse(
            self.strategy.check_better(self.lns)
        )
        self.lns.models["new_model"]["cost"] = {2:1, 1:2}
        self.assertFalse(
            self.strategy.check_better(self.lns)
        )

class TestStrategyClLexiDecl(TestStrategyClLexiRnd):
    """
    Test cases for ClassicLexiDecl class.

    All test cases inherited from TestStrategyClLexiRnd.
    Relax_declarative tested in test_relaxation.py
    """
    def setUp(self) -> None:
        self.solver = ClingoSolver()
        self.strategy = ClassicLexiDecl()
        self.lns = LNS(["./tests/ref/golf.lp"], self.solver, self.strategy)

    

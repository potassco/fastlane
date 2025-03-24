"""
Test cases for DefaultStrategy classes.
"""

import time
from unittest import TestCase

from clingo.symbol import Function, Number, String

from mod_lns import LNS
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lns_config import LNSConfig
from mod_lns.utils.conversions import str_to_symbols


class TestDefaultStrategy(TestCase):
    """
    Test cases for DefaultStrategy class.
    """

    def setUp(self) -> None:
        self.strategy = DefaultStrategy()
        config = LNSConfig(strategy=self.strategy)
        self.lns = LNS(["./tests/ref/golf.lp"], config)

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
        self.assertDictEqual(self.strategy.calculate_cost(model), ref)

    def test_first_solution(self):
        """
        Test finding of first solution.
        """
        self.lns.set_seed(123)
        self.lns.solver.setup(self.lns)
        self.assertTrue(self.strategy.get_first_solution(self.lns))
        self.assertIsNotNone(self.lns.models["new_model"])
        self.assertEqual(type(self.lns.models["new_model"]), dict)
        self.assertIsNotNone(self.lns.models["current_model"])
        self.assertEqual(type(self.lns.models["current_model"]), dict)
        self.assertIsNotNone(self.lns.models["best_model"])
        self.assertEqual(type(self.lns.models["best_model"]), dict)

        self.lns.solver.setup(self.lns)
        self.assertTrue(
            self.strategy.get_first_solution(self.lns, str_to_symbols("meets(7,8,3)"))
        )
        self.assertIsNotNone(self.lns.models["new_model"])
        self.assertEqual(type(self.lns.models["new_model"]), dict)
        self.assertIsNotNone(self.lns.models["current_model"])
        self.assertEqual(type(self.lns.models["current_model"]), dict)
        self.assertIsNotNone(self.lns.models["best_model"])
        self.assertEqual(type(self.lns.models["best_model"]), dict)

        self.lns.set_parameters({"files": ["./tests/ref/bad_encoding.lp"], "seed": 123})
        self.lns.solver.setup(self.lns)
        self.assertFalse(self.strategy.get_first_solution(self.lns))

    def test_check_stop(self):
        """
        Test check_stop.
        """
        self.lns.start_time = time.time()
        self.lns.models["best_model"]["cost"] = {2: 1, 1: 0}
        self.assertFalse(self.strategy.check_stop(self.lns))
        self.lns.set_parameters({"overall_time_limit": 0})
        self.assertTrue(self.strategy.check_stop(self.lns))
        self.lns.set_parameters({"overall_time_limit": 10000, "max_steps": 1})
        self.lns.step_c = 2
        self.assertTrue(self.strategy.check_stop(self.lns))
        self.lns.set_parameters({"max_steps": "-"})
        self.assertFalse(self.strategy.check_stop(self.lns))
        self.lns.set_parameters({"overall_time_limit": 0})
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
        self.assertIsNotNone(
            self.strategy.relax(model, {"relax_rate": 0.2, "base_relax_rate": 0})
        )

    def test_repair(self):
        """
        Test atom reparation.

        Concrete repair methods tested in test_solvers.py.
        """
        self.lns.solver.setup(self.lns)
        self.lns.solver.ground_base(self.lns)
        self.assertTrue(self.strategy.repair(self.lns, []).satisfiable)

    def test_check_accept(self):
        """
        Test acceptance check.
        """
        self.lns.models["current_model"]["shown"] = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
            Function("plays", [Number(5), Number(1), Number(1)], True),
            Function("plays", [Number(9), Number(1), Number(1)], True),
            Function("plays", [Number(1), Number(2), Number(1)], True),
        ]
        self.lns.models["new_model"]["shown"] = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
            Function("plays", [Number(5), Number(1), Number(1)], True),
            Function("plays", [Number(9), Number(1), Number(1)], True),
            Function("plays", [Number(1), Number(2), Number(1)], True),
        ]
        self.assertTrue(self.strategy.check_accept(self.lns))
        self.lns.param_values["vari_accept"] = 0.4
        self.assertFalse(self.strategy.check_accept(self.lns))
        self.lns.models["new_model"]["shown"] = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
            Function("plays", [Number(5), Number(1), Number(1)], True),
            Function("plays", [Number(7), Number(1), Number(1)], True),
            Function("plays", [Number(8), Number(2), Number(1)], True),
        ]
        self.assertTrue(self.strategy.check_accept(self.lns))

    def test_check_better(self):
        """
        Test better check.
        """
        self.lns.models["new_model"]["cost"] = {2: 1, 1: 1}
        self.lns.models["best_model"]["cost"] = {2: 1, 1: 2}
        self.assertTrue(self.strategy.check_better(self.lns))
        self.lns.models["new_model"]["cost"] = {2: 2, 1: 0}
        self.assertFalse(self.strategy.check_better(self.lns))
        self.lns.models["new_model"]["cost"] = {2: 1, 1: 4}
        self.assertFalse(self.strategy.check_better(self.lns))
        self.lns.models["new_model"]["cost"] = {2: 1, 1: 2}
        self.assertFalse(self.strategy.check_better(self.lns))

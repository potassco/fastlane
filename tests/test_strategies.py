"""
Test cases for DefaultStrategy classes.
"""

import time
from unittest import TestCase

from clingo.symbol import Function, Number

from mod_lns import Model
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lns import LNS
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

    def test_first_solution(self):
        """
        Test finding of first solution.
        """
        self.lns.set_seed(123)
        self.lns.solver.setup(self.lns)
        self.assertTrue(self.strategy.get_first_solution(self.lns))
        self.assertIsInstance(self.lns.new_model, Model)
        self.assertIsInstance(self.lns.current_model, Model)
        self.assertIsInstance(self.lns.best_model, Model)

        self.lns.solver.setup(self.lns)
        self.assertTrue(
            self.strategy.get_first_solution(self.lns, str_to_symbols("meets(7,8,3)"))
        )
        self.assertIsInstance(self.lns.new_model, Model)
        self.assertIsInstance(self.lns.current_model, Model)
        self.assertIsInstance(self.lns.best_model, Model)

        self.lns.set_parameters({"files": ["./tests/ref/bad_encoding.lp"], "seed": 123})
        self.lns.solver.setup(self.lns)
        self.assertFalse(self.strategy.get_first_solution(self.lns))

    def test_check_stop(self):
        """
        Test check_stop.
        """
        self.lns.start_time = time.time()
        self.lns.best_model.cost = [1, 0]
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
        model = Model()
        model.shown = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
            Function("plays", [Number(5), Number(1), Number(1)], True),
            Function("plays", [Number(9), Number(1), Number(1)], True),
            Function("plays", [Number(1), Number(2), Number(1)], True),
        ]
        model.true = [
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
        ]
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
        self.lns.current_model.shown = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
            Function("plays", [Number(5), Number(1), Number(1)], True),
            Function("plays", [Number(9), Number(1), Number(1)], True),
            Function("plays", [Number(1), Number(2), Number(1)], True),
        ]
        self.lns.new_model.shown = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
            Function("plays", [Number(5), Number(1), Number(1)], True),
            Function("plays", [Number(9), Number(1), Number(1)], True),
            Function("plays", [Number(1), Number(2), Number(1)], True),
        ]
        self.assertTrue(self.strategy.check_accept(self.lns))
        self.lns.param_values["vari_accept"] = 0.4
        self.assertFalse(self.strategy.check_accept(self.lns))
        self.lns.new_model.shown = [
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
        self.lns.new_model.cost = [1, 1]
        self.lns.best_model.cost = [1, 2]
        self.assertTrue(self.strategy.check_better(self.lns))
        self.lns.new_model.cost = [2, 0]
        self.assertFalse(self.strategy.check_better(self.lns))
        self.lns.new_model.cost = [1, 4]
        self.assertFalse(self.strategy.check_better(self.lns))
        self.lns.new_model.cost = [1, 2]
        self.assertFalse(self.strategy.check_better(self.lns))

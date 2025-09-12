"""
Test cases for LNS class.
"""

import time
from logging import Logger
from unittest import TestCase

from clingo.symbol import Function, Number

from mod_lns import Model, Timer
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lns import LNS


class TestModel(TestCase):
    """
    Test cases for Model class.
    """

    def test_init(self):
        """
        Test initialization.
        """
        model = Model()
        self.assertEqual(model.shown, [])
        self.assertEqual(model.true, [])
        self.assertEqual(model.cost, [])
        self.assertEqual(model.assignments, [])
        self.assertFalse(model.opt)

    def test_get_cost_str(self):
        """
        Test get cost str.
        """
        model = Model()
        self.assertEqual(model.get_cost_str(), "")
        model.cost = [1]
        self.assertEqual(model.get_cost_str(), "1")
        model.cost = [4, 3, 2]
        self.assertEqual(model.get_cost_str(), "4 3 2")

    def test_print_model(self):
        """
        Test print model.
        """
        model = Model()
        model.shown = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
        ]
        model.true = [
            Function("meets", [Number(7), Number(8), Number(3)], True),
        ]
        model.assignments = [
            "test=42",
        ]
        model.cost = [2]
        ref_str = "Answer\nplays(3,1,1)\nAssignments:\ntest=42\nCost: 2\n"
        self.assertEqual(model.print_model(), ref_str)


class TestTimer(TestCase):
    """
    Test cases for Timer class.
    """

    def test_init(self):
        """
        Test initialization.
        """
        timer = Timer()
        self.assertFalse(timer._started)
        self.assertFalse(timer._ringing)
        self.assertEqual(timer._start_time, 0)
        self.assertIsNone(timer._time_limit)

    def test_start(self):
        """
        Test start method.
        """
        timer = Timer()
        timer.start(10)
        self.assertTrue(timer._started)
        self.assertFalse(timer.is_ringing)
        self.assertIsNotNone(timer._start_time)
        self.assertEqual(timer._time_limit, 10)

    def test_reset(self):
        """
        Test reset method.
        """
        timer = Timer()
        timer.start(0)
        self.assertTrue(timer._started)
        self.assertTrue(timer.is_ringing)
        timer.reset()
        self.assertFalse(timer._started)
        self.assertFalse(timer.is_ringing)
        self.assertEqual(timer._start_time, 0)
        self.assertIsNone(timer._time_limit)

    def test_remaining_time(self):
        """
        Test remaining_time method.
        """
        timer = Timer()
        timer.start(2)
        self.assertGreaterEqual(timer.remaining_time(), 0)
        self.assertLessEqual(timer.remaining_time(), 2)
        time.sleep(3)
        self.assertEqual(timer.remaining_time(), 0)

        timer.reset()
        timer.start(None)
        self.assertEqual(timer.remaining_time(), -1)

    def test_get_elapsed_time(self):
        """
        Test get_elapsed_time method.
        """
        timer = Timer()
        timer.start(10)
        time.sleep(1)
        self.assertGreaterEqual(timer.get_elapsed_time(), 1)
        self.assertLessEqual(timer.get_elapsed_time(), 2)

        timer.reset()
        self.assertEqual(timer.get_elapsed_time(), 0)

    def test_is_ringing(self):
        """
        Test is_ringing property.
        """
        timer = Timer()
        self.assertFalse(timer.is_ringing)

        timer.start(1)
        self.assertFalse(timer.is_ringing)
        time.sleep(2)
        self.assertTrue(timer.is_ringing)


class TestLNS(TestCase):
    """
    Test cases for LNS class.
    """

    def test_init(self):
        """
        Test LNS initialization.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        self.assertEqual(lns.files, ["./tests/ref/golf.lp"])
        self.assertIsInstance(lns.strategy, DefaultStrategy)
        self.assertIsInstance(lns.logger, Logger)
        self.assertEqual(lns.step_c, 0)
        self.assertIsInstance(lns.current_model, Model)
        self.assertIsInstance(lns.best_model, Model)
        self.assertIsNone(lns.new_model)

    # see integration tests for main() testing

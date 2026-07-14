"""
Test helper classes/functions for the LNS framework.
"""

import time
from io import StringIO
from unittest import TestCase, mock

from clingo.symbol import Function, Number

from mod_lns import Model, Timer, UnsetMarker

# pylint: disable=protected-access


class TestUnsetMarker(TestCase):
    """
    Test cases for UnsetMarker class.
    """

    def setUp(self):
        self.marker = UnsetMarker()

    def test_singleton(self):
        """
        Test that UnsetMarker is a singleton.
        """
        other_marker = UnsetMarker()
        self.assertIs(self.marker, other_marker)

    def test_str_representation(self):
        """
        Test string representation of UnsetMarker.
        """
        self.assertEqual(repr(self.marker), "UNSET")

    def test_bool_representation(self):
        """
        Test boolean representation of UnsetMarker.
        """
        self.assertFalse(bool(self.marker))


class TestModel(TestCase):
    """
    Test cases for Model class.
    """

    def test_init(self):
        """
        Test initialization.
        """
        model = Model()
        self.assertEqual(model.shown, set())
        self.assertEqual(model.true, set())
        self.assertEqual(model.cost, [])
        self.assertEqual(model.assignments, [])

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
        model.shown = {
            Function("plays", [Number(3), Number(1), Number(1)], True),
        }
        model.true = {
            Function("meets", [Number(7), Number(8), Number(3)], True),
        }
        model.assignments = [
            "test=42",
        ]
        model.cost = [2]
        with mock.patch("sys.stdout", new=StringIO()) as out:
            model.print_model()
            # fmt: off
            self.assertEqual(
                out.getvalue(),
                (
                    "Answer\n"
                    "plays(3,1,1)\n"
                    "Assignments:\n"
                    "test=42\n"
                    "Optimization: 2\n\n"
                ),
            )
            # fmt: on


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
        self.assertEqual(timer._time_limit, 0)

    def test_restart(self):
        """
        Test restart method.
        """
        timer = Timer()
        timer._time_limit = 5
        with mock.patch.object(timer, "reset") as mock_reset, mock.patch.object(timer, "start") as mock_start:
            timer.restart()
            mock_reset.assert_called_once()
            mock_start.assert_called_once_with(timer._time_limit)

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

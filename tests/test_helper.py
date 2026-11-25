"""
Test helper classes/functions for the LNS framework.
"""

from io import StringIO
from threading import Event
from unittest import TestCase, mock

from clingo.symbol import Function, Number

from fastlane import Model, ThreadedTimer, Timer, UnsetMarker

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
        with mock.patch("fastlane.time.time", side_effect=[100.0, 100.2, 101.2]):
            timer.start(1)
            self.assertEqual(timer.remaining_time(), 1)
            self.assertEqual(timer.remaining_time(), 0)

        timer.reset()
        timer.start(None)
        self.assertEqual(timer.remaining_time(), -1)

    def test_get_elapsed_time(self):
        """
        Test get_elapsed_time method.
        """
        timer = Timer()
        with mock.patch("fastlane.time.time", side_effect=[200.0, 201.4]):
            timer.start(10)
            self.assertAlmostEqual(timer.get_elapsed_time(), 1.4, places=6)

        timer.reset()
        self.assertEqual(timer.get_elapsed_time(), 0)

    def test_is_ringing(self):
        """
        Test is_ringing property.
        """
        timer = Timer()
        self.assertFalse(timer.is_ringing)
        with mock.patch("fastlane.time.time", side_effect=[300.0, 300.4, 301.0]):
            timer.start(1)
            self.assertFalse(timer.is_ringing)
            self.assertTrue(timer.is_ringing)


class TestThreadedTimer(TestCase):
    """
    Test cases for ThreadedTimer class.
    """

    def setUp(self):
        self.callback = mock.Mock()
        self.timer = ThreadedTimer(self.callback)

    def test_init(self):
        """
        Test the initial timer state without starting a worker.
        """
        self.assertIs(self.timer._on_timeout, self.callback)
        self.assertIsNone(self.timer._time_limit)
        self.assertIsNone(self.timer._start_time)
        self.assertIsNone(self.timer._deadline)
        self.assertFalse(self.timer._ringing)
        self.assertFalse(self.timer._stopped)
        self.assertIsNone(self.timer._thread)

    def test_start(self):
        """
        Test deadlines, disabled timers and reuse of the single worker.
        """
        self.timer._condition = mock.MagicMock()
        with (
            mock.patch("fastlane.time.monotonic", side_effect=[100, 101, 102]),
            mock.patch("fastlane.threading.Thread") as thread,
        ):
            for start_time, time_limit, armed, deadline in (
                (100, 5, True, 105),
                (101, 5, False, None),
                (102, None, True, None),
            ):
                with self.subTest(time_limit=time_limit, armed=armed):
                    self.timer._ringing = True
                    self.timer.start(time_limit, armed=armed)
                    self.assertEqual(self.timer._time_limit, time_limit)
                    self.assertEqual(self.timer._start_time, start_time)
                    self.assertEqual(self.timer._deadline, deadline)
                    self.assertFalse(self.timer.is_ringing)
            thread.assert_called_once_with(target=self.timer._run)
            thread.return_value.start.assert_called_once_with()
            self.assertIs(self.timer._thread, thread.return_value)
        self.assertEqual(self.timer._condition.notify.call_count, 3)

    def test_start_invalid(self):
        """
        Test rejecting negative timeouts and permanently stopped timers.
        """
        with mock.patch("fastlane.threading.Thread") as thread:
            with self.assertRaisesRegex(ValueError, "Timeout must be nonnegative or None"):
                self.timer.start(-1)
            self.timer._stopped = True
            with self.assertRaisesRegex(RuntimeError, "Cannot start a stopped timer"):
                self.timer.start(1)
            thread.assert_not_called()
        self.assertIsNone(self.timer._start_time)

    def test_restart(self):
        """
        Test restarting with the saved duration, a replacement or no limit.
        """
        self.timer._start_time = 100
        self.timer._time_limit = 5
        with mock.patch.object(self.timer, "start") as start:
            self.timer.restart()
            self.timer.restart(2)
            self.timer.restart(None)
            self.assertEqual(start.call_args_list, [mock.call(5), mock.call(2), mock.call(None)])

    def test_restart_not_started(self):
        """
        Test that a saved duration cannot be used before the first start.
        """
        with mock.patch.object(self.timer, "start") as start:
            with self.assertRaisesRegex(RuntimeError, "Timer has not been started"):
                self.timer.restart()
            start.assert_not_called()

    def test_get_elapsed_time(self):
        """
        Test elapsed time before and after a start using a monotonic clock.
        """
        with mock.patch("fastlane.time.monotonic", return_value=101.5) as clock:
            self.assertEqual(self.timer.get_elapsed_time(), 0)
            clock.assert_not_called()
            self.timer._start_time = 100
            self.assertEqual(self.timer.get_elapsed_time(), 1.5)
            clock.assert_called_once_with()

    def test_run(self):
        """
        Test waiting for an armed deadline and signalling expiration exactly once.
        """
        self.timer._condition = mock.MagicMock()

        def wait(*args):
            if not args:
                self.timer._deadline = 105

        self.timer._condition.wait.side_effect = wait
        self.callback.side_effect = lambda: setattr(self.timer, "_stopped", True)
        with mock.patch("fastlane.time.monotonic", side_effect=[100, 105]):
            self.timer._run()
        self.assertEqual(self.timer._condition.wait.call_args_list, [mock.call(), mock.call(5)])
        self.callback.assert_called_once_with()
        self.assertTrue(self.timer.is_ringing)
        self.assertIsNone(self.timer._deadline)

    def test_stop(self):
        """
        Test permanent shutdown and waking the waiting worker.
        """
        self.timer._condition = mock.MagicMock()
        self.timer.stop()
        self.assertTrue(self.timer._stopped)
        self.timer._condition.notify.assert_called_once_with()
        self.callback.assert_not_called()

    def test_join(self):
        """
        Test joining only a worker that has actually started.
        """
        self.timer.join()
        self.timer._thread = mock.Mock(ident=None)
        self.timer.join()
        self.timer._thread.join.assert_not_called()
        self.timer._thread.ident = 1
        self.timer.join()
        self.timer._thread.join.assert_called_once_with()

    def test_is_ringing(self):
        """
        Test exposing the synchronized expiration state.
        """
        self.assertFalse(self.timer.is_ringing)
        self.timer._ringing = True
        self.assertTrue(self.timer.is_ringing)

    def test_thread_restart_and_stop(self):
        """
        Test rearming and shutting down a real worker using events rather than sleeps.
        """
        first, second = Event(), Event()

        def on_timeout():
            event = first if not first.is_set() else second
            event.set()

        self.callback.side_effect = on_timeout
        self.timer.start(0, armed=False)
        worker = self.timer._thread
        try:
            self.assertFalse(self.timer.is_ringing)
            self.assertFalse(first.is_set())
            self.timer.restart()
            self.assertTrue(first.wait(timeout=2), "Restart did not arm the timer")
            self.assertTrue(self.timer.is_ringing)
            self.timer.restart(0)
            self.assertTrue(second.wait(timeout=2), "The worker did not handle the next deadline")
            self.assertIs(self.timer._thread, worker)
            self.assertEqual(self.callback.call_count, 2)
        finally:
            self.timer.stop()
            worker.join(timeout=2)
        self.assertFalse(worker.is_alive(), "Stop did not wake the timer worker")

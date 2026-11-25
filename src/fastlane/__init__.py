"""
Helper classes.
"""

import threading
import time
from typing import Any, Callable, ClassVar, Optional

from clingo import Symbol

LINE = "-" * 86


class UnsetMarker:
    """
    Singleton helper class to distinguish between unset and None.
    """

    instance: ClassVar[Optional["UnsetMarker"]] = None

    def __new__(cls) -> "UnsetMarker":
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "UNSET"


# ! assigned variables should support None as value
UNSET: Any = UnsetMarker()


class Model:
    """
    Simplified Model class

    :ivar shown: Set of shown atoms.
    :ivar true: Set of true atoms.
    :ivar cost: List of costs.
    :ivar assignments: List of assignments.
    """

    def __init__(self) -> None:
        self.shown: set[Symbol] = set()
        self.true: set[Symbol] = set()
        self.cost: list[int] = []
        self.assignments: list[str] = []

    def get_cost_str(self) -> str:
        """
        Get cost of model as string.
        :return: Cost as string.
        """
        cost = self.cost
        if len(cost) != 0:
            return " ".join([str(c) for c in cost])
        return ""

    def print_model(self) -> str:
        """
        Print model.

        :return: Printed string.
        """
        answer_string = " ".join([str(atom) for atom in self.shown])
        if len(self.assignments) != 0:
            answer_string += "\nAssignments:\n" + " ".join(self.assignments)
        s = "Answer\n" f"{answer_string}\n" f"Optimization: {self.get_cost_str()}\n"
        print(s)
        return s


class Timer:
    """
    Timer class for measuring time intervals.

    :ivar _started: Indicates if the timer has started.
    :ivar _ringing: Indicates if the timer is ringing (time limit reached).
    :ivar _start_time: The time when the timer was started.
    :ivar _time_limit: The time limit in seconds (None for no limit).
    """

    def __init__(self) -> None:
        """
        Initialize the timer.
        """
        self._started: bool = False
        self._ringing: bool = False
        self._start_time: float = 0.0
        self._time_limit: Optional[int] = None

    def start(self, time_limit: Optional[int]) -> None:
        """
        Start the timer with a specified time limit.
        None for no time limit.

        :param time_limit: Time limit in seconds.
        """
        self._started = True
        self._ringing = False
        self._start_time = time.time()
        self._time_limit = time_limit

    def reset(self) -> None:
        """
        Reset the timer.
        """
        self._started = False
        self._ringing = False
        self._start_time = 0.0

    def restart(self) -> None:
        """
        Restart the timer with the same time limit.
        """
        self.reset()
        self.start(self._time_limit)

    def remaining_time(self) -> int:
        """
        Get the remaining time before the timer rings.

        :return: Remaining time in seconds, -1 for infinite.
        """
        if self._time_limit is None:
            return -1
        elapsed_time = int(time.time() - self._start_time)
        return max(0, self._time_limit - elapsed_time)

    def get_elapsed_time(self) -> float:
        """
        Get the elapsed time since the timer started.

        :return: Elapsed time in seconds.
        """
        if not self._started:
            return 0.0
        return time.time() - self._start_time

    @property
    def is_ringing(self) -> bool:
        """
        Check if the timer is ringing (i.e., if the time limit has been reached).
        """
        if self._time_limit is None:
            return False
        if self._started and not self._ringing:
            elapsed_time = time.time() - self._start_time
            if elapsed_time >= self._time_limit:
                self._ringing = True
        return self._ringing


# pylint: disable=too-many-instance-attributes
class ThreadedTimer:
    """
    A resettable timer with one worker.
    stop() shuts it down permanently.

    :ivar _condition: threading.Condition for synchronizing access to the timer state.
    :ivar _on_timeout: Callback function to be called when the timer expires.
    :ivar _timeout: Timeout duration in seconds.
    :ivar _start_time: Time when the timer was started.
    :ivar _deadline: Absolute time when the timer will expire.
    :ivar _ringing: Boolean indicating if the timer has expired.
    :ivar _stopped: Boolean indicating if the timer has been stopped.
    :ivar _thread: Worker thread for the timer.
    """

    def __init__(self, on_timeout: Callable[[], None]) -> None:
        """
        Initialize the timer with the given timeout callback.

        :param on_timeout: Callback function to be called when the timer expires.
        """
        self._condition: threading.Condition = threading.Condition()
        self._on_timeout: Callable[[], None] = on_timeout
        self._time_limit: Optional[float] = None
        self._start_time: Optional[float] = None
        self._deadline: Optional[float] = None
        self._ringing: bool = False
        self._stopped: bool = False
        self._thread: Optional[threading.Thread] = None

    def start(self, time_limit: Optional[float], *, armed: bool = True) -> None:
        """
        Start the timer with the given timeout and armed status.
        None for no time limit.

        :param time_limit: Timeout duration in seconds.
        :param armed: Whether the timer should be armed immediately.
        """
        with self._condition:
            if self._stopped:
                raise RuntimeError("Cannot start a stopped timer")
            if time_limit is not None and time_limit < 0:
                raise ValueError("Timeout must be nonnegative or None")
            self._time_limit = time_limit
            self._start_time = time.monotonic()
            self._deadline = None if time_limit is None or not armed else self._start_time + time_limit
            self._ringing = False
            if self._thread is None:
                self._thread = threading.Thread(target=self._run)
                self._thread.start()
            self._condition.notify()

    def restart(self, time_limit: Optional[float] = UNSET) -> None:
        """
        Restart with the saved duration, a new duration, or None for no limit.

        :param time_limit: Timeout duration in seconds.
        """
        with self._condition:
            if time_limit is UNSET:
                if self._start_time is None:
                    raise RuntimeError("Timer has not been started")
                time_limit = self._time_limit
            self.start(time_limit)

    def get_elapsed_time(self) -> float:
        """
        Seconds since the latest start/restart, or 0.0 before starting.
        """
        with self._condition:
            if self._start_time is None:
                return 0.0
            return time.monotonic() - self._start_time

    def _run(self) -> None:
        """
        Timer thread main loop.
        Waits until the deadline is reached or the timer is stopped.
        """
        with self._condition:
            while not self._stopped:
                if self._deadline is None:
                    self._condition.wait()
                    continue
                remaining = self._deadline - time.monotonic()
                if remaining > 0:
                    self._condition.wait(remaining)
                    continue
                self._deadline = None
                self._ringing = True
                # serialize expiration with resets, only signal the watcher here.
                self._on_timeout()

    def stop(self) -> None:
        """
        Stop the timer thread.
        """
        with self._condition:
            self._stopped = True
            self._condition.notify()

    def join(self) -> None:
        """
        Wait for the timer thread to finish.
        """
        if self._thread is not None and self._thread.ident is not None:
            self._thread.join()

    @property
    def is_ringing(self) -> bool:
        """
        Check if the timer is currently ringing.
        """
        with self._condition:
            return self._ringing

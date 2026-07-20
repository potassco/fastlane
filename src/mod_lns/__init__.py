"""
Helper classes.
"""

import time
from typing import Any, ClassVar, Optional

from clingo import Symbol


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

    Attributes:
        shown (set[Symbol]): Set of shown atoms.
        true (set[Symbol]): Set of true atoms.
        cost (list[int]): List of costs.
        assignments (list[str]): List of assignments.
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

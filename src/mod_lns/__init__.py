"""
Helper classes.
"""

import time


class Model:
    "Simplified Model class"

    def __init__(self):
        self.shown = []
        self.true = []
        self.cost = []
        self.assignments = []
        self.opt = False

    def get_cost_str(self) -> str:
        """
        Get cost of model as string.
        :return: Cost as string.
        :rtype: str
        """
        cost = self.cost
        if len(cost) != 0:
            return " ".join([str(c) for c in cost])
        return ""

    def print_model(self) -> str:
        """
        Print model.

        :return: Printed string.
        :rtype: str
        """
        # print(self.string)
        answer_string = " ".join([str(atom) for atom in self.shown])
        if len(self.assignments) != 0:
            answer_string += "\nAssignments:\n" + " ".join(self.assignments)
        s = "Answer\n" f"{answer_string}\n" f"Cost: {self.get_cost_str()}\n"
        print(s)
        return s


class Timer:
    """
    Timer class for measuring time intervals.
    """

    _started: bool
    _ringing: bool
    _start_time: float
    _time_limit: int

    def __init__(self):
        """
        Initialize the timer.
        """
        self._started = False
        self._ringing = False

    def start(self, time_limit: int) -> None:
        """
        Start the timer with a specified time limit.

        :param time_limit: Time limit in seconds.
        :type time_limit: float
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

    def remaining_time(self) -> int:
        """
        Get the remaining time before the timer rings.

        :return: Remaining time in seconds.
        :rtype: int
        """
        if not self._started:
            return 0
        elapsed_time = int(time.time() - self._start_time)
        return max(0, self._time_limit - elapsed_time)

    def get_elapsed_time(self) -> float:
        """
        Get the elapsed time since the timer started.

        :return: Elapsed time in seconds.
        :rtype: int
        """
        if not self._started:
            return 0
        return time.time() - self._start_time

    @property
    def is_ringing(self) -> bool:
        """
        Check if the timer is ringing (i.e., if the time limit has been reached).
        """
        if self._started and not self._ringing:
            elapsed_time = time.time() - self._start_time
            if elapsed_time >= self._time_limit:
                self._ringing = True
        return self._ringing

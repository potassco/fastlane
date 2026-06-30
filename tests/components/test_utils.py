"""
Test cases for utility functions of the LNS framework.
"""

from unittest import TestCase, mock

from mod_lns import Timer
from mod_lns.lib.components.utils import (
    calculate_variability,
    get_unique_list,
    increase_cutoff,
    increase_solve_limit,
    increase_time_limit,
    update_time_limit,
)
from mod_lns.lns import LNS
from mod_lns.lns_options import LNSOptions


class TestUtils(TestCase):
    """
    Test cases for utility functions of the LNS framework.
    """

    def test_calculate_variability(self):
        """
        Test variability calculation.
        """
        l1 = {0, 1, 2, 3, 4, 5}
        l2 = {1, 3}
        self.assertEqual(calculate_variability(l1, l2), 0)
        l2 = {0, 2, 6, 7}
        self.assertEqual(calculate_variability(l1, l2), 50)
        self.assertEqual(calculate_variability(l2, l1), 50)

    def test_get_unique_list(self):
        """
        Test get_unique_list function.
        """
        l = [2, 1, 2, 2, 3, 1, 4, 5, 5]
        self.assertEqual(get_unique_list(l), [2, 1, 3, 4, 5])

    def test_update_time_limit(self):
        """
        Test the update_time_limit function.
        """
        lns_object = mock.Mock(spec=LNS)
        lns_object.timer = mock.Mock(spec=Timer)
        lns_object.options = mock.Mock(spec=LNSOptions)
        lns_object.logger = mock.Mock()
        solver_config = mock.Mock()

        solver_config.time_limit = 10
        lns_object.options.time_limit = None
        update_time_limit(lns_object, solver_config)
        self.assertEqual(solver_config.time_limit, 10)

        lns_object.options.time_limit = 40
        with mock.patch.object(lns_object.timer, "remaining_time", return_value=21):
            solver_config.time_limit = None
            update_time_limit(lns_object, solver_config)
            self.assertEqual(solver_config.time_limit, 21)

            solver_config.time_limit = 50
            update_time_limit(lns_object, solver_config)
            self.assertEqual(solver_config.time_limit, 21)

            solver_config.time_limit = 10
            update_time_limit(lns_object, solver_config)
            self.assertEqual(solver_config.time_limit, 10)

    def test_increase_solve_limit(self):
        """
        Test the increase_solve_limit function.
        """
        current_solve_limit = "1000,umax"

        # increase rate 0
        self.assertEqual(increase_solve_limit(current_solve_limit, 0), "1000,umax")
        # increase rate 20%, umax should remain unchanged
        self.assertEqual(increase_solve_limit(current_solve_limit, 20), "1200,umax")
        # increase past UINT_MAX, should return umax
        self.assertEqual(increase_solve_limit("4294967295,umax", 50), "umax,umax")

    def test_increase_time_limit(self):
        """
        Test the increase_time_limit function.
        """
        timer = mock.Mock(spec=Timer)
        timer.remaining_time.return_value = 10
        time_limit = 50
        solver_time_limit = 20

        # increase rate 0
        self.assertEqual(increase_time_limit(timer, time_limit, solver_time_limit, 0), 20)
        # increase rate 50%, remaining time exceeded, dont increase
        self.assertEqual(increase_time_limit(timer, time_limit, solver_time_limit, 50), 20)
        # increase rate 50%, remaining time not exceeded, increase
        timer.remaining_time.return_value = 40
        self.assertEqual(increase_time_limit(timer, time_limit, solver_time_limit, 50), 30)
        # no overall time limit, should increase
        self.assertEqual(increase_time_limit(timer, None, solver_time_limit, 50), 30)

    def test_increase_cutoff(self):
        """
        Test the increase_cutoff function.
        """
        current_cutoff = 10
        cutoff_threshold = 5
        timer = mock.Mock(spec=Timer)
        timer.remaining_time.return_value = 9
        time_limit = 50
        latest_stats = {"no_improvement_cutoff_count": 4}

        # increase rate 0
        self.assertEqual(
            increase_cutoff(
                current_cutoff=current_cutoff,
                cutoff_threshold=cutoff_threshold,
                increase_rate=0,
                timer=timer,
                time_limit=time_limit,
                latest_stats=latest_stats,
            ),
            10,
        )
        # increase rate 50%, remaining time exceeded, dont increase
        self.assertEqual(
            increase_cutoff(
                current_cutoff=current_cutoff,
                cutoff_threshold=cutoff_threshold,
                increase_rate=50,
                timer=timer,
                time_limit=time_limit,
                latest_stats=latest_stats,
            ),
            10,
        )
        # increase rate 50%, remaining time not exceeded, cutoff below threshold, dont increase
        timer.remaining_time.return_value = 40
        self.assertEqual(
            increase_cutoff(
                current_cutoff=current_cutoff,
                cutoff_threshold=cutoff_threshold,
                increase_rate=50,
                timer=timer,
                time_limit=time_limit,
                latest_stats=latest_stats,
            ),
            10,
        )
        # increase rate 50%, remaining time not exceeded, cutoff thresh met, increase
        latest_stats["no_improvement_cutoff_count"] = 5
        self.assertEqual(
            increase_cutoff(
                current_cutoff=current_cutoff,
                cutoff_threshold=cutoff_threshold,
                increase_rate=50,
                timer=timer,
                time_limit=time_limit,
                latest_stats=latest_stats,
            ),
            15,
        )

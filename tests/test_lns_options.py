"""
Tests for the LNSOptions class.
"""

from unittest import TestCase, mock

from mod_lns import UNSET
from mod_lns.interfaces.solver import SolverConfig
from mod_lns.lib.adaptive_strategies.roulette_wheel import RouletteWheelStrategy
from mod_lns.lib.adaptive_strategies.static import StaticStrategy
from mod_lns.lns_options import LNSOptions

# pylint: disable=protected-access


class TestLNSOptions(TestCase):
    """
    Test cases for the LNSOptions class.
    """

    def setUp(self) -> None:
        """
        Set up the test case.
        """
        self.lns_options = LNSOptions()

    def test_parse_lns_opt_mode_string(self) -> None:
        """
        Test the _parse_lns_opt_mode_string method.
        """
        self.assertDictEqual(
            self.lns_options._parse_lns_opt_mode_string("opt"), {"mode": "opt", "nf": None, "modifier": None}
        )
        self.assertDictEqual(
            self.lns_options._parse_lns_opt_mode_string("opt,5"), {"mode": "opt", "nf": "5", "modifier": "dynamic"}
        )
        self.assertDictEqual(
            self.lns_options._parse_lns_opt_mode_string("opt,5,4,static"),
            {"mode": "opt", "nf": "5,4", "modifier": "static"},
        )
        self.assertDictEqual(
            self.lns_options._parse_lns_opt_mode_string("opt,5,4"), {"mode": "opt", "nf": "5", "modifier": "dynamic"}
        )

    def test_apply_overrides(self) -> None:
        """
        Test the apply_overrides method.
        """
        overrides = {
            "lns_opt_mode": "opt,5,4,static",
            "time_limit": None,
            "init_time_limit": 30,
            "lns_time_limit": UNSET,
            "invalid": "10",
        }

        self.lns_options.lns_opt_mode = {"mode": None, "nf": None, "modifier": None}
        self.lns_options.time_limit = 40
        self.lns_options.init_time_limit = None
        self.lns_options.lns_time_limit = 10
        self.lns_options.apply_overrides(overrides)
        self.assertDictEqual(self.lns_options.lns_opt_mode, {"mode": "opt", "nf": "5,4", "modifier": "static"})
        self.assertIsNone(self.lns_options.time_limit)
        self.assertEqual(self.lns_options.init_time_limit, 30)
        self.assertEqual(self.lns_options.lns_time_limit, 10)

    def test_apply_preset(self) -> None:
        """
        Test the apply_preset method.
        """
        self.lns_options.preset = "basic-assumptions"
        with mock.patch.object(self.lns_options, "apply_overrides") as mock_apply_overrides:
            self.lns_options.apply_preset()
            mock_apply_overrides.assert_called_once_with(self.lns_options.preset_values[self.lns_options.preset])

        with self.assertRaises(ValueError):
            self.lns_options.preset = "non-existent-preset"
            self.lns_options.apply_preset()

    def test_get_supported_adaptive_strategy_names(self) -> None:
        """
        Test the get_supported_adaptive_strategy_names method.
        """
        supported_strategies = LNSOptions.get_supported_adaptive_strategy_names()
        self.assertIn("static", supported_strategies)

    def test_build_adaptive_strategy(self) -> None:
        """
        Test the build_adaptive_strategy method.
        """
        self.assertIsInstance(self.lns_options.build_adaptive_strategy("static", mock.Mock()), StaticStrategy)
        self.assertIsInstance(self.lns_options.build_adaptive_strategy("roulette", mock.Mock()), RouletteWheelStrategy)
        with self.assertRaises(ValueError):
            self.lns_options.build_adaptive_strategy("non-existent-strategy", mock.Mock())

    def test_prepare(self) -> None:
        """
        Test the prepare method.
        """
        self.lns_options.time_limit = UNSET
        self.lns_options.relaxation = ("declarative", 20)
        self.lns_options.constrained = True
        self.lns_options.lns_solve_limit_increase_rate = -20
        self.lns_options.lns_time_limit_increase_rate = 200
        self.lns_options.prepare()
        self.assertIsNone(self.lns_options.time_limit)
        self.assertTrue(self.lns_options.declarative)
        self.assertEqual(self.lns_options.relax_rate, 20)
        self.assertDictEqual(self.lns_options.lns_opt_mode, {"mode": "opt", "nf": "0", "modifier": "dynamic"})
        self.assertEqual(self.lns_options.lns_solve_limit_increase_rate, 0)
        self.assertEqual(self.lns_options.lns_time_limit_increase_rate, 100)

    def test_get_init_solver_configuration(self) -> None:
        """
        Test the get_init_solver_configuration method.
        """
        self.lns_options.init_time_limit = 30
        self.lns_options.init_restart_on_model = True
        config = self.lns_options.get_init_solver_configuration()
        self.assertIsInstance(config, SolverConfig)
        self.assertEqual(config.time_limit, 30)
        self.assertEqual(config.restart_on_model, "1")

    def test_get_lns_solver_configuration(self) -> None:
        """
        Test the get_lns_solver_configuration method.
        """
        self.lns_options.lns_time_limit = 30
        self.lns_options.lns_restart_on_model = True
        self.lns_options.fix = "heuristics"
        self.lns_options.lns_heuristic = "my_heuristic"
        config = self.lns_options.get_lns_solver_configuration()
        self.assertIsInstance(config, SolverConfig)
        self.assertEqual(config.time_limit, 30)
        self.assertEqual(config.restart_on_model, "1")
        self.assertEqual(config.heuristic, "my_heuristic")

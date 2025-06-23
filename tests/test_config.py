"""
Test cases for LNSConfig class.
"""

from unittest import TestCase
from unittest.mock import patch

from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.default_strategy import DefaultStrategy
from mod_lns.lns_config import LNSConfig


# pylint: disable=protected-access
class TestLNSConfig(TestCase):
    """
    Test cases for LNSConfig class.
    """

    def test_init(self):
        """
        Test config initialization.
        """
        ref_lns_opt = {
            "heuristics": False,
            "constrained": False,
            "declarative": False,
            "relax_rate": 0.2,
            "max_steps": "2000",
            "solve_time_limit": 20,
            "overall_time_limit": 600,
        }
        ref_clingo_opt = ["--rand-freq=0.05"]
        config = LNSConfig()
        self.assertDictEqual(config.lns_options, ref_lns_opt)
        self.assertCountEqual(config.clingo_options, ref_clingo_opt)
        self.assertIsInstance(config.solver, ClingoSolver)
        self.assertIsInstance(config.strategy, DefaultStrategy)

        ref_lns_opt = {
            "heuristics": False,
            "constrained": True,
            "declarative": False,
            "relax_rate": 0.2,
            "max_steps": "2000",
            "solve_time_limit": 20,
            "overall_time_limit": 600,
            "test_opt": "abc",
        }
        ref_clingo_opt = ["--test_opt=123"]
        ref_solver = ClingoSolver()
        ref_strat = DefaultStrategy()

        config = LNSConfig(
            {"test_opt": "abc", "constrained": True},
            ["--test_opt=123"],
            ref_solver,
            ref_strat,
        )
        self.assertDictEqual(config.lns_options, ref_lns_opt)
        self.assertCountEqual(config.clingo_options, ref_clingo_opt)
        self.assertIsInstance(config.solver, type(ref_solver))
        self.assertIsInstance(config.strategy, type(ref_strat))

        with patch(
            "mod_lns.lns_config.enable_heuristics", return_value=ref_solver
        ) as mock_method:
            config = LNSConfig({"heuristics": True})
            mock_method.assert_called_once()
        self.assertEqual(config.solver, ref_solver)

        with patch(
            "mod_lns.lns_config.enable_constrained_approach",
            return_value=(ref_solver, ref_strat),
        ) as mock_method:
            config = LNSConfig({"constrained": True})
            mock_method.assert_called_once()
        self.assertEqual(config.solver, ref_solver)
        self.assertEqual(config.strategy, ref_strat)

        with patch(
            "mod_lns.lns_config.enable_declarative", return_value=ref_strat
        ) as mock_method:
            config = LNSConfig({"declarative": True})
            mock_method.assert_called_once()
        self.assertEqual(config.strategy, ref_strat)

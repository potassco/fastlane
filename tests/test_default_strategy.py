"""
Test cases for DefaultStrategy classes.
"""

import argparse
from io import StringIO
from unittest import TestCase, mock

from clingo.symbol import Function, Number

from mod_lns import Model
from mod_lns.lib.parser.default_parser import get_default_parser
from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.default_strategy import DefaultStrategy, LNSConfig
from mod_lns.lns import LNS

# pylint: disable=protected-access


class TestDefaultParser(TestCase):
    """
    Test cases for the default parser.
    """

    def test_parser(self):
        """
        Test the parser.
        """

        parser = get_default_parser(
            LNSConfig, argparse.ArgumentParser().add_subparsers(title="system")
        )
        # general options
        ret = parser.parse_args(["--solver", "clingo"])
        self.assertIsInstance(ret.solver, ClingoSolver)
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--solver", "abc"])
        ret = parser.parse_args(["--seed", "123"])
        self.assertEqual(ret.seed, 123)
        ret = parser.parse_args(["--time-limit", "42"])
        self.assertEqual(ret.time_limit, 42)
        ret = parser.parse_args(["--max-steps", "42"])
        self.assertEqual(ret.max_steps, 42)
        ret = parser.parse_args(["--relax-rate", "20"])
        self.assertEqual(ret.relax_rate, 20)
        # solver options for first solution
        ret = parser.parse_args(["--init-solve-limit", "100"])
        self.assertEqual(ret.init_solve_limit, "100")
        ret = parser.parse_args(["--init-solve-limit", "100,200"])
        self.assertEqual(ret.init_solve_limit, "100,200")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--init-solve-limit", "abc"])
        ret = parser.parse_args(["--init-time-limit", "42"])
        self.assertEqual(ret.init_time_limit, 42)
        # lns options
        ret = parser.parse_args(["--lns-constrained"])
        self.assertEqual(ret.constrained, True)
        ret = parser.parse_args(["--lns-declarative"])
        self.assertEqual(ret.declarative, True)
        ret = parser.parse_args(["--lns-accept-variability", "30"])
        self.assertEqual(ret.accept_variability, 30)
        # lns solver options
        ret = parser.parse_args(["--lns-solve-limit", "100"])
        self.assertEqual(ret.lns_solve_limit, "100")
        ret = parser.parse_args(["--lns-solve-limit", "100,200"])
        self.assertEqual(ret.lns_solve_limit, "100,200")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--lns-solve-limit", "abc"])
        ret = parser.parse_args(["--lns-time-limit", "42"])
        self.assertEqual(ret.lns_time_limit, 42)


class TestLNSConfig(TestCase):
    """
    Test cases for LNSConfig class.
    """

    def test_config(self):
        """
        Test the LNSConfig class.
        """
        config = LNSConfig(
            seed=123,
            init_solve_limit="100,200",
            init_time_limit=10,
            lns_solve_limit="300",
            lns_time_limit=20,
        )
        init_config = config.get_init_solver_configuration()
        self.assertEqual(init_config.solve_limit, "100,200")
        self.assertEqual(init_config.time_limit, 10)
        self.assertEqual(init_config.seed, 123)
        lns_config = config.get_lns_solver_configuration()
        self.assertEqual(lns_config.solve_limit, "300")
        self.assertEqual(lns_config.time_limit, 20)
        self.assertEqual(lns_config.seed, 123)


class TestDefaultStrategy(TestCase):
    """
    Test cases for DefaultStrategy class.
    """

    def setUp(self) -> None:
        self.strategy = DefaultStrategy()
        self.strategy.log_level = 50
        self.lns = LNS(["./tests/ref/golf.lp"], self.strategy)

    def test_get_parser(self):
        """
        Test the get_parser method.
        """
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(title="strategy")
        strat_parser = mock.MagicMock()
        strat_parser.set_defaults = mock.MagicMock()
        with mock.patch(
            "mod_lns.lib.strategies.default_strategy.get_default_parser",
            return_value=strat_parser,
        ) as get_parser:
            ret_parser = self.strategy.get_parser(subparsers)
            self.assertEqual(ret_parser, strat_parser)
            get_parser.assert_called_once_with(LNSConfig, subparsers)
            ret_parser.set_defaults.assert_called_once_with(strategy=self.strategy)

    def test_parse_options(self):
        """
        Test the parse_options method.
        """
        args = argparse.Namespace(
            solver=ClingoDLSolver(),
            seed=123,
            time_limit=42,
            max_steps=100,
            relax_rate=20,
            init_solve_limit="100,200",
            init_time_limit=None,
            constrained=True,
            declarative=True,
            accept_variability=30,
            lns_solve_limit="300",
            lns_time_limit=20,
            opt=5,
        )
        rest = self.strategy.parse_options(args)
        self.assertEqual(self.strategy.config.solver, args.solver)
        self.assertEqual(self.strategy.config.seed, 123)
        self.assertEqual(self.strategy.config.time_limit, 42)
        self.assertEqual(self.strategy.config.max_steps, 100)
        self.assertEqual(self.strategy.config.relax_rate, 20)
        self.assertEqual(self.strategy.config.init_solve_limit, "100,200")
        self.assertEqual(self.strategy.config.constrained, True)
        self.assertEqual(self.strategy.config.declarative, True)
        self.assertEqual(self.strategy.config.accept_variability, 30)
        self.assertEqual(self.strategy.config.lns_solve_limit, "300")
        self.assertEqual(self.strategy.config.lns_time_limit, 20)
        self.assertEqual(self.strategy.solver, args.solver)
        self.assertEqual(self.strategy.log_level, 30)
        # None -> default value
        self.assertEqual(self.strategy.config.init_time_limit, 20)
        # rest
        self.assertEqual(rest, {"opt": 5})

    def test_pre_setup(self):
        """
        Test the pre_setup method.
        """
        self.strategy.config.time_limit = 42
        self.strategy.config.init_time_limit = None
        with mock.patch.object(
            self.strategy.timer, "start"
        ) as mock_timer_start, mock.patch.object(
            self.strategy.config,
            "get_lns_solver_configuration",
            wraps=self.strategy.config.get_lns_solver_configuration,
        ) as mock_get_lns_config, mock.patch.object(
            self.strategy.config,
            "get_init_solver_configuration",
            wraps=self.strategy.config.get_init_solver_configuration,
        ) as mock_get_init_config:
            self.strategy.pre_setup(self.lns)
            mock_timer_start.assert_called_once_with(42)
            mock_get_init_config.assert_called_once()
            mock_get_lns_config.assert_called_once()
            self.assertEqual(self.strategy.init_solver_config.time_limit, 42)

            self.strategy.config.init_time_limit = 10
            self.strategy.pre_setup(self.lns)
            self.assertEqual(self.strategy.init_solver_config.time_limit, 10)

            self.strategy.config.init_time_limit = 50
            self.strategy.pre_setup(self.lns)
            self.assertEqual(self.strategy.init_solver_config.time_limit, 42)

    def test_setup_solver(self):
        """
        Test the setup_solver method.
        """
        self.strategy.solver = ClingoSolver()
        self.strategy.config.seed = 123
        with mock.patch.object(self.strategy.solver, "setup") as mock_setup:
            self.strategy.setup_solver(self.lns)
            mock_setup.assert_called_once_with(self.lns, ["--seed=123"])

    def test_post_setup(self):
        """
        Test the post_setup method.
        """
        self.strategy.solver = ClingoSolver()
        with mock.patch.object(self.strategy.solver, "ground") as mock_ground:
            self.strategy.post_setup(self.lns)
            mock_ground.assert_called_once()

    def test_get_first_solution(self):
        """
        Test the get_first_solution method.
        """
        self.strategy.solver = ClingoSolver()
        with mock.patch.object(
            self.strategy.solver, "solve", return_value=None
        ) as mock_solve:
            self.assertFalse(self.strategy.get_first_solution(self.lns))
            mock_solve.assert_called_once_with(self.strategy.init_solver_config)

        model = Model()
        with mock.patch.object(
            self.strategy.solver, "solve", return_value=model
        ) as mock_solve:
            self.assertTrue(self.strategy.get_first_solution(self.lns))
            mock_solve.assert_called_once_with(self.strategy.init_solver_config)
            self.assertEqual(self.lns.current_model, model)
            self.assertEqual(self.lns.best_model, model)
            self.assertEqual(self.lns.new_model, model)

    def test_calc_opt_bound(self):
        """
        Test the _calc_opt_bound method.
        """
        self.strategy._calc_opt_bound(self.strategy.lns_solver_config, [2, 4])
        self.assertEqual(self.strategy.lns_solver_config.opt_mode, "opt, 2, 3")

    def test_update_lns_solver_time_limit(self):
        """
        Test the _update_lns_solver_time_limit method.
        """
        self.strategy.config.time_limit = 42
        with mock.patch.object(self.strategy.timer, "remaining_time", return_value=21):
            self.strategy.lns_solver_config.time_limit = None
            self.strategy._update_lns_solver_time_limit()
            self.assertEqual(self.strategy.lns_solver_config.time_limit, 21)

            self.strategy.lns_solver_config.time_limit = 10
            self.strategy._update_lns_solver_time_limit()
            self.assertEqual(self.strategy.lns_solver_config.time_limit, 10)

            self.strategy.lns_solver_config.time_limit = 50
            self.strategy._update_lns_solver_time_limit()
            self.assertEqual(self.strategy.lns_solver_config.time_limit, 21)

    def test_post_first_solution(self):
        """
        Test the post_first_solution method.
        """
        self.strategy.solver = ClingoSolver()
        self.lns.current_model.cost = [2, 4]
        with mock.patch.object(
            self.strategy, "_update_lns_solver_time_limit"
        ) as mock_update_time_limit, mock.patch.object(
            self.strategy, "_calc_opt_bound"
        ) as mock_calc_opt_bound:
            self.strategy.solver.finished = True
            self.strategy.post_first_solution(self.lns)
            mock_update_time_limit.assert_not_called()
            mock_calc_opt_bound.assert_not_called()

            self.strategy.solver.finished = False
            self.strategy.config.constrained = False
            mock_update_time_limit.reset_mock()
            mock_calc_opt_bound.reset_mock()
            self.strategy.post_first_solution(self.lns)
            mock_update_time_limit.assert_called_once()
            mock_calc_opt_bound.assert_not_called()

            self.strategy.solver.finished = False
            self.strategy.config.constrained = True
            mock_update_time_limit.reset_mock()
            mock_calc_opt_bound.reset_mock()
            self.strategy.post_first_solution(self.lns)
            mock_update_time_limit.assert_called_once()
            mock_calc_opt_bound.assert_called_once_with(
                self.strategy.lns_solver_config, [2, 4]
            )

    def test_check_stop(self):
        """
        Test check_stop.
        """
        self.strategy.solver = ClingoSolver()

        # nothing
        self.assertFalse(self.strategy.check_stop(self.lns))

        # time limit
        self.strategy.config.time_limit = 42
        with mock.patch(
            "mod_lns.Timer.is_ringing", mock.PropertyMock(return_value=True)
        ):
            self.assertTrue(self.strategy.check_stop(self.lns))

        # step limit
        self.strategy.config.max_steps = 10
        self.lns.step_c = 11
        self.assertTrue(self.strategy.check_stop(self.lns))

        # solver stop
        self.lns.step_c = 0
        self.strategy.solver.stop = True
        self.assertTrue(self.strategy.check_stop(self.lns))

    def test_pre_relax(self):
        """
        Test the pre_relax method.
        """
        self.lns.step_c = 5
        self.lns.best_model.cost = [2, 4]
        out = StringIO()
        with mock.patch.object(
            self.strategy.timer, "get_elapsed_time", return_value=10
        ), mock.patch("sys.stdout", out):
            self.strategy.pre_relax(self.lns)
            self.assertEqual(out.getvalue(), "10.000s: Iteration: 5 || 2 4\n")

    def test_relax(self):
        """
        Test the relax method.
        """
        x = []
        y = []
        with mock.patch(
            "mod_lns.lib.strategies.default_strategy.relax_declarative", return_value=x
        ) as mock_relax_declarative, mock.patch(
            "mod_lns.lib.strategies.default_strategy.relax_random", return_value=y
        ) as mock_relax_random:
            self.strategy.config.declarative = False
            self.assertEqual(self.strategy.relax(self.lns), y)
            mock_relax_declarative.assert_not_called()
            mock_relax_random.assert_called_once_with(
                self.lns.current_model, self.strategy.config.relax_rate
            )

            self.strategy.config.declarative = True
            mock_relax_declarative.reset_mock()
            mock_relax_random.reset_mock()
            self.assertEqual(self.strategy.relax(self.lns), x)
            mock_relax_declarative.assert_called_once_with(
                self.lns.current_model, self.strategy.config.relax_rate
            )
            mock_relax_random.assert_not_called()

    def test_repair(self):
        """
        Test the repair method.
        """
        self.strategy.solver = ClingoSolver()
        model = Model()
        fixed_atoms = [
            Function("a", [Number(1)], True),
        ]
        assumptions = [
            (Function("a", [Number(1)], True), True),
        ]
        with mock.patch.object(
            self.strategy.solver, "solve", return_value=model
        ) as mock_solve, mock.patch.object(
            self.strategy, "_update_lns_solver_time_limit"
        ) as mock_update_time_limit:
            self.assertEqual(self.strategy.repair(self.lns, fixed_atoms), model)
            mock_solve.assert_called_once_with(
                self.strategy.lns_solver_config, assumptions
            )
            mock_update_time_limit.assert_called_once()

    def test_check_accept(self):
        """
        Test the check_accept method.
        """
        # None
        self.lns.new_model = None
        self.assertFalse(self.strategy.check_accept(self.lns))

        with mock.patch(
            "mod_lns.lib.strategies.default_strategy.calculate_variability",
            return_value=33,
        ) as mock_variability:
            self.lns.new_model = Model()
            self.lns.new_model.shown = [
                Function("a", [Number(1)], True),
            ]
            self.lns.current_model = Model()
            self.lns.current_model.shown = [
                Function("b", [Number(2)], True),
            ]

            # variability check fails
            self.strategy.config.accept_variability = 100
            self.assertFalse(self.strategy.check_accept(self.lns))
            mock_variability.assert_called_once_with(
                self.lns.new_model.shown,
                self.lns.current_model.shown,
            )

            mock_variability.reset_mock()

            # variability check passes
            self.strategy.config.accept_variability = 0
            self.assertTrue(self.strategy.check_accept(self.lns))
            mock_variability.assert_called_once_with(
                self.lns.new_model.shown,
                self.lns.current_model.shown,
            )

    def test_accepted(self):
        """
        Test the accepted method.
        """
        with mock.patch.object(self.strategy, "_calc_opt_bound") as mock_calc_opt_bound:
            self.strategy.config.constrained = False
            self.strategy.accepted(self.lns)
            mock_calc_opt_bound.assert_not_called()

            self.strategy.config.constrained = True
            self.strategy.accepted(self.lns)
            mock_calc_opt_bound.assert_called_once_with(
                self.strategy.lns_solver_config, self.lns.current_model.cost
            )

    def test_check_better(self):
        """
        Test the check_better method.
        """
        # None
        self.lns.new_model = None
        self.assertFalse(self.strategy.check_better(self.lns))

        self.lns.new_model = Model()
        self.lns.new_model.cost = [2, 4]

        self.lns.best_model = Model()
        self.lns.best_model.cost = [2, 4]

        # not better
        self.assertFalse(self.strategy.check_better(self.lns))

        # better
        self.lns.new_model.cost = [1, 5]
        self.assertTrue(self.strategy.check_better(self.lns))

    def test_better(self):
        """
        Test the better method.
        """
        self.lns.step_c = 5
        self.lns.best_model.cost = [2, 4]
        out = StringIO()
        with mock.patch.object(
            self.strategy.timer, "get_elapsed_time", return_value=10
        ), mock.patch("sys.stdout", out):
            self.strategy.better(self.lns)
            self.assertEqual(out.getvalue(), "10.000s: New best solution: 2 4\n")

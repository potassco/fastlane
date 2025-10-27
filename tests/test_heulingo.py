"""
Test cases for Heulingo classes.
"""

import argparse
from io import StringIO
from unittest import TestCase, mock

from clingo.symbol import Function, Number

import mod_lns
from mod_lns import Model
from mod_lns.interfaces.solver import SolverConfig
from mod_lns.lib.parser.heulingo_parser import get_heulingo_parser
from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.lib.strategies.heulingo import Heulingo, HeulingoConfig
from mod_lns.lns import LNS

# pylint: disable=protected-access, too-many-statements, too-many-lines, too-many-public-methods


class TestHeulingoParser(TestCase):
    """
    Test cases for the heulingo parser.
    """

    def test_parser(self):
        """
        Test the parser.
        """

        parser = get_heulingo_parser(HeulingoConfig, argparse.ArgumentParser().add_subparsers(title="system"))
        # general options
        ret = parser.parse_args(["--solver", "clingo"])
        self.assertIsInstance(ret.solver, ClingoSolver)
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--solver", "abc"])
        ret = parser.parse_args(["--seed", "42"])
        self.assertEqual(ret.seed, 42)
        ret = parser.parse_args(["--time-limit", "10"])
        self.assertEqual(ret.time_limit, 10)
        ret = parser.parse_args(["--max-steps", "5"])
        self.assertEqual(ret.max_steps, 5)
        ret = parser.parse_args(["--clingo-args", "-c n=42,-t 4"])
        self.assertEqual(ret.clingo_args, "-c n=42,-t 4")
        ret = parser.parse_args(["--parallel_mode", "4"])
        self.assertEqual(ret.parallel_mode, "4")
        ret = parser.parse_args(["--parallel_mode", "4,split"])
        self.assertEqual(ret.parallel_mode, "4,split")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--parallel_mode", "abc"])
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--parallel_mode", "103"])
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--parallel_mode", "3,test"])
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--parallel_mode", "1,compete,x"])
        ret = parser.parse_args(["--minimize-variable", "x"])
        self.assertEqual(ret.minimize_variable, Function("x", [], True))
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--minimize-variable", "x,x"])
        ret = parser.parse_args(["--falsify", "inf"])
        self.assertEqual(ret.falsify, "inf")
        ret = parser.parse_args(["--falsify", "3"])
        self.assertEqual(ret.falsify, "3")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--falsify", "abc"])
        # solver options for first solution
        ret = parser.parse_args(["--init-configuration", "jumpy"])
        self.assertEqual(ret.init_configuration, "jumpy")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--init-configuration", "abc"])
        ret = parser.parse_args(["--init-opt-strategy", "usc,11"])
        self.assertEqual(ret.init_opt_strategy, "usc,11")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--init-opt-strategy", "abc"])
        ret = parser.parse_args(["--init-opt-heuristic", "sign"])
        self.assertEqual(ret.init_opt_heuristic, "sign")
        ret = parser.parse_args(["--init-restart-on-model"])
        self.assertTrue(ret.init_restart_on_model)
        ret = parser.parse_args(["--init-opt-mode", "optN,10"])
        self.assertEqual(ret.init_opt_mode, "optN,10")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--init-opt-mode", "abc"])
        ret = parser.parse_args(["--init-solve-limit", "100,10"])
        self.assertEqual(ret.init_solve_limit, "100,10")
        ret = parser.parse_args(["--init-solve-limit", "100"])
        self.assertEqual(ret.init_solve_limit, "100")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--init-solve-limit", "abc"])
        ret = parser.parse_args(["--init-time-limit", "10"])
        self.assertEqual(ret.init_time_limit, 10)
        # lns options
        ret = parser.parse_args(["--solve-limit-increase-rate", "1.5"])
        self.assertEqual(ret.solve_limit_increase_rate, 1.5)
        ret = parser.parse_args(["--time-limit-increase-rate", "2.0"])
        self.assertEqual(ret.time_limit_increase_rate, 2.0)
        ret = parser.parse_args(["--acceptance-rate", "5.0"])
        self.assertEqual(ret.acceptance_rate, 5.0)
        ret = parser.parse_args(["--heulingo-configuration", "tsp"])
        self.assertEqual(ret.heulingo_configuration, "tsp")
        # lns solver options
        ret = parser.parse_args(["--lns-opt-strategy", "usc,11"])
        self.assertEqual(ret.lns_opt_strategy, "usc,11")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--lns-opt-strategy", "abc"])
        ret = parser.parse_args(["--lns-opt-heuristic", "sign"])
        self.assertEqual(ret.lns_opt_heuristic, "sign")
        ret = parser.parse_args(["--lns-restart-on-model"])
        self.assertTrue(ret.lns_restart_on_model)
        ret = parser.parse_args(["--lns-opt-mode", "opt"])
        self.assertDictEqual(ret.lns_opt_mode, {"mode": "opt", "nf": None, "modifier": None})
        ret = parser.parse_args(["--lns-opt-mode", "optN,10"])
        self.assertDictEqual(ret.lns_opt_mode, {"mode": "optN", "nf": "10", "modifier": "dynamic"})
        ret = parser.parse_args(["--lns-opt-mode", "optN,10,5,static"])
        self.assertDictEqual(ret.lns_opt_mode, {"mode": "optN", "nf": "10,5", "modifier": "static"})
        ret = parser.parse_args(["--lns-opt-mode", "optN,10,dynamic"])
        self.assertDictEqual(ret.lns_opt_mode, {"mode": "optN", "nf": "10", "modifier": "dynamic"})
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--lns-opt-mode", "abc"])
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--lns-opt-mode", "optN,abc"])
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--lns-opt-mode", "optN,abc,static"])
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--lns-opt-mode", "optN,10,5,dynamic"])
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--lns-opt-mode", "optN,abc,dynamic"])
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--lns-opt-mode", "optN,10,abc"])
        ret = parser.parse_args(["--lns-solve-limit", "100,10"])
        self.assertEqual(ret.lns_solve_limit, "100,10")
        ret = parser.parse_args(["--lns-solve-limit", "100"])
        self.assertEqual(ret.lns_solve_limit, "100")
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", new=StringIO()):
            parser.parse_args(["--lns-solve-limit", "abc"])
        ret = parser.parse_args(["--lns-time-limit", "10"])
        self.assertEqual(ret.lns_time_limit, 10)


class TestHeulingoConfig(TestCase):
    """
    Test cases for the HeulingoConfig class.
    """

    def test_apply_config(self):
        """
        Test the apply_config method.
        """
        config = HeulingoConfig()
        config.heulingo_configuration = "sd"
        self.assertIsNone(config.init_configuration)
        self.assertIsNone(config.init_opt_strategy)
        self.assertIsNone(config.init_solve_limit)
        self.assertDictEqual(config.lns_opt_mode, {"mode": None, "nf": None, "modifier": None})
        self.assertIsNone(config.lns_solve_limit)
        config.apply_config()
        self.assertEqual(config.init_configuration, "handy")
        self.assertEqual(config.init_opt_strategy, "usc,3")
        self.assertEqual(config.init_solve_limit, "900000")
        self.assertDictEqual(config.lns_opt_mode, {"mode": "opt", "nf": "0", "modifier": "dynamic"})
        self.assertEqual(config.lns_solve_limit, "40000")

        config.heulingo_configuration = "test"
        config.lns_opt_mode = {"mode": None, "nf": None, "modifier": None}
        config.heulingo_configuration_values["test"] = {"lns_opt_mode": "opt"}
        config.apply_config()
        self.assertDictEqual(config.lns_opt_mode, {"mode": "opt", "nf": None, "modifier": None})

        config.lns_opt_mode = {"mode": None, "nf": None, "modifier": None}
        config.heulingo_configuration_values["test"] = {"lns_opt_mode": "opt,0"}
        config.apply_config()
        self.assertDictEqual(config.lns_opt_mode, {"mode": "opt", "nf": "0", "modifier": "dynamic"})

        config.lns_opt_mode = {"mode": None, "nf": None, "modifier": None}
        config.heulingo_configuration_values["test"] = {"lns_opt_mode": "opt,1,2,static"}
        config.apply_config()
        self.assertDictEqual(config.lns_opt_mode, {"mode": "opt", "nf": "1,2", "modifier": "static"})

    def test_get_init_solver_configuration(self):
        """
        Test the get_init_solver_configuration method.
        """
        config = HeulingoConfig()
        config.init_configuration = "handy"
        config.init_opt_strategy = "usc,3"
        config.init_opt_heuristic = "sign"
        config.init_restart_on_model = True
        config.init_opt_mode = "optN,10"
        config.init_solve_limit = "100,10"
        config.init_time_limit = 10
        config.seed = 42
        solver_config = config.get_init_solver_configuration()
        self.assertEqual(solver_config.configuration, "handy")
        self.assertEqual(solver_config.opt_strategy, "usc,3")
        self.assertEqual(solver_config.opt_heuristic, "sign")
        self.assertEqual(solver_config.restart_on_model, "1")
        self.assertEqual(solver_config.opt_mode, "optN,10")
        self.assertEqual(solver_config.solve_limit, "100,10")
        self.assertEqual(solver_config.time_limit, 10)
        self.assertEqual(solver_config.seed, 42)

    def test_get_lns_solver_configuration(self):
        """
        Test the get_lns_solver_configuration method.
        """
        config = HeulingoConfig()
        config.lns_configuration = "handy"
        config.lns_opt_strategy = "usc,3"
        config.lns_opt_heuristic = "sign"
        config.lns_restart_on_model = True
        config.lns_solve_limit = "100,10"
        config.lns_time_limit = 10
        config.seed = 42
        self.assertEqual(config.lns_heuristic, "Domain")
        solver_config = config.get_lns_solver_configuration()
        self.assertEqual(solver_config.configuration, "handy")
        self.assertEqual(solver_config.opt_strategy, "usc,3")
        self.assertEqual(solver_config.opt_heuristic, "sign")
        self.assertEqual(solver_config.restart_on_model, "1")
        self.assertEqual(solver_config.heuristic, "Domain")
        self.assertEqual(solver_config.solve_limit, "100,10")
        self.assertEqual(solver_config.time_limit, 10)
        self.assertEqual(solver_config.seed, 42)


class TestHeulingo(TestCase):
    """
    Test cases for the Heulingo class.
    """

    def setUp(self) -> None:
        self.strategy = Heulingo()
        self.strategy.config.log_level = 50
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
            "mod_lns.lib.strategies.heulingo.get_heulingo_parser",
            return_value=strat_parser,
        ) as get_parser:
            ret_parser = self.strategy.get_parser(subparsers)
            self.assertEqual(ret_parser, strat_parser)
            get_parser.assert_called_once_with(HeulingoConfig, subparsers)
            ret_parser.set_defaults.assert_called_once_with(strategy=self.strategy)

    def test_prep_values(self):
        """
        Test the prep_values method.
        """
        self.strategy.config.solve_limit_increase_rate = 140
        self.strategy.config.time_limit_increase_rate = -20
        with mock.patch(
            "mod_lns.lib.strategies.heulingo.clamp",
            wraps=mod_lns.lib.strategies.heulingo.clamp,
        ) as mock_clamp:
            self.strategy._prep_values()
            mock_clamp.assert_has_calls([mock.call(140, 0, 100), mock.call(-20, 0, 100)])
            self.assertEqual(self.strategy.config.solve_limit_increase_rate, 100)
            self.assertEqual(self.strategy.config.time_limit_increase_rate, 0)

    def test_parse_options(self):
        """
        Test the parse_options method.
        """
        args = {
            "heulingo_configuration": "tsp",
            "solver": ClingoDLSolver(),
            "seed": 123,
            "init_solve_limit": "100,200",
            "lns_solve_limit": "300",
            "lns_time_limit": 20,
            "acceptance_rate": None,
            "opt": 5,
            "log_level": 50,
        }
        with mock.patch.object(self.strategy.config, "apply_config") as mock_apply:
            rest = self.strategy.parse_options(args)
            mock_apply.assert_called_once()
            self.assertEqual(self.strategy.config.heulingo_configuration, "tsp")
            self.assertEqual(self.strategy.config.solver, args["solver"])
            self.assertEqual(self.strategy.config.seed, 123)
            self.assertEqual(self.strategy.config.init_solve_limit, "100,200")
            self.assertEqual(self.strategy.config.lns_solve_limit, "300")
            self.assertEqual(self.strategy.config.lns_time_limit, 20)
            self.assertEqual(self.strategy.solver, args["solver"])
            self.assertEqual(self.strategy._log_level, 50)
            # None -> default value
            self.assertEqual(self.strategy.config.acceptance_rate, 0.0)
            # rest
            self.assertEqual(rest, {"opt": 5})

    def test_pre_setup(self):
        """
        Test the pre_setup method.
        """
        self.strategy.config.time_limit = 42
        self.strategy.config.init_time_limit = None
        self.strategy.config.lns_opt_mode = {
            "mode": "opt",
            "nf": 0,
            "modifier": "dynamic",
        }
        self.strategy.config.acceptance_rate = 1
        self.strategy.config.falsify = "3"
        self.assertFalse(self.strategy._falsified)
        self.assertEqual(self.strategy._false_weight, Function("inf"))
        with (
            mock.patch.object(self.strategy.timer, "start") as mock_timer_start,
            mock.patch.object(
                self.strategy.config,
                "get_lns_solver_configuration",
                wraps=self.strategy.config.get_lns_solver_configuration,
            ) as mock_get_lns_config,
            mock.patch.object(
                self.strategy.config,
                "get_init_solver_configuration",
                wraps=self.strategy.config.get_init_solver_configuration,
            ) as mock_get_init_config,
        ):
            self.strategy.pre_setup(self.lns)
            mock_timer_start.assert_called_once_with(42)
            mock_get_init_config.assert_called_once()
            mock_get_lns_config.assert_called_once()
            self.assertEqual(self.strategy.init_solver_config.time_limit, 42)
            self.assertTrue(self.strategy._falsified)
            self.assertEqual(self.strategy._false_weight, Number(3))

            self.strategy.config.init_time_limit = 10
            self.strategy.pre_setup(self.lns)
            self.assertEqual(self.strategy.init_solver_config.time_limit, 10)

            self.strategy.config.init_time_limit = 50
            self.strategy.pre_setup(self.lns)
            self.assertEqual(self.strategy.init_solver_config.time_limit, 42)

    def test_setup_solver(self):
        """
        Test the _setup_solver method.
        """
        self.strategy.solver = ClingoSolver()
        self.strategy.config.seed = 123
        self.strategy.config.parallel_mode = "4,split"
        self.strategy.config.clingo_args = "--c n=42,-n 3"
        self.strategy.config.minimize_variable = Function("x")
        with mock.patch.object(self.strategy.solver, "setup") as mock_setup:
            self.strategy.setup_solver(self.lns)
            mock_setup.assert_called_once_with(self.lns, ["--seed=123", "--parallel-mode=4,split", "--c n=42", "-n 3"])
            self.assertEqual(self.strategy.solver.minimize_variable, Function("x"))

    def test_post_setup(self):
        """
        Test the post_setup method.
        """
        self.strategy.solver = ClingoSolver()
        with mock.patch.object(self.strategy.solver, "ground") as mock_ground:
            self.strategy.post_setup(self.lns)
            mock_ground.assert_called_once()

    def test_update_time_limit(self):
        """
        Test the _update_time_limit method.
        """
        self.strategy.config.time_limit = 42
        with mock.patch.object(self.strategy.timer, "remaining_time", return_value=21):
            self.strategy.lns_solver_config.time_limit = None
            self.strategy._update_time_limit(self.strategy.lns_solver_config)
            self.assertEqual(self.strategy.lns_solver_config.time_limit, 21)

            self.strategy.lns_solver_config.time_limit = 10
            self.strategy._update_time_limit(self.strategy.lns_solver_config)
            self.assertEqual(self.strategy.lns_solver_config.time_limit, 10)

            self.strategy.lns_solver_config.time_limit = 50
            self.strategy._update_time_limit(self.strategy.lns_solver_config)
            self.assertEqual(self.strategy.lns_solver_config.time_limit, 21)

    def test_get_first_solution(self):
        """
        Test the get_first_solution method.
        """
        self.strategy.solver = ClingoSolver()
        with (
            mock.patch.object(self.strategy.solver, "solve", return_value=None) as mock_solve,
            mock.patch.object(self.strategy, "_update_time_limit") as mock_update_time,
        ):
            self.assertFalse(self.strategy.get_first_solution(self.lns))
            mock_update_time.assert_called_once_with(self.strategy.init_solver_config)
            mock_solve.assert_called_once_with(self.strategy.init_solver_config)

        model = Model()
        with (
            mock.patch.object(self.strategy.solver, "solve", return_value=model) as mock_solve,
            mock.patch.object(self.strategy, "_update_time_limit") as mock_update_time,
        ):
            self.assertTrue(self.strategy.get_first_solution(self.lns))
            mock_solve.assert_called_once_with(self.strategy.init_solver_config)
            mock_update_time.assert_called_once_with(self.strategy.init_solver_config)
            self.assertEqual(self.lns.current_model, model)
            self.assertEqual(self.lns.best_model, model)
            self.assertEqual(self.lns.new_model, model)

    def test_calc_opt_bound(self):
        """
        Test the _calc_opt_bound method.
        """
        cost = [10, 20]
        self.assertIsNone(self.strategy.lns_solver_config.opt_mode)

        self.strategy.config.lns_opt_mode = {
            "mode": "optN",
            "nf": "1",
            "modifier": "static",
        }
        self.strategy._calc_opt_bound(self.strategy.lns_solver_config, cost)
        self.assertEqual(self.strategy.lns_solver_config.opt_mode, "optN,1")

        self.strategy.config.lns_opt_mode = {
            "mode": "optN",
            "nf": "50",
            "modifier": "dynamic",
        }
        self.strategy._calc_opt_bound(self.strategy.lns_solver_config, cost)
        self.assertEqual(self.strategy.lns_solver_config.opt_mode, "optN,10,29")

        self.strategy.config.lns_opt_mode = {
            "mode": "opt",
            "nf": None,
            "modifier": None,
        }
        self.strategy._calc_opt_bound(self.strategy.lns_solver_config, cost)
        self.assertEqual(self.strategy.lns_solver_config.opt_mode, "opt")

    def test_load_lnps_config(self):
        """
        Test the _load_lnps_config method.
        """
        self.lns = LNS(["./tests/ref/lnps_ref.lp"], self.strategy)
        solver = ClingoSolver()
        solver.setup(self.lns)

        # default, select all
        solver.control.ground()
        self.strategy._load_lnps_config(
            solver.control,
            [
                Function("test", [Number(2), Number(4)], True),
                Function("plays", [Number(1), Number(2), Number(3)], True),
            ],
        )
        self.assertEqual(
            self.strategy._lnps_config,
            [
                {
                    "predicate_name": "test",
                    "arity": 2,
                    "mask": [3],
                    "pn": [Function("p", [Number(0)], True)],
                    "weight": Number(1),
                    "modifier": Function("true"),
                },
                {
                    "predicate_name": "plays",
                    "arity": 3,
                    "mask": [7],
                    "pn": [Function("p", [Number(0)], True)],
                    "weight": Number(1),
                    "modifier": Function("true"),
                },
            ],
        )

        # config
        self.strategy._lnps_config = []
        solver.ground([("config", [])])
        self.strategy._load_lnps_config(
            solver.control,
            [
                Function("test", [Number(2), Number(4)], True),
                Function("plays", [Number(1), Number(2), Number(3)], True),
            ],
        )
        self.assertEqual(
            self.strategy._lnps_config,
            [
                {
                    "predicate_name": "plays",
                    "arity": 3,
                    "mask": [2],
                    "pn": [Function("p", [Number(15)], True)],
                    "weight": Number(1),
                    "modifier": Function("true"),
                }
            ],
        )

    def test_check_variability(self):
        """
        Test the _check_variability method.
        """
        self.strategy._falsified = False
        self.strategy._lnps_config = [
            {
                "predicate_name": "plays",
                "arity": 3,
                "mask": [7],
                "pn": [Function("p", [Number(0)], True)],
                "weight": Function("inf"),
                "modifier": Function("true"),
            },
        ]
        self.assertFalse(self.strategy._check_variability())

        self.strategy._lnps_config = [
            {
                "predicate_name": "plays",
                "arity": 3,
                "mask": [7],
                "pn": [Function("p", [Number(0)], True)],
                "weight": Number(1),
                "modifier": Function("true"),
            },
        ]
        self.assertTrue(self.strategy._check_variability())

        self.strategy._falsified = True
        self.strategy._false_weight = Function("inf")
        self.assertFalse(self.strategy._check_variability())

    def test_post_first_solution(self):
        """
        Test the post_first_solution method.
        """
        self.strategy.solver = ClingoSolver()
        self.strategy.solver.setup(self.lns)
        self.strategy.solver.finished = False
        self.strategy._falsified = True
        self.strategy._variability = False
        self.strategy.config.time_limit = 12345678
        self.strategy.config.max_steps = 12345678
        self.lns.current_model.cost = [10, 20]
        self.lns.best_model.cost = [1, 2, 3, 4]
        self.lns.current_model.shown = [Function("a"), Function("b")]
        self.strategy._lnps_config = [
            {
                "predicate_name": "plays",
                "arity": 3,
                "mask": [7],
                "pn": [Function("p", [Number(0)], True)],
                "weight": Number(1),
                "modifier": Function("true"),
            },
        ]
        rules = (
            ":- not plays(X0,X1,X2), heuristic(plays(X0,X1,X2),inf,true,t)."
            ":- plays(X0,X1,X2), heuristic(plays(X0,X1,X2),inf,false,t)."
            "#heuristic plays(X0,X1,X2) : heuristic(plays(X0,X1,X2),W,M,t), W != inf. [W,M]"
            ":- plays(X0,X1,X2), not projected(plays(X0,X1,X2),t), __w(inf,t)."
            "#heuristic plays(X0,X1,X2) : plays(X0,X1,X2), not projected(plays(X0,X1,X2),t), "
            "__w(W,t), W != inf. [W,false]"
        )

        with (
            mock.patch.object(self.strategy, "_calc_opt_bound") as mock_calc_opt,
            mock.patch.object(self.strategy.solver, "ground") as mock_ground,
            mock.patch.object(self.strategy, "_load_lnps_config") as mock_load_lnps,
            mock.patch.object(self.strategy.solver, "add") as mock_add,
            mock.patch.object(self.strategy, "_check_variability", return_value=True) as mock_check_var,
            mock.patch.object(self.strategy.timer, "get_elapsed_time", return_value=2.748),
            mock.patch("sys.stdout", new=StringIO()) as out,
        ):
            self.strategy.post_first_solution(self.lns)
            mock_calc_opt.assert_called_once_with(self.strategy.lns_solver_config, self.lns.current_model.cost)
            mock_ground.assert_called_once_with([("config", [])])
            mock_load_lnps.assert_called_once_with(self.strategy.solver.control, self.lns.current_model.shown)
            mock_add.assert_called_once_with("heuristic", ["t"], rules)
            mock_check_var.assert_called_once()
            self.assertTrue(self.strategy._variability)

            self.assertEqual(self.strategy._iter_format, "{0:>12.3f} - {1:>8}: {2:>7}")
            # fmt: off
            self.assertEqual(
                out.getvalue(),
                (
                    "   time in s -     step:    cost\n"
                    "       2.748 -  initial: 1 2 3 4\n"
                ),
            )
            # fmt: on

    def test_check_stop(self):
        """
        Test the check_stop method.
        """
        self.strategy.solver = ClingoSolver()

        # nothing
        self.assertFalse(self.strategy.check_stop(self.lns))

        # time limit
        self.strategy.config.time_limit = 42
        with mock.patch("mod_lns.Timer.is_ringing", mock.PropertyMock(return_value=True)):
            self.assertTrue(self.strategy.check_stop(self.lns))

        # step limit
        self.strategy.config.max_steps = 10
        self.lns.step_c = 11
        self.assertTrue(self.strategy.check_stop(self.lns))

        # solver finished
        self.lns.step_c = 0
        self.strategy.solver.finished = True
        self.assertTrue(self.strategy.check_stop(self.lns))

    def test_pre_relax(self):
        """
        Test the pre_relax method.
        """
        self.strategy._printout = True
        self.strategy.pre_relax(self.lns)
        self.assertFalse(self.strategy._printout)

    def test_project(self):
        """
        Test the _project method.
        """
        shown_atoms = [
            Function("test"),
            Function("plays", [Number(1), Number(2), Number(3)], True),
        ]
        config = {
            "predicate_name": "plays",
            "arity": 3,
            "mask": [7],
            "pn": [Function("p", [Number(0)], True)],
            "weight": Number(1),
            "modifier": Function("true"),
        }
        self.assertEqual(
            self.strategy._project(shown_atoms, config),
            [Function("plays", [Number(1), Number(2), Number(3)], True)],
        )

    def test_filter(self):
        """
        Test the _filter method.
        """
        shown_atoms = [
            Function("plays", [Number(1), Number(2), Number(3)], True),
            Function("plays", [Number(3), Number(2), Number(3)], True),
        ]
        filtered_atoms = self.strategy._filter(shown_atoms, 3, 6, Function("p", [Number(50)], True))
        self.assertEqual(len(filtered_atoms), 1)
        self.assertTrue(filtered_atoms[0] in shown_atoms)

        filtered_atoms = self.strategy._filter(shown_atoms, 3, 7, Function("n", [Number(1)], True))
        self.assertEqual(len(filtered_atoms), 1)
        self.assertTrue(filtered_atoms[0] in shown_atoms)

        self.assertListEqual(
            self.strategy._filter(shown_atoms, 3, 0, Function("p", [Number(1)], True)),
            [],
        )

    def test_destroy(self):
        """
        Test the _destroy method.
        """
        shown_atoms = [
            Function("test"),
            Function("plays", [Number(1), Number(2), Number(3)], True),
            Function("plays", [Number(3), Number(2), Number(3)], True),
        ]
        config = {
            "predicate_name": "plays",
            "arity": 3,
            "mask": [7],
            "pn": [Function("p", [Number(50)], True)],
            "weight": Number(1),
            "modifier": Function("true"),
        }
        filtered_atoms = [Function("plays", [Number(1), Number(2), Number(3)], True)]
        with mock.patch.object(self.strategy, "_filter", return_value=filtered_atoms) as mock_filter:
            self.assertListEqual(
                self.strategy._destroy(shown_atoms, config),
                [Function("plays", [Number(3), Number(2), Number(3)], True)],
            )
            mock_filter.assert_called_once()

            mock_filter.reset_mock()
            config = {
                "predicate_name": "plays",
                "arity": 3,
                "mask": [7],
                "pn": [Function("p", [Number(-50)], True)],
                "weight": Number(1),
                "modifier": Function("true"),
            }
            self.assertListEqual(
                self.strategy._destroy(shown_atoms, config),
                [Function("plays", [Number(1), Number(2), Number(3)], True)],
            )
            mock_filter.assert_called_once()

    def test_prioritize(self):
        """
        Test the _prioritize method.
        """
        targets = [Function("plays", [Number(1), Number(2), Number(3)], True)]
        config = {
            "predicate_name": "plays",
            "arity": 3,
            "mask": [7],
            "pn": [Function("p", [Number(50)], True)],
            "weight": Number(1),
            "modifier": Function("true"),
        }
        self.assertListEqual(
            self.strategy._prioritize(targets, config, 42),
            [
                Function(
                    "heuristic",
                    [
                        Function("plays", [Number(1), Number(2), Number(3)], True),
                        Number(1),
                        Function("true"),
                        Number(42),
                    ],
                )
            ],
        )

    def test_generate_projected_atoms(self):
        """
        Test the _generate_projected_atoms method.
        """
        atoms = [Function("plays", [Number(1), Number(2), Number(3)], True)]
        self.assertListEqual(
            self.strategy._generate_projected_atoms(atoms, 42),
            [
                Function(
                    "projected",
                    [
                        Function("plays", [Number(1), Number(2), Number(3)], True),
                        Number(42),
                    ],
                )
            ],
        )

    def test_relax(self):
        """
        Test the relax method.
        """
        self.strategy._falsified = True
        self.strategy._false_weight = Number(12)
        self.lns.step_c = 42
        self.strategy._lnps_config = [
            {
                "predicate_name": "plays",
                "arity": 3,
                "mask": [7],
                "pn": [Function("p", [Number(50)], True)],
                "weight": Number(1),
                "modifier": Function("true"),
            }
        ]
        self.lns.current_model.shown = [
            Function("test"),
            Function("plays", [Number(1), Number(2), Number(3)], True),
            Function("plays", [Number(3), Number(2), Number(3)], True),
        ]
        with (
            mock.patch.object(
                self.strategy,
                "_project",
                return_value=[
                    Function("plays", [Number(1), Number(2), Number(3)], True),
                    Function("plays", [Number(3), Number(2), Number(3)], True),
                ],
            ) as mock_project,
            mock.patch.object(
                self.strategy,
                "_destroy",
                return_value=[Function("plays", [Number(1), Number(2), Number(3)], True)],
            ) as mock_destroy,
            mock.patch.object(
                self.strategy,
                "_prioritize",
                return_value=[
                    Function(
                        "heuristic",
                        [
                            Function("plays", [Number(1), Number(2), Number(3)], True),
                            Number(1),
                            Function("true"),
                            Number(42),
                        ],
                    )
                ],
            ) as mock_prioritize,
            mock.patch.object(
                self.strategy,
                "_generate_projected_atoms",
                return_value=[
                    Function(
                        "projected",
                        [
                            Function("plays", [Number(1), Number(2), Number(3)], True),
                            Number(42),
                        ],
                        True,
                    ),
                    Function(
                        "projected",
                        [
                            Function("plays", [Number(3), Number(2), Number(3)], True),
                            Number(42),
                        ],
                        True,
                    ),
                ],
            ) as mock_generate,
        ):
            self.assertListEqual(
                self.strategy.relax(self.lns),
                [
                    Function(
                        "heuristic",
                        [
                            Function("plays", [Number(1), Number(2), Number(3)], True),
                            Number(1),
                            Function("true", [], True),
                            Number(42),
                        ],
                        True,
                    ),
                    Function(
                        "projected",
                        [
                            Function("plays", [Number(1), Number(2), Number(3)], True),
                            Number(42),
                        ],
                        True,
                    ),
                    Function(
                        "projected",
                        [
                            Function("plays", [Number(3), Number(2), Number(3)], True),
                            Number(42),
                        ],
                        True,
                    ),
                    Function("__w", [Number(12), Number(42)], True),
                ],
            )
            mock_project.assert_called_once_with(self.lns.current_model.shown, self.strategy._lnps_config[0])
            mock_destroy.assert_called_once_with(self.lns.current_model.shown, self.strategy._lnps_config[0])
            mock_prioritize.assert_called_once_with(
                [Function("plays", [Number(1), Number(2), Number(3)], True)],
                self.strategy._lnps_config[0],
                42,
            )
            mock_generate.assert_called_once_with(
                [
                    Function("plays", [Number(1), Number(2), Number(3)], True),
                    Function("plays", [Number(3), Number(2), Number(3)], True),
                ],
                42,
            )

    def test_repair(self):
        """
        Test the repair method.
        """
        self.strategy.solver = ClingoSolver()
        self.lns.step_c = 42
        self.strategy.prev_fixed_atoms = [
            Function(
                "heuristic",
                [
                    Function("plays", [Number(1), Number(2), Number(3)], True),
                    Number(1),
                    Function("true", [], True),
                    Number(41),
                ],
                True,
            )
        ]
        fixed_atoms = [
            Function(
                "heuristic",
                [
                    Function("plays", [Number(3), Number(2), Number(3)], True),
                    Number(1),
                    Function("true", [], True),
                    Number(42),
                ],
                True,
            )
        ]
        new_model = Model()

        with (
            mock.patch.object(self.strategy.solver, "release_external") as mock_release_external,
            mock.patch.object(self.strategy.solver, "add") as mock_add,
            mock.patch.object(self.strategy.solver, "ground") as mock_ground,
            mock.patch.object(self.strategy.solver, "assign_external") as mock_assign_external,
            mock.patch.object(self.strategy, "_update_time_limit") as mock_update_time,
            mock.patch.object(self.strategy.solver, "solve", return_value=new_model) as mock_solve,
        ):
            self.assertEqual(self.strategy.repair(self.lns, fixed_atoms), new_model)
            mock_release_external.assert_called_once_with(
                Function(
                    "heuristic",
                    [
                        Function("plays", [Number(1), Number(2), Number(3)], True),
                        Number(1),
                        Function("true", [], True),
                        Number(41),
                    ],
                    True,
                )
            )
            mock_add.assert_called_once_with("external", ["t"], "#external heuristic(plays(3,2,3),1,true,42).")
            mock_ground.assert_has_calls(
                [
                    mock.call([("external", [Number(42)])]),
                    mock.call([("heuristic", [Number(42)])]),
                ]
            )
            mock_assign_external.assert_called_once_with(
                Function(
                    "heuristic",
                    [
                        Function("plays", [Number(3), Number(2), Number(3)], True),
                        Number(1),
                        Function("true", [], True),
                        Number(42),
                    ],
                    True,
                ),
                True,
            )
            mock_update_time.assert_called_once_with(self.strategy.lns_solver_config)
            mock_solve.assert_called_once_with(self.strategy.lns_solver_config)

    def test_check_accept(self):
        """
        Test the check_accept method.
        """
        self.lns.current_model.cost = [10, 20]
        self.strategy.config.acceptance_rate = 20  # 20%
        self.lns.new_model = None
        self.assertFalse(self.strategy.check_accept(self.lns))

        self.lns.new_model = Model()
        self.lns.new_model.cost = [10, 24]
        self.assertFalse(self.strategy.check_accept(self.lns))
        self.lns.new_model.cost = [10, 23]
        self.assertTrue(self.strategy.check_accept(self.lns))

    def test_accepted(self):
        """
        Test the accepted method.
        """
        with mock.patch.object(self.strategy, "_calc_opt_bound") as mock_calc_opt_bound:
            self.strategy.accepted(self.lns)
            mock_calc_opt_bound.assert_called_once_with(self.strategy.lns_solver_config, self.lns.current_model.cost)

    def test_check_better(self):
        """
        Test the check_better method.
        """
        self.lns.best_model.cost = [10, 20]
        self.lns.new_model = None
        self.assertFalse(self.strategy.check_better(self.lns))

        self.lns.new_model = Model()
        self.lns.new_model.cost = [10, 24]
        self.assertFalse(self.strategy.check_better(self.lns))
        self.lns.new_model.cost = [10, 9]
        self.assertTrue(self.strategy.check_better(self.lns))

    def test_better(self):
        """
        Test the better method.
        """
        self.strategy._printout = False
        self.strategy.better(self.lns)
        self.assertTrue(self.strategy._printout)

    def test_increase_solve_limit(self):
        """
        Test the _increase_solve_limit method.
        """
        self.strategy.config.solve_limit_increase_rate = 20
        config = SolverConfig()

        config.solve_limit = "200,umax"
        self.strategy._increase_solve_limit(config)
        self.assertEqual(config.solve_limit, "240,umax")

        config.solve_limit = "200,4294967295"
        self.strategy._increase_solve_limit(config)
        self.assertEqual(config.solve_limit, "240,umax")

    def test_increase_time_limit(self):
        """
        Test the _increase_time_limit method.
        """
        self.strategy.config.time_limit = 1000
        self.strategy.config.time_limit_increase_rate = 20
        config = SolverConfig()

        with mock.patch.object(self.strategy.timer, "remaining_time", return_value=400):
            config.time_limit = 500
            self.strategy._increase_time_limit(config)
            self.assertEqual(config.time_limit, 500)

        with mock.patch.object(self.strategy.timer, "remaining_time", return_value=800):
            config.time_limit = 200
            self.strategy._increase_time_limit(config)
            self.assertEqual(config.time_limit, 240)

    def test_pre_next_iteration(self):
        """
        Test the pre_next_iteration method.
        """
        self.strategy._printout = True
        self.strategy.config.status_interval = 5
        self.lns.step_c = 4
        self.lns.best_model.cost = [2, 4]
        with (
            mock.patch.object(self.strategy, "_increase_solve_limit") as mock_increase_solve,
            mock.patch.object(self.strategy, "_increase_time_limit") as mock_increase_time,
            mock.patch("sys.stderr", new=StringIO()) as out,
        ):
            with self.assertRaises(RuntimeError):
                self.strategy.pre_next_iteration(self.lns)
                mock_increase_solve.assert_called_once_with(self.strategy.lns_solver_config)
                mock_increase_time.assert_called_once_with(self.strategy.lns_solver_config)

        self.strategy._iter_format = "{0:>9.3f} - {1:>7}: {2:>4}"

        with (
            mock.patch.object(self.strategy.timer, "get_elapsed_time", return_value=10),
            mock.patch("sys.stdout", new=StringIO()) as out,
        ):
            self.strategy.pre_next_iteration(self.lns)
            self.assertEqual(out.getvalue(), "   10.000 -       4:  2 4\n")

        self.strategy._printout = False
        self.lns.step_c = 5
        with (
            mock.patch.object(self.strategy.timer, "get_elapsed_time", return_value=10),
            mock.patch("sys.stdout", new=StringIO()) as out,
        ):
            self.strategy.pre_next_iteration(self.lns)
            self.assertEqual(out.getvalue(), "   10.000 -       5:  2 4\n")

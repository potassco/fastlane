"""
Test cases for LNS class.
"""

from io import StringIO
from unittest import TestCase, mock

from clingo.symbol import Function, Number, String

from mod_lns import Model, Timer
from mod_lns.interfaces.solver import SolverConfig
from mod_lns.lns import LNS
from mod_lns.lns_options import LNSOptions

# pylint: disable=protected-access, too-many-public-methods


class TestLNS(TestCase):
    """
    Test cases for the LNS class.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        self.lns = LNS(["example.lp"])
        self.lns.logger = mock.Mock()

    def test_init(self):
        """
        Test the initialization of the LNS class.
        """
        self.assertIsInstance(self.lns.options, LNSOptions)
        logger = mock.Mock()
        config = mock.Mock()
        config.log_level = 20

        with (
            mock.patch("mod_lns.lns.LNS.parse_options") as mock_parse_options,
            mock.patch("mod_lns.lns.setup_logger", return_value=logger) as mock_setup_logger,
        ):
            lns = LNS(["example.lp"], {"time_limit": 10}, config)

            mock_parse_options.assert_called_once_with({"time_limit": 10})
            mock_setup_logger.assert_called_once_with("LNS", 20)

        self.assertEqual(lns.options, config)
        self.assertEqual(lns.files, ["example.lp"])
        self.assertEqual(lns.step_c, 0)
        self.assertFalse(lns._printout)
        self.assertIsInstance(lns.timer, Timer)

    def test_parse_options(self) -> None:
        """
        Test the parse_options method.
        """
        with mock.patch.object(self.lns.options, "prepare") as mock_prepare:
            self.lns.options.time_limit = 10
            self.lns.parse_options({})
            self.assertEqual(self.lns.options.time_limit, 10)

            LNSOptions.preset_values["test"] = {"time_limit": 20}
            self.lns.parse_options({"preset": "test"})
            self.assertEqual(self.lns.options.time_limit, 20)

            self.lns.parse_options({"preset": "test", "time_limit": 30})
            self.assertEqual(self.lns.options.time_limit, 30)
            self.assertEqual(mock_prepare.call_count, 3)

    def test_pre_setup(self):
        """
        Test the pre_setup method.
        """
        self.lns.options.time_limit = 10
        self.lns.options.seed = 42
        init_solver_config = SolverConfig()
        lns_solver_config = SolverConfig()

        with (
            mock.patch.object(self.lns.timer, "start") as mock_start,
            mock.patch.object(
                self.lns.options, "get_init_solver_configuration", return_value=init_solver_config
            ) as mock_get_init_solver_configuration,
            mock.patch.object(
                self.lns.options, "get_lns_solver_configuration", return_value=lns_solver_config
            ) as mock_get_lns_solver_configuration,
            mock.patch("mod_lns.lns.random.seed") as mock_seed,
        ):
            self.lns.pre_setup()

            mock_start.assert_called_once_with(self.lns.options.time_limit)
            mock_get_init_solver_configuration.assert_called_once()
            mock_get_lns_solver_configuration.assert_called_once()
            self.assertEqual(self.lns.init_solver_config.time_limit, self.lns.options.time_limit)
            mock_seed.assert_called_once_with(42)

        init_solver_config.time_limit = 20
        with (
            mock.patch.object(self.lns.timer, "start") as mock_start,
            mock.patch.object(
                self.lns.options, "get_init_solver_configuration", return_value=init_solver_config
            ) as mock_get_init_solver_configuration,
            mock.patch.object(
                self.lns.options, "get_lns_solver_configuration", return_value=lns_solver_config
            ) as mock_get_lns_solver_configuration,
            mock.patch("mod_lns.lns.random.seed") as mock_seed,
        ):
            self.lns.pre_setup()

            mock_start.assert_called_once_with(self.lns.options.time_limit)
            mock_get_init_solver_configuration.assert_called_once()
            mock_get_lns_solver_configuration.assert_called_once()
            mock_seed.assert_called_once_with(42)
            self.assertEqual(self.lns.init_solver_config.time_limit, self.lns.options.time_limit)

    def test_setup_solver(self):
        """
        Test the setup_solver method.
        """
        self.lns.solver = mock.Mock()
        self.lns.options.minimize_variable = Function("x")
        self.lns.options.seed = 42
        self.lns.options.parallel_mode = "2"
        self.lns.options.clingo_args = "--some-arg"

        self.lns.setup_solver()

        self.lns.solver.setup.assert_called_once_with(self.lns, ["--seed=42", "--parallel-mode=2", "--some-arg"])
        self.assertEqual(self.lns.solver.minimize_variable, self.lns.options.minimize_variable)

    def test_post_setup(self):
        """
        Test the post_setup method.
        """
        self.lns.solver = mock.Mock()

        self.lns.post_setup()

        self.lns.solver.ground.assert_called_once_with([("base", [])], self.lns.options.context)

    def test_get_first_solution(self):
        """
        Test the get_first_solution method.
        """
        self.lns.solver = mock.Mock()
        self.lns.init_solver_config = mock.Mock()
        self.lns.solver.solve.return_value = None
        prev_current_model = self.lns.current_model
        prev_best_model = self.lns.best_model

        with mock.patch("mod_lns.lns.update_time_limit") as mock_update_time_limit:
            self.assertFalse(self.lns.get_first_solution())
            mock_update_time_limit.assert_called_once_with(self.lns, self.lns.init_solver_config)

        self.lns.solver.solve.assert_called_once_with(self.lns.init_solver_config)
        self.assertIsNone(self.lns.new_model)
        self.assertIs(self.lns.current_model, prev_current_model)
        self.assertIs(self.lns.best_model, prev_best_model)

        self.lns.solver = mock.Mock()
        new_model = mock.Mock()
        self.lns.solver.solve.return_value = new_model

        with mock.patch("mod_lns.lns.update_time_limit") as mock_update_time_limit:
            self.assertTrue(self.lns.get_first_solution())
            mock_update_time_limit.assert_called_once_with(self.lns, self.lns.init_solver_config)

        self.lns.solver.solve.assert_called_once_with(self.lns.init_solver_config)
        self.assertIs(self.lns.new_model, new_model)
        self.assertIs(self.lns.current_model, new_model)
        self.assertIs(self.lns.best_model, new_model)

    def test_post_first_solution(self):
        """
        Test the post_first_solution method.
        """
        self.lns.solver = mock.Mock()
        self.lns.solver.finished = False
        self.lns.options.fix = "heuristics"

        self.lns.current_model = mock.Mock()
        self.lns.best_model = mock.Mock()
        self.lns.best_model.get_cost_str.return_value = "3 1"

        self.lns.timer = mock.Mock()
        self.lns.timer.get_elapsed_time.return_value = 12.5

        config_catalog = {"strategy": "roulette", "configs": {"c1": {}}}
        strategy = mock.Mock()
        strategy.get_initial_config.return_value = {"selected": "c1"}

        header_fmt = "header: {} | {} | {}"
        iter_fmt = "iter: {} | {} | {}"

        with (
            mock.patch("mod_lns.lns.ConfigParser.parse_lns_config", return_value=config_catalog) as mock_parse,
            mock.patch.object(self.lns.options, "build_adaptive_strategy", return_value=strategy) as mock_build,
            mock.patch("mod_lns.lns.generate_heuristic_subprogram", return_value="heuristic_rule.") as mock_heur,
            mock.patch("mod_lns.lns.get_output_format", return_value=(header_fmt, iter_fmt)) as mock_output,
            mock.patch("builtins.print") as mock_print,
        ):
            self.lns.post_first_solution()

            mock_parse.assert_called_once_with(self.lns)
            mock_build.assert_called_once_with(config_catalog["strategy"], self.lns.logger)
            strategy.get_initial_config.assert_called_once_with(config_catalog, self.lns.current_model)

            mock_heur.assert_called_once_with(config_catalog)
            self.lns.logger.debug.assert_called_once_with("Adding heuristics:\n%s", "heuristic_rule.")
            self.lns.solver.add.assert_called_once_with("heuristic", ["t"], "heuristic_rule.")

            mock_output.assert_called_once_with("3 1", self.lns.options.time_limit, self.lns.options.max_steps)
            self.assertEqual(self.lns._iter_format, iter_fmt)

            mock_print.assert_has_calls(
                [
                    mock.call("header: time in s | step | cost"),
                    mock.call("iter: 12.5 | initial | 3 1", flush=True),
                ]
            )
            self.assertEqual(mock_print.call_count, 2)

            self.assertEqual(self.lns.best_model.get_cost_str.call_count, 2)
            self.lns.timer.get_elapsed_time.assert_called_once()

    def test_check_stop(self):
        """
        Test the check_stop method.
        """
        self.lns.timer = mock.Mock()
        self.lns.timer.is_ringing = False
        self.lns.options.time_limit = 10
        self.lns.options.max_steps = 3
        self.lns.solver = mock.Mock()
        self.lns.solver.stop = False
        self.lns.solver.finished = False
        self.lns.step_c = 2

        with mock.patch("builtins.print") as mock_print:
            # dont stop
            self.assertFalse(self.lns.check_stop())

            # exceeding time limit
            self.lns.timer.is_ringing = True
            self.assertTrue(self.lns.check_stop())

            # exceeding max steps
            self.lns.timer.is_ringing = False
            self.lns.step_c = 3
            self.assertTrue(self.lns.check_stop())

            # solver done
            self.lns.step_c = 2
            self.lns.solver.finished = True
            self.assertTrue(self.lns.check_stop())

            self.lns.solver.stop = True
            self.lns.solver.finished = False
            self.assertTrue(self.lns.check_stop())

            mock_print.assert_has_calls(
                [
                    mock.call("Time limit (10 seconds) reached."),
                    mock.call("Maximum number of steps (3) reached."),
                ]
            )
            self.assertEqual(mock_print.call_count, 2)

    def test_check_variability(self):
        """
        Test the _check_variability method.
        """
        self.lns._active_config = {
            "prioritize_operators": [
                {"name": "1_true", "value": "inf", "modifier": "true"},
                {"name": "5_sign", "value": 5, "modifier": "sign"},
            ]
        }
        self.assertFalse(self.lns._check_variability())

        self.lns._active_config = {"prioritize_operators": [{"name": "5_sign", "value": 5, "modifier": "sign"}]}
        self.assertTrue(self.lns._check_variability())

    def test_pre_destroy(self):
        """
        Test the pre_destroy method.
        """
        self.lns._printout = True
        self.lns._is_variable = False
        model = mock.Mock()
        self.lns.current_model = model
        specs = {
            "_project": {
                Function(
                    "_project",
                    [String("plays_3"), Function("plays", [Number(1), Number(2), Number(3)], True)],
                    True,
                )
            }
        }

        with (
            mock.patch.object(self.lns, "_check_variability", return_value=True) as mock_check,
            mock.patch("mod_lns.lns.ConfigParser.get_op_specs", return_value=specs) as mock_get_specs,
        ):
            self.lns.pre_destroy()

            mock_check.assert_called_once()
            mock_get_specs.assert_called_once_with(model)
            self.assertFalse(self.lns._printout)
            self.assertTrue(self.lns._is_variable)
            self.assertDictEqual(self.lns._op_specs, specs)

    def test_destroy(self):
        """
        Test the destroy method.
        """
        r_set = {Function("plays", [Number(1), Number(2), Number(3)], True)}
        model = mock.Mock()
        config = mock.Mock()
        specs = mock.Mock()
        self.lns.current_model = model
        self.lns._active_config = config
        self.lns._op_specs = specs

        with mock.patch("mod_lns.lns.destroy_config", return_value=r_set) as mock_destroy:
            result = self.lns.destroy()

            mock_destroy.assert_called_once_with(model, config, specs, self.lns.logger)
            self.assertEqual(result, r_set)

    def test_prepare_lns_solver_config(self):
        """
        Test the _prepare_lns_solver_config method.
        """
        self.lns._is_variable = True
        self.lns.lns_solver_config = mock.Mock()
        self.lns.current_model = mock.Mock()
        self.lns.current_model.cost = [4, 2]
        self.lns.options.lns_opt_mode = {"mode": "opt", "modifier": "dynamic", "nf": 2}
        with (
            mock.patch("mod_lns.lns.get_opt_bound", return_value="opt,2,dynamic") as mock_get_opt,
            mock.patch("mod_lns.lns.update_time_limit") as mock_update_time_limit,
        ):
            self.lns._prepare_lns_solver_config()

            mock_get_opt.assert_called_once_with([4, 2], "opt", opt_modifier="dynamic", opt_nf=2)
            mock_update_time_limit.assert_called_once_with(self.lns, self.lns.lns_solver_config)
            self.assertEqual(self.lns.lns_solver_config.opt_mode, "opt,2,dynamic")
            self.assertTrue(self.lns.lns_solver_config.variability)

    def test_next_no_improvement_cutoff_count(self):
        """
        Test the _next_no_improvement_cutoff_count method.
        """
        self.lns.stats = []
        model = None
        self.lns.solver = mock.Mock()
        model = mock.Mock()
        model.cost = [4, 2]
        self.lns.best_model = mock.Mock()
        self.lns.best_model.cost = [3, 2]

        # unsat, no stats -> default 0
        self.lns.solver.result = "UNSATISFIABLE"
        self.assertEqual(self.lns._next_no_improvement_cutoff_count(model), 0)
        # unsat, keep ic
        self.lns.stats = [{"no_improvement_cutoff_count": 2}]
        self.assertEqual(self.lns._next_no_improvement_cutoff_count(model), 2)
        # sat, model not better, increase ic
        self.lns.solver.result = "SATISFIABLE"
        self.assertEqual(self.lns._next_no_improvement_cutoff_count(model), 3)
        # model better, reset ic
        model.cost = [1, 2]
        self.assertEqual(self.lns._next_no_improvement_cutoff_count(model), 0)

    def test_update_stats(self):
        """
        Test the update_stats method.
        """
        self.lns.solver = mock.Mock()
        self.lns.solver.stats = {"some_stat": 42}
        model = mock.Mock()
        self.lns.step_c = 1

        with (
            mock.patch.object(self.lns, "_next_no_improvement_cutoff_count", return_value=2) as mock_next_ic,
            mock.patch.object(self.lns.timer, "get_elapsed_time", return_value=5.0) as mock_elapsed,
        ):
            self.lns.update_stats(model)

            mock_next_ic.assert_called_once_with(model)
            mock_elapsed.assert_called_once()
            self.assertDictEqual(
                self.lns.stats[-1], {"step": 1, "elapsed_time": 5.0, "no_improvement_cutoff_count": 2, "some_stat": 42}
            )

    def test_repair(self):
        """
        Test the repair method.
        """
        model = mock.Mock()
        fixed_atoms = {mock.Mock()}
        fixed_heu = {mock.Mock()}
        self.lns.stats = [{}]

        self.lns.options.fix = "heuristics"
        with (
            mock.patch.object(self.lns, "_prepare_lns_solver_config") as mock_prepare,
            mock.patch("mod_lns.lns.get_fixed_atoms_heuristics", return_value=fixed_heu) as mock_fixed_heu,
            mock.patch("mod_lns.lns.repair_heuristics", return_value=model) as mock_repair,
            mock.patch.object(self.lns, "update_stats") as mock_update_stats,
        ):
            new_model = self.lns.repair(fixed_atoms)

            mock_prepare.assert_called_once()
            mock_fixed_heu.assert_called_once()
            mock_repair.assert_called_once()
            mock_update_stats.assert_called_once_with(new_model)
            self.assertIs(new_model, model)
            self.assertSetEqual(self.lns.prev_fixed_atoms, fixed_heu)

        self.lns.options.fix = "assumptions"
        with (
            mock.patch.object(self.lns, "_prepare_lns_solver_config") as mock_prepare,
            mock.patch("mod_lns.lns.repair_assumptions", return_value=model) as mock_repair,
            mock.patch.object(self.lns, "update_stats") as mock_update_stats,
        ):
            new_model = self.lns.repair(fixed_atoms)

            mock_prepare.assert_called_once()
            mock_repair.assert_called_once()
            mock_update_stats.assert_called_once_with(new_model)
            self.assertIs(new_model, model)

        with self.assertRaises(RuntimeError):
            self.lns.options.fix = "unknown"
            self.lns.repair(fixed_atoms)

    def test_post_repair(self):
        """
        Test the post_repair method.
        """
        config = mock.Mock()
        self.lns._adaptive_strategy = mock.Mock()
        self.lns._adaptive_strategy.update_config.return_value = config

        self.lns.post_repair()

        self.assertIs(self.lns._active_config, config)

    def test_check_accept(self):
        """
        Test the check_accept method.
        """
        self.lns.options.accept_variability = 30
        self.lns.options.accept_improvement = 10

        self.lns.current_model = mock.Mock()
        self.lns.current_model.shown = {"curr"}
        self.lns.current_model.cost = [10, 100]

        # no model -> not accepted, variability is not calculated
        self.lns.new_model = None
        with mock.patch("mod_lns.lns.calculate_variability") as mock_calculate:
            self.assertFalse(self.lns.check_accept())
            mock_calculate.assert_not_called()

        # accepted: variability high enough and cost below threshold [10, 110]
        self.lns.new_model = mock.Mock()
        self.lns.new_model.shown = {"new"}
        self.lns.new_model.cost = [10, 109]
        with mock.patch("mod_lns.lns.calculate_variability", return_value=40) as mock_calculate:
            self.assertTrue(self.lns.check_accept())
            mock_calculate.assert_called_once_with(self.lns.new_model.shown, self.lns.current_model.shown)

        # rejected: variability too low
        self.lns.new_model.cost = [10, 1]
        with mock.patch("mod_lns.lns.calculate_variability", return_value=20) as mock_calculate:
            self.assertFalse(self.lns.check_accept())
            mock_calculate.assert_called_once_with(self.lns.new_model.shown, self.lns.current_model.shown)

        # rejected: cost not strictly better than threshold (equal is not enough)
        self.lns.new_model.cost = [10, 110]
        with mock.patch("mod_lns.lns.calculate_variability", return_value=40) as mock_calculate:
            self.assertFalse(self.lns.check_accept())
            mock_calculate.assert_called_once_with(self.lns.new_model.shown, self.lns.current_model.shown)

    def test_accepted(self):
        """
        Test the accepted method.
        """
        self.lns.accepted()
        self.lns.logger.debug.assert_called_once_with("new model accepted")

    def test_check_better(self):
        """
        Test the check_better method.
        """
        self.lns.best_model = mock.Mock()
        self.lns.best_model.cost = [10, 100]

        # no model -> not better
        self.lns.new_model = None
        self.assertFalse(self.lns.check_better())

        # better: cost strictly better
        self.lns.new_model = mock.Mock()
        self.lns.new_model.cost = [10, 99]
        self.assertTrue(self.lns.check_better())

        # not better: cost equal
        self.lns.new_model.cost = [10, 100]
        self.assertFalse(self.lns.check_better())

        # not better: cost worse
        self.lns.new_model.cost = [10, 101]
        self.assertFalse(self.lns.check_better())

    def test_better(self):
        """
        Test the better method.
        """
        self.lns._printout = False

        self.lns.better()

        self.lns._printout = True

    def test_pre_next_iteration(self):
        """
        Test the pre_next_iteration method.
        """
        self.lns.lns_solver_config = mock.Mock()
        self.lns.lns_solver_config.solve_limit = "1000,1000"
        self.lns.lns_solver_config.time_limit = 10
        self.lns.lns_solver_config.cutoff = 10
        self.lns._printout = True
        self.lns._iter_format = "iter: {} | {} | {}"
        self.lns.stats = [{}]

        with (
            mock.patch("mod_lns.lns.increase_solve_limit", return_value="1200,1200") as mock_increase_solve,
            mock.patch("mod_lns.lns.increase_time_limit", return_value=12) as mock_increase_time,
            mock.patch("mod_lns.lns.increase_cutoff", return_value=12) as mock_increase_cutoff,
            mock.patch("builtins.print") as mock_print,
        ):
            self.lns.pre_next_iteration()

            mock_increase_solve.assert_called_once()
            mock_increase_time.assert_called_once()
            mock_increase_cutoff.assert_called_once()

            self.assertEqual(self.lns.lns_solver_config.solve_limit, "1200,1200")
            self.assertEqual(self.lns.lns_solver_config.time_limit, 12)
            self.assertEqual(self.lns.lns_solver_config.cutoff, 12)
            mock_print.assert_called_once()

            self.lns._iter_format = ""
            with self.assertRaises(RuntimeError):
                self.lns.pre_next_iteration()

    def test_print_result(self):
        """
        Test the print_result method.
        """
        self.lns.best_model = mock.Mock()
        self.lns.timer = mock.Mock()
        self.lns.timer.get_elapsed_time.return_value = 12.5
        self.lns.solver = mock.Mock()
        self.lns.solver.result = "SATISFIABLE"
        self.lns.solver.optimum = "yes"
        self.lns.step_c = 5

        with mock.patch("sys.stdout", new=StringIO()) as out:
            self.lns.print_result()
            self.lns.best_model.print_model.assert_called_once()
            self.assertEqual(
                out.getvalue(),
                (
                    "--------------------------------------------------------------------------------------\n"
                    "Result\n"
                    "--------------------------------------------------------------------------------------\n"
                    "SATISFIABLE\n"
                    "Optimum: yes\n"
                    "Iterations: 5\n"
                    "Overall time: 12.500s\n"
                    "--------------------------------------------------------------------------------------\n"
                ),
            )

    def test_main(self):
        """
        Test the main method (successful run).
        """
        initial_model = Model()
        initial_model.shown = {Function("a")}
        repaired_model = Model()

        def _get_first_solution_side_effect():
            self.lns.new_model = initial_model
            self.lns.current_model = initial_model
            self.lns.best_model = initial_model
            return True

        with (
            mock.patch.object(self.lns, "pre_setup") as mock_pre_setup,
            mock.patch.object(self.lns, "setup_solver") as mock_setup_solver,
            mock.patch.object(self.lns, "post_setup") as mock_post_setup,
            mock.patch.object(
                self.lns, "get_first_solution", side_effect=_get_first_solution_side_effect
            ) as mock_get_first_solution,
            mock.patch.object(self.lns, "post_first_solution") as mock_post_first_solution,
            mock.patch.object(self.lns, "check_stop", side_effect=[False, True]) as mock_check_stop,
            mock.patch.object(self.lns, "pre_destroy") as mock_pre_destroy,
            mock.patch.object(self.lns, "destroy", return_value={Function("a")}) as mock_destroy,
            mock.patch.object(self.lns, "repair", return_value=repaired_model) as mock_repair,
            mock.patch.object(self.lns, "post_repair") as mock_post_repair,
            mock.patch.object(self.lns, "check_accept", return_value=True) as mock_check_accept,
            mock.patch.object(self.lns, "accepted") as mock_accepted,
            mock.patch.object(self.lns, "check_better", return_value=True) as mock_check_better,
            mock.patch.object(self.lns, "better") as mock_better,
            mock.patch.object(self.lns, "pre_next_iteration") as mock_pre_next_iteration,
            mock.patch.object(self.lns, "print_result") as mock_print_result,
        ):
            self.lns.main()

            mock_pre_setup.assert_called_once()
            mock_setup_solver.assert_called_once()
            mock_post_setup.assert_called_once()
            mock_get_first_solution.assert_called_once()
            mock_post_first_solution.assert_called_once()

            self.assertEqual(mock_check_stop.call_count, 2)
            mock_pre_destroy.assert_called_once()
            mock_destroy.assert_called_once()
            mock_repair.assert_called_once()
            mock_post_repair.assert_called_once()
            mock_check_accept.assert_called_once()
            mock_accepted.assert_called_once()
            mock_check_better.assert_called_once()
            mock_better.assert_called_once()
            mock_pre_next_iteration.assert_called_once()
            mock_print_result.assert_called_once()

            self.assertIs(self.lns.current_model, repaired_model)
            self.assertIs(self.lns.best_model, repaired_model)
            self.assertEqual(self.lns.step_c, 1)

    def test_main_no_first_solution(self):
        """
        Test main method when no initial solution is found.
        """
        with (
            mock.patch.object(self.lns, "pre_setup") as mock_pre_setup,
            mock.patch.object(self.lns, "setup_solver") as mock_setup_solver,
            mock.patch.object(self.lns, "post_setup") as mock_post_setup,
            mock.patch.object(self.lns, "get_first_solution", return_value=False) as mock_get_first_solution,
            mock.patch.object(self.lns, "post_first_solution") as mock_post_first_solution,
            mock.patch.object(self.lns, "print_result") as mock_print_result,
        ):
            with self.assertRaises(SystemExit):
                self.lns.main()

            mock_pre_setup.assert_called_once()
            mock_setup_solver.assert_called_once()
            mock_post_setup.assert_called_once()
            mock_get_first_solution.assert_called_once()
            mock_post_first_solution.assert_not_called()
            mock_print_result.assert_not_called()

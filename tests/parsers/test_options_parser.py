"""
Test cases for the options parser module.
"""

import logging
import tempfile
from argparse import ArgumentTypeError
from unittest import TestCase, mock

from clingo import parse_term

from fastlane import UNSET
from fastlane.lib.auto_destruction_converters.last_improv import LastImprovementDestructionConverter
from fastlane.lib.solvers.clingcon_solver import ClingconSolver
from fastlane.parsers.options_parser import (
    OptionsParser,
    _build_preset_description_text,
    _build_preset_help_text,
    _format_preset_option_value,
    _parse_0_1_float,
    _parse_adaptive_strategy,
    _parse_auto_converter,
    _parse_configuration,
    _parse_context,
    _parse_destruction,
    _parse_heuristic,
    _parse_init_opt_mode,
    _parse_lns_opt_mode,
    _parse_minimize_variable,
    _parse_opt_heuristic,
    _parse_opt_strategy,
    _parse_parallel_mode,
    _parse_percent,
    _parse_pos_int,
    _parse_pos_int_or_none,
    _parse_solve_limit,
    _parse_solver,
    _replace_default,
)

# pylint: disable=too-many-public-methods


class TestOptionsParser(TestCase):
    """
    Test cases for the OptionsParser class.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        self.parser = OptionsParser.get_parser()

    def test_parse_solver(self):
        """
        Test the _parse_solver function.
        """
        solver = mock.Mock()
        solvers = {"solver_name": solver}
        self.assertEqual(_parse_solver(solvers, "solver_name"), solver)
        with self.assertRaises(ArgumentTypeError):
            _parse_solver(solvers, "unknown_solver")

    def test_parse_pos_int(self):
        """
        Test the _parse_pos_int function.
        """
        self.assertEqual(_parse_pos_int("5"), 5)
        with self.assertRaises(ArgumentTypeError):
            _parse_pos_int("None")
        with self.assertRaises(ArgumentTypeError):
            _parse_pos_int("-1")
        with self.assertRaises(ArgumentTypeError):
            _parse_pos_int("abc")

    def test_parse_pos_int_or_none(self):
        """
        Test the _parse_pos_int_or_none function.
        """
        self.assertEqual(_parse_pos_int_or_none("5"), 5)
        self.assertIsNone(_parse_pos_int_or_none("None"))
        with self.assertRaises(ArgumentTypeError):
            _parse_pos_int_or_none("-1")
        with self.assertRaises(ArgumentTypeError):
            _parse_pos_int_or_none("abc")

    def test_parse_solve_limit(self):
        """
        Test the _parse_solve_limit function.
        """
        self.assertEqual(_parse_solve_limit("5,umax"), "5,umax")
        self.assertIsNone(_parse_solve_limit("None"))
        with self.assertRaises(ArgumentTypeError):
            _parse_solve_limit("abc")

    def test_parse_0_1_float(self):
        """
        Test the _parse_0_1_float function.
        """
        self.assertEqual(_parse_0_1_float("0.5"), 0.5)
        self.assertEqual(_parse_0_1_float("0"), 0.0)
        self.assertEqual(_parse_0_1_float("1"), 1.0)
        with self.assertRaises(ArgumentTypeError):
            _parse_0_1_float("None")
        with self.assertRaises(ArgumentTypeError):
            _parse_0_1_float("-0.1")
        with self.assertRaises(ArgumentTypeError):
            _parse_0_1_float("1.1")
        with self.assertRaises(ArgumentTypeError):
            _parse_0_1_float("abc")

    def test_parse_percent(self):
        """
        Test the _parse_percent function.
        """
        self.assertEqual(_parse_percent("50"), 50)
        self.assertEqual(_parse_percent("0"), 0)
        self.assertEqual(_parse_percent("100"), 100)
        with self.assertRaises(ArgumentTypeError):
            _parse_percent("None")
        with self.assertRaises(ArgumentTypeError):
            _parse_percent("-1")
        with self.assertRaises(ArgumentTypeError):
            _parse_percent("101")
        with self.assertRaises(ArgumentTypeError):
            _parse_percent("abc")

    def test_parse_destruction(self):
        """
        Test the _parse_destruction function.
        """
        self.assertEqual(_parse_destruction("declarative"), ("declarative", 0))
        self.assertEqual(_parse_destruction("simple,20"), ("simple", 20))
        self.assertEqual(_parse_destruction("simple,auto"), ("simple", -1))
        with self.assertRaises(ArgumentTypeError):
            _parse_destruction("None")
        with self.assertRaises(ArgumentTypeError):
            _parse_destruction("simple,-1")
        with self.assertRaises(ArgumentTypeError):
            _parse_destruction("declarative,20")

    def test_parse_parallel_mode(self):
        """
        Test the _parse_parallel_mode function.
        """
        self.assertEqual(_parse_parallel_mode("5"), "5")
        self.assertEqual(_parse_parallel_mode("2,compete"), "2,compete")
        self.assertEqual(_parse_parallel_mode("10,split"), "10,split")
        with self.assertRaises(ArgumentTypeError):
            _parse_parallel_mode("None")
        with self.assertRaises(ArgumentTypeError):
            _parse_parallel_mode("0")
        with self.assertRaises(ArgumentTypeError):
            _parse_parallel_mode("80")
        with self.assertRaises(ArgumentTypeError):
            _parse_parallel_mode("20,unknown_mode")
        with self.assertRaises(ArgumentTypeError):
            _parse_parallel_mode("other,invalid,format")

    def test_parse_minimize_variable(self):
        """
        Test the _parse_minimize_variable function.
        """
        self.assertEqual(_parse_minimize_variable("var1"), parse_term("var1"))
        with self.assertRaises(ArgumentTypeError):
            _parse_minimize_variable("")
        with self.assertRaises(ArgumentTypeError):
            _parse_minimize_variable("3,)4/(")

    def test_parse_context(self):
        """
        Test the _parse_context function.
        """
        with self.assertRaises(ArgumentTypeError):
            _parse_context("missing_context_file.py")

        with tempfile.TemporaryDirectory() as tmp_dir:
            # valid single class
            valid_file = f"{tmp_dir}/valid_context.py"
            # fmt: off
            with open(valid_file, "w", encoding="utf-8") as file:
                file.write(
                    "class ValidContext:\n"
                    "    def value(self):\n"
                    "        return 7\n"
                )
            context = _parse_context(valid_file)
            self.assertEqual(context.__class__.__name__, "ValidContext")
            self.assertEqual(context.value(), 7)

            # valid class with varargs
            varargs_context_file = f"{tmp_dir}/varargs_context.py"
            with open(varargs_context_file, "w", encoding="utf-8") as file:
                file.write(
                    "class VarArgsContext:\n"
                    "    def __init__(self, *args, **kwargs):\n"
                    "        self.value_ = 9\n"
                    "\n"
                    "    def value(self):\n"
                    "        return self.value_\n"
                )
            context = _parse_context(varargs_context_file)
            self.assertEqual(context.__class__.__name__, "VarArgsContext")
            self.assertEqual(context.value(), 9)

            # invalid class with required args
            no_valid_class_file = f"{tmp_dir}/no_valid_context.py"
            with open(no_valid_class_file, "w", encoding="utf-8") as file:
                file.write(
                    "class NeedsArgs:\n"
                    "    def __init__(self, x):\n"
                    "        self.x = x\n"
                )

            with self.assertRaises(ArgumentTypeError):
                _parse_context(no_valid_class_file)

            # invalid context with multiple valid classes
            multiple_valid_classes_file = f"{tmp_dir}/multiple_contexts.py"
            with open(multiple_valid_classes_file, "w", encoding="utf-8") as file:
                file.write(
                    "class A:\n"
                    "    pass\n"
                    "\n"
                    "class B:\n"
                    "    pass\n"
                )
            # fmt: on
            with self.assertRaises(ArgumentTypeError):
                _parse_context(multiple_valid_classes_file)

            # Error during import
            import_error_file = f"{tmp_dir}/import_error_context.py"
            with open(import_error_file, "w", encoding="utf-8") as file:
                file.write("raise RuntimeError('error')\n")
            with self.assertRaises(ArgumentTypeError):
                _parse_context(import_error_file)

            # Spec loader fails
            with mock.patch(
                "fastlane.parsers.options_parser.importlib.util.spec_from_file_location",
                return_value=mock.Mock(loader=None),
            ):
                with self.assertRaises(ArgumentTypeError):
                    _parse_context(valid_file)

    def test_parse_adaptive_strategy(self):
        """
        Test the _parse_adaptive_strategy function.
        """
        self.assertEqual(_parse_adaptive_strategy(["roulette_wheel"], "roulette_wheel"), "roulette_wheel")
        with self.assertRaises(ArgumentTypeError):
            _parse_adaptive_strategy(["roulette_wheel"], "unknown_strategy")

    def test_parse_auto_converter(self):
        """
        Test the _parse_auto_converter function.
        """
        converter = mock.Mock()
        converters = {"converter_name": converter}
        self.assertEqual(_parse_auto_converter(converters, "converter_name"), converter)
        with self.assertRaises(ArgumentTypeError):
            _parse_auto_converter(converters, "unknown_converter")

    def test_parse_init_opt_mode(self):
        """
        Test the _parse_init_opt_mode function.
        """
        self.assertEqual(_parse_init_opt_mode("opt"), "opt")
        self.assertEqual(_parse_init_opt_mode("optN,20"), "optN,20")
        with self.assertRaises(ArgumentTypeError):
            _parse_init_opt_mode("None")
        with self.assertRaises(ArgumentTypeError):
            _parse_init_opt_mode("unknown_mode")

    def test_parse_lns_opt_mode(self):
        """
        Test the _parse_lns_opt_mode function.
        """
        self.assertEqual(_parse_lns_opt_mode("opt"), {"mode": "opt", "nf": None, "modifier": None})
        self.assertEqual(_parse_lns_opt_mode("optN,20"), {"mode": "optN", "nf": "20", "modifier": "dynamic"})
        self.assertEqual(
            _parse_lns_opt_mode("optN,20,30,static"), {"mode": "optN", "nf": "20,30", "modifier": "static"}
        )
        self.assertEqual(_parse_lns_opt_mode("optN,20,dynamic"), {"mode": "optN", "nf": "20", "modifier": "dynamic"})
        with self.assertRaises(ArgumentTypeError):
            _parse_lns_opt_mode("None")
        with self.assertRaises(ArgumentTypeError):
            _parse_lns_opt_mode("unknown_mode")
        with self.assertRaises(ArgumentTypeError):
            _parse_lns_opt_mode("opt,abc")
        with self.assertRaises(ArgumentTypeError):
            _parse_lns_opt_mode("opt,abc,static")
        with self.assertRaises(ArgumentTypeError):
            _parse_lns_opt_mode("opt,20,20,dynamic")
        with self.assertRaises(ArgumentTypeError):
            _parse_lns_opt_mode("opt,abc,dynamic")
        with self.assertRaises(ArgumentTypeError):
            _parse_lns_opt_mode("opt,20,unknown_modifier")

    def test_parse_opt_strategy(self):
        """
        Test the _parse_opt_strategy function.
        """
        self.assertEqual(_parse_opt_strategy("bb"), "bb")
        with self.assertRaises(ArgumentTypeError):
            _parse_opt_strategy("unknown_strategy")

    def test_parse_opt_heuristic(self):
        """
        Test the _parse_opt_heuristic function.
        """
        self.assertEqual(_parse_opt_heuristic("sign"), "sign")
        with self.assertRaises(ArgumentTypeError):
            _parse_opt_heuristic("unknown_heuristic")

    def test_parse_configuration(self):
        """
        Test the _parse_configuration function.
        """
        self.assertEqual(_parse_configuration("tweety"), "tweety")
        with self.assertRaises(ArgumentTypeError):
            _parse_configuration("unknown_configuration")

    def test_parse_heuristic(self):
        """
        Test the _parse_heuristic function.
        """
        self.assertEqual(_parse_heuristic("Domain"), "Domain")
        with self.assertRaises(ArgumentTypeError):
            _parse_heuristic("unknown_heuristic")

    def test_replace_default(self):
        """
        Test the _replace_default function.
        """
        self.assertEqual(_replace_default("Help text [%(default)s]", 30), "Help text [30]")
        self.assertEqual(_replace_default("Help text [%(default)s]", "test"), "Help text [test]")

    def test_format_preset_option_value(self):
        """
        Test the _format_preset_option_value function.
        """
        m = mock.Mock()
        self.assertEqual(_format_preset_option_value("destruction", ("simple", 20), {}), "simple,20")
        self.assertEqual(_format_preset_option_value("auto_converter", m, {type(m): "test"}), "test")
        self.assertEqual(_format_preset_option_value("unknown_option", 5, {}), "5")

    def test_build_preset_help_text(self):
        """
        Test the _build_preset_help_text function.
        """
        preset = {
            "lns": {
                "description": "Classic LNS using assumptions and a fixed destruction rate.",
                "destruction": ("simple", 40),
                "init_time_limit": 10,
                "lns_time_limit": 5,
                "fix": "assumptions",
            },
        }
        converter_mapping = {type(mock.Mock()): "test"}
        help_text = _build_preset_help_text(preset, converter_mapping)
        # fmt: off
        expected_help_text = (
            "[lns]:\n"
            " --destruction=simple,40  --init-time-limit=10\n" " --lns-time-limit=5  --fix=assumptions"
        )
        # fmt: on
        self.assertEqual(help_text, expected_help_text)

    def test_build_preset_description_text(self):
        """
        Test the _build_preset_description_text function.
        """
        preset = {
            "lns": {
                "description": "Classic LNS using assumptions and a fixed destruction rate.",
                "fix": "assumptions",
            },
            "test": {
                "description": "test description.",
                "fix": "heuristics",
            },
        }
        description_text = _build_preset_description_text(preset)
        # fmt: off
        expected_description_text = (
            "lns: Classic LNS using assumptions and a fixed destruction rate.\n"
            "test: test description."
        )
        # fmt: on
        self.assertEqual(description_text, expected_description_text)

    def test_parser(self):
        """
        Test the parse_args method.
        """

        ret = self.parser.parse_args(["x.lp"])
        self.assertDictEqual(
            ret.__dict__,
            {
                "log_level": UNSET,
                "solver": UNSET,
                "preset": UNSET,
                "seed": UNSET,
                "time_limit": UNSET,
                "max_steps": UNSET,
                "parallel_mode": UNSET,
                "clingo_args": UNSET,
                "context": UNSET,
                "minimize_variable": UNSET,
                "init_time_limit": UNSET,
                "init_cutoff": UNSET,
                "init_solve_limit": UNSET,
                "init_configuration": UNSET,
                "init_opt_strategy": UNSET,
                "init_opt_heuristic": UNSET,
                "init_restart_on_model": UNSET,
                "init_opt_mode": UNSET,
                "default_adaptive_strategy_name": UNSET,
                "lex_weight": UNSET,
                "learning_rate": UNSET,
                "constrained": UNSET,
                "destruction": UNSET,
                "fix": UNSET,
                "auto_converter": UNSET,
                "accept_variability": UNSET,
                "accept_improvement": UNSET,
                "lns_time_limit": UNSET,
                "lns_cutoff": UNSET,
                "lns_solve_limit": UNSET,
                "lns_configuration": UNSET,
                "lns_opt_strategy": UNSET,
                "lns_opt_heuristic": UNSET,
                "lns_heuristic": UNSET,
                "lns_restart_on_model": UNSET,
                "lns_opt_mode": UNSET,
                "lns_time_limit_increase_rate": UNSET,
                "lns_cutoff_threshold": UNSET,
                "lns_cutoff_increase_rate": UNSET,
                "lns_solve_limit_increase_rate": UNSET,
                "files": ["x.lp"],
            },
        )

        ret = self.parser.parse_args(
            [
                "--log-level",
                "info",
                "--solver",
                "clingcon",
                "--preset",
                "lns",
                "--seed",
                "42",
                "--time-limit",
                "60",
                "--max-steps",
                "100",
                "--parallel-mode",
                "4,compete",
                "--clingo-args",
                "'--some-clingo-arg=value'",
                "--minimize-variable",
                "var1",
                "--init-time-limit",
                "30",
                "--init-cutoff",
                "10",
                "--init-solve-limit",
                "5,umax",
                "--init-configuration",
                "tweety",
                "--init-opt-strategy",
                "bb",
                "--init-opt-heuristic",
                "sign",
                "--init-restart-on-model",
                "--init-opt-mode",
                "optN,20",
                "--default-adaptive-strategy",
                "roulette",
                "--lex-weight",
                "10",
                "--learning-rate",
                "0.1",
                "--constrained",
                "--destruction",
                "simple,20",
                "--fix",
                "assumptions",
                "--auto-converter",
                "last-improv",
                "--accept-variability",
                "20",
                "--accept-improvement",
                "10",
                "--lns-time-limit",
                "5",
                "--lns-cutoff",
                "2",
                "--lns-solve-limit",
                "5",
                "--lns-configuration",
                "tweety",
                "--lns-opt-strategy",
                "bb",
                "--lns-opt-heuristic",
                "sign",
                "--lns-heuristic",
                "Domain",
                "--lns-restart-on-model",
                "--lns-opt-mode",
                "optN,20",
                "--lns-time-limit-increase-rate",
                "30",
                "--lns-cutoff-threshold",
                "3",
                "--lns-cutoff-increase-rate",
                "20",
                "--lns-solve-limit-increase-rate",
                "10",
                "x.lp",
            ]
        )

        ref_ret_dict = {
            "log_level": logging.INFO,
            # "solver": ClingconSolver,
            "preset": "lns",
            "seed": 42,
            "time_limit": 60,
            "max_steps": 100,
            "parallel_mode": "4,compete",
            "clingo_args": "'--some-clingo-arg=value'",
            "context": UNSET,
            "minimize_variable": parse_term("var1"),
            "init_time_limit": 30,
            "init_cutoff": 10,
            "init_solve_limit": "5,umax",
            "init_configuration": "tweety",
            "init_opt_strategy": "bb",
            "init_opt_heuristic": "sign",
            "init_restart_on_model": True,
            "init_opt_mode": "optN,20",
            "default_adaptive_strategy_name": "roulette",
            "lex_weight": 10,
            "learning_rate": 0.1,
            "constrained": True,
            "destruction": ("simple", 20),
            "fix": "assumptions",
            # "auto_converter": "last-improv",
            "accept_variability": 20,
            "accept_improvement": 10,
            "lns_time_limit": 5,
            "lns_cutoff": 2,
            "lns_solve_limit": "5",
            "lns_configuration": "tweety",
            "lns_opt_strategy": "bb",
            "lns_opt_heuristic": "sign",
            "lns_heuristic": "Domain",
            "lns_restart_on_model": True,
            "lns_opt_mode": {"mode": "optN", "nf": "20", "modifier": "dynamic"},
            "lns_time_limit_increase_rate": 30,
            "lns_cutoff_threshold": 3,
            "lns_cutoff_increase_rate": 20,
            "lns_solve_limit_increase_rate": 10,
            "files": ["x.lp"],
        }

        self.assertTrue(ref_ret_dict.keys() <= ret.__dict__.keys())
        for key, ref_value in ref_ret_dict.items():
            self.assertEqual(ret.__dict__[key], ref_value, f"Mismatch for key '{key}'")
        self.assertIsInstance(ret.solver, ClingconSolver)
        self.assertIsInstance(ret.auto_converter, LastImprovementDestructionConverter)

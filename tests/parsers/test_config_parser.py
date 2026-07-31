"""
Test cases for config parser.
"""

import tempfile
from unittest import TestCase, mock
from weakref import WeakKeyDictionary

import clingo
from clingo.symbol import Function, Number, String

from mod_lns import Model
from mod_lns.lib.solvers.clingo_solver import ClingoSolver
from mod_lns.parsers.config_parser import ConfigParser
from mod_lns.utils.types import DestroyOperator, PrioritizeOperator, ProjectOperator

# pylint: disable=protected-access


class TestConfigParser(TestCase):
    """
    Test cases for config parser.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        self.solver = ClingoSolver()
        self.solver.control = clingo.Control()
        self.logger = mock.Mock()

    def test_is_atom(self):
        """
        Test the _is_atom method.
        """
        self.assertTrue(ConfigParser._is_atom(Function("a", [])))
        self.assertTrue(ConfigParser._is_atom(Function("b", [Number(1)])))
        self.assertFalse(ConfigParser._is_atom(Function("", [Number(1)])))
        self.assertFalse(ConfigParser._is_atom(Number(1)))

    def test_parse_project_operator(self):
        """
        Test the _parse_project_operator method.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", encoding="utf-8", delete_on_close=False) as temp_file:
            # fmt: off
            temp_file.write(
                # valid
                '_project_op("plays_3", (plays,3)).'
                '_project_op(other, (abc,2)).'
                # invalid
                '_project_op(invalid, (abc)).'    
            )
            # fmt: on
            temp_file.close()
            self.solver.control.load(temp_file.name)
            self.solver.control.ground([("base", [])])
        project_operators = ConfigParser._parse_project_operator(self.solver, True, self.logger)
        self.assertDictEqual(
            project_operators,
            {
                "plays_3": ProjectOperator.from_signatures(name="plays_3", signatures={("plays", 3)}),
                "other": ProjectOperator.from_signatures(name="other", signatures={("abc", 2)}),
                "invalid": ProjectOperator(name="invalid"),
            },
        )

        model = Model()
        model.shown = {Function("a", [Number(1), Number(2)]), Function("abc", [Number(2)]), Function("", [Number(1)])}
        self.solver.last_model = model
        project_operators = ConfigParser._parse_project_operator(self.solver, False, self.logger)
        self.assertDictEqual(
            project_operators,
            {
                "default": ProjectOperator.from_signatures(name="default", signatures={("a", 2), ("abc", 1)}),
            },
        )

    def test_is_percent_or_number(self):
        """
        Test the _is_percent_or_number method.
        """
        self.assertTrue(ConfigParser._is_percent_or_number(Function("p", [Number(50)])))
        self.assertTrue(ConfigParser._is_percent_or_number(Function("n", [Number(3)])))
        self.assertFalse(ConfigParser._is_percent_or_number(Function("p", [String("test")])))
        self.assertFalse(ConfigParser._is_percent_or_number(Function("p", [Number(50), Number(1)])))
        self.assertFalse(ConfigParser._is_percent_or_number(Function("invalid", [Number(50)])))

    def test_parse_destroy_operators(self):
        """
        Test the _parse_destroy_operators method.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", encoding="utf-8", delete_on_close=False) as temp_file:
            # fmt: off
            temp_file.write(
                # valid
                '_destroy_op("percent", p(50)).'
                '_destroy_op(number, n(3)).'
                '_destroy_op(auto, auto).'
                '_destroy_op(multi, (p(10),p(20),n(3))).'
                # invalid
                '_destroy_op(bad_multi, (p(10),p(20),abc,n(3))).'
                '_destroy_op(invalid, abc(3)).'
                '_destroy_op(invalid2, 2).'
                # multiple destroy operators with the same name
                '_destroy_op("percent", p(30)).' 
            )
            # fmt: on
            temp_file.close()
            self.solver.control.load(temp_file.name)
            self.solver.control.ground([("base", [])])
        destroy_operators = ConfigParser._parse_destroy_operators(self.solver, True, self.logger)
        self.assertDictEqual(
            destroy_operators,
            {
                "percent": DestroyOperator.from_specs("percent", [{"type": "p", "value": 50}]),
                "number": DestroyOperator.from_specs("number", [{"type": "n", "value": 3}]),
                "auto": DestroyOperator.from_specs("auto", [{"type": "auto", "value": None}]),
                "invalid": DestroyOperator.from_specs("invalid", [{"type": "auto", "value": None}]),
                "invalid2": DestroyOperator.from_specs("invalid2", [{"type": "auto", "value": None}]),
                "multi": DestroyOperator.from_specs(
                    "multi", [{"type": "p", "value": 10}, {"type": "p", "value": 20}, {"type": "n", "value": 3}]
                ),
                "bad_multi": DestroyOperator.from_specs("bad_multi", [{"type": "auto", "value": None}]),
            },
        )

        destroy_operators = ConfigParser._parse_destroy_operators(self.solver, False, self.logger)
        self.assertDictEqual(
            destroy_operators,
            {
                "default": DestroyOperator.from_specs("default", [{"type": "auto", "value": None}]),
            },
        )

    def test_is_heuristic_modifier(self):
        """
        Test the _is_heuristic_modifier method.
        """
        self.assertTrue(ConfigParser._is_heuristic_modifier(Function("sign")))
        self.assertTrue(ConfigParser._is_heuristic_modifier(Function("level")))
        self.assertTrue(ConfigParser._is_heuristic_modifier(Function("true")))
        self.assertTrue(ConfigParser._is_heuristic_modifier(Function("false")))
        self.assertTrue(ConfigParser._is_heuristic_modifier(Function("init")))
        self.assertTrue(ConfigParser._is_heuristic_modifier(Function("factor")))
        self.assertFalse(ConfigParser._is_heuristic_modifier(Function("sign", [Number(1)])))
        self.assertFalse(ConfigParser._is_heuristic_modifier(Function("invalid")))

    def test_parse_prioritize_operators(self):
        """
        Test the _parse_prioritize_operators method.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", encoding="utf-8", delete_on_close=False) as temp_file:
            # fmt: off
            temp_file.write(
                # valid
                '_prioritize_op("op1", 3, false).'
                '_prioritize_op(op2, inf, sign).'
                # invalid
                '_prioritize_op(invalid, abc, level).'
                '_prioritize_op(invalid2, 1, abc).'
                # multiple prioritize operators with the same name
                '_prioritize_op("op1", 1, true).'
            )
            # fmt: on
            temp_file.close()
            self.solver.control.load(temp_file.name)
            self.solver.control.ground([("base", [])])
        prioritize_operators = ConfigParser._parse_prioritize_operators(self.solver, True, self.logger)
        self.assertDictEqual(
            prioritize_operators,
            {
                "op1": PrioritizeOperator.from_spec("op1", {"value": 3, "modifier": "false"}),
                "op2": PrioritizeOperator.from_spec("op2", {"value": "inf", "modifier": "sign"}),
                "invalid": PrioritizeOperator.from_spec("invalid", {"value": 1, "modifier": "true"}),
                "invalid2": PrioritizeOperator.from_spec("invalid2", {"value": 1, "modifier": "true"}),
            },
        )

        prioritize_operators = ConfigParser._parse_prioritize_operators(self.solver, False, self.logger)
        self.assertDictEqual(
            prioritize_operators,
            {
                "default": PrioritizeOperator.from_spec("default", {"value": 1, "modifier": "true"}),
            },
        )

    def test_parse_configs(self):
        """
        Test the _parse_configs method.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", encoding="utf-8", delete_on_close=False) as temp_file:
            # fmt: off
            temp_file.write(
                '_config("config1", "plays_3", "random_n", "1_true").'
                '_config(config2, plays_3, auto, sign_inf).'
                # multiple configs with the same name
                '_config("config1", "plays_3", "auto", "1_true").'
            )
            # fmt: on
            temp_file.close()
            self.solver.control.load(temp_file.name)
            self.solver.control.ground([("base", [])])
        project_operators = ["plays_3"]
        destroy_operators = ["random_n", "auto", "extra"]
        prioritize_operators = ["1_true", "sign_inf"]
        configs = ConfigParser._parse_configs(
            self.solver, project_operators, destroy_operators, prioritize_operators, True, self.logger
        )
        self.assertDictEqual(
            configs,
            {
                "config1": {
                    "project_operators": ["plays_3"],
                    "destroy_operators": ["auto", "random_n"],
                    "prioritize_operators": ["1_true"],
                },
                "config2": {
                    "project_operators": ["plays_3"],
                    "destroy_operators": ["auto"],
                    "prioritize_operators": ["sign_inf"],
                },
            },
        )

        configs = ConfigParser._parse_configs(
            self.solver, project_operators, destroy_operators, prioritize_operators, False, self.logger
        )
        self.assertDictEqual(
            configs,
            {
                "default": {
                    "project_operators": ["plays_3"],
                    "destroy_operators": ["auto", "extra", "random_n"],
                    "prioritize_operators": ["1_true", "sign_inf"],
                },
            },
        )

        self.logger.reset_mock()
        ConfigParser._parse_configs(self.solver, [], [], [], True, self.logger)
        # 3 configs with 3 missing operators each = 9 warnings
        self.assertEqual(self.logger.warning.call_count, 9)

    def test_parse_strategy(self):
        """
        Test the _parse_strategy method.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", encoding="utf-8", delete_on_close=False) as temp_file:
            # fmt: off
            temp_file.write(
                # not supported
                '_strategy(invalid, test).'
                # valid
                '_strategy("roulette", "config1").'
                '_strategy(roulette, config2).'
                # undefined config
                '_strategy("roulette", "undefined").'
                # second strategy defined -> ignore
                '_strategy("second", "config2").'
            )
            # fmt: on
            temp_file.close()
            self.solver.control.load(temp_file.name)
            self.solver.control.ground([("base", [])])
        configs = {
            "config1": {
                "project_operators": ["plays_3"],
                "destroy_operators": ["random_n"],
                "prioritize_operators": ["1_true"],
            },
            "config2": {
                "project_operators": ["plays_3"],
                "destroy_operators": ["auto"],
                "prioritize_operators": ["sign_inf"],
            },
            "config3": {
                "project_operators": ["plays_2"],
                "destroy_operators": ["auto"],
                "prioritize_operators": ["sign_inf"],
            },
        }
        supported_strategies = ["roulette", "default", "second"]
        default_strategy = "default"
        strategy, candidate_configs = ConfigParser._parse_strategy(
            self.solver, configs, supported_strategies, default_strategy, True, self.logger
        )
        self.assertTupleEqual(
            (strategy, candidate_configs),
            (
                "roulette",
                {
                    "config1": {
                        "project_operators": ["plays_3"],
                        "destroy_operators": ["random_n"],
                        "prioritize_operators": ["1_true"],
                    },
                    "config2": {
                        "project_operators": ["plays_3"],
                        "destroy_operators": ["auto"],
                        "prioritize_operators": ["sign_inf"],
                    },
                },
            ),
        )

        strategy, candidate_configs = ConfigParser._parse_strategy(
            self.solver, configs, supported_strategies, default_strategy, False, self.logger
        )
        self.assertTupleEqual(
            (strategy, candidate_configs),
            (
                "default",
                {
                    "config1": {
                        "project_operators": ["plays_3"],
                        "destroy_operators": ["random_n"],
                        "prioritize_operators": ["1_true"],
                    },
                    "config2": {
                        "project_operators": ["plays_3"],
                        "destroy_operators": ["auto"],
                        "prioritize_operators": ["sign_inf"],
                    },
                    "config3": {
                        "project_operators": ["plays_2"],
                        "destroy_operators": ["auto"],
                        "prioritize_operators": ["sign_inf"],
                    },
                },
            ),
        )

    def test_parse_lns_config(self):
        """
        Test the parse_lns_config method.
        """
        lns_object = mock.Mock()
        lns_object.logger = self.logger
        solver = mock.Mock()
        options = mock.Mock()
        options._declarative = True
        options.get_supported_adaptive_strategy_names = mock.Mock(return_value=["default", "roulette"])
        options.default_adaptive_strategy_name = "default"
        lns_object.solver = solver
        lns_object.options = options
        # declarative = True
        with (
            mock.patch.object(
                ConfigParser,
                "_parse_project_operator",
                return_value={"plays_3": ProjectOperator.from_signatures("plays_3", {("plays", 3)})},
            ) as mock_parse_project_operator,
            mock.patch.object(
                ConfigParser,
                "_parse_destroy_operators",
                return_value={"random_n": DestroyOperator.from_specs("random_n", [{"type": "p", "value": 20}])},
            ) as mock_parse_destroy_operators,
            mock.patch.object(
                ConfigParser, "_parse_prioritize_operators", return_value={"1_true": {"value": 1, "modifier": "true"}}
            ) as mock_parse_prioritize_operators,
            mock.patch.object(
                ConfigParser,
                "_parse_configs",
                return_value={
                    "default": {
                        "project_operators": ["plays_3"],
                        "destroy_operators": ["random_n"],
                        "prioritize_operators": ["1_true"],
                    },
                },
            ) as mock_parse_configs,
            mock.patch.object(
                ConfigParser,
                "_parse_strategy",
                return_value=(
                    "default",
                    {
                        "default": {
                            "project_operators": ["plays_3"],
                            "destroy_operators": ["random_n"],
                            "prioritize_operators": ["1_true"],
                        }
                    },
                ),
            ) as mock_parse_strategy,
        ):
            catalog = ConfigParser.parse_lns_config(lns_object)
            mock_parse_project_operator.assert_called_once_with(solver, options._declarative, self.logger.getChild())
            mock_parse_destroy_operators.assert_called_once_with(solver, options._declarative, self.logger.getChild())
            mock_parse_prioritize_operators.assert_called_once_with(
                solver, options._declarative, self.logger.getChild()
            )
            mock_parse_configs.assert_called_once_with(
                solver, ["plays_3"], ["random_n"], ["1_true"], options._declarative, self.logger.getChild()
            )
            mock_parse_strategy.assert_called_once_with(
                solver,
                {
                    "default": {
                        "project_operators": ["plays_3"],
                        "destroy_operators": ["random_n"],
                        "prioritize_operators": ["1_true"],
                    }
                },
                ["default", "roulette"],
                "default",
                options._declarative,
                self.logger.getChild(),
            )
            self.assertDictEqual(
                catalog,
                {
                    "configs": {
                        "default": {
                            "destroy_operators": ["random_n"],
                            "prioritize_operators": ["1_true"],
                            "project_operators": ["plays_3"],
                        }
                    },
                    "destroy_operators": {
                        "random_n": DestroyOperator.from_specs("random_n", [{"type": "p", "value": 20}])
                    },
                    "prioritize_operators": {"1_true": {"value": 1, "modifier": "true"}},
                    "project_operators": {"plays_3": ProjectOperator.from_signatures("plays_3", {("plays", 3)})},
                    "strategy": "default",
                },
            )
        # declarative = False
        options._declarative = False
        options._destruction_rate = 30
        with (
            mock.patch.object(
                ConfigParser,
                "_parse_project_operator",
                return_value={"plays_3": ProjectOperator.from_signatures("plays_3", {("plays", 3)})},
            ) as mock_parse_project_operator,
            mock.patch.object(
                ConfigParser,
                "_parse_destroy_operators",
                return_value={"default": DestroyOperator.from_specs("default", [{"type": "auto", "value": None}])},
            ) as mock_parse_destroy_operators,
            mock.patch.object(
                ConfigParser, "_parse_prioritize_operators", return_value={"default": {"value": 1, "modifier": "true"}}
            ) as mock_parse_prioritize_operators,
            mock.patch.object(
                ConfigParser,
                "_parse_configs",
                return_value={
                    "default": {
                        "project_operators": ["plays_3"],
                        "destroy_operators": ["default"],
                        "prioritize_operators": ["default"],
                    },
                },
            ) as mock_parse_configs,
            mock.patch.object(
                ConfigParser,
                "_parse_strategy",
                return_value=(
                    "default",
                    {
                        "default": {
                            "project_operators": ["plays_3"],
                            "destroy_operators": ["default"],
                            "prioritize_operators": ["default"],
                        }
                    },
                ),
            ) as mock_parse_strategy,
        ):
            catalog = ConfigParser.parse_lns_config(lns_object)
            self.assertDictEqual(
                catalog,
                {
                    "configs": {
                        "default": {
                            "destroy_operators": ["default"],
                            "prioritize_operators": ["default"],
                            "project_operators": ["plays_3"],
                        }
                    },
                    "destroy_operators": {
                        "default": DestroyOperator.from_specs(
                            "default", [{"type": "p", "value": options._destruction_rate}]
                        )
                    },
                    "prioritize_operators": {"default": {"value": 1, "modifier": "true"}},
                    "project_operators": {"plays_3": ProjectOperator.from_signatures("plays_3", {("plays", 3)})},
                    "strategy": "default",
                },
            )
        # declarative = False, destruction_rate = 0
        options._destruction_rate = 0
        with (
            mock.patch.object(
                ConfigParser,
                "_parse_project_operator",
                return_value={"plays_3": ProjectOperator.from_signatures("plays_3", {("plays", 3)})},
            ) as mock_parse_project_operator,
            mock.patch.object(
                ConfigParser,
                "_parse_destroy_operators",
                return_value={"default": DestroyOperator.from_specs("default", [{"type": "auto", "value": None}])},
            ) as mock_parse_destroy_operators,
            mock.patch.object(
                ConfigParser, "_parse_prioritize_operators", return_value={"default": {"value": 1, "modifier": "true"}}
            ) as mock_parse_prioritize_operators,
            mock.patch.object(
                ConfigParser,
                "_parse_configs",
                return_value={
                    "default": {
                        "project_operators": ["plays_3"],
                        "destroy_operators": ["default"],
                        "prioritize_operators": ["default"],
                    },
                },
            ) as mock_parse_configs,
            mock.patch.object(
                ConfigParser,
                "_parse_strategy",
                return_value=(
                    "default",
                    {
                        "default": {
                            "project_operators": ["plays_3"],
                            "destroy_operators": ["default"],
                            "prioritize_operators": ["default"],
                        }
                    },
                ),
            ) as mock_parse_strategy,
        ):
            catalog = ConfigParser.parse_lns_config(lns_object)
            self.assertDictEqual(
                catalog,
                {
                    "configs": {
                        "default": {
                            "destroy_operators": ["default"],
                            "prioritize_operators": ["default"],
                            "project_operators": ["plays_3"],
                        }
                    },
                    "destroy_operators": {
                        "default": DestroyOperator.from_specs("default", [{"type": "auto", "value": None}])
                    },
                    "prioritize_operators": {"default": {"value": 1, "modifier": "true"}},
                    "project_operators": {"plays_3": ProjectOperator.from_signatures("plays_3", {("plays", 3)})},
                    "strategy": "default",
                },
            )

    def test_format_config_catalog(self):
        """
        Test the _format_config_catalog method.
        """
        catalog = {
            "configs": {
                "default": {
                    "destroy_operators": ["random_n"],
                    "prioritize_operators": ["1_true"],
                    "project_operators": ["plays_3"],
                }
            },
            "destroy_operators": {"random_n": DestroyOperator.from_specs("random_n", [{"type": "p", "value": 20}])},
            "prioritize_operators": {"1_true": {"value": 1, "modifier": "true"}},
            "project_operators": {"plays_3": ProjectOperator.from_signatures("plays_3", {("plays", 3)})},
            "strategy": "default",
        }
        self.assertEqual(
            ConfigParser._format_config_catalog(catalog),
            # fmt: off
            "project_operators={plays_3{plays/3}}, "
            "destroy_operators={random_n{p(20)}}, "
            "prioritize_operators={1_true{1,true}}, "
            "configs={default[project_operators={plays_3},"
                "destroy_operators={random_n},prioritize_operators={1_true}]}, "
            "strategy=default",
            # fmt: on
        )

    def test_get_op_specs(self):
        """
        Test the _get_op_specs method.
        """
        model = Model()
        model.true = {
            Function("_project", [String("plays_3"), Function("plays", [Number(1), Number(2), Number(3)])]),
            Function("_destroy", [String("random_n"), Function("plays", [Number(1), Number(2), Number(3)]), Number(2)]),
            Function("_prioritize", [String("1_true"), Function("plays", [Number(1), Number(2), Number(3)])]),
        }
        specs = ConfigParser.get_op_specs(model)
        self.assertDictEqual(
            specs,
            {
                "_project": {
                    Function(
                        "_project",
                        [String("plays_3"), Function("plays", [Number(1), Number(2), Number(3)], True)],
                        True,
                    )
                },
                "_destroy": {
                    Function(
                        "_destroy",
                        [String("random_n"), Function("plays", [Number(1), Number(2), Number(3)], True), Number(2)],
                        True,
                    )
                },
                "_prioritize": {
                    Function(
                        "_prioritize",
                        [String("1_true"), Function("plays", [Number(1), Number(2), Number(3)], True)],
                        True,
                    )
                },
            },
        )

        # Repeated calls for the same model should return the cached object.
        self.assertIs(specs, ConfigParser.get_op_specs(model))

    def test_get_projected_atoms(self):
        """
        Test the _get_projected_atoms method.
        """
        ConfigParser._projected_atoms_cache = WeakKeyDictionary()
        model = Model()
        model.shown = {
            Function("plays", [Number(1), Number(2), Number(3)]),
            Function("plays", [Number(4), Number(5), Number(6)]),
            Function("abc", [Number(1), Number(2)]),
        }
        op_specs = {
            "_project": {
                Function(
                    "_project",
                    [String("plays_3"), Function("plays", [Number(1), Number(2), Number(3)], True)],
                    True,
                ),
                Function(
                    "_project",
                    [String("abc_2"), Function("abc", [Number(1), Number(2)], True)],
                    True,
                ),
                Function(
                    "_project",
                    [Function("other_2"), Function("other", [Number(3), Number(4)], True)],
                    True,
                ),
            }
        }
        with mock.patch.object(ConfigParser, "get_op_specs", return_value=op_specs):
            projected_atoms = ConfigParser.get_projected_atoms(model, "plays_3")
        self.assertSetEqual(
            projected_atoms,
            {Function("plays", [Number(1), Number(2), Number(3)])},
        )

        # Repeated calls with the same inputs should return the cached object.
        with mock.patch.object(ConfigParser, "get_op_specs", return_value=op_specs):
            self.assertIs(projected_atoms, ConfigParser.get_projected_atoms(model, "plays_3"))

        ConfigParser._projected_atoms_cache = WeakKeyDictionary()
        with mock.patch.object(ConfigParser, "get_op_specs", return_value={}):
            default_projected_atoms = ConfigParser.get_projected_atoms(model, "plays_3")
        self.assertSetEqual(default_projected_atoms, model.shown)
        self.assertIsNot(projected_atoms, default_projected_atoms)

    def test_get_atom_term_pairs(self):
        """
        Test the _get_atom_term_pairs method.
        """
        ConfigParser._atom_term_pairs_cache = WeakKeyDictionary()
        model = Model()
        projected_atoms = {
            Function("plays", [Number(1), Number(2), Number(3)]),
            Function("abc", [Number(1), Number(2), Number(3)]),
        }
        op_specs = {
            "_destroy": {
                Function(
                    "_destroy",
                    [String("random_n"), Function("plays", [Number(1), Number(2), Number(3)], True), Number(2)],
                    True,
                ),
                Function(
                    "_destroy",
                    [String("random_n"), Function("plays", [Number(4), Number(5), Number(6)], True), Number(5)],
                    True,
                ),
                Function(
                    "_destroy",
                    [Function("other"), Function("other", [Number(1), Number(2)], True), Number(1)],
                    True,
                ),
            }
        }
        with mock.patch.object(ConfigParser, "get_op_specs", return_value=op_specs):
            atom_term_pairs = ConfigParser.get_atom_term_pairs(model, projected_atoms, "random_n")
        self.assertEqual(
            atom_term_pairs,
            [
                {"atom": Function("plays", [Number(1), Number(2), Number(3)], True), "term": Number(2)},
            ],
        )

        # Repeated calls with the same inputs should return the cached object.
        with mock.patch.object(ConfigParser, "get_op_specs", return_value=op_specs):
            self.assertIs(atom_term_pairs, ConfigParser.get_atom_term_pairs(model, projected_atoms, "random_n"))

        ConfigParser._atom_term_pairs_cache = WeakKeyDictionary()
        with mock.patch.object(ConfigParser, "get_op_specs", return_value={}):
            default_atom_term_pairs = ConfigParser.get_atom_term_pairs(model, projected_atoms, "random_n")
        self.assertEqual(len(default_atom_term_pairs), 2)

    def test_get_destruction_candidate_atoms(self):
        """
        Test the _get_destruction_candidate_atoms method.
        """
        model = mock.Mock(spec=Model)
        projected_atoms = mock.Mock()
        op_name = "random_n"
        with mock.patch.object(
            ConfigParser,
            "get_atom_term_pairs",
            return_value=[
                {"atom": Function("plays", [Number(1), Number(2), Number(3)], True), "term": Number(2)},
                {"atom": Function("plays", [Number(4), Number(5), Number(6)], True), "term": Number(5)},
            ],
        ) as mock_get_atom_term_pairs:
            candidates = ConfigParser.get_destruction_candidate_atoms(model, projected_atoms, op_name)
            mock_get_atom_term_pairs.assert_called_once_with(model, projected_atoms, op_name)
            self.assertSetEqual(
                candidates,
                {
                    Function("plays", [Number(1), Number(2), Number(3)], True),
                    Function("plays", [Number(4), Number(5), Number(6)], True),
                },
            )

    def test_get_heuristic_targets(self):
        """
        Test the _get_heuristic_targets method.
        """
        ConfigParser._heuristic_targets_cache = WeakKeyDictionary()
        model = Model()
        op_specs = {
            "_prioritize": {
                Function(
                    "_prioritize",
                    [String("1_true"), Function("plays", [Number(1), Number(2), Number(3)], True)],
                    True,
                ),
                Function(
                    "_prioritize",
                    [String("1_true"), Function("plays", [Number(4), Number(5), Number(6)], True)],
                    True,
                ),
                Function(
                    "_prioritize",
                    [Function("other"), Function("abc", [Number(4), Number(5)], True)],
                    True,
                ),
            }
        }
        undestroyed_atoms = {
            Function("plays", [Number(1), Number(2), Number(3)]),
            Function("abc", [Number(1), Number(2)]),
        }
        with mock.patch.object(ConfigParser, "get_op_specs", return_value=op_specs):
            heuristic_targets = ConfigParser.get_heuristic_targets(model, undestroyed_atoms, "1_true")
        self.assertSetEqual(
            heuristic_targets,
            {Function("plays", [Number(1), Number(2), Number(3)])},
        )

        # Repeated calls with the same inputs should return the cached object.
        with mock.patch.object(ConfigParser, "get_op_specs", return_value=op_specs):
            self.assertIs(heuristic_targets, ConfigParser.get_heuristic_targets(model, undestroyed_atoms, "1_true"))

        ConfigParser._heuristic_targets_cache = WeakKeyDictionary()
        with mock.patch.object(ConfigParser, "get_op_specs", return_value={}):
            default_heuristic_targets = ConfigParser.get_heuristic_targets(model, undestroyed_atoms, "1_true")
        self.assertSetEqual(default_heuristic_targets, undestroyed_atoms)

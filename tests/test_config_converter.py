"""
Tests for the fastlane configuration converter.
"""

import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from clingo import Function, String, Tuple_

from fastlane.utils.config_converter import convert, main, parse_destroy, parse_search


class TestConfigConverter(TestCase):
    """
    Test cases for the fastlane configuration converter.
    """

    def test_empty_configuration(self):
        """
        Test empty json.
        """
        self.assertEqual(convert({}), "")

    def test_parse_destroy(self):
        """
        Test destroy operator parsing.
        """
        output = []
        warnings = StringIO()
        with redirect_stderr(warnings):
            operators, parameters, auxiliary_rules = parse_destroy(
                [
                    {"type": "declarative", "name": "weeks", "sizes": [0.1, 0.25, 0.1]},
                    {"type": "declarative", "name": "weeks", "sizes": [0.25, 0.5]},
                    {"type": "declarative", "name": "days", "sizes": [0, 3]},
                    {"type": "declarative", "name": "groups", "sizes": "auto"},
                    {"type": "randomAtoms", "sizes": [0.1, 0.25]},
                    {"type": "unsupported"},
                ],
                output,
            )
        self.assertEqual(
            output,
            [
                "_destroy_sizes_0(10;25).",
                "_destroy_op((weeks,N), p(N)) :- _destroy_sizes_0(N).",
                "_destroy_sizes_1(0;3).",
                "_destroy_op((days,N), n(N)) :- _destroy_sizes_1(N).",
                '_destroy_op((groups,"auto"), auto(0)).',
            ],
        )
        self.assertEqual(
            [str(operator) for operator in operators],
            ["(weeks,N)", "(days,N)", '(groups,"auto")'],
        )
        self.assertEqual(
            {str(operator): body for operator, body in auxiliary_rules.items()},
            {"(weeks,N)": "_destroy_sizes_0(N)", "(days,N)": "_destroy_sizes_1(N)"},
        )
        self.assertEqual(parameters, {"randomAtoms": [10, 25]})
        self.assertEqual(
            warnings.getvalue(),
            "Warning: Duplicate destroy operator (weeks,10); skipped.\n"
            "Warning: Duplicate destroy operator name weeks; skipped.\n",
        )

        invalid_entries = [
            None,
            {"type": "declarative", "sizes": [1]},
            {"type": "declarative", "name": "not a term", "sizes": [1]},
            {"type": "declarative", "name": "empty", "sizes": []},
            {"type": "declarative", "name": "mixed", "sizes": [0.1, 1]},
            {"type": "declarative", "name": "digits", "sizes": [0.1, 0.125]},
            {"type": "declarative", "name": "valid", "sizes": [0.1, 0.125]},
            {"type": "declarative", "name": "upper_limit", "sizes": [0.1, 1.1]},
            {"type": "declarative", "name": "lower_limit", "sizes": [1, -1]},
            {"type": "randomAtoms", "sizes": "auto"},
        ]
        for invalid_entry in invalid_entries:
            with self.subTest(entry=invalid_entry):
                output = []
                warnings = StringIO()
                with redirect_stderr(warnings):
                    operators, parameters, auxiliary_rules = parse_destroy(
                        [invalid_entry, {"type": "declarative", "name": "valid", "sizes": [2]}], output
                    )
                self.assertEqual(
                    output,
                    ["_destroy_sizes_0(2).", "_destroy_op((valid,N), n(N)) :- _destroy_sizes_0(N)."],
                )
                self.assertEqual([str(operator) for operator in operators], ["(valid,N)"])
                self.assertEqual(list(auxiliary_rules.values()), ["_destroy_sizes_0(N)"])
                self.assertEqual(parameters, {})
                self.assertIn("Failed to parse entry", warnings.getvalue())

    def test_parse_search(self):
        """
        Test search operator parsing.
        """
        output = []
        warnings = StringIO()
        with redirect_stderr(warnings):
            operators, auxiliary_rules = parse_search(
                [
                    {
                        "name": "first",
                        "configuration": {"solver": {"opt_strategy": "bb,lin"}},
                        "cutoff": 3,
                        "timeouts": [5, 10],
                    },
                    {"name": "second", "cutoff": 4},
                    {"name": "second", "cutoff": 2},
                    None,
                ],
                {"randomAtoms": [10]},
                output,
            )
        self.assertEqual(
            output,
            [
                '_search_param(("first","opt_strategy"), ("opt_strategy", "bb,lin")).',
                '_search_param(("first","cutoff"), ("cutoff", 3)).',
                "_times_0(5;10).",
                '_search_param(("first",T), ("time-limit", T)) :- _times_0(T).',
                '_search_param(("second","cutoff"), ("cutoff", 4)).',
            ],
        )
        self.assertDictEqual(
            operators,
            {
                String("first"): {
                    Tuple_([String("first"), String("opt_strategy")]): None,
                    Tuple_([String("first"), String("cutoff")]): None,
                },
                String("second"): {Tuple_([String("second"), String("cutoff")]): None},
            },
        )
        self.assertDictEqual(
            auxiliary_rules,
            {
                String("first"): (
                    Tuple_([String("first"), Function("T")]),
                    "_times_0(T)",
                )
            },
        )
        self.assertEqual(
            warnings.getvalue(),
            'Warning: Duplicate search operator ("second","cutoff"); skipped.\n'
            "Warning: searchParams entry must be an object. Skipping search operator None.\n",
        )

    def test_convert(self):
        """
        Test conversion.
        """
        self.assertEqual(
            convert(
                {
                    "relaxOperators": [{"type": "declarative", "name": "weeks", "sizes": [2]}],
                    "searchOperators": [{"name": "search", "cutoff": 3}],
                    "strategy": {"name": "roulette"},
                }
            ),
            "_destroy_sizes_0(2).\n"
            "_destroy_op((weeks,N), n(N)) :- _destroy_sizes_0(N).\n"
            '_search_param(("search","cutoff"), ("cutoff", 3)).\n'
            '_config(((weeks,N),"search"), default, (weeks,N), default, (("search","cutoff")))'
            " :- _destroy_sizes_0(N).\n"
            '_strategy("roulette", C) :- _config(C, _, _, _, _).\n'
            '_strategy("roulette", C) :- _config(C, _, _, _).\n',
        )

        # with time-limits
        self.assertEqual(
            convert(
                {
                    "relaxOperators": [{"type": "declarative", "name": "weeks", "sizes": [2]}],
                    "searchOperators": [{"name": "search", "timeouts": [5, 10], "cutoff": 3}],
                }
            ),
            "_destroy_sizes_0(2).\n"
            "_destroy_op((weeks,N), n(N)) :- _destroy_sizes_0(N).\n"
            "_times_0(5;10).\n"
            '_search_param(("search",T), ("time-limit", T)) :- _times_0(T).\n'
            '_search_param(("search","cutoff"), ("cutoff", 3)).\n'
            '_config(((weeks,N),("search",T)), default, (weeks,N), default, (("search",T)))'
            " :- _destroy_sizes_0(N), _times_0(T).\n"
            '_config(((weeks,N),("search",T)), default, (weeks,N), default, (("search","cutoff")))'
            " :- _destroy_sizes_0(N), _times_0(T).\n",
        )

    def test_invalid_sections(self):
        """
        Additional tests for invalid sections, search options, and strategies."""
        warnings = StringIO()
        with redirect_stderr(warnings):
            self.assertEqual(
                convert(
                    {
                        "destroyOperators": {},
                        "searchParams": [{"name": "search", "timeouts": [True], "unknown": 1}],
                        "strategy": {"name": ""},
                    }
                ),
                "",
            )
        self.assertIn("destroyOperators must be an array; skipping it.", warnings.getvalue())
        self.assertIn("Timeouts must be nonnegative integers.", warnings.getvalue())
        self.assertIn('Unknown key unknown in search operator "search".', warnings.getvalue())
        self.assertIn("Skipping strategy.", warnings.getvalue())

    def test_main(self):
        """
        Test main function.
        """
        with TemporaryDirectory() as directory:
            source = Path(directory) / "config.json"
            source.write_text(json.dumps({"strategy": {"name": "roulette"}}), encoding="utf-8")
            output = StringIO()
            with patch("sys.argv", ["config_converter", str(source)]), redirect_stdout(output):
                main()
        self.assertEqual(
            output.getvalue(),
            '_strategy("roulette", C) :- _config(C, _, _, _, _).\n'
            '_strategy("roulette", C) :- _config(C, _, _, _).\n',
        )

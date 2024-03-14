"""
Test cases for main application functionality.
"""
# pylint: disable=protected-access
import logging
import os
from io import StringIO
from unittest import TestCase, mock

import clingo

from large_neighbourhood_search import LNS
from large_neighbourhood_search.utils.logger import setup_logger
from large_neighbourhood_search.utils.parser import get_parser
from large_neighbourhood_search.utils.pf_handling import (
    create_param_file,
    gen_example_params,
    load_param_file,
    save_param_file,
)


class TestMain(TestCase):
    """
    Test cases for main application functionality.
    """

    def test_logger(self):
        """
        Test the logger.
        """
        log = setup_logger("global", logging.INFO)
        sio = StringIO()
        for handler in log.handlers:
            handler.setStream(sio)
        log.info("test123")
        self.assertRegex(sio.getvalue(), "test123")

    def test_parser(self):
        """
        Test the parser.
        """
        parser = get_parser()
        ret = parser.parse_args(["--log", "info"])
        self.assertEqual(ret.log, logging.INFO)

    def test_load_param_file(self):
        """
        Test the loading of parameters from file.
        """
        ref_content = {
            "name": "example_params",
            "relaxation": {
                "mode": "declarative",
                "rates": [0.2, 0.4, 0.6],
                "threshold": 3,
            },
            "search": {
                "mode": "hard_constraint",
                "bound": {"mode": "overall", "type": "steps", "value": 2000},
            },
            "seed": None,
        }
        test_content = load_param_file("./tests/ref/example_params_ref.json")
        self.assertDictEqual(test_content, ref_content)

    def test_save_param_file(self):
        """
        Test the saving of parameters.
        """
        ref_content = {
            "name": "example_params",
            "relaxation": {
                "mode": "declarative",
                "rates": [0.2, 0.4, 0.6],
                "threshold": 3,
            },
            "search": {
                "mode": "hard_constraint",
                "bound": {"mode": "overall", "type": "steps", "value": 2000},
            },
            "seed": None,
        }
        save_param_file(ref_content, "./tests/test.json")
        test_content = load_param_file("./tests/test.json")
        os.remove("./tests/test.json")
        self.assertDictEqual(test_content, ref_content)

    def test_gen_example_param_file(self):
        """
        Test the generation of an example parameter file.
        """
        gen_example_params("./tests")
        test_content = load_param_file("./tests/example_params.json")
        os.remove("./tests/example_params.json")
        ref_content = load_param_file("./tests/ref/example_params_ref.json")
        self.assertDictEqual(test_content, ref_content)

    @mock.patch("large_neighbourhood_search.utils.pf_handling.input", create=True)
    def test_create_param_file(self, mocked_input):
        """
        Test the creation of a new parameter file.
        """
        mocked_input.side_effect = [
            "test",
            "bla",
            "1",
            "-2",
            "0.2",
            "x",
            "0.4",
            "0",
            "-3",
            "3",
            "3",
            "0",
            "-2",
            "1",
            "bla",
            "0",
            "-3",
            "1500",
            "bla",
            "None",
        ]
        create_param_file("./tests/")
        test_content = load_param_file("./tests/test.json")
        os.remove("./tests/test.json")
        ref_content = {
            "name": "test",
            "relaxation": {
                "mode": "declarative",
                "rates": [0.2, 0.4],
                "threshold": 3,
            },
            "search": {
                "mode": "hard_constraint",
                "bound": {"mode": "per_improvement", "type": "steps", "value": 1500},
            },
            "seed": None,
        }
        self.assertDictEqual(test_content, ref_content)

    def test_lns_load_params(self):
        """
        Test the loading of parameters for LNS.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            None,
            0.2,
            False,
            False,
            "./tests/ref/example_params_ref.json",
        )
        lns.load_params(lns.param_path)
        self.assertEqual(lns._relax_mode, "declarative")
        self.assertEqual(lns._relax_rates, [0.2, 0.4, 0.6])
        self.assertEqual(lns._relax_rate, 0.2)
        self.assertEqual(lns._unsat_threshold, 3)
        self.assertEqual(lns._search_mode, "hard_constraint")
        self.assertEqual(lns._bound_mode, "overall")
        self.assertEqual(lns._bound_type, "steps")
        self.assertEqual(lns._bound, 2000)
        self.assertEqual(lns._seed, None)

    def test_lns_setup(self):
        """
        Test the clingo setup for LNS.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            123,
            0.2,
            False,
            False,
            "./tests/test.json",
        )
        params = {
            "name": "example_params",
            "relaxation": {
                "mode": "declarative",
                "rates": [0.2, 0.4, 0.6],
                "threshold": 3,
            },
            "search": {
                "mode": "hard_constraint",
                "bound": {"mode": "overall", "type": "steps", "value": 2000},
            },
            "seed": 123,
        }
        save_param_file(params, "./tests/test.json")
        test_ctl = lns.setup()
        self.assertEqual(lns._clingo_args, ["--seed=123"])
        self.assertIsInstance(test_ctl, clingo.control.Control)

        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            None,
            0.2,
            False,
            False,
            "./tests/test.json",
        )
        params["seed"] = None
        params["search"]["mode"] = "classic"
        save_param_file(params, "./tests/test.json")
        test_ctl = lns.setup()
        self.assertEqual(lns._clingo_args, ["--rand-freq=0.8"])
        self.assertIsInstance(test_ctl, clingo.control.Control)

        lns = LNS(
            ["./tests/ref/golf.lp"],
            None,
            123,
            0.2,
            True,
            False,
            "./tests/test.json",
        )
        test_ctl = lns.setup()
        self.assertEqual(lns._relax_rate, 1)
        self.assertIsInstance(test_ctl, clingo.control.Control)
        os.remove("./tests/test.json")

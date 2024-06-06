"""
Test cases theory components.
"""

from unittest import TestCase

import clingo
import clingodl

import large_neighbourhood_search as lns_pkg
from large_neighbourhood_search import LNS


class TestTheory(TestCase):
    """
    Test cases for theory components.
    """

    def test_setup_clingo(self):
        """
        Test the clingo setup for LNS.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.set_params({"seed": 123})
        test_ctl, test_thy = lns_pkg.lib.theory.setup_clingo(lns)
        self.assertDictEqual(
            lns.param_values["clingo_args"], {"rand-freq": 0.8, "seed": 123}
        )
        self.assertIsInstance(test_ctl, clingo.control.Control)
        self.assertIsNone(test_thy)

        lns = LNS(["./tests/ref/golf.lp"])
        test_ctl, test_thy = lns_pkg.lib.theory.setup_clingo(lns)
        self.assertDictEqual(lns.param_values["clingo_args"], {"rand-freq": 0.8})
        self.assertIsInstance(test_ctl, clingo.control.Control)
        self.assertIsNone(test_thy)

    def test_setup_clingo_dl(self):
        """
        Test the clingo-dl setup for LNS.
        """
        lns = LNS(
            ["./tests/ref/golf.lp"],
        )
        lns.set_params({"seed": 123})
        test_ctl, test_thy = lns_pkg.lib.theory.setup_clingo_dl(lns)
        self.assertDictEqual(
            lns.param_values["clingo_args"], {"rand-freq": 0.8, "seed": 123}
        )
        self.assertIsInstance(test_ctl, clingo.control.Control)
        self.assertIsInstance(test_thy, clingodl.ClingoDLTheory)

        lns = LNS(["./tests/ref/golf.lp"])
        test_ctl, test_thy = lns_pkg.lib.theory.setup_clingo_dl(lns)
        self.assertDictEqual(lns.param_values["clingo_args"], {"rand-freq": 0.8})
        self.assertIsInstance(test_ctl, clingo.control.Control)
        self.assertIsInstance(test_thy, clingodl.ClingoDLTheory)

    def test_repair_clingo(self):
        """
        Test reparation of solution using clingo.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.set_params({"seed": 123})

        ctl = lns_pkg.lib.theory.setup_clingo(lns)[0]
        lns_pkg.lib.theory.ground_base(lns, ctl)
        self.assertTrue(
            lns_pkg.lib.theory.repair_clingo(lns, ctl, [], None).satisfiable
        )
        self.assertTrue(lns.models["new_model"])

        assumptions = lns_pkg.lib.search.relax_random(
            lns.models["new_model"], {"relax_rate": 0.2}
        )
        lns.models["new_model"] = {}
        self.assertTrue(
            lns_pkg.lib.theory.repair_clingo(lns, ctl, assumptions, None).satisfiable
        )
        self.assertTrue(lns.models["new_model"])

        assumptions_atoms = list(map(lambda x: x[0], assumptions))
        for atom in assumptions_atoms:
            self.assertIn(atom, lns.models["new_model"]["true"])

        lns = LNS(["./tests/ref/bad_encoding.lp"])
        lns.set_params({"seed": 123})
        ctl, thy = lns_pkg.lib.theory.setup_clingo(lns)
        lns_pkg.lib.theory.ground_base(lns, ctl)
        self.assertFalse(
            lns_pkg.lib.theory.repair_clingo(lns, ctl, [], thy).satisfiable
        )

    def test_repair_clingo_dl(self):
        """
        Test reparation of solution using clingo-dl.
        """
        lns = LNS(["./tests/ref/golf.lp"])
        lns.set_params({"seed": 123})

        ctl, thy = lns_pkg.lib.theory.setup_clingo_dl(lns)
        lns_pkg.lib.theory.ground_base(lns, ctl)
        self.assertTrue(
            lns_pkg.lib.theory.repair_clingo_dl(lns, ctl, [], thy).satisfiable
        )
        self.assertTrue(lns.models["new_model"])

        assumptions = lns_pkg.lib.search.relax_random(
            lns.models["new_model"], {"relax_rate": 0.2}
        )
        lns.models["new_model"] = {}
        self.assertTrue(
            lns_pkg.lib.theory.repair_clingo_dl(lns, ctl, assumptions, thy).satisfiable
        )
        self.assertTrue(lns.models["new_model"])

        assumptions_atoms = list(map(lambda x: x[0], assumptions))
        for atom in assumptions_atoms:
            self.assertIn(atom, lns.models["new_model"]["true"])

        lns = LNS(["./tests/ref/bad_encoding.lp"])
        lns.set_params({"seed": 123})
        ctl, thy = lns_pkg.lib.theory.setup_clingo_dl(lns)
        lns_pkg.lib.theory.ground_base(lns, ctl)
        self.assertFalse(
            lns_pkg.lib.theory.repair_clingo_dl(lns, ctl, [], thy).satisfiable
        )

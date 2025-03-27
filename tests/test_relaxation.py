"""
Test cases for relaxation components.
"""

import random
from unittest import TestCase

from clingo.symbol import Function, Number

from mod_lns import Model
from mod_lns.lib.relaxation import relax_declarative, relax_random


class TestSearch(TestCase):
    """
    Test cases for relaxation components.
    """

    def test_relax(self):
        """
        Test random atom relaxation. Seed: 123
        """
        model = Model()
        model.shown = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
            Function("plays", [Number(5), Number(1), Number(1)], True),
            Function("plays", [Number(9), Number(1), Number(1)], True),
            Function("plays", [Number(1), Number(2), Number(1)], True),
        ]
        model.true = [
            Function("_lns_select", [Number(1)], True),
            Function("_lns_select", [Number(2)], True),
            Function("_lns_select", [Number(3)], True),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(1), Number(1), Number(3)], True),
                    Number(1),
                ],
                True,
            ),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(2), Number(1), Number(3)], True),
                    Number(2),
                ],
                True,
            ),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(3), Number(1), Number(1)], True),
                    Number(3),
                ],
                True,
            ),
        ]
        seed = 123
        random.seed(seed)
        ref = [
            (Function("plays", [Number(3), Number(1), Number(1)], True), True),
            (Function("plays", [Number(5), Number(1), Number(1)], True), True),
            (Function("plays", [Number(1), Number(2), Number(1)], True), True),
        ]
        self.assertListEqual(
            relax_random(model, {"relax_rate": 0.2, "base_relax_rate": 0}), ref
        )

        random.seed(seed)
        ref = [
            (Function("plays", [Number(1), Number(1), Number(3)], True), True),
            (Function("plays", [Number(2), Number(1), Number(3)], True), True),
        ]
        self.assertListEqual(
            relax_declarative(model, {"relax_rate": 0.2, "base_relax_rate": 0}), ref
        )

        model = Model()
        model.shown = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
        ]
        model.true = [
            Function("_lns_select", [Number(1)], True),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(1), Number(1), Number(3)], True),
                    Number(1),
                ],
                True,
            ),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(2), Number(1), Number(3)], True),
                    Number(1),
                ],
                True,
            ),
        ]
        random.seed(seed)
        ref = [
            (Function("plays", [Number(1), Number(1), Number(3)], True), True),
            (Function("plays", [Number(2), Number(1), Number(3)], True), True),
        ]
        self.assertListEqual(
            relax_declarative(model, {"relax_rate": 0.2, "base_relax_rate": 0}), ref
        )

        model = Model()
        model.shown = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
        ]
        model.true = [
            Function("_lns_select", [Function("", [Number(2), Number(2)], True)], True),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(1), Number(1), Number(3)], True),
                    Function("", [Number(2), Number(2)], True),
                ],
                True,
            ),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(2), Number(1), Number(3)], True),
                    Number(1),
                ],
                True,
            ),
        ]
        random.seed(seed)
        ref = [
            (Function("plays", [Number(1), Number(1), Number(3)], True), True),
        ]
        self.assertListEqual(
            relax_declarative(model, {"relax_rate": 0.2, "base_relax_rate": 0}), ref
        )

        model = Model()
        model.shown = [
            Function("plays", [Number(3), Number(1), Number(1)], True),
        ]
        model.true = [
            Function("_lns_select", [Number(1)], True),
            Function("_lns_select", [Number(2)], True),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(1), Number(1), Number(3)], True),
                    Number(1),
                ],
                True,
            ),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(1), Number(2), Number(3)], True),
                    Number(1),
                ],
                True,
            ),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(2), Number(1), Number(3)], True),
                    Number(2),
                ],
                True,
            ),
            Function(
                "_lns_fix",
                [
                    Function("plays", [Number(2), Number(2), Number(3)], True),
                    Number(2),
                ],
                True,
            ),
        ]
        random.seed(seed)
        ref = [
            (Function("plays", [Number(1), Number(1), Number(3)], True), True),
            (Function("plays", [Number(2), Number(2), Number(3)], True), True),
        ]
        self.assertListEqual(
            relax_declarative(model, {"relax_rate": 0, "base_relax_rate": 0.5}), ref
        )

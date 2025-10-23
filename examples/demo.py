"""
Examples on how to use the LNS framework.

Check out the Guide section in the documentation for
a step by step introduction.
"""

from mod_lns.lib.strategies.default_strategy import DefaultStrategy, LNSConfig
from mod_lns.lib.strategies.heulingo import Heulingo, HeulingoConfig
from mod_lns.lns import LNS
from mod_lns.utils.conversions import symbol_to_str


def main():
    # classic LNS with random relaxation using clingo with assumptions
    cl_strategy = DefaultStrategy()
    cl_strategy.config = LNSConfig(
        seed=123, relax_rate=40, init_time_limit=2, max_steps=500
    )

    # constrained LNS using clingo with assumptions and random relaxation
    con_strategy = DefaultStrategy()
    con_strategy.config = LNSConfig(
        seed=123, relax_rate=40, init_time_limit=2, max_steps=500, constrained=True
    )

    # classic LNS with declarative relaxation using clingo with assumptions
    cl_decl_strategy = DefaultStrategy()
    cl_decl_strategy.config = LNSConfig(
        seed=123, relax_rate=40, init_time_limit=2, max_steps=500, declarative=True
    )

    # Example of custom strategy
    class NewStrategy(DefaultStrategy):
        def relax(self, lns_object):
            r = super().relax(lns_object)
            for s in r:
                print(symbol_to_str(s))
            print("--")
            return r

    # Use new config to inspect declarative relaxation
    decl_custom = NewStrategy()
    decl_custom.config = LNSConfig(
        seed=123, relax_rate=40, init_time_limit=2, max_steps=5, declarative=True
    )

    # Example using heulingo strategy
    heuristic_strategy = Heulingo()
    heuristic_strategy.config = HeulingoConfig(
        seed=123,
        init_time_limit=2,
        lns_time_limit=2,
        max_steps=500,
        clingo_args="-c n=40",
    )
    # lns = LNS(["examples/golf_demo.lp", "examples/golf_lnps.lp"], heuristic_strategy)

    lns = LNS(["examples/golf_demo.lp"], cl_strategy)
    lns.main()


if __name__ == "__main__":
    main()

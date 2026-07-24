# demo.py

```python
"""
Examples on how to use the LNS framework.

Check out the Guide section in the documentation for
a step by step introduction.
"""
from mod_lns.lns import LNS
from mod_lns.utils.conversions import symbol_to_str


def main():

    # classic LNS
    files = ["./examples/golf_demo.lp"]
    classic_lns = {
            "preset": "lns",
            "seed": 42,
            "init_time_limit": 2,
            "max_steps": 100,
        }
    lns = LNS(files, classic_lns)
    
    # LNPS
    files = ["./examples/golf_demo.lp"]
    lnps = {
            "preset": "lnps",
            "seed": 42,
            "init_time_limit": 2,
            "lns_time_limit": 2,
        }
    #lns = LNS(files, lnps)

    # ALNPS
    files = ["./examples/golf_demo.lp", "./examples/golf_config.lp"]
    alnps = {
            "preset": "alnps",
            "seed": 42,
            "init_time_limit": 2,
            "lns_time_limit": 2,
            "log_level": 10,
        }
    #lns = LNS(files, alnps)

    # Example of custom LNS
    class NewLNS(LNS):
        def relax(self):
            r = super().relax()
            for s in r:
                print(symbol_to_str(s))
            print("--")
            return r
    files = ["./examples/golf_demo.lp", "./examples/golf_declarative.lp"]
    options = {
            "preset": "lns",
            "seed": 42,
            "init_time_limit": 2,
            "lns_time_limit": 2,
            "relaxation": ("declarative",0),
            "max_steps": 3,
    }
    #lns = NewLNS(files, options)

    lns.main()


if __name__ == "__main__":
    main()
```
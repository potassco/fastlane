"""
Examples on how to use the LNS framework.

Check out the Guide section in the documentation for
a step by step introduction.
"""
from mod_lns.lns import LNS
from mod_lns.lns_config import LNSConfig
from mod_lns.utils.conversions import symbol_to_str

def main():
    # classic LNS with random relaxation using clingo with assumptions
    cl_config = LNSConfig(
        lns_options={
            "seed": 123,
            "relax_rate": 0.2,
        })

    # constrained LNS using clingo with assumptions and random relaxation
    con_config = LNSConfig(
        lns_options={
            "constrained":True,
            "seed": 123,
            "relax_rate": 0.2, 
            "solve_time_limit": 10
        })
    

    # classic LNS with declarative relaxation using clingo with assumptions
    cl_decl_config = LNSConfig(
        lns_options={
            "declarative": True, 
            "seed": 123
        })
    
    # Example of custom configuration
    class NewLNSConfig(LNSConfig):
        
        def __init__(self, lns_options = {}, clingo_options = []):
            # add new default value
            default_options = {
                "new_opt": False,
            }
            self.lns_options = {**default_options, **lns_options}

            # keep functionality of LNSConfig
            super().__init__(self.lns_options, clingo_options)
            
            # add new functionality
            if self.lns_options["new_opt"] == True:
                self._enable_new_opt()
        
        def _enable_new_opt(self):
            # get current strategy to modify
            
            def relax(
                self,
                model,
                relax_parameters,
            ):
                # keep functionality
                r = super(EnNewOpt, self).relax(model,relax_parameters)
                # new functionality
                for s in r:
                    print(symbol_to_str(s[0]))
                print("--")
                return r
            # set new strategy
            base = type(self.strategy)
            EnNewOpt = type("EnNewOpt", (base,), {"relax": relax})
            self.strategy = EnNewOpt()

    # Use new config to inspect declarative relaxation
    con_decl_custom_config = NewLNSConfig(
        lns_options={
            "new_opt": True, 
            "declarative": True, 
            "seed": 123, 
            "max_steps": 5
        })

    lns = LNS(["examples/golf_demo.lp"], cl_config)
    lns.main()

if __name__ == "__main__":
    main()
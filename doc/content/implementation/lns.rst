.. _ref_lns:

LNS
====

.. currentmodule:: mod_lns.lns_config

.. note::

    The default LNS object uses the default :class:`LNSConfig` configuration and has the
    following default parameters: (parameters are going to be reworked in the near future)

    .. code-block:: python

        self.param_values: Dict[str, Any] = {
            "files": files,                     # Encodings set during initialization, List[String]
            "seed": None,                       # Seed used both for solving and random relaxation, Int
            "relax_rate": 0.2,                  # Relax rate, Float
            "max_steps": "2000",                # Step limit for the search, non-int string for no limit, Int,Str
            "solve_time_limit": 20,             # Time limit for the individual solve call in seconds, Int
            "overall_time_limit": 600,          # Time limit for the entire search in seconds, Int
            "stuck_after_no_improv": None,      # After how many iterations without improvement the
                                                #  search is determined as stuck, 
                                                #  non-int string for no limit, Int,Str
            "start_sol": None,                  # Start solution, fixed during first solve call, String
            "vari_accept": 0,                   # New solution is accepted if given variability is
                                                # achieved, 0 = always accept, should be lower than 
                                                # relax rate, Float
            "base_relax_rate": 0                # base relax rate applied on top of declarative relaxation, Float
        }

    .. currentmodule:: mod_lns.lib
    
    The default configuration uses the :class:`solvers.clingo_solver.ClingoSolver` solver and
    the :class:`strategies.default_strategy.DefaultStrategy`. 
    
    The following solver/strategy modifications are supported:
        - "heuristics": Atoms are fixed using heuristics
        - "constrained": Constrained LNS approach
        - "declarative": Declarative relaxation of atoms

.. currentmodule:: mod_lns.lns

.. autoclass:: LNS
    :members:

.. currentmodule:: mod_lns.lns_config

.. autoclass:: LNSConfig
    :members:

.. currentmodule:: mod_lns.__init__

.. autoclass:: Model
    :members:

.. _ref_lns:

LNS
====

.. currentmodule:: mod_lns.lib

.. note::

    The default LNS object uses the :class:`solvers.clingo_solver.ClingoSolver` solver and
    :class:`strategies.classic_weighted_sum_rnd.ClassicWeightedSumRnd` strategy and
    has the following default parameters:

    .. code-block:: python

        self.param_values: Dict[str, Any] = {
            "files": files,                     # Encodings set during initialization, List[String]
            "seed": None,                       # Seed used both for solving and random relaxation, Int
            "relax_rate": 0.1,                  # Relax rate, Float
            "max_steps": 2000,                  # Step limit for the search, non-int string for no limit, Int,Str
            "clingo_args": {"rand-freq": 0.18},  # Additional clingo arguments, Dict[String, Any]
            "solve_time_limit": 20,             # Time limit for the individual solve call in seconds, Int
            "overall_time_limit": 600,          # Time limit for the entire search in seconds, Int
            "stuck_after_no_improv": None,      # After how many iterations without improvement the
                                                #  search is determined as stuck, 
                                                #  non-int string for no limit, Int,Str
            "start_sol": None,                  # Start solution, fixed during first solve call, String
            "vari_accept": 0,                   # New solution is accepted if given variability is
                                                # achieved, 0 = always accept, should be lower than 
                                                # relax rate, Float
            "pre_files": [],                    # ASP files used for pre-solving, List[String]
            "pre_tl": 1800,                     # Time limit for pre-solving in seconds, Int
            "base_relax_rate": 0                # base relax rate applied on top of declarative relaxation, Float
        }

.. currentmodule:: mod_lns.__init__

.. autoclass:: LNS
    :members:

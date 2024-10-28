.. _ref_lns:

LNS
====

.. currentmodule:: large_neighbourhood_search.lib

.. note::

    The default LNS object uses the :class:`solvers.clingo_solver.ClingoSolver` solver and
    :class:`strategies.classic_weighted_sum_rnd.ClassicWeightedSumRnd` strategy and
    has the following default parameters:

    .. code-block:: python

        self.param_values: Dict[str, Any] = {
            "files": files,                     # Encodings set during initialization, List[String]
            "seed": None,                       # Seed used both for solving and random relaxation, Int
            "relax_rate": 0.2,                  # Relax rate, Float
            "max_steps": 2000,                  # Step limit for the search, None for no limit, Int
            "clingo_args": {"rand-freq": 0.8},  # Additional clingo arguments, Dict[String, Any]
            "solve_time_limit": 20,             # Time limit for the individual solve call in seconds, Int
            "overall_time_limit": 600,          # Time limit for the entire search in seconds, Int
            "stuck_after_no_improv": 1000,      # After how many interations without improvement the
                                                #  search is determined as stuck, Int
            "start_sol": None,                  # Start solution, fixed during first solve call, String
            "vari_accept": 0,                   # New solution is accepted if given variability is
                                                # achieved, 0 = always accept, should be lower than 
                                                # relax rate, Float
            "pre_files": [],                    # ASP files used for pre-solving, List[String]
            "pre_tl": 1800,                     # Time limit for pre-solving in seconds, Int
        }

.. currentmodule:: large_neighbourhood_search.__init__

.. autoclass:: LNS
    :members:

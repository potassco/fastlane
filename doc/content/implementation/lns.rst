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
            "files": files,                     # Encodings set during initialization
            "seed": None,                       # Seed used both for solving and random relaxation
            "relax_rate": 0.2,                  # Relax rate
            "max_steps": 2000,                  # Step limit for the search, None for no limit
            "clingo_args": {"rand-freq": 0.8},  # Additional clingo arguments
            "solve_time_limit": 20,             # Time limit for the individual solve call in seconds
            "overall_time_limit": 600,          # Time limit for the entire search in seconds
            "stuck_after_no_improv": 1000,      # After how many interations without improvement the
                                                #  search is determined as stuck
            "start_sol": None,                  # Start solution, fixed during first solve call
            "vari_accept": 0,                   # New solution is accepted if given variability is
                                                # achieved, 0 = always accept, should be lower than 
                                                # relax rate
        }

.. currentmodule:: large_neighbourhood_search.__init__

.. autoclass:: LNS
    :members:

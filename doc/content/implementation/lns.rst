.. _ref_lns:

LNS
====

.. currentmodule:: mod_lns.lib.strategies.default_strategy

.. note::

    The default LNS object uses the default strategy :class:`DefaultStrategy` with its :class:`LNSConfig`
    configuration class and has the following default parameters:

    .. code-block:: python

        # utils
        log_level: int = 30

        # general configuration
        solver: SolverInterface = ClingoSolver()    # Solver to be used
        seed: Optional[int] = None                  # Seed used for both solving and random relaxation
        time_limit: Optional[int] = None            # Overall time limit for the search in seconds
        max_steps: Optional[int] = None             # Step limit for the search
        relax_rate: Optional[int] = None            # Relax rate in percent
        status_interval: int = 50                   # Interval in steps for logging the current status
        preset: Optional[str] = None                # Preset configuration to be applied

        # init solver configuration
        init_time_limit: Optional[int] = None       # Time limit for the initial solve call in seconds
        init_solve_limit: Optional[str] = None      # Stop initial solve call after this many conflicts
                                                    # and restarts, "umax,umax" for no limit

        # lns configuration
        constrained: bool = False                   # Use constrained LNS approach
        declarative: bool = False                   # Use declarative relaxation of atoms
        accept_variability: int = 0                 # New solution is accepted if given variability between
                                                    # new and current solution is achieved,
                                                    # 0 = always accept, should be lower than relax rate

        # lns solver configuration
        lns_time_limit: Optional[int] = None        # Time limit for the iterative solve calls in seconds
        lns_solve_limit: Optional[str] = None       # Stop iterative solve calls after this many conflicts
                                                    # and restarts, None or "umax,umax" for no limit


    Additional default parameters can be set using the `preset` argument/option. The `basic`
    preset has the following values:

    .. code-block:: python

        # basic preset
        # general configuration
        time_limit: int = 600
        max_steps: int = 2000
        relax_rate: int = 20

        # init solver configuration
        init_time_limit: int = 20
        init_solve_limit: Optional[str] = "2500000,5000"
        
        # lns solver configuration
        lns_time_limit: Optional[int] = 20
        lns_solve_limit: Optional[str] = "2500000,5000"
 

    .. currentmodule:: mod_lns.lib

    The default configuration uses the :class:`solvers.clingo_solver.ClingoSolver` solver and
    the :class:`strategies.default_strategy.DefaultStrategy`.

.. currentmodule:: mod_lns.lns

.. autoclass:: LNS
    :members:

.. currentmodule:: mod_lns.__init__

.. autoclass:: Model
    :members:

.. autoclass:: Timer
    :members:

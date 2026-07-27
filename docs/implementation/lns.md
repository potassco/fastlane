# LNS

This page gives an overview of the `LNS` class with all its methods.
If you want to modify the LNS adjusting these methods is the best start to do so.
Most LNS parameters are stored inside a `LNSOptions` instance. Default values can be accessed
via the provided presets.  

!!! note

    The `LNSOptions` class has the following attributes:

    ```python

    # utils
    log_level: int = 30

    # general options
    solver: Solver = ClingoSolver()             # Solver to be used
    seed: Optional[int] = None                  # Seed used for both solving and random destruction
    time_limit: Optional[int] = None            # Overall time limit for the search in seconds
    max_steps: Optional[int] = None             # Step limit for the search
    status_interval: int = 50                   # Interval in steps for logging the current status
    parallel_mode: Optional[str] = None         # Clingo parallel mode, see clingo -t option
    clingo_args: Optional[str] = None           # Additional arguments passed to the solver
    context: Any = None                         # Solving context
    minimize_variable: Optional[Symbol] = None  # Minimize variable for clingo-dl optimization
    preset: Optional[str] = None                # Preset to be applied

    # adaptive options
    lex_weight: int = 1000                      # Weight factor for scalarizing lexicographic costs
    learning_rate: float = 0.5                  # learning rate for updating config weights
    default_adaptive_strategy_name: str = "static" 
                                                # default adaptive strategy for selecting LNS
                                                # configurations in each iteration

    # init solver configuration
    init_time_limit: Optional[int] = 20         # Time limit for the initial solve call in seconds
    init_solve_limit: Optional[str] = None      # Stop initial solve call after this many conflicts
                                                # and restarts, None or "umax,umax" for no limit
    init_cutoff: Optional[int] = None           # Time limit to find new model during initial solving
    init_configuration: Optional[str] = None    # More options passed to the solver
    init_opt_strategy: Optional[str] = None
    init_opt_heuristic: Optional[str] = None
    init_restart_on_model: Optional[bool] = None
    init_opt_mode: Optional[str] = None

    # lns configuration
    constrained: bool = False                   # Use constrained LNS approach
    destruction: tuple[str, int] = ("simple", 20) 
                                                # Destruction approach ["simple","declarative"] and
                                                # destruction percent for "simple" destruction,
                                                # "auto" for automatic destruction rate
    auto_converter: AutoDestructionConverter = LastImprovementDestructionConverter()
                                                # Automatic destroy percentage converter
    fix: str = "assumptions"                    # How to fix atoms ["assumptions", "heuristics"]
    accept_variability: int = 0                 # New solution is accepted if given variability between
                                                # new and current solution is achieved in percent,
                                                # 0 = always accept, should be lower than destruction rate
    accept_improvement: int = 0                 # New solution is accepted if threshold is passed in percent
                                                # 20 = solution can be upto 20% worse and still accepted
                                                # 0 = solution has to be strictly better

    # lns solver configuration
    lns_time_limit: Optional[int] = 20          # Time limit for the iterative solve calls in seconds
    lns_solve_limit: Optional[str] = UNSET      # Stop iterative solve calls after this many conflicts
                                                # and restarts, None or "umax,umax" for no limit
    lns_cutoff: Optional[int] = None            # Time limit to find new model during initial solving
    lns_configuration: Optional[str] = None     # More options passed to the solver
    lns_opt_strategy: Optional[str] = None
    lns_opt_heuristic: Optional[str] = None
    lns_restart_on_model: Optional[bool] = None
    lns_heuristic: Optional[str] = "Domain"
    lns_opt_mode: dict[str, Optional[str]] = {"mode": None, "nf": None, "modifier": None}

    lns_time_limit_increase_rate: int = 0       # Increase lns solver time limit after each iteration
                                                # by given percent
    lns_solve_limit_increase_rate: int = 0      # Increase lns solver solve limit after each iteration
                                                # by given percent
    lns_cutoff_threshold: Optional[int] = None  # Increase cutoff after <n> times no better solution
                                                # could be found
    lns_cutoff_increase_rate: int = 0           # Increase lns solver cutoff after each iteration by
                                                # given percent
    ```

    `UNSET` can used as a marker to differentiate between parameters that were not set and those
    that were explicitly set to `None`. Before starting the search, all remaining `UNSET` parameters
    will be set to `None`.
    Additional default parameters can be set using the `preset` argument/option.
    Use `mod_lns -h` to see all available presets and their parameter values.

::: mod_lns.lns.LNS


## Helper classes

::: mod_lns.Model

::: mod_lns.Timer

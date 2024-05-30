.. _ref_lns:

LNS
====

.. currentmodule:: large_neighbourhood_search.__init__

.. note::

    The default LNS object contains the following parameter values.
    These can be changed by using the :meth:`get_params` method.

    .. code-block:: python

        self.param_values: Dict[str, Any] = {
            "files": files,                     # Encodings set during initialization
            "seed": None,                       # Seed used both for solving and random relaxation
            "relax_rates": [0.2, 0.4, 0.6],     # Relax rates, search starts with the first one 
            "bound": 2000,                      # Step limit for the search, None for no limit
            "switch_rr_after_no_improv": 3,     # Switch relax rate to the next one after given amount
                                                #   of no improvements
            "clingo_args": {"rand-freq": 0.8},  # Additional clingo arguments
            "time_limit": 20,                   # Time limit for the individual solve call in seconds
            "overall_time_limit": 600,          # Time limit for the entire search in seconds
                                                #   solve calls can be made any time before this limit
                                                #   with their full time, which may lead to exceeding
                                                #   this limit by the amount specified above
        }

.. autoclass:: LNS
    :members:

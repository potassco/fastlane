Usage
============

While this project is mainly build as its usage as an easily modifiable api, 
it can still be used on its own with the provided features described below.
For all options supported during the default module execution use:

.. code-block:: console

    $ large_neighbourhood_search -h


For finer control over the performed Large-Neighbourhood-Search (LNS) this module should be used as an api.
During initialization of the LNS object all callables, which should be used during execution can be replaced.
Some example callables can be found in the :code:`lib` submodule. An example of the LNS initialization can be seen below
or in :code:`./examples/demo.py`:

.. code-block:: python

    from large_neighbourhood_search import LNS
    from large_neighbourhood_search.lib.lns_functions import check_stop_time

    lns = LNS(
        ["./examples/golf.lp"],             # ASP encoding
        {"check_stop": check_stop_time},    # Callable dictionary
        42,                                 # Seed
        [0.2],                              # Relax rate(s)
        None                                # clingo arguments
    )

Additional parameters such as the step limit for the LNS can be set using the :code:`set_params()` method.

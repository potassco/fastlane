Usage
============

While this project is mainly build as its usage as an easily modifiable api, 
it can still be used on its own, but heavily limited as described below.
For all options supported during the default module execution use:

.. code-block:: console

    $ large_neighbourhood_search -h

The direct execution supports only a default LNS using hard constraints and a random relaxation of shown atoms.
The search is limited to 2000 steps and relax rates of 0.2, 0.4 and 0.6, which are switched after 3 consecutive
failed attempts respectively, to improve the solution. Additional clingo arguments can be set after the default options.

For finer control over the performed Large-Neighbourhood-Search (LNS) this module should be used as an api.
During initialization of the LNS object, all callables, which will be used during execution, can be replaced and
are further explained :ref:`here<ref_call>`.
Some example callables can be found in the :ref:`lib<ref_lib>` submodule. Additional parameters such as relax rates or
the step limit for the LNS can be set using the :code:`set_params()` method. An example of the LNS initialization can be seen below
or in :code:`./examples/demo.py`:

.. code-block:: python

    from large_neighbourhood_search import LNS
    from large_neighbourhood_search.lib.lns_functions import check_stop_time

    lns = LNS(
        ["./examples/golf.lp"],             # ASP encoding
        {"check_stop": check_stop_time},    # Callables dictionary
        None                                # clingo arguments
    )
    lns.set_params({"seed": 123})


At the moment clingo and clingo-dl are supported via their respective functions :code:`setup_clingo()`, :code:`repair_clingo()` 
and :code:`setup_clingo_dl()`, :code:`repair_clingo_dl()`.

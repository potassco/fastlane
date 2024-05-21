Usage
============

While this project is mainly build as its usage as an easily modifiable api, 
it can still be used on its own, but heavily limited as described below.
For all options supported during the default module execution use:

.. code-block:: console

    $ large_neighbourhood_search -h

.. currentmodule:: large_neighbourhood_search.__init__

The direct execution supports only a default LNS using hard constraints and a random relaxation of shown atoms.
The search is limited to 2000 steps and relax rates of 0.2, 0.4 and 0.6, which are switched after 3 consecutive
failed attempts respectively, to improve the solution. Additional clingo arguments can be set after the default options.

For finer control over the performed Large-Neighbourhood-Search (LNS) this module should be used as an api.
During initialization of the LNS object, all callables, which will be used during execution, can be replaced and
are further explained :ref:`here<ref_call>`.
Some example callables can be found in the :ref:`lib<ref_lib>` submodule. Additional parameters such as relax rates or
the step limit for the LNS can be set using the :meth:`set_params` method. An example of the LNS initialization can be seen below
or in :file:`./examples/demo.py`:

.. code-block:: python

    from large_neighbourhood_search import LNS
    from large_neighbourhood_search.lib.lns_functions import check_stop_time

    lns = LNS(
        ["./examples/golf.lp"],             # ASP encoding
        {"check_stop": check_stop_time},    # Callables dictionary
        None                                # clingo arguments
    )
    lns.set_params({"seed": 123})

.. currentmodule:: large_neighbourhood_search.lib.theory

At the moment clingo and clingo-dl are supported via their respective functions :func:`setup_clingo`, :func:`repair_clingo` 
and :func:`setup_clingo_dl`, :func:`repair_clingo_dl`.

.. _ref_enc:

Encoding
----------

.. currentmodule:: large_neighbourhood_search

For a correct program execution the ASP encoding has to contain some form of derivation for the :code:`_opt(I,(O,W))` predicate
to indicate optimization criteria. An example definition can be seen in :file:`./examples/golf.lp`.

.. code-block::
    
    _opt(
            I,      % Unique identifier
            (
                M,  % Multiplier, used to implement lexicographic ordering
                W   % Weight
            )
        )
        :- <BODY>.

By default this project performs only minimization. Maximization with only minor changes can be achieved by
multiplying the weight :code:`W` by -1.
To make changes, on how the optimization is handled, one has to edit :func:`lib.lns_utils.calculate_opt_val`
and :func:`lib.search.get_first_solution_hard_constraint` if hard constraints are used.

When using :func:`lib.search.relax_declarative`, :code:`_lns_select/1` and :code:`_lns_fix/2` have to be used
in the encoding. While :code:`_lns_select/1` selects a set of terms, :code:`_lns_fix/2` maps atoms those terms,
that should be fixed if the corresponding atom is selected. During LNS a random number of selected terms is then chosen.
An example can be found in :file:`./examples/golf.lp`, where weeks :code:`W` are selected and mapped to
a fixation of all plays in the corresponding week.

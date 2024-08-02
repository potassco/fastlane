Usage
============

While this project is mainly build to be used as an easily modifiable framework, 
it can still be used on its own, but heavily limited, as described below.
For all options supported during the default module execution use:

.. code-block:: console

    $ large_neighbourhood_search -h

.. currentmodule:: large_neighbourhood_search.__init__

The direct execution supports only a default classic LNS using weighted sums and a random relaxation of shown atoms.
The search is limited to 2000 steps or 10 min with 20s per solve call and a relax rate of 0.2. The search is interrupted,
if no better solutions is found after 1000 consecutive steps.

For finer control over the performed Large-Neighbourhood-Search (LNS) this module should be used as a framework.
During initialization of the LNS object, the solver and strategy used during execution can be replaced.

The solver and strategy should be implemented according to the interfaces described :ref:`here<ref_inter>` and
have to implement all abstract methods.
Some example implementations can be found in the :ref:`lib<ref_lib>` submodule. 

Additional parameters such as the relax rate or
the step limit for the search can be set during initialization or using the :meth:`set_params` method. 
An example of the LNS initialization can be seen below or in :file:`./examples/demo.py`:

.. code-block:: python

    from large_neighbourhood_search import LNS
    from large_neighbourhood_search.lib.solvers.clingo_dl_solver import ClingoDLSolver
    from large_neighbourhood_search.lib.strategies.classic_lexicographic_rnd import ClassicLexiRnd

    lns = LNS(
        ["./examples/golf.lp"],     # ASP encoding
        ClingoDLSolver(),           # Solver
        ClassicLexiRnd(),           # Strategy
        {"seed": 123},              # Additional parameters
    )

.. _ref_enc:

Encoding
----------

.. currentmodule:: large_neighbourhood_search

For a correct program execution the ASP encoding has to contain some form of derivation for the :code:`_lns_penalty(N,I,W)` predicate
to indicate optimization criteria and :code:`_lns_priority(N,P)` facts to denote their priority. An example definition can be seen in :file:`./examples/golf.lp`.

.. code-block::
    
    _lns_priority(
        N,      % Name of the optimization criteria
        P       % Priority of the criteria (greater value = higher priority)
    ).
    _lns_penalty(
        N,      % Name of the optimization criteria
        I,      % Unique identifier
        W       % Weight of the criteria
    ) :- <BODY>.

By default this project performs minimization using weighted sums, where the priority is simply ignored.
Alternatively minimization with lexicographic optimization is also supported.

When using :func:`lib.relaxation.relax_declarative`, :code:`_lns_select/1` and :code:`_lns_fix/2` have to be used
in the encoding. While :code:`_lns_select/1` selects a set of terms, :code:`_lns_fix/2` maps atoms those terms,
that should be fixed if the corresponding atom is selected. During LNS a random number of selected terms is then chosen.
An example can be found in :file:`./examples/golf.lp`, where weeks :code:`W` are selected and mapped to
a fixation of all plays in the corresponding week.

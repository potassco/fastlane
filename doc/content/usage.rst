.. _ref_usage:

Usage
============

While this project is mainly build to be used as an easily modifiable framework, 
it can still be used on its own with the provided example classes, as described below.
For all options supported during default module execution use:

.. code-block:: console

    $ mod_lns -h

.. currentmodule:: mod_lns.__init__

The default parameters make use of classic LNS using assumptions and a random relaxation of shown atoms.
The search is limited to 2000 steps or 10 min with 20s per solve call and a relax rate of 0.2.

For finer control over the performed Large-Neighbourhood-Search (LNS) this module should be used as a framework.
During initialization of the LNS object, a LNSConfig object can be passed to modify or replace the used solver,
strategy and lns parameters.

Any solver and strategy should be implemented according to the interfaces described :ref:`here<ref_inter>` and
have to implement all abstract methods.
Some default implementations can be found in the :ref:`lib<ref_lib>` submodule. 

Additional parameters such as the relax rate or
the step limit for the search can be set during initialization or using the :meth:`set_params` method. 
An example of the LNS initialization can be seen below or in :file:`./examples/demo.py`. For a more detailed and
step by step introduction to the framework look :ref:`here<ref_guide>`.

.. code-block:: python

    from mod_lns.lns import LNS
    from mod_lns.lns_config import LNSConfig
    from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver

    lns = LNS(
        ["./examples/golf.lp"],         # ASP encoding
        LNSConfig(                      # LNSConfig object
            lns_options={               # lns search parameters
                "seed"=123,             # set seed
            },
            solver=ClingoDLSolver(),    # change solver
        )
    )

.. _ref_enc:

The same search can be performed through the command line as follows:

.. code-block:: console

    $ mod_lns -i ./examples/golf.lp --seed=123 --solver=ClingoDLSolver 

Encoding
----------

.. currentmodule:: mod_lns

The encodings should contain some kind of optimization statement or soft constraint. The lns framework will work
with the solution cost derived by the solver.

When using :func:`lib.relaxation.relax_declarative`, :code:`_lns_select/1` and :code:`_lns_fix/2` have to be used
in the encoding. While :code:`_lns_select/1` selects a set of terms, :code:`_lns_fix/2` maps atoms those terms,
that should be fixed if the corresponding atom is selected. During LNS a random number of selected terms is then chosen.
An example can be found in :file:`./examples/golf.lp`, where weeks :code:`W` are selected and mapped to
a fixation of all plays in the corresponding week.

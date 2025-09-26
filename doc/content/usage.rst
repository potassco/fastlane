.. _ref_usage:

Usage
============

This framework can be used both as a command line tool and as a python module.
When using as a command line tool use the `-h` flag to see all available options.
Since different strategies support wildly different parameters, strategies are implemented as
subprograms.  
To see all available options for specific strategies use the `-h` flag after
selecting the corresponding subprogram as seen below:

.. code-block:: console

    $ mod_lns -h
    $ mod_lns examples/golf.lp default -h

.. currentmodule:: mod_lns.__init__

The framework currently supports implementation of the clingo, clingo-dl and clingcon solvers,
a default strategy for basic LNS and heulingo a LNS approach using heuristics and a prioritized search.
Both strategies can be used in combination with any solver. 

For finer control one can implement their own solver and/or strategy or modify existing ones through inheritance.

Any solver and strategy should be implemented according to the interfaces described :ref:`here<ref_inter>` and
has to implement all abstract methods.
The implementations of provided solvers and strategies can be found in the :ref:`lib<ref_lib>` submodule.

When using the framework as a python module, the LNS object has to be initialized with the encoding files and the
strategy. After the initialization of the strategy, parameters can be set through the strategy's configuration class.
Alternatively, parameters can be passed during initialization of the `LNS` object by using a Namespace object.
An example of the LNS initialization can be seen below or in :file:`./examples/demo.py`. For a more detailed and
step by step introduction to the framework look :ref:`here<ref_guide>`.

.. code-block:: python

    from argparse import Namespace
    from mod_lns.lns import LNS
    from mod_lns.lib.strategies.default_strategy import DefaultStrategy, LNSConfig
    from mod_lns.lib.solvers.clingo_dl_solver import ClingoDLSolver

    strategy = DefaultStrategy()
    strategy.config = LNSConfig(solver=ClingoDLSolver(), seed=123)
    lns = LNS(
        ["./examples/golf.lp"],         # ASP encoding
        strategy,                       # strategy to be used
        Namespace(                      # set additional parameters
            time_limit=60,              # overall time limit in seconds
        )
    )

.. _ref_enc:

The same search can be performed through the command line as follows:

.. code-block:: console

    $ mod_lns ./examples/golf.lp default --solver=clingo-dl --seed=123 --time-limit=60

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

.. note::
    For heulingo to function correctly additional helper atoms have be defined in one of the input encodings.
    These include :code:`_lnps_project/2`, :code:`_lnps_destroy/4` and :code:`_lnps_prioritize/4`. For more
    information check the heulingo documentation. An example can be found in :file:`./examples/golf_lnps.lp`.

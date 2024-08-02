.. _ref_lib:

lib
===============


This library contains multiple example implementations of the Solver- and StrategyInterfaces and 
some additional helper functions which can be used for LNS.


.. note::
    When using :func:`lib.relaxation.relax_declarative`, :code:`_lns_select/1` and :code:`_lns_fix/2` have to be used
    in the encoding. While :code:`_lns_select/1` selects a set of terms, :code:`_lns_fix/2` maps atoms to those terms,
    that should be fixed if the corresponding term is selected. During LNS a random number of terms are selected and
    the corresponding atoms fixed.
    An example can be found in :file:`./examples/golf.lp`, where weeks :code:`W` are selected and mapped to
    a fixation of all plays in the corresponding week.

.. toctree::
    :maxdepth: 1
    
    solvers.rst
    utils.rst
    strategies.rst
    relaxation.rst
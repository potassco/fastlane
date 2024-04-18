LNS functions
======================

This library file contains multiple example functions which can be used for LNS.

.. automodule:: large_neighbourhood_search.lib.lns_functions
    :members:


.. note::
    Functions :code:`check_better_always`, :code:`better_solution_found_hard_constraint` and :code:`get_first_solution_hard_constraint`
    should be used together. Likewise functions :code:`check_better_classic`, :code:`better_solution_found_classic` and
    :code:`get_first_solution_classic` should be used together.

    When using :code:`relax_declarative`, to be relaxed atoms have to be selected using :code:`_lns_select/1` and optionally a subset
    fixed using :code:`_lns_fix/2`.
    An example can be found in :file:`./examples/golf.lp`


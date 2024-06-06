.. _ref_lib:

lib
===============


This library file contains multiple example functions which can be used for LNS.


.. note::
    Functions :code:`check_better_always()`, :code:`better_solution_found_hard_constraint()` and :code:`get_first_solution_hard_constraint()`
    should be used together. Likewise functions :code:`check_better_classic()`, :code:`better_solution_found_classic()` and
    :code:`get_first_solution_classic()` should be used together.

    Solver specific functions should never be mixed.

    When using :func:`lib.search.relax_declarative`, :code:`_lns_select/1` and :code:`_lns_fix/2` have to be used
    in the encoding. While :code:`_lns_select/1` selects a set of terms, :code:`_lns_fix/2` maps atoms those terms,
    that should be fixed if the corresponding atom is selected. During LNS a random number of selected terms is then chosen.
    An example can be found in :file:`./examples/golf.lp`, where weeks :code:`W` are selected and mapped to
    a fixation of all plays in the corresponding week.

    Function :code:`check_stop_time()` is not an exact limit, since the check occurs only between solve calls.
    For a true time limit, a multi-process solution is required.


.. toctree::
    :maxdepth: 1
    
    boundary.rst
    lns_utils.rst
    search.rst
    theory.rst
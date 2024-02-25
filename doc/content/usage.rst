Usage
============

This project allows a multitude of options to customize the LNS. For a list of all possible options run:

.. code-block:: console

    $ large_neighbourhood_search -h


For complete control of search parameters, a parameter file has to be used. An example of such parameter file can be created at the target 
directory using:

.. code-block:: console

    $ large_neighbourhood_search --gen_example DIR


.. note::
    
    The use of a parameter file is still under development and only supported in a bare-bones state.


Example
-------

An example call for LNS using hard constraints in declarative mode with a constant relax rate of 0.4  on the provided social golfer example would look like this:

.. code-block:: console

    $ large_neighbourhood_search -i ./examples/golf.lp --declarative -rr 0.4 


Declarative mode
----------------

When using declarative mode to be relaxed atoms have to be selected using :code:`_lns_select/1` and optionally a subset fixed using :code:`_lns_fix/2`.
An example can be found in :file:`./examples/golf.lp`

